"""cad_fetch.py - download a part's 3D model (STEP) from JLC/EasyEDA and file it in the library (rule LIB-13).

Usage:
  python cad_fetch.py <MPN or LCSC C-number> [--footprint NAME] [--force] [--keep-raw] [--exe PATH] [--global-root DIR]
Steps:
  1. Library first (LIB-09): the part's catalog footprint already has a registered model -> nothing to do.
  2. LCSC number from the component database record (suppliers), or the C-number given.
  3. JLC2KiCadLib <C> --no_symbol -models STEP into a staging folder (installed by tools\\setup.ps1).
  4. Box check: the STEP's bounding box against the record's package length / width / height (min..max). Outside
     the range by more than 5 % is printed as CHECK for a person (the model may include leads, or be a different body); it does not
     stop the run, the user accepts the model at G1.
  5. cad_register.py: renamed to <footprint>.step, copied to library\\models\\step\\<package type>\\, sha256 and
     source recorded in models\\index.json, catalog footprint "step" field set.
  6. The staging folder (KiCad footprint, raw STEP) is deleted unless --keep-raw.
The footprint comes from the catalog component with this MPN, or --footprint (needed for a part not yet in the catalog).
Exit 0 when a model is registered or already there, 1 otherwise.
"""
import argparse, glob, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import libcat as lc
import cad_register

ROOT = os.path.dirname(os.path.dirname(HERE))
CHECK_PCT = 5.0
POINT = re.compile(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)")


def default_exe():
    for name in ("JLC2KiCadLib.exe", "JLC2KiCadLib"):
        for d in ("Scripts", "bin"):
            p = os.path.join(ROOT, "tools", "mcp", "jlc2kicad", ".venv", d, name)
            if os.path.isfile(p):
                return p
    return shutil.which("JLC2KiCadLib")


def step_box(path):
    """(dx, dy, dz) in mm of all CARTESIAN_POINTs, or None. Includes leads and terminations."""
    with open(path, encoding="latin-1") as f:
        pts = [tuple(float(v) for v in m.groups()) for m in POINT.finditer(f.read())]
    if not pts:
        return None
    return tuple(round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3))


def record_box(rec):
    """((min, max) or None) for the record's package length, width, height."""
    pk = (rec or {}).get("facts", {}).get("package", {})
    def rng(k):
        v = pk.get(k)
        if isinstance(v, (int, float)):
            return v, v
        if isinstance(v, dict):
            lo, hi = v.get("min", v.get("typ", v.get("value"))), v.get("max", v.get("typ", v.get("value")))
            if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
                return lo, hi
        return None
    return rng("length"), rng("width"), rng("height")


def compare(box, want):
    """Lines comparing the model box with the record's L / W / H range (planar sizes matched largest to largest).
    OK inside min - 5 % .. max + 5 %, else CHECK for a person."""
    if box is None:
        return ["CHECK model box: no coordinates found in the STEP file"]
    planar = sorted(box[:2], reverse=True)
    got = dict(length=planar[0], width=planar[1], height=box[2])
    out = []
    for k, w in zip(("length", "width", "height"), want):
        if w is None:
            out.append(f"-     {k:6s} model {got[k]:.2f} mm, record has no {k}")
            continue
        ok = w[0] * (1 - CHECK_PCT / 100) <= got[k] <= w[1] * (1 + CHECK_PCT / 100)
        out.append(f"{'OK   ' if ok else 'CHECK'} {k:6s} model {got[k]:.2f} mm, record {w[0]:.2f}..{w[1]:.2f} mm")
    return out


def resolve(key, footprint, root):
    """(lcsc, record, footprint name, error)."""
    import parts
    hits = parts.find_record(key)
    if len(hits) > 1:
        return None, None, None, f"{key}: several part records match: " + ", ".join(os.path.basename(f) for f, _ in hits)
    rec = hits[0][1] if hits else None
    if re.fullmatch(r"C\d+", key):
        lcsc = key
    elif not rec:
        return None, None, None, f"{key}: no component database record (run parts.py new / fetch first, RQ-01)"
    else:
        lcsc = next((s.get("sku") for s in rec.get("suppliers", []) if s.get("name") == "LCSC" and s.get("sku")), None)
        if not lcsc:
            return None, rec, None, f"{key}: the record has no LCSC number; get the model from the maker's site (LIB-13)"
    if not footprint:
        cat = lc.load_catalog(root)
        mpn = rec.get("mpn") if rec else None
        comp = next((c for c in cat["components"] if mpn and c.get("mpn") == mpn), None)
        footprint = comp.get("footprint") if comp else None
        if not footprint:
            return lcsc, rec, None, f"{key}: no catalog component with this MPN; pass --footprint <name>"
    return lcsc, rec, footprint, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("part", help="MPN (from the component database) or an LCSC C-number")
    ap.add_argument("--footprint")
    ap.add_argument("--force", action="store_true", help="download even when the footprint already has a model")
    ap.add_argument("--keep-raw", action="store_true", help="keep the staging folder (KiCad footprint, raw STEP)")
    ap.add_argument("--exe", help="JLC2KiCadLib executable (default: tools\\mcp\\jlc2kicad\\.venv)")
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    root = a.global_root
    if root:
        os.environ["EDA_GLOBAL"] = root   # parts.py finds the component database here

    lcsc, rec, fp_name, err = resolve(a.part, a.footprint, root)
    if err:
        print("FAIL", err)
        return 1
    cat = lc.load_catalog(root)
    fp = lc.find(cat, "f", fp_name)
    if fp is None:
        print(f"FAIL footprint {fp_name} not in the catalog")
        return 1
    have = fp.get("step") and os.path.isfile(lc.gpath(*fp["step"].split("/"), root=root))
    if have and not a.force:
        print(f"library first: {fp_name} already has {fp['step']}; nothing to download (--force to replace)")
        return 0

    exe = a.exe or default_exe()
    if not exe:
        print("FAIL JLC2KiCadLib not found: run tools\\setup.ps1 (installs it in tools\\mcp\\jlc2kicad\\.venv)")
        return 1
    stage = tempfile.mkdtemp(prefix=f"cad_{lcsc}_")
    try:
        cmd = ([sys.executable, exe] if exe.endswith(".py") else [exe]) + [lcsc, "-dir", stage, "--no_symbol", "-models", "STEP"]
        print(">", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print((r.stdout + r.stderr)[-1500:])
            print(f"FAIL JLC2KiCadLib exit {r.returncode}")
            return 1
        steps = sorted(glob.glob(os.path.join(stage, "**", "*.step"), recursive=True))
        if not steps:
            print(f"FAIL JLC/EasyEDA has no 3D model for {lcsc}: try the maker's site, or a similar body as a marked "
                  f"substitute the user accepts at G1 (LIB-13)")
            return 1
        src = steps[0]
        print(f"downloaded {os.path.basename(src)} for {lcsc}" + (f" ({len(steps)} files, using the first)" if len(steps) > 1 else ""))
        for line in compare(step_box(src), record_box(rec)):
            print("  ", line)
        code = cad_register.main([src, "--footprint", fp_name, "--source", f"JLC/EasyEDA {lcsc} via JLC2KiCadLib"]
                                 + (["--global-root", root] if root else []))
        if code == 0:
            print("Check it in Altium before G1: pin 1 corner, seating plane, height (LIB-13).")
        return code
    finally:
        if a.keep_raw:
            print(f"raw files kept in {stage}")
        else:
            shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
