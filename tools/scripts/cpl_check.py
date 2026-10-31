"""cpl_check.py - make a pick-and-place (CPL) file right for the assembler, by numbers, never by eye (rule FAB-06).

Run from the workspace folder in cmd.exe, for example:
  python tools\\scripts\\cpl_check.py fit --ours U104.kicad_mod --jlc library\\models\\jlc\\C2838168.json
  python tools\\scripts\\cpl_check.py convert board-pos.csv out\\board_CPL.csv --src kicad --offsets ai\\cpl_offsets.json
  python tools\\scripts\\cpl_check.py check out\\board_CPL.csv --bom out\\board_BOM.csv

Commands:
  fit      --ours F --jlc F [--name N] [--save ai\\cpl_offsets.json --key FOOTPRINT]
           Fit the assembler's footprint (JLC/EasyEDA, from cad_fetch / JLC2KiCadLib) onto ours by PIN NUMBER and
           print the rotation offset (deg) and centre shift (mm) to add to the CPL. Pads whose numbers do not land on
           the same-numbered pad are listed (wrong pin numbering in a library, e.g. E and B swapped on a SOT-23).
           F may be: a .kicad_mod file, a JLC record library\\models\\jlc\\<C>.json, or a JSON pad list
           [{"number": "1", "x": 0.0, "y": 0.0}, ...] (mm, y up). KiCad files are y down and are converted.
           --save writes the result into an offsets table under --key (the footprint name used in the CPL source).
  convert  <in.csv> <out.csv> --src kicad|altium|jlc [--offsets F] [--footprint-col NAME] [--flip-axis y|x]
           Read a KiCad .pos/.csv or an Altium Pick Place .csv/.txt, write JLC columns
           Designator, Mid X, Mid Y, Layer, Rotation (mm, degrees 0-359).
           Side rule: KiCad bottom parts -> JLC rotation = (180 - rotation) mod 360 (checked on a 103-part bottom-side
           board, 2026-10-30). Altium: no side rule known yet, rotation copied; confirm with the JLC preview (FAB-06)
           and record the result in rules/fab-profiles/jlcpcb_assembly.json "cpl_side_rule".
           --offsets: per-footprint (or per-designator) table from `fit`: rotation offset added after the side rule,
           centre shift rotated with the part (mirrored for bottom parts).
  check    <cpl.csv> [--bom bom.csv] [--bbox XMIN,YMIN,XMAX,YMAX]
           Columns present, every designator once, rotation 0-359, layer Top/Bottom, positions inside the board box,
           CPL designators = BOM designators (DNP and hand-soldered parts left out on both sides).
Formulas (y up, angles counter-clockwise, offset theta from `fit` means ours = R(theta)*jlc + t):
  top:    JLC = r + theta              position + R(r)*t
  bottom: JLC = 180 - r + theta        position + R(r)*M*t   (M = KiCad left-right flip, x -> -x)
Python standard library only. Exit 0 = PASS, 1 = FAIL.
"""
import argparse, csv, json, math, os, re, sys

CPL_COLS = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
TOL_MM = 0.05


# ---------- pads ----------
def pads_kicad_mod(text):
    """[(number, x, y)] in mm, y up, from a .kicad_mod (or one footprint block of a .kicad_pcb)."""
    out = []
    for m in re.finditer(r'\(pad\s+"?([^"\s)]*)"?\s+\w+\s+\w+[^()]*\(at\s+([-\d.]+)\s+([-\d.]+)', text):
        num, x, y = m.group(1), float(m.group(2)), float(m.group(3))
        if num:
            out.append((num, x, -y))
    return out


def load_pads(path):
    with open(path, encoding="utf-8") as f:
        s = f.read()
    if path.lower().endswith((".kicad_mod", ".kicad_pcb")) or s.lstrip().startswith("("):
        return pads_kicad_mod(s)
    d = json.loads(s)
    if isinstance(d, dict) and "jlc_footprint" in d:      # library\models\jlc\<C>.json from cad_fetch (KiCad frame)
        return [(str(p["number"]), float(p["x"]), -float(p["y"])) for p in d["jlc_footprint"]["pads"] if p.get("number")]
    if isinstance(d, dict) and "pads" in d:
        d = d["pads"]
    return [(str(p["number"]), float(p["x"]), float(p["y"])) for p in d if str(p.get("number", ""))]


def centroids(pads):
    """One point per pad number (a number on several pads, such as a thermal pad split, uses their mean)."""
    acc = {}
    for n, x, y in pads:
        a = acc.setdefault(n, [0.0, 0.0, 0])
        a[0] += x; a[1] += y; a[2] += 1
    return {n: (a[0] / a[2], a[1] / a[2]) for n, a in acc.items()}


def rot(theta_deg, x, y):
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    return c * x - s * y, s * x + c * y


def fit(ours, jlc):
    """Best rigid fit ours = R(theta)*jlc + t over common pad numbers. Returns dict."""
    a, b = centroids(ours), centroids(jlc)
    common = sorted(set(a) & set(b), key=lambda n: (len(n), n))
    if len(common) < 2:
        return {"ok": False, "error": f"only {len(common)} common pad numbers (ours {sorted(a)}, jlc {sorted(b)})"}
    ax = sum(a[n][0] for n in common) / len(common); ay = sum(a[n][1] for n in common) / len(common)
    bx = sum(b[n][0] for n in common) / len(common); by = sum(b[n][1] for n in common) / len(common)
    sxx = sxy = 0.0
    for n in common:
        px, py = b[n][0] - bx, b[n][1] - by
        qx, qy = a[n][0] - ax, a[n][1] - ay
        sxx += px * qx + py * qy
        sxy += px * qy - py * qx
    theta = math.degrees(math.atan2(sxy, sxx))
    snapped = round(theta / 90.0) * 90.0 % 360 if abs(((theta + 45) % 90) - 45) < 2 else theta % 360
    rx, ry = rot(snapped, bx, by)
    tx, ty = ax - rx, ay - ry
    resid = {}
    for n in common:
        x, y = rot(snapped, *b[n])
        resid[n] = math.hypot(x + tx - a[n][0], y + ty - a[n][1])
    bad = [n for n in common if resid[n] > TOL_MM]
    return {"ok": not bad, "theta": round(snapped, 3), "theta_raw": round(theta, 3), "shift_mm": [round(tx, 4), round(ty, 4)],
            "pads": len(common), "max_err_mm": round(max(resid.values()), 4), "misfit_pads": bad,
            "only_ours": sorted(set(a) - set(b)), "only_jlc": sorted(set(b) - set(a))}


# ---------- CPL in / out ----------
def num(s):
    m = re.search(r"-?\d+(\.\d+)?", str(s))
    if not m:
        raise ValueError(f"no number in {s!r}")
    v = float(m.group(0))
    return v * 0.0254 if "mil" in str(s).lower() else v


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    lines = [l for l in text.splitlines() if l.strip()]
    if lines and lines[0].startswith("#"):        # KiCad .pos (ascii): "# Ref Val Package PosX PosY Rot Side"
        hdr = lines[0].lstrip("#").split()
        return [dict(zip(hdr, l.split())) for l in lines[1:] if not l.startswith("#")]
    start = next((i for i, l in enumerate(lines) if re.search(r"designator|\bref\b", l, re.I)), 0)  # Altium report header
    return list(csv.DictReader(lines[start:]))


def pick(row, *names):
    low = {k.strip().lower(): v for k, v in row.items() if k}
    for n in names:
        if n.lower() in low and low[n.lower()] not in (None, ""):
            return low[n.lower()]
    return None


def norm(src_row):
    ref = pick(src_row, "Designator", "Ref")
    x = pick(src_row, "Mid X", "PosX", "Center-X(mm)", "Center-X", "Ref X", "X")
    y = pick(src_row, "Mid Y", "PosY", "Center-Y(mm)", "Center-Y", "Ref Y", "Y")
    r = pick(src_row, "Rotation", "Rot")
    side = (pick(src_row, "Layer", "Side", "TB") or "top").strip().lower()
    fp = pick(src_row, "Footprint", "Package")
    if ref is None or x is None or y is None or r is None:
        raise ValueError(f"row without designator/x/y/rotation: {src_row}")
    return {"ref": ref.strip(), "x": num(x), "y": num(y), "r": num(r) % 360,
            "bottom": side.startswith(("b", "bot")), "fp": (fp or "").strip()}


def to_jlc(p, src, offsets, flip_axis="y"):
    off = offsets.get(p["ref"]) or offsets.get(p["fp"]) or {}
    theta = float(off.get("theta", 0.0))
    tx, ty = off.get("shift_mm", [0.0, 0.0])
    if p["bottom"]:
        base = (180 - p["r"]) % 360 if src == "kicad" else p["r"]
        mtx, mty = (-tx, ty) if flip_axis == "y" else (tx, -ty)
        dx, dy = rot(p["r"], mtx, mty)
    else:
        base = p["r"]
        dx, dy = rot(p["r"], tx, ty)
    return {"Designator": p["ref"], "Mid X": f"{p['x'] + dx:.4f}mm", "Mid Y": f"{p['y'] + dy:.4f}mm",
            "Layer": "Bottom" if p["bottom"] else "Top", "Rotation": f"{round((base + theta) % 360, 3):g}"}


def split_designators(cell):
    out = []
    for d in re.split(r"[,;\s]+", cell or ""):
        if d:
            out.append(d.strip())
    return out


def check(cpl_path, bom_path=None, bbox=None):
    errs, refs = [], {}
    with open(cpl_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        missing = [c for c in CPL_COLS if c not in (r.fieldnames or [])]
        if missing:
            errs.append(f"CPL columns missing: {missing} (have {r.fieldnames})")
            return errs, 0
        rows = list(r)
    for i, row in enumerate(rows, 2):
        d = row["Designator"].strip()
        if d in refs:
            errs.append(f"line {i}: {d} also on line {refs[d]}")
        refs[d] = i
        try:
            rot_v, x, y = float(row["Rotation"]), num(row["Mid X"]), num(row["Mid Y"])
        except ValueError as e:
            errs.append(f"line {i}: {d}: {e}"); continue
        if not 0 <= rot_v < 360:
            errs.append(f"line {i}: {d}: rotation {rot_v} not in 0-359")
        if row["Layer"].strip() not in ("Top", "Bottom"):
            errs.append(f"line {i}: {d}: layer '{row['Layer']}' is not Top/Bottom")
        if bbox and not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
            errs.append(f"line {i}: {d}: ({x:.2f}, {y:.2f}) outside the board box {bbox}")
    if bom_path:
        with open(bom_path, newline="", encoding="utf-8-sig") as f:
            br = list(csv.DictReader(f))
        bom_refs = set()
        for row in br:
            for d in split_designators(row.get("Designator", "")):
                if re.search(r"\w\d+\s*-\s*\w*\d+", d):
                    errs.append(f"BOM designator range '{d}': list each designator (FAB-04)")
                bom_refs.add(d)
        only_cpl, only_bom = sorted(set(refs) - bom_refs), sorted(bom_refs - set(refs))
        if only_cpl:
            errs.append(f"in CPL, not in BOM: {only_cpl}")
        if only_bom:
            errs.append(f"in BOM, not in CPL: {only_bom}")
    return errs, len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit"); f.add_argument("--ours", required=True); f.add_argument("--jlc", required=True)
    f.add_argument("--save"); f.add_argument("--key"); f.add_argument("--note", default="")
    c = sub.add_parser("convert"); c.add_argument("src_file"); c.add_argument("out")
    c.add_argument("--src", choices=("kicad", "altium", "jlc"), required=True); c.add_argument("--offsets")
    c.add_argument("--flip-axis", choices=("y", "x"), default="y")
    k = sub.add_parser("check"); k.add_argument("cpl"); k.add_argument("--bom"); k.add_argument("--bbox")
    a = ap.parse_args(argv)

    if a.cmd == "fit":
        res = fit(load_pads(a.ours), load_pads(a.jlc))
        if "error" in res:
            print("FAIL", res["error"]); return 1
        print(f"rotation offset {res['theta']:g} deg (raw {res['theta_raw']:g}), centre shift x {res['shift_mm'][0]:g} mm, "
              f"y {res['shift_mm'][1]:g} mm, {res['pads']} pads, max error {res['max_err_mm']} mm")
        for lab, key in (("only in ours", "only_ours"), ("only in JLC", "only_jlc")):
            if res[key]:
                print(f"NOTE pad numbers {lab}: {res[key]}")
        if res["misfit_pads"]:
            print(f"FAIL pads {res['misfit_pads']} do not land on the same-numbered pad: pin numbering differs "
                  "(fix the library footprint, or ask the user), do not just rotate")
        if a.save and res["ok"]:
            if not a.key:
                print("FAIL --save needs --key <footprint name as written in the CPL source>"); return 1
            tab = json.load(open(a.save, encoding="utf-8")) if os.path.isfile(a.save) else {}
            tab[a.key] = {"theta": res["theta"], "shift_mm": res["shift_mm"], "jlc": os.path.basename(a.jlc),
                          "max_err_mm": res["max_err_mm"], "note": a.note}
            with open(a.save, "w", encoding="utf-8") as fh:
                json.dump(tab, fh, indent=1, sort_keys=True)
            print(f"saved {a.key} into {a.save}")
        return 0 if res["ok"] else 1

    if a.cmd == "convert":
        offsets = json.load(open(a.offsets, encoding="utf-8")) if a.offsets else {}
        offsets = {k: v for k, v in offsets.items() if not k.startswith("_")}
        rows = [to_jlc(norm(r), a.src, offsets, a.flip_axis) for r in read_rows(a.src_file)]
        with open(a.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CPL_COLS); w.writeheader(); w.writerows(rows)
        used = sorted({r["ref"] for r in map(norm, read_rows(a.src_file)) if r["ref"] in offsets or r["fp"] in offsets})
        print(f"{len(rows)} placements written to {a.out} ({sum(r['Layer'] == 'Bottom' for r in rows)} bottom); "
              f"library offsets applied to: {', '.join(used) or 'none'}")
        if a.src == "altium" and any(r["Layer"] == "Bottom" for r in rows):
            print("NOTE Altium bottom-side rule not confirmed yet: check every bottom part in the JLC preview (FAB-06)")
        return 0 if rows else 1

    bbox = [float(v) for v in a.bbox.split(",")] if a.bbox else None
    errs, n = check(a.cpl, a.bom, bbox)
    for e in errs:
        print("FAIL", e)
    print(f"{n} placements, {len(errs)} problems")
    return 1 if errs or not n else 0


if __name__ == "__main__":
    sys.exit(main())
