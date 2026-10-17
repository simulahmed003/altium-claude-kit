"""lib_update.py - plan the update of a project's local parts to the newest global rev (rule LIB-06).

Usage:
  python lib_update.py <project dir> [ID ...] [--global-root DIR]
Without IDs: every part that lib_status.py reports as UPDATE. A part reported LOCAL CHANGED is refused
(local edits would be lost: promote them after G1 or revert first). Writes the same plan as lib_pull.py
(ai\\lib_pull_plan.json, manifest "planned"); after the altium-lib copies run lib_pull.py --verify, then
P4 (Update From Libraries, conn_check.py). Announce it first: replacing a local part is a destructive edit.
Exit 0 when a plan was written (or nothing to update), 1 on refusal.
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_pull, lib_status


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("project")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    rows = {(r[0], r[1]): r[2] for r in lib_status.status(a.project, a.global_root)}
    comp = {i: st for (k, i), st in rows.items() if k == "component"}
    ids = a.ids or [i for i, st in comp.items() if st == "UPDATE"]
    refused = [i for i in ids if comp.get(i) == "LOCAL CHANGED"]
    for i in refused:
        print(f"FAIL {i}: local copy changed - promote (after G1) or revert before updating")
    if refused:
        print("RESULT FAIL")
        return 1
    if not ids:
        print("nothing to update")
        print("RESULT PASS")
        return 0
    copies, errs = lib_pull.plan(a.project, ids, a.global_root)
    for e in errs:
        print("FAIL", e)
    print(f"{len(copies)} altium-lib copies planned for {ids}")
    print("RESULT", "FAIL" if errs else "PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
