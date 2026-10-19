"""cad_fetch.py - download a part's 3D model from JLC/EasyEDA, check it against the part record, store it (rule LIB-13).

Usage:
  python cad_fetch.py <component id | MPN | LCSC C-number> [--footprint NAME] [--lcsc C123 (same or similar body; marked substitute)]
                      [--no-check] [--tol 0.05] [--replace] [--dry-run] [--keep] [--global-root DIR]
Steps:
  1. Resolve the part: catalog component (id or former id) or component-database record (MPN / LCSC sku) gives the
     LCSC number, the footprint (catalog) and the body size (record facts package.length / width / height).
  2. Download with JLC2KiCadLib (tools\\mcp\\jlc2kicad, installed by setup.ps1) into a temporary folder: the STEP
     model plus the KiCad footprint and symbol (their data is recorded, step 5).
  3. Check the STEP (skip with --no-check, only after the user agreed): STEP header, millimetre units, the box of the
     model's vertices as the footprint places it (the footprint's model rotation / offset) against the record's body
     length (X), width (Y) and height (Z) inside the datasheet min/max +- --tol mm. The footprint's model rotation is
     kept; the offset is set so the body is centred on the footprint and sits on the board (JLC's own offset is
     recorded but not used). Pin 1 of a polarised body is not checked here: look at it in Altium at G1.
  4. Store it: cad_register.py renames it to <footprint>.step under library\\models\\step\\<package type>\\, records
     sha256, source, rotation and offset in models\\index.json and sets the footprint's step field. One model per
     footprint: a footprint that already has one is skipped unless --replace.
  5. Record what the other two files say in library\\models\\jlc\\<C-number>.json: pads, courtyard, body outline, paste
     shapes, model placement (footprint) and pins and properties (symbol), for later comparison - never as a source.
  6. Delete the temporary folder (--keep leaves it).
--dry-run: steps 1-3 and the report only. Exit 0 = stored (or dry run passed), 1 = any failure (nothing stored).
Python standard library only.
"""
import argparse, glob, json, math, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import libcat as lc, cad_register, parts as P

JLC_EXE = os.path.join(lc.ROOT, "tools", "mcp", "jlc2kicad", ".venv", "Scripts", "JLC2KiCadLib.exe")


# ---------------- STEP ----------------
def step_info(path):
    """Header, length unit and bounding box (mm, model axes) from the CARTESIAN_POINTs of a STEP file."""
    with open(path, encoding="latin-1") as f:
        t = f.read()
    info = {"header_ok": t.lstrip().startswith("ISO-10303-21"),
            "schema": (re.findall(r"FILE_SCHEMA\s*\(\s*\(\s*'([^']*)'", t) or [""])[0],
            "product": (re.findall(r"PRODUCT\s*\(\s*'([^']*)'", t) or [""])[0],
            "mm": bool(re.search(r"SI_UNIT\s*\(\s*\.MILLI\.\s*,\s*\.METRE\.\s*\)", t)),
            "meter": bool(re.search(r"SI_UNIT\s*\(\s*\$\s*,\s*\.METRE\.\s*\)", t)),
            "inch": bool(re.search(r"CONVERSION_BASED_UNIT\s*\(\s*'INCH'", t, re.I))}
    # body box from the topological vertices only: B-spline control points and placement origins lie off the body
    coords = {}
    for m in re.finditer(r"#(\d+)\s*=\s*CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(([^)]*)\)\s*\)", t):
        v = m.group(2).split(",")
        if len(v) == 3:
            try:
                coords[m.group(1)] = tuple(float(x) for x in v)
            except ValueError:
                pass
    vids = re.findall(r"VERTEX_POINT\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*\)", t)
    pts = [coords[i] for i in vids if i in coords]
    info["box_from"] = "vertices"
    if not pts:                                    # no topology: fall back to every point (may over-estimate)
        pts, info["box_from"] = list(coords.values()), "all points"
    scale = 1.0 if info["mm"] else 1000.0 if info["meter"] else 25.4 if info["inch"] else 1.0
    info["points"] = len(pts)
    info["bbox"] = [[min(p[i] for p in pts) * scale, max(p[i] for p in pts) * scale] for i in range(3)] if pts else None
    return info


def rotate_box(bbox, rot_deg, offset):
    """Box of the model after the footprint's rotation (X, then Y, then Z, degrees) and offset (mm)."""
    corners = [(x, y, z) for x in bbox[0] for y in bbox[1] for z in bbox[2]]
    rx, ry, rz = (math.radians(a) for a in rot_deg)

    def rot(p):
        x, y, z = p
        y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
        x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
        x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
        return x + offset[0], y + offset[1], z + offset[2]

    c = [rot(p) for p in corners]
    return [[round(min(q[i] for q in c), 4), round(max(q[i] for q in c), 4)] for i in range(3)]


# ---------------- KiCad footprint / symbol (records only) ----------------
def kicad_footprint(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        t = f.read()
    num = r"(-?[\d.]+)"
    pads = [dict(number=m.group(1), kind=m.group(2), shape=m.group(3), x=float(m.group(4)), y=float(m.group(5)),
                 w=float(m.group(7)), h=float(m.group(8)))
            for m in re.finditer(rf'\(pad\s+"?([^"\s)]+)"?\s+(\w+)\s+(\w+)\s+\(at\s+{num}\s+{num}(?:\s+{num})?\)\s+\(size\s+{num}\s+{num}\)', t)]

    def layer_box(layer):
        xs, ys = [], []
        for m in re.finditer(r"\((?:fp_line|fp_poly|fp_rect)\b(.*?)\(layer\s+" + re.escape(layer) + r"\)", t, re.S):
            for x, y in re.findall(rf"\((?:start|end|xy)\s+{num}\s+{num}\)", m.group(1)):
                xs.append(float(x)); ys.append(float(y))
        return [[min(xs), max(xs)], [min(ys), max(ys)]] if xs else None

    model = re.search(r"\(model\s+(\S+)(.*?)\n\s*\)", t, re.S)
    place = {"file": None, "offset_mm": [0.0, 0.0, 0.0], "rotate_deg": [0.0, 0.0, 0.0]}
    if model:
        body = model.group(2)
        place["file"] = model.group(1)
        off = re.search(rf"\(offset\s+\(xyz\s+{num}\s+{num}\s+{num}\)\)", body)
        at = re.search(rf"\(at\s+\(xyz\s+{num}\s+{num}\s+{num}\)\)", body)        # old format: inches
        if off:
            place["offset_mm"] = [float(v) for v in off.groups()]
        elif at:
            place["offset_mm"] = [float(v) * 25.4 for v in at.groups()]
        r = re.search(rf"\(rotate\s+\(xyz\s+{num}\s+{num}\s+{num}\)\)", body)
        if r:
            place["rotate_deg"] = [float(v) for v in r.groups()]
    name = re.search(r'\((?:module|footprint)\s+"?([^"\s)]+)', t)
    return {"name": name.group(1) if name else "", "pads": pads, "courtyard": layer_box("F.CrtYd"),
            "body_outline": layer_box("Cmts.User") or layer_box("F.Fab"), "silk": layer_box("F.SilkS"),
            "custom_paste": "(layer F.Paste)" in t and "fp_poly" in t, "model": place}


def kicad_symbol(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        t = f.read()
    props = dict(re.findall(r'\(property\s+"([^"]+)"\s+"([^"]*)"', t))
    pins = [dict(type=m.group(1), number=m.group(3), name=m.group(2))
            for m in re.finditer(r'\(pin\s+(\w+)\s+\w+.*?\(name\s+"([^"]*)".*?\(number\s+"([^"]*)"', t, re.S)]
    name = re.search(r'\(symbol\s+"([^"]+)"', t)
    return {"name": name.group(1) if name else "", "properties": props, "pins": pins}


# ---------------- part resolution and body check ----------------
def resolve(key, root=None):
    """(catalog component or None, part record or None)."""
    cat = lc.load_catalog(root)
    comp = lc.find(cat, "c", key)
    rec = None
    for k in ([comp.get("mpn")] if comp else []) + [key]:
        if k and k != "-":
            hits = P.find_record(k)
            if len(hits) == 1:
                rec = hits[0][1]
                break
    if comp is None and rec:
        comp = next((lc.find(cat, "c", i) for i in rec.get("catalog_ids", []) if lc.find(cat, "c", i)), None)
    return comp, rec


def body_limits(rec, tol):
    """{axis: (lo, hi, what)} from the record's package facts; None when the record has no body size."""
    if not rec:
        return None
    pk = rec.get("facts", {}).get("package", {})
    out = {}
    for axis, key in (("x", "length"), ("y", "width"), ("z", "height")):
        f = pk.get(key)
        if not f:
            continue
        lo = f.get("min", f.get("typ", f.get("value")))
        hi = f.get("max", f.get("typ", f.get("value")))
        if lo is None and hi is None:
            continue
        lo = lo if lo is not None else 0.0
        if "min" not in f and "max" in f:
            lo = 0.0                                       # only a maximum is given (e.g. "Max. 10.3")
        out[axis] = (lo - tol, hi + tol, f"{key} {lo}-{hi} mm (record) +-{tol}")
    return out or None


def check_box(box, limits, tol):
    problems = []
    for i, axis in enumerate("xyz"):
        size = box[i][1] - box[i][0]
        if axis in limits:
            lo, hi, what = limits[axis]
            if not lo <= size <= hi:
                problems.append(f"model {axis} size {size:.3f} mm outside {what}")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("key")
    ap.add_argument("--footprint")
    ap.add_argument("--lcsc")
    ap.add_argument("--no-check", action="store_true", help="skip the box check (only after the user agreed)")
    ap.add_argument("--tol", type=float, default=0.05, help="mm added to the datasheet min/max (default 0.05)")
    ap.add_argument("--replace", action="store_true", help="replace the model a footprint already has")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the temporary download folder")
    ap.add_argument("--exe", default=os.environ.get("JLC2KICADLIB") or (JLC_EXE if os.path.isfile(JLC_EXE) else shutil.which("JLC2KiCadLib")))
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    root = a.global_root
    comp, rec = resolve(a.key, root)
    own = (comp or {}).get("lcsc") or next((s["sku"] for s in (rec or {}).get("suppliers", []) if s.get("name") == "LCSC"), None)
    lcsc = a.lcsc or own
    # a part with no LCSC number (or a JLC model that fails) may borrow the model of the same or a similar body sold on
    # LCSC: --lcsc <its C-number>. It is stored marked as a substitute the user accepts at G1 (LIB-13).
    substitute = bool(a.lcsc) and a.lcsc != own
    fp = a.footprint or (comp or {}).get("footprint")
    if not lcsc or not re.fullmatch(r"C\d+", lcsc or ""):
        print(f"FAIL no LCSC C-number for '{a.key}' (give --lcsc)")
        return 1
    if not fp:
        print(f"FAIL no footprint for '{a.key}' (give --footprint; the footprint must be in the catalog)")
        return 1
    cat = lc.load_catalog(root)
    f = lc.find(cat, "f", fp)
    if f is None:
        print(f"FAIL footprint {fp} not in the catalog")
        return 1
    if f.get("step") and not a.replace and not a.dry_run:
        print(f"SKIP {fp} already has a model ({f['step']}); one model per footprint (--replace to change it)")
        return 0
    limits = body_limits(rec, a.tol)
    if limits is None and not a.no_check:
        print(f"FAIL no body size in the component database for '{a.key}': add package length/width/height (parts.py) "
              f"or, after the user agreed, run with --no-check")
        return 1
    if not a.exe or not os.path.isfile(a.exe):
        print("FAIL JLC2KiCadLib not found (run tools\\setup.ps1 or give --exe)")
        return 1
    tmp = tempfile.mkdtemp(prefix="cad_fetch_")
    try:
        r = subprocess.run([a.exe, lcsc, "-dir", tmp, "-models", "STEP"], capture_output=True, text=True, timeout=300)
        steps = glob.glob(os.path.join(tmp, "**", "*.step"), recursive=True) + glob.glob(os.path.join(tmp, "**", "*.stp"), recursive=True)
        mods = glob.glob(os.path.join(tmp, "**", "*.kicad_mod"), recursive=True)
        syms = glob.glob(os.path.join(tmp, "**", "*.kicad_sym"), recursive=True)
        if r.returncode != 0 or not steps:
            print(f"FAIL JLC2KiCadLib gave no STEP model for {lcsc} (exit {r.returncode}): {(r.stderr or r.stdout)[-300:]}")
            return 1
        step = steps[0]
        sinfo = step_info(step)
        fpinfo = kicad_footprint(mods[0]) if mods else None
        syinfo = kicad_symbol(syms[0]) if syms else None
        place = (fpinfo or {}).get("model") or {"rotate_deg": [0, 0, 0], "offset_mm": [0, 0, 0]}
        box = rotate_box(sinfo["bbox"], place["rotate_deg"], place["offset_mm"]) if sinfo["bbox"] else None
        # Placement: keep JLC's rotation (it orients the body to the land), but place the box ourselves: our footprints
        # are centred, and JLC's model offset is unreliable (written in mm into the old inch field, or centred bodies).
        jlc_offset = list(place["offset_mm"])
        box = rotate_box(sinfo["bbox"], place["rotate_deg"], [0, 0, 0]) if sinfo["bbox"] else None
        if box:
            off = [round(-(box[0][0] + box[0][1]) / 2, 4), round(-(box[1][0] + box[1][1]) / 2, 4), round(-box[2][0], 4)]
            place = dict(place, offset_mm=off)
            box = rotate_box(sinfo["bbox"], place["rotate_deg"], off)
            if any(abs(v) > 0.01 for v in off) or any(abs(v) > 0.01 for v in jlc_offset):
                print(f"  note: model centred on the footprint and set on the board: offset {off} mm (JLC gave {jlc_offset})")
        problems = []
        if not sinfo["header_ok"]:
            problems.append("not a STEP file (no ISO-10303-21 header)")
        if not (sinfo["mm"] or sinfo["meter"] or sinfo["inch"]):
            problems.append("length unit not found in the STEP file")
        if box is None:
            problems.append("no geometry points in the STEP file")
        elif not a.no_check:
            problems += check_box(box, limits, a.tol)

        size = [round(b[1] - b[0], 3) for b in box] if box else None
        print(f"{lcsc} -> footprint {fp}: STEP '{sinfo['product']}' {sinfo['schema']}, placed size (L x W x H) {size} mm, "
              f"rotation {place['rotate_deg']}, offset {place['offset_mm']}")
        for axis, (lo, hi, what) in (limits or {}).items():
            print(f"  record {axis}: {what}")
        for pr in problems:
            print(f"  FAIL {pr}")
        report = {"schema": 1, "lcsc": lcsc, "substitute": substitute, "mpn": (rec or comp or {}).get("mpn"), "footprint": fp, "fetched": lc.today(),
                  "tool": "JLC2KiCadLib", "check": "skipped (--no-check)" if a.no_check else ("PASS" if not problems else "FAIL"),
                  "problems": problems,
                  "step": {k: sinfo[k] for k in ("product", "schema", "mm", "points")} | {"bbox_model_mm": sinfo["bbox"],
                                                                                           "bbox_placed_mm": box},
                  "jlc_footprint": fpinfo, "jlc_symbol": syinfo,
                  "note": "JLC/EasyEDA footprint and symbol data: for comparison only, never a source (RQ-01, LIB-12)"}
        if a.dry_run or problems:
            print(json.dumps({k: report[k] for k in ("check", "problems")}))
            print("dry run: nothing stored" if a.dry_run and not problems else "nothing stored: ask the user (wrong model, or --no-check)")
            return 1 if problems else 0
        source = f"JLCPCB/EasyEDA {lcsc} via JLC2KiCadLib"
        if substitute:
            source += f" (SUBSTITUTE: model of {lcsc} used for {a.key}, user accepts at G1)"
            print(f"  note: {lcsc} is not this part's own LCSC number: stored as a marked substitute (LIB-13)")
        code = cad_register.main([step, "--footprint", fp, "--source", source,
                                  "--rot", *[str(v) for v in place["rotate_deg"]],
                                  "--offset", *[str(v) for v in place["offset_mm"]]] + (["--global-root", root] if root else []))
        if code:
            return code
        out = lc.gpath("models", "jlc", f"{lcsc}.json", root=root)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1)
        print(f"recorded footprint / symbol data in {os.path.relpath(out, lc.gpath(root=root))}")
        return 0
    finally:
        if a.keep:
            print(f"kept {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
