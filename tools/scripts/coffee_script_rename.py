"""coffee_script_rename.py - give altium-coffee's Altium script project its own name, so it never clashes with eda-agent's.

Both live servers ship a script project called Altium_API.PrjScr. When coffee opens its copy while eda-agent's is
loaded, Altium has two projects with one name: eda-agent then reports two loaded projects, and a RunScript can resolve
to the wrong one (first_run_test.py test 5). This copies coffee's project file to AltiumCoffee.PrjScr in the same folder
(same units, so ProcName "Altium_API>Run" still finds Altium_API.pas) and points coffee's config.json script_path at it.
coffee reads that key on start and runs the project from there; nothing in tools/mcp is edited.

Usage:
  python tools\\scripts\\coffee_script_rename.py            # after every coffee update (tools\\setup.ps1 runs it)
  python tools\\scripts\\coffee_script_rename.py --check    # report only
Options: --coffee <altium-mcp folder> (default tools/mcp/altium-mcp), --config <coffee config.json>
(default %ALTIUM_MCP_HOME% or ~/.altium-mcp, file config.json).
Exit 0 = coffee uses its own project name, 1 = not (or files missing). Standard library only.
"""
import argparse
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OLD, NEW = "Altium_API.PrjScr", "AltiumCoffee.PrjScr"


def default_config():
    home = os.environ.get("ALTIUM_MCP_HOME") or os.path.join(os.path.expanduser("~"), ".altium-mcp")
    return os.path.join(home, "config.json")


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def current_project(cfg_path, default):
    """The project coffee will run: config script_path if that file exists, else its shipped default."""
    p = load(cfg_path).get("script_path", "")
    return p if p and os.path.isfile(p) else default


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--coffee", default=os.path.join(ROOT, "tools", "mcp", "altium-mcp"))
    ap.add_argument("--config", default=default_config())
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    a = ap.parse_args(argv)
    folder = os.path.join(a.coffee, "server", "AltiumScript")
    src, dst = os.path.join(folder, OLD), os.path.join(folder, NEW)
    if not os.path.isfile(src):
        print(f"FAIL coffee script project not found: {src}")
        return 1
    if not a.check:
        shutil.copyfile(src, dst)                     # refreshed every run, so a coffee update is picked up
        cfg = load(a.config)
        if cfg.get("script_path") != dst:
            cfg["script_path"] = dst
            os.makedirs(os.path.dirname(a.config), exist_ok=True)
            with open(a.config, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4)
        print(f"copied {OLD} -> {NEW}; {a.config} script_path = {dst}")
    used = current_project(a.config, src)
    ok = os.path.basename(used).lower() != OLD.lower()
    print(f"{'PASS' if ok else 'FAIL'} coffee runs {used}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
