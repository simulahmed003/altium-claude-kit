"""cad_check.py - structure check of the global CAD store (no geometry check).

Usage:
  python cad_check.py [--global-root DIR]
Checks library\\cad\\index.json: every model file exists, has a STEP header, and its sha256 matches; the
footprint exists in the catalog and points back to the model; every file in cad\\step\\ is in the index.
An empty index is valid. Exit 0 when clean, 1 otherwise.
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libcat as lc
from cad_register import load_index, is_step


def check(root=None):
    idx, cat, errs = load_index(root), lc.load_catalog(root), []
    if not os.path.isfile(lc.gpath("models", "index.json", root=root)):
        errs.append("models\\index.json missing")
    listed = set()
    for m in idx["models"]:
        p = lc.gpath("models", m["file"], root=root)
        listed.add(os.path.normcase(os.path.abspath(p)))
        if not os.path.isfile(p):
            errs.append(f"{m['file']}: file missing")
            continue
        if not is_step(p):
            errs.append(f"{m['file']}: no STEP header")
        if lc.sha256(p) != m["sha256"]:
            errs.append(f"{m['file']}: sha256 changed")
        f = lc.find(cat, "f", m["footprint"])
        if f is None:
            errs.append(f"{m['file']}: footprint {m['footprint']} not in the catalog")
        elif f.get("step") != f"models/{m['file']}":
            errs.append(f"{m['file']}: catalog footprint {m['footprint']} step field is {f.get('step')}")
    d = lc.gpath("models", "step", root=root)
    if os.path.isdir(d):
        for n in os.listdir(d):
            p = os.path.normcase(os.path.abspath(os.path.join(d, n)))
            if n.lower().endswith((".step", ".stp")) and p not in listed:
                errs.append(f"step/{n}: not in index.json")
    return idx, errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    idx, errs = check(a.global_root)
    for e in errs:
        print("FAIL", e)
    print(f"{len(idx['models'])} models, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
