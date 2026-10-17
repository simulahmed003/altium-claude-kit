"""gen_sym.py - symbol JSON for altium-lib write_schlib from a short spec (rules LIB-01, LIB-02, LIB-03).

Usage:
  python gen_sym.py <spec.json> <out.json> [--check lib.SchLib]
spec.json:
  {"pcblib": "<p>.PcbLib",                (file name only: Altium finds it among the project libraries)
   "symbols": [{"name": "R_10k_1%_0603", "kind": "R", "prefix": "R", "footprint": "RESC1608_0603",
                "value": "10k", "mfr": "..", "mpn": "..", "lcsc": "C25804", "tier": "Basic",
                "datasheet": "x.pdf", "description": ".."}, ...]}
kind: R | C | L (two-pin, 400 / 200 / 400 mil between pin ends), testpoint (one pin), connector ("pins": n,
100 mil pitch, pins on the left), ic ("body": [x1, y1, x2, y2] and "pins": [{designator, name, x, y,
length, orientation, electrical_type}] in schematic units, 10 = 100 mil; optional "lines", "polygons", "arcs").
Every symbol gets the same style: line colour, line width 1, Designator + Comment "=Value" visible, every
other parameter hidden. Pin ends must land on the 100 mil grid (checked here; exit 1 if not).
--check compares the generated pin ends with an existing library (same symbol names). Exit 0 / 1.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_io import schlib_symbols, pin_tip

LINE = 0x800000   # BGR dark blue
FILL = 0xB0FFFF   # light yellow
DIR = {"left": 2, "right": 0, "up": 1, "down": 3}


def params(s):
    p = [dict(name="Comment", value="=Value", hidden=False, font_id=1, color=LINE),
         dict(name="Value", value=s.get("value", "-"), hidden=True)]
    for k, f in (("Manufacturer", "mfr"), ("MPN", "mpn"), ("LCSC", "lcsc"), ("JLCPCB Type", "tier"), ("Datasheet", "datasheet")):
        p.append(dict(name=k, value=s.get(f) or "-", hidden=True))
    return p


def _pin(d, x, y, length, orient, **kw):
    return dict(designator=str(d), name=kw.pop("name", str(d)), x=x, y=y, length=length, orientation=orient, **kw)


def geometry(s):
    k = s["kind"]
    quiet = dict(show_name=False, show_designator=False)
    if k == "R":
        return dict(rectangles=[dict(x1=-10, y1=-4, x2=10, y2=4, filled=False, line_color=LINE, line_width=1)],
                    text=(-10, 14, -10, -24), pins=[_pin(1, -10, 0, 10, "left", **quiet), _pin(2, 10, 0, 10, "right", **quiet)])
    if k == "C":
        return dict(lines=[dict(x1=-2, y1=-8, x2=-2, y2=8, line_width=1, color=LINE),
                           dict(x1=2, y1=-8, x2=2, y2=8, line_width=1, color=LINE)],
                    text=(-10, 18, -10, -28), pins=[_pin(1, -2, 0, 8, "left", **quiet), _pin(2, 2, 0, 8, "right", **quiet)])
    if k == "L":
        return dict(arcs=[dict(x=c, y=0, radius=2.5, start_angle=0, end_angle=180, line_width=1, color=LINE)
                          for c in (-7.5, -2.5, 2.5, 7.5)],
                    text=(-10, 12, -10, -20), pins=[_pin(1, -10, 0, 10, "left", **quiet), _pin(2, 10, 0, 10, "right", **quiet)])
    if k == "testpoint":
        return dict(arcs=[dict(x=0, y=0, radius=3, line_width=1, color=LINE)], text=(-5, 6, -5, -14),
                    pins=[_pin(1, -3, 0, 7, "left", **quiet)])
    if k == "connector":
        n = int(s["pins"])
        return dict(rectangles=[dict(x1=0, y1=-10 * n + 5, x2=15, y2=5, line_color=LINE, fill_color=FILL, line_width=1)],
                    text=(0, 29, 0, 15), pins=[_pin(i + 1, 0, -10 * i, 10, "left", show_name=False) for i in range(n)])
    if k == "ic":
        x1, y1, x2, y2 = s["body"]
        g = dict(rectangles=[dict(x1=x1, y1=y1, x2=x2, y2=y2, line_color=LINE, fill_color=FILL, line_width=1)],
                 pins=[dict(p, designator=str(p["designator"])) for p in s["pins"]],
                 text=tuple(s.get("text", (x1 + 10, y2 + 24, x1 + 10, y2 + 10))))
        for key in ("lines", "arcs"):
            if key in s:
                g[key] = [dict(dict(line_width=1, color=LINE), **e) for e in s[key]]
        if "polygons" in s:
            g["polygons"] = [dict(dict(line_width=1, line_color=LINE, fill_color=LINE), **e) for e in s["polygons"]]
        return g
    raise ValueError(f"{s['name']}: unknown kind {k}")


def build(spec):
    out, errs = [], []
    for s in spec["symbols"]:
        g = geometry(s)
        dx, dy, cx, cy = g.pop("text")
        ps = params(s)
        ps[0].update(x=cx, y=cy)
        sym = dict(name=s["name"], designator_prefix=s.get("prefix", s["kind"][0].upper()),
                   description=s.get("description", ""), parameters=ps,
                   footprints=[dict(name=s["footprint"], library_path=spec["pcblib"])],
                   designator_x=dx, designator_y=dy, **g)
        for p in sym["pins"]:
            t = tip(p)
            if t[0] % 10 or t[1] % 10:
                errs.append(f"{s['name']} pin {p['designator']}: end {t} off the 100 mil grid")
        if len(s.get("description", "")) > 256:
            errs.append(f"{s['name']}: description over 256 characters")
        out.append(sym)
    return out, errs


def tip(p):
    return pin_tip(dict(x=p["x"], y=p["y"], rot=DIR[p["orientation"]], length=p["length"]))


def compare(syms, lib):
    errs = []
    have = schlib_symbols(lib)
    for s in syms:
        h = have.get(s["name"])
        if h is None:
            errs.append(f"{s['name']}: not in {lib}")
            continue
        a = sorted((p["designator"], tip(p)) for p in s["pins"])
        b = sorted((p["designator"], pin_tip(p)) for p in h["pins"])
        if a != b:
            errs.append(f"{s['name']}: pin ends differ: generated {a} vs library {b}")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("spec"); ap.add_argument("out")
    ap.add_argument("--check", help="existing .SchLib to compare pin ends with")
    a = ap.parse_args(argv)
    syms, errs = build(json.load(open(a.spec, encoding="utf-8")))
    if a.check:
        errs += compare(syms, a.check)
    json.dump(syms, open(a.out, "w"), indent=1)
    for e in errs:
        print("FAIL", e)
    print(f"{len(syms)} symbols written to {a.out}, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
