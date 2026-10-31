"""new_project.py - create a project from templates/project (playbook P1, rule WF-03).

Usage (cmd.exe, from the workspace folder):
  python tools\\scripts\\new_project.py <name> [--root DIR]        (default root D:\\EDA\\projects)
  python tools\\scripts\\new_project.py <name> --attach "D:\\Work\\Acme\\Board1"
--attach (rule WF-09): the design stays where it is (an employer's or a customer's folder, any drive). The kit's
project files go into a new <folder>\\_eda\\ sub-folder only; nothing else in <folder> is created, moved or changed.
project.json then has "design_dir": ".." so gate_check.py finds the .PrjPcb/.SchDoc in <folder>. Run the checkers on
<folder>\\_eda (for example gate_check.py G1 "D:\\Work\\Acme\\Board1\\_eda").
<name>: lowercase letters, digits and hyphens. Refuses an existing folder.
Copies the template (not the old ai\\*.py copies: checkers live in tools\\scripts), creates hw\\, libs\\_dryrun\\,
docs\\datasheets\\, outputs\\, ai\\review\\, fills {{NAME}} / {{DATE}} / {{RULES_VERSION}} / {{GLOBAL_ROOT}} (this
workspace's library, wherever it was cloned) in .md and .json files,
and writes an empty libs\\lib_manifest.json. Then: fill requirements.md and constraints.md (P1).
Exit 0 when created, 1 otherwise.
"""
import argparse, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import libcat as lc

TEMPLATE = os.path.join(ROOT, "templates", "project")


def create(name, root, attach=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        return None, "use lowercase letters, digits and hyphens only"
    if attach:
        if not os.path.isdir(attach):
            return None, f"{attach} is not an existing folder"
        dest = os.path.join(attach, "_eda")
    else:
        dest = os.path.join(root, name)
    if os.path.exists(dest):
        return None, f"{dest} already exists"
    shutil.copytree(TEMPLATE, dest, ignore=lambda d, names: [n for n in names if n.endswith(".py") or n == "__pycache__"])
    for sub in (() if attach else ("hw",)) + (os.path.join("libs", "_dryrun"), os.path.join("docs", "datasheets"), "outputs", os.path.join("ai", "review")):
        os.makedirs(os.path.join(dest, sub), exist_ok=True)
    rep = {"{{NAME}}": name, "{{DATE}}": lc.today(), "{{RULES_VERSION}}": lc.rules_version(),
           "{{GLOBAL_ROOT}}": os.path.abspath(lc.GLOBAL).replace("\\", "/")}
    for d, _, files in os.walk(dest):
        for fn in files:
            if fn.endswith((".md", ".json")):
                p = os.path.join(d, fn)
                with open(p, encoding="utf-8") as f:
                    s = f.read()
                for k, v in rep.items():
                    s = s.replace(k, v)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(s)
    if attach:
        pj = os.path.join(dest, "project.json")
        with open(pj, encoding="utf-8") as f:
            d = json.load(f)
        d["design_dir"] = ".."
        with open(pj, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    lc.save_manifest(dest, lc.load_manifest(dest))
    return dest, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("name")
    ap.add_argument("--root", default=os.path.join(ROOT, "projects"))
    ap.add_argument("--attach", help="existing design folder: kit files go to <folder>\\_eda only (WF-09)")
    a = ap.parse_args(argv)
    dest, err = create(a.name, a.root, a.attach)
    if err:
        print("FAIL", err)
        return 1
    print(f"Created {dest} (rules VERSION {lc.rules_version()})")
    print("Next: fill requirements.md and constraints.md (playbook P1), then gate_check.py G1 when libraries exist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
