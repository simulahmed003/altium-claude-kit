"""first_run_test.py - run docs/FIRST_RUN_TESTS.md (bridge, guard hook, kill switch) with as little typing as possible.

Usage (Windows, from the workspace folder, Altium open with the eda-agent scripts installed):
  python tools\\scripts\\first_run_test.py            # all six tests, asks before anything that saves or kills
  python tools\\scripts\\first_run_test.py --only 1 2  # some tests
  python tools\\scripts\\first_run_test.py --yes      # no questions (app_detach SAVES modified Altium documents)

Live MCP calls go through `claude -p`, so the guard hook (tools/bridge/guard.ps1) decides and shows its popups
exactly as in a normal session; this script never talks to an MCP server directly.
Tests:
  1 bridge.cmd status prints without an error
  2 the eda-agent loop is "responding" (you start StartMCPServer in Altium when asked)
  3 one read-only altium-coffee call while the loop runs: did the guard ask, did Altium survive
  4 eda-agent app_detach (SAVES modified documents), then the loop must be "not responding"
  5 the two live servers' script projects cannot be mixed up in Altium (both are named Altium_API.PrjScr; that is
    safe while coffee runs its project by full path, finds its exchange folder by a fixed path, and calls no unit
    that the eda-agent project also has)
  6 kill switch: KILL.cmd, then .mcp.json disabled, lock present, MCP calls blocked, Altium untouched; REARM.cmd
Every result is printed and appended to logs/MCP_LOG.md. Exit 0 = all run tests PASS, 1 = any FAIL.
"""
import argparse
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coffee_script_rename  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LOG = os.path.join(ROOT, "logs", "MCP_LOG.md")
CLAUDE_TIMEOUT = 600          # the guard may wait on a popup
DONE = "TOOL RESULT RECEIVED"  # Claude prints this line only when the MCP tool really returned
TELL = (f" If the tool returned a result, print it and then a last line exactly '{DONE}'. If the call was blocked, "
        "refused or the tool is not available, print the reason verbatim and do NOT print that line. Do not retry "
        "and do not call any other tool.")


def tool_ran(out):
    return any(line.strip() == DONE for line in out.splitlines())


def parse_status(text):
    """bridge.cmd status output -> {'active bridge': 'none', 'eda-agent loop': 'responding', ...}"""
    out = {}
    for line in text.splitlines():
        m = re.match(r"\s*([^:]+?)\s*:\s*(.*)$", line)
        if m:
            out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


def clashes(eda_paths, coffee_paths):
    """Script project file names that both live servers install."""
    names = lambda ps: {os.path.basename(p).lower() for p in ps}
    return sorted(names(eda_paths) & names(coffee_paths))


def mixup_risks(eda_units, coffee_main, coffee_pas):
    """Ways Altium could run the wrong script project when both servers' projects share a name.
    eda_units: .pas file names of the eda-agent project; coffee_main: text of altium-mcp server/main.py;
    coffee_pas: {file name: text} of coffee's Pascal units. Empty list = no known way to mix them up.
    Same name is fine on its own: Altium keys open projects by full path (phase 0 test 5, 2026-10-13)."""
    risks = []
    procs = re.findall(r'ProcName="([^">]+)>', coffee_main)
    if not procs:
        risks.append("coffee main.py: no RunScript ProcName found (launch code changed, check it)")
    if re.search(r'RunScript\(ProjectName="\{', coffee_main) is None:
        risks.append("coffee main.py: RunScript no longer passes the script project by full path")
    eda = {u.lower() for u in eda_units}
    for unit in sorted(set(procs)):
        if unit.lower() + ".pas" in eda:
            risks.append(f"coffee calls unit {unit}, which the eda-agent project also has")
    main_unit = next((t for n, t in coffee_pas.items() if n.lower() == "altium_api.pas"), "")
    if not re.search(r"ROOT_DIR\s*:=\s*'[A-Za-z]:\\", main_unit):
        risks.append("coffee Altium_API.pas: exchange folder ROOT_DIR is not a fixed path any more")
    for n, t in coffee_pas.items():
        if re.search(r"(?<!\w)ScriptProjectPath\s*\(", re.sub(r"function\s+ScriptProjectPath", "", t)):
            risks.append(f"coffee {n} calls ScriptProjectPath (finds its project by name among open projects)")
    return risks


class Runner:
    def __init__(self, yes):
        self.yes = yes
        self.results = []

    # ---------- helpers ----------
    def cmd(self, name, *args, timeout=120):
        r = subprocess.run(["cmd", "/c", os.path.join(ROOT, name), *args], cwd=ROOT,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()

    def status(self):
        code, out = self.cmd("bridge.cmd", "status")
        return code, out, parse_status(out)

    def claude(self, prompt, allowed):
        exe = shutil.which("claude")
        if not exe:
            return 1, "claude not found on PATH"
        try:
            r = subprocess.run([exe, "-p", prompt, "--allowedTools", allowed, "--output-format", "text"],
                               cwd=ROOT, capture_output=True, text=True, timeout=CLAUDE_TIMEOUT)
            return r.returncode, (r.stdout + r.stderr).strip()
        except subprocess.TimeoutExpired:
            return 1, f"no answer from claude within {CLAUDE_TIMEOUT} s"

    def ask(self, question):
        if self.yes:
            return True
        return input(f"   {question} [y/N] ").strip().lower() == "y"

    def wait_user(self, what):
        if not self.yes:
            input(f"   {what}  Press Enter when done.")

    def record(self, n, ok, note):
        word = "PASS" if ok is True else "FAIL" if ok is False else "SKIP"
        self.results.append((n, word, note))
        print(f"{word}  test {n}: {note}")

    # ---------- tests ----------
    def t1(self):
        code, out, s = self.status()
        print("   " + out.replace("\n", "\n   "))
        self.record(1, code == 0 and "eda-agent loop" in s, f"bridge.cmd status exit {code}")

    def t2(self):
        _, _, s = self.status()
        if s.get("eda-agent loop") != "responding":
            self.wait_user("In Altium: File > Run Script > Altium_API > Dispatcher.pas > StartMCPServer > Run.")
            for _ in range(10):                     # the loop can take a few seconds to answer
                _, _, s = self.status()
                if s.get("eda-agent loop") == "responding":
                    break
                time.sleep(3)
        loop = s.get("eda-agent loop", "?")
        self.record(2, loop == "responding",
                    f"Altium running: {s.get('altium running', '?')}, eda-agent loop: {loop}")

    def t3(self):
        _, _, before = self.status()
        print("   asking Claude for one read-only altium-coffee call (the guard may show a popup: answer it)")
        code, out = self.claude("Call exactly one read-only altium-coffee tool, for example get_server_status."
                                + TELL, "mcp__altium-coffee")
        print("   " + out[-1500:].replace("\n", "\n   "))
        _, _, after = self.status()
        asked = "not asked (--yes)" if self.yes else self.ask("Did the guard show a popup asking you to release the eda-agent loop?")
        alive = after.get("altium running", "").lower() == "true"
        self.record(3, tool_ran(out) and alive,
                    f"loop before: {before.get('eda-agent loop')}, tool ran: {tool_ran(out)}, popup asked: {asked}, "
                    f"Altium running after: {after.get('altium running')}, active bridge: {after.get('active bridge')}")

    def t4(self):
        _, _, before = self.status()
        if before.get("eda-agent loop") != "responding":
            return self.record(4, False, "eda-agent loop is not running, so there is nothing to detach "
                                         "(start StartMCPServer, then run --only 2 4)")
        if not self.ask("app_detach SAVES every modified Altium document first. Run it?"):
            return self.record(4, None, "skipped by the user")
        code, out = self.claude("Call the altium-eda tool app_detach once." + TELL, "mcp__altium-eda__app_detach")
        print("   " + out[-1500:].replace("\n", "\n   "))
        _, _, s = self.status()
        loop = s.get("eda-agent loop", "?")
        self.record(4, tool_ran(out) and loop == "not responding",
                    f"app_detach ran: {tool_ran(out)}, eda-agent loop after: {loop}")

    def t5(self):
        home = os.path.expanduser("~")
        eda = glob.glob(os.path.join(home, "EDA Agent", "scripts", "**", "*.PrjScr"), recursive=True)
        cm = os.path.join(ROOT, "tools", "mcp", "altium-mcp")
        shipped = os.path.join(cm, "server", "AltiumScript", "Altium_API.PrjScr")
        coffee = coffee_script_rename.current_project(coffee_script_rename.default_config(), shipped)
        for p in eda:
            print(f"   eda-agent: {p}")
        print(f"   coffee runs: {coffee}")
        main_py = os.path.join(cm, "server", "main.py")
        if not eda or not os.path.isfile(coffee) or not os.path.isfile(main_py):
            return self.record(5, None, "script project of one server not found (eda-agent install-scripts or "
                                        "tools\\setup.ps1 not run?)")
        dup = clashes(eda, [coffee])
        eda_units = [os.path.basename(p) for p in glob.glob(os.path.join(home, "EDA Agent", "scripts", "**", "*.pas"),
                                                             recursive=True)]
        read = lambda p: open(p, encoding="utf-8", errors="replace").read()
        coffee_pas = {os.path.basename(p): read(p) for p in
                      glob.glob(os.path.join(cm, "server", "AltiumScript", "*.pas"))}
        risks = mixup_risks(eda_units, read(main_py), coffee_pas)
        for r in risks:
            print(f"   risk: {r}")
        self.record(5, not dup and not risks,
                    f"same project name in both servers: {dup or 'none'}"
                    + (" (fix: python tools\\scripts\\coffee_script_rename.py)" if dup else "")
                    + f", ways to mix them up: {'; '.join(risks) or 'none'}")

    def t6(self):
        if not self.ask("Engage the kill switch now (stops the MCP servers, never touches Altium; REARM follows)?"):
            return self.record(6, None, "skipped by the user")
        print("   running KILL.cmd (press OK on its popup)")
        self.cmd("KILL.cmd", timeout=300)
        lock = os.path.isfile(os.path.join(ROOT, "tools", "bridge", "KILLED.lock"))
        mcp_off = not os.path.isfile(os.path.join(ROOT, ".mcp.json"))
        _, _, s = self.status()
        code, out = self.claude("Call the altium-coffee tool get_server_status once." + TELL, "mcp__altium-coffee")
        blocked = not tool_ran(out)              # guard refusal or servers gone: either way nothing reached Altium
        alive = s.get("altium running", "").lower() == "true"
        print("   running REARM.cmd (press OK on its popup)")
        self.cmd("REARM.cmd", timeout=300)
        rearmed = os.path.isfile(os.path.join(ROOT, ".mcp.json")) and not os.path.isfile(
            os.path.join(ROOT, "tools", "bridge", "KILLED.lock"))
        self.record(6, lock and mcp_off and blocked and alive and rearmed,
                    f"lock: {lock}, .mcp.json disabled: {mcp_off}, MCP call blocked: {blocked}, "
                    f"Altium untouched: {alive}, rearmed: {rearmed}")

    def log(self):
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        new = not os.path.isfile(LOG)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG, "a", encoding="utf-8") as f:
            if new:
                f.write("# MCP log\n\n| time | event |\n|---|---|\n")
            for n, word, note in self.results:
                f.write(f"| {stamp} | first_run_test {n} {word}: {note.replace('|', '/')} |\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="+", type=int, choices=range(1, 7), help="run only these tests")
    ap.add_argument("--yes", action="store_true", help="do not ask (app_detach saves, kill switch runs)")
    a = ap.parse_args(argv)
    if os.name != "nt":
        print("first_run_test.py needs Windows with Altium Designer")
        return 1
    r = Runner(a.yes)
    for n in a.only or range(1, 7):
        print(f"\n== test {n} ==")
        try:
            getattr(r, f"t{n}")()
        except Exception as e:                      # one broken test must not hide the others
            r.record(n, False, f"error: {e}")
    r.log()
    fails = [x for x in r.results if x[1] == "FAIL"]
    print(f"\nfirst_run_test: {len(r.results)} tests, {len(fails)} FAIL (results appended to logs\\MCP_LOG.md)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
