"""altium_unstick.py - find why Altium's script engine is stuck and free it without the user (TOOL-21). Windows only.

Usage:
  python altium_unstick.py                 report only: Altium instances and every dialog Altium shows, with its cause
  python altium_unstick.py --fix           answer the dialogs that are safe to answer, close a duplicate Altium that a
                                           command-line handoff started, then report again
  python altium_unstick.py --json          the report as JSON (for agents)
  python altium_unstick.py --today         how many stuck runs the log holds for today (TOOL-20: stop after 2 per stage)
Exit 0 = Altium is free (nothing stuck, or everything fixed); 1 = still stuck or a step only the user can do
(the last line says which); 0 with "skipped" on other systems.

What it recognises (wedge study 2026-11-07, AD26 26.11.1) and what --fix does:
  script_error      dialog 'X2' "...Continue execution?" (a runtime error)   Cancel; then the "Operation aborted" box closes.
                                                                             Cancel stops the script fully; OK would run on.
  bom               the same with "Unknown identifier: ï" (file saved with a UTF-8 BOM)   Cancel; fix: save without BOM
  aborted           'Error' box "Operation aborted" (after a Cancel)         close
  template          "Expression expected but % found": the coffee server running is older than its files (an update
                    while Claude Code ran); every coffee script fails       close; fix: restart Claude Code
  engine_busy       "not able to execute more than one script": the eda-agent loop holds the engine   close; the loop
                    itself is released only by the user or eda-agent app_detach (it SAVES documents: ask first)
  second_instance   "There is another instance of running, but it is busy": an X2.exe command line ran while a dialog
                    was open, and started a second Altium                   close; end that new, empty X2.exe
  run_params        the script parameter form                               close
  eda_loop          the "EDA Agent" window: the loop is open (it blocks every other script, even when paused)   report
  unknown_modal     any other dialog                                         report: bridge.cmd popup unknown_modal
Never: X2.exe -REditScript:Stop (TOOL-18), opening or closing a design, pressing OK on a question, ending the
Altium that was running first. A paused debugger without a dialog is not visible here: bridge.cmd popup script_crashed.
Every finding and action is appended to logs\\altium_unstick.log.
"""
import argparse, datetime, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LOG = os.path.join(ROOT, "logs", "altium_unstick.log")
DUPLICATE_MAX_AGE_S = 600          # a handoff duplicate is seconds old; never end an Altium older than this

# (kind, test on (class, title, text), action, advice); first match wins
RULES = [
    ("bom", lambda c, t, x: "continue execution" in x and "unknown identifier: ï" in x, "cancel",
     "the script was saved with a UTF-8 byte-order mark: save it without BOM (kit pas_lint finds it)"),
    ("script_error", lambda c, t, x: "continue execution" in x, "cancel",
     "the script had a runtime error (line in the text): fix it before running it again (kit pas_lint)"),
    ("template", lambda c, t, x: "% found" in x or "%guard_seconds%" in x, "close",
     "the coffee server is older than its files (updated while Claude Code ran): restart Claude Code"),
    ("engine_busy", lambda c, t, x: "more than one script" in x or "another script" in x, "close",
     "the eda-agent loop holds the script engine: release it (eda-agent app_detach saves all documents: ask the user)"),
    ("second_instance", lambda c, t, x: "another instance" in x and "busy" in x, "close",
     "an X2.exe command line ran while a dialog was open: never call X2.exe while a dialog shows (TOOL-22)"),
    ("aborted", lambda c, t, x: "operation aborted" in x, "close", ""),
    ("run_params", lambda c, t, x: c == "TForm_RunScriptParameters", "close", ""),
    ("eda_loop", lambda c, t, x: "eda agent" in t, "none",
     "the eda-agent loop window is open: coffee scripts cannot run until it is released (ask the user first)"),
    ("aborted", lambda c, t, x: c == "TMessageForm" and t in ("error",) and not x, "close",
     "an error box without readable text (usually 'Operation aborted' after a Cancel)"),
]
DIALOG_CLASSES = ("#32770", "TMessageForm", "TForm_RunScriptParameters")
STUCK_KINDS = {"script_error", "bom", "template", "engine_busy", "second_instance", "unknown_modal", "eda_loop"}


def classify(win):
    """win: {cls, title, text, owned, owner_disabled} -> (kind, action, advice), or None for a window that is not a dialog."""
    c, t, x = win.get("cls", ""), (win.get("title") or "").lower(), (win.get("text") or "").lower()
    for kind, test, action, advice in RULES:
        if test(c, t, x):
            return kind, action, advice
    if c in DIALOG_CLASSES or (win.get("owned") and win.get("owner_disabled")):    # a modal disables its owner
        return "unknown_modal", "none", "a dialog the tool does not know: bridge.cmd popup unknown_modal"
    return None


def pick_duplicates(procs, second_pids, now):
    """procs: [{pid, started}] of X2.exe. The first-started Altium is kept; a later one is a duplicate to end only
    when it showed 'another instance ... busy' (proof it is a handoff) and is younger than DUPLICATE_MAX_AGE_S."""
    if len(procs) < 2:
        return [], []
    order = sorted(procs, key=lambda p: p.get("started") or 0)
    end, keep = [], []
    for p in order[1:]:
        young = p.get("started") is not None and now - p["started"] < DUPLICATE_MAX_AGE_S
        (end if p["pid"] in second_pids and young else keep).append(p["pid"])
    return end, keep


def log(rows):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(" | ".join(str(v).replace("\n", " ").replace("|", "/") for v in r) + "\n")
    except OSError:
        pass


def stuck_runs_today(path=LOG, today=None):
    today = today or datetime.date.today().isoformat()
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return 0
    return sum(1 for l in lines if l.startswith(today) and " | RUN | " in l and "stuck=0" not in l)


# ---- Windows part -------------------------------------------------------------------------------------------------
def _win():
    import ctypes
    from ctypes import wintypes as w
    u, k = ctypes.WinDLL("user32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
    proc_t = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    H = w.HWND                                             # 64-bit handles: declare types, never the int default
    for name, res, args in (("GetWindow", H, [H, w.UINT]), ("IsWindowEnabled", w.BOOL, [H]),
                            ("IsWindowVisible", w.BOOL, [H]), ("GetWindowTextLengthW", ctypes.c_int, [H]),
                            ("GetWindowTextW", ctypes.c_int, [H, w.LPWSTR, ctypes.c_int]),
                            ("GetClassNameW", ctypes.c_int, [H, w.LPWSTR, ctypes.c_int]),
                            ("GetWindowThreadProcessId", w.DWORD, [H, ctypes.POINTER(w.DWORD)]),
                            ("PostMessageW", w.BOOL, [H, w.UINT, w.WPARAM, w.LPARAM]),
                            ("EnumWindows", w.BOOL, [proc_t, w.LPARAM]),
                            ("EnumChildWindows", w.BOOL, [H, proc_t, w.LPARAM])):
        getattr(u, name).restype, getattr(u, name).argtypes = res, args
    k.OpenProcess.restype, k.OpenProcess.argtypes = w.HANDLE, [w.DWORD, w.BOOL, w.DWORD]
    k.CloseHandle.argtypes = [w.HANDLE]

    def text(h):
        n = u.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, b, n + 1)
        return b.value

    def cls(h):
        b = ctypes.create_unicode_buffer(256)
        u.GetClassNameW(h, b, 256)
        return b.value

    def pid_of(h):
        p = w.DWORD()
        u.GetWindowThreadProcessId(h, ctypes.byref(p))
        return p.value

    def children(h):
        out = []
        cb = proc_t(lambda c, _: (out.append(c), True)[1])
        u.EnumChildWindows(h, cb, 0)
        return out

    def started(pid):
        h = k.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return None
        try:
            ft = [w.FILETIME() for _ in range(4)]
            if not k.GetProcessTimes(h, *[ctypes.byref(f) for f in ft]):
                return None
            v = (ft[0].dwHighDateTime << 32) | ft[0].dwLowDateTime
            return v / 1e7 - 11644473600                   # FILETIME -> Unix seconds
        finally:
            k.CloseHandle(h)

    def post(h, msg, wp=0):
        return bool(u.PostMessageW(h, msg, wp, 0))

    return dict(u=u, proc_t=proc_t, text=text, cls=cls, pid_of=pid_of, children=children, started=started, post=post)


def x2_pids():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq X2.EXE", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    out = []
    for l in r.stdout.splitlines():
        f = [x.strip('"') for x in l.split('","')]
        if f and f[0].upper() == "X2.EXE" and len(f) > 1 and f[1].isdigit():
            out.append(int(f[1]))
    return out


def scan(W):
    pids = set(x2_pids())
    procs = [dict(pid=p, started=W["started"](p)) for p in sorted(pids)]
    wins = []

    def each(h, _):
        if W["u"].IsWindowVisible(h) and W["pid_of"](h) in pids:
            kids = W["children"](h)
            txt = "\n".join(t for t in (W["text"](c) for c in kids if W["cls"](c) in ("Static", "TLabel", "TMemo",
                                                                                      "TRichEdit", "Edit"))
                            if t)
            wins.append(dict(hwnd=h, pid=W["pid_of"](h), cls=W["cls"](h), title=W["text"](h), text=txt,
                             owned=bool(W["u"].GetWindow(h, 4)),
                             owner_disabled=bool(W["u"].GetWindow(h, 4)) and not W["u"].IsWindowEnabled(W["u"].GetWindow(h, 4)),
                             buttons=[W["text"](c) for c in kids if W["cls"](c) in ("Button", "TButton")]))
        return True

    W["u"].EnumWindows(W["proc_t"](each), 0)
    found = []
    for win in wins:
        c = classify(win)
        if c:
            win["kind"], win["action"], win["advice"] = c
            found.append(win)
    return procs, found


def act(W, win):
    if win["action"] == "cancel":
        return W["post"](win["hwnd"], 0x0111, 2)            # WM_COMMAND IDCANCEL
    if win["action"] == "close":
        return W["post"](win["hwnd"], 0x0010)               # WM_CLOSE
    return False


def report(procs, found, out=print):
    out(f"Altium instances: {len(procs)}" + (" (" + ", ".join(f"pid {p['pid']}" for p in procs) + ")" if procs else ""))
    for f in found:
        line = f.get("text", "").replace("\r", "").replace("\n", " / ")[:160]
        out(f"{'STUCK' if f['kind'] in STUCK_KINDS else 'BOX':5}  {f['kind']:15} pid {f['pid']} '{f['title']}': {line}"
            + (f"\n       cause: {f['advice']}" if f.get("advice") else ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--today", action="store_true")
    ap.add_argument("--passes", type=int, default=4, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if a.today:
        n = stuck_runs_today()
        print(f"altium_unstick: {n} stuck run(s) logged today" + (" - TOOL-20: after 2 in one stage, finish it offline"
                                                                  if n >= 2 else ""))
        return 0
    if os.name != "nt":
        print("altium_unstick: skipped (Windows only)")
        return 0
    W = _win()
    stamp = lambda: datetime.datetime.now().isoformat(timespec="seconds")
    procs, found = scan(W)
    first = list(found)
    done, second = [], set()
    if a.fix:
        for _ in range(a.passes):
            todo = [f for f in found if f["action"] != "none"]
            if not todo:
                break
            for f in todo:
                if f["kind"] == "second_instance":
                    second.add(f["pid"])
                ok = act(W, f)
                done.append(f)
                log([(stamp(), "ACT", f["kind"], f["action"] + ("" if ok else " FAILED"), f["pid"], f["title"], f["text"])])
            time.sleep(1.5)                                  # Cancel brings up "Operation aborted"
            procs, found = scan(W)
        end, keep = pick_duplicates(procs, second, time.time())
        for pid in end:
            for _ in range(10):                              # it often exits by itself once its box is closed
                if pid not in x2_pids():
                    break
                time.sleep(1)
            else:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
                log([(stamp(), "ACT", "second_instance", "ended duplicate X2.exe", pid, "", "")])
        procs, found = scan(W)
    stuck = [f for f in found if f["kind"] in STUCK_KINDS]
    advice = []
    if len(procs) > 1:
        advice.append(f"{len(procs)} Altium instances: save your work and close the newer one (TOOL-01)")
    advice += sorted({f["advice"] for f in stuck if f.get("advice")})
    for f in first:
        if f.get("advice") and f["kind"] in ("template", "bom", "engine_busy", "second_instance") and f["advice"] not in advice:
            advice.append("fixed now, but " + f["advice"])
    log([(stamp(), "RUN", f"stuck={len(stuck)}", f"found={len(first)}", f"fixed={len(done)}", f"x2={len(procs)}",
          "; ".join(advice))])
    blocked = bool(stuck) or len(procs) > 1
    if a.json:
        print(json.dumps(dict(instances=procs, found_first=[{k: v for k, v in f.items() if k != "hwnd"} for f in first],
                              acted=[f["kind"] for f in done], remaining=[{k: v for k, v in f.items() if k != "hwnd"}
                                                                          for f in found],
                              free=not blocked, advice=advice), indent=1, ensure_ascii=False))
    else:
        if a.fix and first:
            print(f"before: {len(first)} dialog(s); answered {len(done)}")
        report(procs, found)
        for x in advice:
            print(f"next: {x}")
        print("altium_unstick: " + ("still stuck" if blocked else "Altium is free") +
              ("" if a.fix or not found else " (run with --fix to answer the safe dialogs)"))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
