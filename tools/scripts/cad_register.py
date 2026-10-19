"""cad_register.py - register a 3D model (STEP) in the global CAD store (structure only, no geometry check).

Usage:
  python cad_register.py <model.step> --footprint NAME --source URL_OR_NOTE [--rot 0 0 0] [--offset 0 0 0]
                         [--global-root DIR]
Copies the file to library\\models\\step\\<package type>\\<footprint>.step (LIB-13: one model per footprint body), records sha256,
footprint, source, date, rotation (deg) and offset (mm) in library\\models\\index.json, and sets the footprint's "step" field in the catalog.
Refuses a file that does not start with the STEP header "ISO-10303-21" or a footprint not in the catalog.
Linking the model into a PcbLib is a separate altium-lib / Altium step (phase 2, see 03_LIBRARY).
Exit 0 when registered, 1 otherwise.
"""
import argparse, json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libcat as lc


def index_path(root=None):
    return lc.gpath("models", "index.json", root=root)


def load_index(root=None):
    p = index_path(root)
    if not os.path.isfile(p):
        return {"schema": 1, "models": []}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def is_step(path):
    with open(path, "rb") as f:
        return f.read(64).lstrip().startswith(b"ISO-10303-21")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("model")
    ap.add_argument("--footprint", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--rot", nargs=3, type=float, default=[0, 0, 0])
    ap.add_argument("--offset", nargs=3, type=float, default=[0, 0, 0])
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    cat = lc.load_catalog(a.global_root)
    f = lc.find(cat, "f", a.footprint)
    errs = []
    if f is None:
        errs.append(f"footprint {a.footprint} not in the catalog")
    if not os.path.isfile(a.model) or not is_step(a.model):
        errs.append(f"{a.model}: not a STEP file (no ISO-10303-21 header)")
    if errs:
        for e in errs:
            print("FAIL", e)
        return 1
    ext = os.path.splitext(a.model)[1].lower() or ".step"
    name = f"{f.get('package_type') or lc.package_type_of(a.footprint) or 'other'}/{a.footprint}{ext}"
    dst = lc.gpath("models", "step", *name.split("/"), root=a.global_root)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(a.model, dst)
    idx = load_index(a.global_root)
    idx["models"] = [m for m in idx["models"] if m["file"] != f"step/{name}"]
    idx["models"].append(dict(file=f"step/{name}", sha256=lc.sha256(dst), footprint=a.footprint, source=a.source,
                              date=lc.today(), rotation_deg=a.rot, offset_mm=a.offset))
    with open(index_path(a.global_root), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1)
    f["step"] = f"models/step/{name}"
    lc.save_catalog(cat, a.global_root)
    lc.changelog(f"3D model {name} registered for {a.footprint} (source {a.source})", a.global_root)
    print(f"registered {name} for {a.footprint}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
