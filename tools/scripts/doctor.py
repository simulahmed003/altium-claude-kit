"""doctor.py - session preflight: is this workspace ready for an Altium session (rules WF-10, WF-11)? Read-only.

Usage:
  python doctor.py                       all checks (fetches origin/main once to compare)
  python doctor.py --offline             skip the git fetch
  python doctor.py --folder "D:\\Work\\Acme\\Board1"
                                         also print the command that starts Claude Code here with that folder added
Checks (OK / WARN / FAIL, each with the fix to type in cmd.exe):
  1 Python 3.9 or newer
  2 .mcp.json in the workspace names altium-lib, altium-coffee and altium-eda (read only; never edited here)
  3 .claude/settings.json runs tools/bridge/guard.ps1, and that file exists
  4 git: behind / ahead of origin/main, uncommitted files (a stale copy makes new rules reuse taken IDs)
  5 rules VERSION here vs origin/main
  6 kill switch (tools/bridge/KILLED.lock)
  7 Altium instances (Windows: tasklist X2.EXE; more than one is a FAIL, TOOL-01)
  8 altium-lib config.json allowed_paths includes this workspace's library folder
Exit 0 when no FAIL, 1 otherwise. WARN never fails.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SERVERS = ("altium-lib", "altium-coffee", "altium-eda")


def git(*args, root=ROOT):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, what, fix=""):
        self.rows.append((level, what, fix))
        print(f"{level:<4}  {what}" + (f"\n      fix: {fix}" if fix else ""))

    @property
    def failed(self):
        return any(l == "FAIL" for l, _, _ in self.rows)


def check_python(rep):
    v = sys.version_info
    if v >= (3, 9):
        rep.add("OK", f"Python {v.major}.{v.minor}")
    else:
        rep.add("FAIL", f"Python {v.major}.{v.minor} is too old", "install Python 3.11 from python.org, tick 'Add to PATH'")


def check_mcp(rep, root):
    p = os.path.join(root, ".mcp.json")
    if not os.path.isfile(p):
        rep.add("FAIL", ".mcp.json missing: the Altium MCP servers will not load", f"cd /d {root} && powershell -File tools\\setup.ps1")
        return
    try:
        names = set(json.load(open(p, encoding="utf-8")).get("mcpServers", {}))
    except (ValueError, OSError) as e:
        rep.add("FAIL", f".mcp.json unreadable: {e}", "run tools\\setup.ps1 again")
        return
    miss = [s for s in SERVERS if s not in names]
    if miss:
        rep.add("WARN", f".mcp.json lacks {', '.join(miss)}", "run tools\\setup.ps1 (it re-registers the servers)")
    else:
        rep.add("OK", ".mcp.json names " + ", ".join(SERVERS)
                + " (they load only when Claude Code is started in this folder, WF-10)")


def check_hook(rep, root):
    p = os.path.join(root, ".claude", "settings.json")
    if not os.path.isfile(p):
        rep.add("WARN", ".claude/settings.json missing: no guard hook, no permissions", "run tools\\setup.ps1")
        return
    text = open(p, encoding="utf-8").read()
    if "guard.ps1" not in text:
        rep.add("FAIL", "the guard hook is not in .claude/settings.json", "see README.md 'hook'; run tools\\setup.ps1")
    elif "_tools" in text.replace("\\\\", "/").replace("\\", "/"):
        rep.add("FAIL", "the guard hook points to the old _tools folder (every Altium call would be blocked)",
                "python tools\\migrate_from_workspace.py")
    elif not os.path.isfile(os.path.join(root, "tools", "bridge", "guard.ps1")):
        rep.add("FAIL", "tools/bridge/guard.ps1 is missing", "git checkout -- tools\\bridge")
    else:
        rep.add("OK", "guard hook present")


def check_git(rep, root, offline):
    code, _ = git("rev-parse", "--is-inside-work-tree", root=root)
    if code:
        rep.add("WARN", "not a git repository: updates and rule versions cannot be checked")
        return None
    if not offline:
        code, _ = git("fetch", "-q", "origin", "main", root=root)
        if code:
            rep.add("WARN", "git fetch origin main failed (offline?); comparing with the last fetched copy")
    code, out = git("rev-list", "--left-right", "--count", "HEAD...origin/main", root=root)
    if code:
        rep.add("WARN", "no origin/main to compare with")
        return None
    ahead, behind = (int(x) for x in out.split())
    _, br = git("rev-parse", "--abbrev-ref", "HEAD", root=root)
    _, dirty = git("status", "--porcelain", root=root)
    n_dirty = len([l for l in dirty.splitlines() if l.strip()])
    if behind:
        rep.add("WARN", f"branch {br} is {behind} commit(s) behind origin/main: new rules written here may reuse taken IDs",
                f"cd /d {root} && git pull")
    else:
        rep.add("OK", f"branch {br} is up to date with origin/main" + (f" ({ahead} local commit(s) not pushed)" if ahead else ""))
    if n_dirty:
        rep.add("WARN", f"{n_dirty} uncommitted change(s) in the workspace", f"cd /d {root} && git status")
    return behind


def check_version(rep, root):
    try:
        here = open(os.path.join(root, "rules", "VERSION"), encoding="utf-8").read().strip()
    except OSError:
        rep.add("FAIL", "rules/VERSION missing")
        return
    code, main = git("show", "origin/main:rules/VERSION", root=root)
    if code:
        rep.add("OK", f"rules {here}")
    elif tuple(map(int, main.strip().split("."))) > tuple(map(int, here.split("."))):
        rep.add("WARN", f"rules here {here}, on origin/main {main.strip()} (older rules here)", f"cd /d {root} && git pull")
    elif main.strip() != here:
        rep.add("OK", f"rules {here} (origin/main has {main.strip()}; this branch carries unmerged rule changes)")
    else:
        rep.add("OK", f"rules {here} (same as origin/main)")


def check_kill(rep, root):
    if os.path.isfile(os.path.join(root, "tools", "bridge", "KILLED.lock")):
        rep.add("WARN", "KILL SWITCH IS ENGAGED: no Altium work until you re-arm it", f"{root}\\REARM.cmd (only when you choose to)")
    else:
        rep.add("OK", "kill switch not engaged")


def altium_count():
    if os.name != "nt":
        return None
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq X2.EXE", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    return sum(1 for l in r.stdout.splitlines() if l.upper().startswith('"X2.EXE"'))


def check_altium(rep, count):
    if count is None:
        rep.add("OK", "Altium instance check skipped (not Windows)")
    elif count == 0:
        rep.add("OK", "Altium is not running (open it yourself when a live step needs it; agents ask first)")
    elif count == 1:
        rep.add("OK", "one Altium instance running")
    else:
        rep.add("FAIL", f"{count} Altium instances running (licence conflicts, scripts go to the wrong one, TOOL-01)",
                "save your work, close all but one Altium window (or Task Manager > X2.EXE)")


def check_altium_lib(rep, root, cfg=None):
    cfg = cfg or os.path.join(os.path.expanduser("~"), ".altium-designer-mcp", "config.json")
    if not os.path.isfile(cfg):
        rep.add("WARN", f"altium-lib config not found ({cfg})", "run tools\\setup.ps1")
        return
    try:
        paths = [p.replace("\\", "/").rstrip("/").lower() for p in json.load(open(cfg, encoding="utf-8")).get("allowed_paths", [])]
    except (ValueError, OSError):
        rep.add("WARN", "altium-lib config.json unreadable")
        return
    lib = os.path.join(root, "library").replace("\\", "/").rstrip("/").lower()
    if any(lib == p or lib.startswith(p + "/") for p in paths):
        rep.add("OK", "altium-lib may write the workspace library")
    else:
        rep.add("WARN", "altium-lib allowed_paths does not include this workspace's library folder",
                "run tools\\setup.ps1 (it lists the missing paths), then restart Claude Code")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--folder", help="a project folder outside the workspace to add to the session")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    rep = Report()
    print(f"kit doctor: {a.root}")
    check_python(rep)
    check_mcp(rep, a.root)
    check_hook(rep, a.root)
    check_git(rep, a.root, a.offline)
    check_version(rep, a.root)
    check_kill(rep, a.root)
    check_altium(rep, altium_count())
    check_altium_lib(rep, a.root)
    print()
    start = f'cd /d "{a.root}" && claude' + (f' --add-dir "{a.folder}"' if a.folder else "")
    print("Start Claude Code so the Altium servers and the guard load (WF-10):")
    print(f"  {start}")
    if not a.folder:
        print('  (a project in your own folder: kit start "D:\\Work\\Acme\\Board1")')
    print(f"doctor: {sum(l == 'FAIL' for l, _, _ in rep.rows)} FAIL, {sum(l == 'WARN' for l, _, _ in rep.rows)} WARN")
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
