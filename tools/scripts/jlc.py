"""jlc.py - JLCPCB assembly files from the project data, offline (rules FAB-01, FAB-04, RQ-03).

Usage:
  python jlc.py bom <plan.json> <out_bom.csv> [--catalog components.json] [--schlib lib.SchLib] [--exclude J1 J2]
  python jlc.py cpl <board.PcbDoc> <out_cpl.csv> [--exclude J1 J2]
  python jlc.py parse <bom.csv>                     (read a JLCPCB BOM back and check it)
BOM columns: Comment, Designator, Footprint, LCSC Part #  (one row per identical part, designators joined).
CPL columns: Designator, Mid X, Mid Y, Layer, Rotation    (mm; Mid X/Y = component origin from the PcbDoc).
Parts without an LCSC number, DNP parts and --exclude parts (hand-soldered) are left out and listed.
LCSC numbers come from plan.json "lcsc", else the catalog entry for the part's lib_ref, else the symbol's
LCSC parameter (--schlib). A part not marked lcsc_verified in the catalog is NOT VERIFIED (RQ-03): exit 1. Column names follow the JLCPCB upload templates as recorded in FAB-04 (PROPOSED, re-check
the JLCPCB help page before the first order). Only run for a real order after gate_check.py G4 passes.
Exit 0 when the file is complete and every part verified, 1 otherwise.
"""
import argparse, csv, json, os, re, sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import altium_io

BOM_COLS = ["Comment", "Designator", "Footprint", "LCSC Part #"]
CPL_COLS = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]


def natural(s):
    m = re.match(r"(\D*)(\d*)", s)
    return (m.group(1), int(m.group(2) or 0))


def lcsc_lookup(catalog=None, schlibs=()):
    """{symbol name: (lcsc, verified or None)} from the catalog, else from the symbol's LCSC parameter."""
    out = {}
    for lib in schlibs:
        for name, s in altium_io.schlib_symbols(lib).items():
            v = next((p["text"] for p in s["params"] if p["name"].upper() == "LCSC"), "")
            out[name] = (v, None)
    if catalog:
        for c in json.load(open(catalog, encoding="utf-8")).get("components", []):
            out[c.get("symbol")] = (c.get("lcsc", ""), bool(c.get("lcsc_verified")))
    return out


def bom_rows(plan, catalog=None, exclude=(), schlibs=()):
    look = lcsc_lookup(catalog, schlibs)
    groups, left_out, notes = OrderedDict(), [], []
    for p in plan["parts"]:
        ref = p["refdes"]
        lcsc, ver = look.get(p.get("lib_ref"), ("", None))
        lcsc = (p.get("lcsc") or lcsc or "").strip()
        dnp = p.get("dnp") or str(p.get("value", "")).upper() == "DNP"
        if ref in exclude or dnp or not lcsc or lcsc == "-":
            left_out.append(f"{ref} ({'excluded' if ref in exclude else 'DNP' if dnp else 'no LCSC number'})")
            continue
        key = (p.get("value", ""), p.get("footprint", ""), lcsc)
        groups.setdefault(key, []).append(ref)
        if not ver:
            notes.append(f"{ref} {lcsc}: NOT VERIFIED" + ("" if catalog else " (no --catalog given)"))
    rows = [dict(zip(BOM_COLS, (v, ",".join(sorted(refs, key=natural)), fp, l))) for (v, fp, l), refs in groups.items()]
    return rows, left_out, sorted(set(notes))


def cpl_rows(pcb, exclude=()):
    rows = []
    for ref, c in sorted(altium_io.pcbdoc_components(pcb).items(), key=lambda t: natural(t[0] or "")):
        if ref in exclude:
            continue
        rows.append({"Designator": ref, "Mid X": f"{c['x'] * 0.0254:.3f}mm", "Mid Y": f"{c['y'] * 0.0254:.3f}mm",
                     "Layer": "Bottom" if str(c["layer"]).upper() == "BOTTOM" else "Top",
                     "Rotation": f"{c['rotation']:.0f}"})
    return rows


def parse_bom(path):
    errs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if r.fieldnames != BOM_COLS:
            errs.append(f"columns {r.fieldnames} != {BOM_COLS}")
        rows = list(r)
    seen = {}
    for i, row in enumerate(rows, 2):
        if not re.fullmatch(r"C\d+", (row.get("LCSC Part #") or "").strip()):
            errs.append(f"line {i}: LCSC Part # '{row.get('LCSC Part #')}' is not a C-number")
        for d in (row.get("Designator") or "").split(","):
            d = d.strip()
            if d in seen:
                errs.append(f"line {i}: designator {d} also on line {seen[d]}")
            seen[d] = i
    return rows, errs


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bom"); b.add_argument("plan"); b.add_argument("out")
    b.add_argument("--catalog"); b.add_argument("--exclude", nargs="*", default=[])
    b.add_argument("--schlib", nargs="*", default=[], help="read LCSC parameters from these libraries")
    c = sub.add_parser("cpl"); c.add_argument("pcb"); c.add_argument("out"); c.add_argument("--exclude", nargs="*", default=[])
    p = sub.add_parser("parse"); p.add_argument("bom")
    a = ap.parse_args(argv)
    if a.cmd == "bom":
        rows, left, notes = bom_rows(json.load(open(a.plan, encoding="utf-8")), a.catalog, set(a.exclude), a.schlib)
        write_csv(a.out, BOM_COLS, rows)
        print(f"{len(rows)} BOM lines written to {a.out}; left out: {', '.join(left) or 'none'}")
        for n in notes:
            print("FAIL", n)
        return 1 if notes or not rows else 0
    if a.cmd == "cpl":
        rows = cpl_rows(a.pcb, set(a.exclude))
        write_csv(a.out, CPL_COLS, rows)
        print(f"{len(rows)} placements written to {a.out}")
        return 0 if rows else 1
    rows, errs = parse_bom(a.bom)
    for e in errs:
        print("FAIL", e)
    print(f"{len(rows)} BOM lines, {len(errs)} problems")
    return 1 if errs or not rows else 0


if __name__ == "__main__":
    sys.exit(main())
