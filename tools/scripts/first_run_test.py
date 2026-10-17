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
  5 the two live servers do not install script projects with the same file name
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

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LOG = os.path.join(ROOT, "logs", "MCP_LOG.md")
CLAUDE_TIMEOUT = 600          # the guard may wait on a popup


def parse_status(text):
    """bridge.cmd status output -> {'active bridge': 'none', 'eda-agent loop': 'responding', ...}"""
    out = {}
    for line in text.splitlines():
        m = re.match(r"\s*([^:]+?)\s*:\s*(.*)$", line)
        if m:
            out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


def clashes(eda_paths, coffee_paths):
    """Script project file names that both live servers install (Altium may open the wrong one)."""
    names = lambda ps: {os.path.basename(p).lower() for p in ps}
    return sorted(names(eda_paths) & names(coffee_paths))


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
            _, _, s = self.status()
        loop = s.get("eda-agent loop", "?")
        self.record(2, loop == "responding",
                    f"Altium running: {s.get('altium running', '?')}, eda-agent loop: {loop}")

    def t3(self):
        _, _, before = self.status()
        print("   asking Claude for one read-only altium-coffee call (the guard may show a popup: answer it)")
        code, out = self.claude("Call exactly one read-only altium-coffee tool, for example get_server_status, "
                                "and print its result. If the call is blocked, print the block message verbatim "
                                "and stop. Do not call any other tool.", "mcp__altium-coffee")
        print("   " + out[-1500:].replace("\n", "\n   "))
        _, _, after = self.status()
        asked = "not asked (--yes)" if self.yes else self.ask("Did the guard show a popup asking you to release the eda-agent loop?")
        alive = after.get("altium running", "").lower() == "true"
        self.record(3, code == 0 and alive,
                    f"loop before: {before.get('eda-agent loop')}, claude exit {code}, popup asked: {asked}, "
                    f"Altium running after: {after.get('altium running')}, active bridge: {after.get('active bridge')}")

    def t4(self):
        if not self.ask("app_detach SAVES every modified Altium document first. Run it?"):
            return self.record(4, None, "skipped by the user")
        code, out = self.claude("Call the altium-eda tool app_detach once and print its result. "
                                "Do not call any other tool.", "mcp__altium-eda__app_detach")
        print("   " + out[-1500:].replace("\n", "\n   "))
        _, _, s = self.status()
        loop = s.get("eda-agent loop", "?")
        self.record(4, code == 0 and loop == "not responding", f"claude exit {code}, eda-agent loop after: {loop}")

    def t5(self):
        home = os.path.expanduser("~")
        eda = glob.glob(os.path.join(home, "EDA Agent", "scripts", "**", "*.PrjScr"), recursive=True)
        coffee = glob.glob(os.path.join(ROOT, "tools", "mcp", "altium-mcp", "**", "*.PrjScr"), recursive=True)
        for p in eda + coffee:
            print(f"   {p}")
        if not eda or not coffee:
            return self.record(5, None, "script projects of one server not found (eda-agent install-scripts not run?)")
        dup = clashes(eda, coffee)
        self.record(5, not dup, f"{len(eda)} eda-agent + {len(coffee)} coffee script projects, "
                                f"same name in both: {dup or 'none'}")

    def t6(self):
        if not self.ask("Engage the kill switch now (stops the MCP servers, never touches Altium; REARM follows)?"):
            return self.record(6, None, "skipped by the user")
        print("   running KILL.cmd (press OK on its popup)")
        self.cmd("KILL.cmd", timeout=300)
        lock = os.path.isfile(os.path.join(ROOT, "tools", "bridge", "KILLED.lock"))
        mcp_off = not os.path.isfile(os.path.join(ROOT, ".mcp.json"))
        _, _, s = self.status()
        code, out = self.claude("Call the altium-coffee tool get_server_status once and print the result or the "
                                "block message verbatim. Do not retry.", "mcp__altium-coffee")
        blocked = "KILL SWITCH IS ENGAGED" in out or code != 0
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
