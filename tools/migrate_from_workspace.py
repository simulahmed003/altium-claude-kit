"""migrate_from_workspace.py - move an altium-claude-workspace install (D:\\EDA) to the altium-claude-kit layout.

Usage (close Altium Designer and every Claude Code window first):
  python migrate_from_workspace.py                 # D:\\EDA, asks before changing anything
  python migrate_from_workspace.py --root E:\\EDA   # another folder
  python migrate_from_workspace.py --dry-run       # print the plan only
  python migrate_from_workspace.py --yes           # no question

What it does, in order (every changed file is backed up under <root>\\migration_backup\\<time>\\ first):
  1 git: point origin to altium-claude-kit and fast-forward to its main (refuses on uncommitted tracked changes).
  2 move local, git-ignored files to the new folders: _tools\\mcp, _tools\\libraries, _logs\\*, _global\\datasheets\\*.pdf.
  3 rewrite old paths in each projects\\<name>\\ text file (project.json, *.md, ai\\*.json), in
    .claude\\settings.json (guard hook path, deny list) and in
    %USERPROFILE%\\.altium-designer-mcp\\config.json (allowed_paths, audit log).
  4 run tools\\setup.ps1 (rewrites .mcp.json and the kill-switch shortcut; it leaves an existing settings.json alone).
  5 run tools\\selftest.py.
Standard library only. Exit code 0 = done, 1 = stopped with a message.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

KIT_URL = "https://github.com/simulahmed003/altium-claude-kit.git"
B = r"(?<![A-Za-z0-9])"
# Order matters: the specific paths first.
SUBS = [
    (B + r"_tools([/\\]+)templates", "templates"),
    (B + r"_tools([/\\]+)fab_profiles", r"rules\1fab-profiles"),
    (B + r"_global([/\\]+)libs([/\\]+)specs", r"library\1specs"),
    (B + r"_global([/\\]+)cad", r"library\1models"),
    (B + r"_rules(?![A-Za-z0-9])", "rules"),
    (B + r"_guidelines(?![A-Za-z0-9])", "guidelines"),
    (B + r"_global(?![A-Za-z0-9])", "library"),
    (B + r"_logs(?![A-Za-z0-9])", "logs"),
    (B + r"_tools(?![A-Za-z0-9])", "tools"),
]
TEXT_EXT = (".json", ".md", ".txt", ".csv", ".yaml", ".yml", ".py")
SKIP_DIRS = {".git", "__Previews", "History", "migration_backup"}


def rewrite(text):
    for a, b in SUBS:
        text = re.sub(a, b, text)
    return text


class Migration:
    def __init__(self, root, dry, yes, mcp_config, run_setup):
        self.root, self.dry, self.yes, self.run_setup = root, dry, yes, run_setup
        self.mcp_config = mcp_config
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.backup = os.path.join(root, "migration_backup", stamp)
        self.actions = []

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    def git(self, *args, check=True):
        # safe.directory: an elevated (admin) shell does not own the folder, and git would refuse it
        r = subprocess.run(["git", "-c", f"safe.directory={self.root}", "-C", self.root, *args], capture_output=True, text=True)
        if check and r.returncode:
            raise SystemExit(f"STOP git {' '.join(args)} failed:\n{r.stderr.strip()}")
        return r.stdout.strip()

    def save_backup(self, path):
        path = os.path.abspath(path)
        inside = os.path.commonpath([path, self.root]) == self.root
        rel = os.path.relpath(path, self.root) if inside else os.path.join("outside", os.path.basename(path))
        dst = os.path.join(self.backup, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(path, dst)

    # ---------- plan ----------

    def plan_git(self):
        if not os.path.isdir(self.p(".git")):
            raise SystemExit(f"STOP {self.root} is not a git clone. Clone the kit instead:\n  git clone {KIT_URL} {self.root}")
        url = self.git("remote", "get-url", "origin", check=False)
        if os.path.isdir(self.p("rules")) and os.path.isdir(self.p("library")) and not os.path.isdir(self.p("_rules")):
            self.actions.append(("info", "tracked files are already in the kit layout"))
        dirty = [l for l in self.git("status", "--porcelain", "--untracked-files=no").splitlines() if l.strip()]
        if dirty:
            raise SystemExit("STOP uncommitted changes to tracked files (commit or stash them first):\n  " + "\n  ".join(dirty[:20]))
        if "altium-claude-kit" not in url:
            self.actions.append(("git-remote", url))
        self.actions.append(("git-pull", None))

    def plan_moves(self):
        moves = [(("_tools", "mcp"), ("tools", "mcp")),
                 (("_tools", "libraries"), ("tools", "libraries")),
                 (("_tools", "bridge", "bridge_state.json"), ("tools", "bridge", "bridge_state.json")),
                 (("_tools", "bridge", "KILLED.lock"), ("tools", "bridge", "KILLED.lock")),
                 (("_tools", "bridge", "mcp.disabled.json"), ("tools", "bridge", "mcp.disabled.json"))]
        for src, dst in moves:
            if os.path.exists(self.p(*src)):
                self.actions.append(("move", (self.p(*src), self.p(*dst))))
        if os.path.isdir(self.p("_logs")):
            for n in os.listdir(self.p("_logs")):
                if n != "README.md":
                    self.actions.append(("move", (self.p("_logs", n), self.p("logs", n))))
        ds = self.p("_global", "datasheets")
        if os.path.isdir(ds):
            for n in os.listdir(ds):
                if n.lower().endswith(".pdf"):
                    self.actions.append(("move", (os.path.join(ds, n), self.p("library", "datasheets", n))))

    def plan_rewrites(self):
        files = []
        proj = self.p("projects")
        if os.path.isdir(proj):
            for dp, dns, fns in os.walk(proj):
                dns[:] = [d for d in dns if d not in SKIP_DIRS]
                if dp == proj:
                    continue                    # projects\README.md belongs to the kit repo
                files += [os.path.join(dp, f) for f in fns if f.lower().endswith(TEXT_EXT)]
        if os.path.isfile(self.p(".claude", "settings.json")):
            files.append(self.p(".claude", "settings.json"))     # setup.ps1 never rewrites an existing one
        if self.mcp_config and os.path.isfile(self.mcp_config):
            files.append(os.path.abspath(self.mcp_config))
        for f in files:
            try:
                s = open(f, encoding="utf-8", newline="").read()
            except (UnicodeDecodeError, OSError):
                continue
            if rewrite(s) != s:
                self.actions.append(("rewrite", f))

    # ---------- run ----------

    def show(self):
        print(f"Migration plan for {self.root}")
        for kind, arg in self.actions:
            if kind == "git-remote":
                print(f"  git: origin {arg or '(none)'} -> {KIT_URL}")
            elif kind == "git-pull":
                print("  git: fetch origin main, fast-forward (keeps your history: the kit contains the workspace commits)")
            elif kind == "move":
                print(f"  move: {os.path.relpath(arg[0], self.root)} -> {os.path.relpath(arg[1], self.root)}")
            elif kind == "rewrite":
                print(f"  rewrite paths: {arg}")
            else:
                print(f"  note: {arg}")
        print(f"  then: {'run tools/setup.ps1, ' if self.run_setup else ''}run tools/selftest.py")
        print(f"  backups: {self.backup}")

    def execute(self):
        for kind, arg in self.actions:
            if kind == "git-remote":
                if arg:
                    self.git("remote", "set-url", "origin", KIT_URL)
                else:
                    self.git("remote", "add", "origin", KIT_URL)
                print("  origin set to the kit")
            elif kind == "git-pull":
                self.git("fetch", "origin", "main")
                branch = self.git("rev-parse", "--abbrev-ref", "HEAD")
                if branch != "main":
                    self.git("checkout", "main")
                r = subprocess.run(["git", "-c", f"safe.directory={self.root}", "-C", self.root, "merge", "--ff-only", "origin/main"], capture_output=True, text=True)
                if r.returncode:
                    raise SystemExit("STOP your main has commits the kit does not have, so it cannot fast-forward.\n"
                                     "  Push them to a branch first, or run: git merge origin/main  (then re-run this script)\n"
                                     + r.stderr.strip())
                self.git("branch", "--set-upstream-to=origin/main", "main", check=False)
                print("  pulled the kit main")
            elif kind == "move":
                src, dst = arg
                if os.path.exists(dst):
                    print(f"  skip move, target exists: {os.path.relpath(dst, self.root)}")
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                print(f"  moved {os.path.relpath(src, self.root)}")
            elif kind == "rewrite":
                self.save_backup(arg)
                s = open(arg, encoding="utf-8", newline="").read()   # keep CRLF as it was
                with open(arg, "w", encoding="utf-8", newline="") as f:
                    f.write(rewrite(s))
                print(f"  rewrote {arg}")
        self.remove_empty_old_dirs()

    def remove_empty_old_dirs(self):
        for d in ("_tools", "_logs", "_global", "_rules", "_guidelines"):
            path = self.p(d)
            if not os.path.isdir(path):
                continue
            for dp, dns, fns in os.walk(path, topdown=False):
                if not os.listdir(dp):
                    os.rmdir(dp)
            if os.path.isdir(path):
                left = [os.path.relpath(os.path.join(dp, f), self.root) for dp, _, fns in os.walk(path) for f in fns]
                print(f"  NOTE {d} still holds {len(left)} file(s), not moved (check them): {left[:5]}")

    def after(self):
        ok = True
        if self.run_setup:
            ps = shutil.which("powershell") or shutil.which("pwsh")
            if not ps:
                print("  NOTE PowerShell not found: run tools\\setup.ps1 yourself")
                ok = False
            else:
                print("  running tools\\setup.ps1 ...")
                r = subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", self.p("tools", "setup.ps1")],
                                   cwd=self.root)
                ok &= r.returncode == 0
        print("  running tools\\selftest.py ...")
        r = subprocess.run([sys.executable, self.p("tools", "selftest.py")], cwd=self.root)
        ok &= r.returncode == 0
        return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=r"D:\EDA" if os.name == "nt" else os.getcwd())
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--mcp-config", default=os.path.join(os.path.expanduser("~"), ".altium-designer-mcp", "config.json"))
    ap.add_argument("--no-setup", action="store_true", help="skip tools/setup.ps1")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    m = Migration(root, a.dry_run, a.yes, a.mcp_config, not a.no_setup)
    m.plan_git()
    m.plan_moves()
    m.plan_rewrites()
    m.show()
    if a.dry_run:
        return 0
    if not a.yes and input("Close Altium and Claude Code first. Proceed? [y/N] ").strip().lower() != "y":
        print("stopped, nothing changed")
        return 1
    m.execute()
    # project and config paths are rewritten again in case the pull added files that still use old paths
    m.actions = []
    m.plan_rewrites()
    m.execute()
    ok = m.after()
    print("DONE" if ok else "DONE with problems: read the output above")
    print("Next: start Claude Code in the folder, type /mcp (altium-lib, altium-coffee, altium-eda), then docs\\FIRST_RUN_TESTS.md.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
