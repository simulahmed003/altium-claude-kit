"""sch_plan.py - schematic coordinate plan: check it before placing, or read it back from a sheet (rule SCH-R).

Usage:
  python sch_plan.py check <layout.json> <lib.SchLib> <plan.json> [--grid 100]
  python sch_plan.py from-sheet <sheet.SchDoc> <layout.json>       (write the layout of a saved sheet)
  python sch_plan.py pins <layout.json> <lib.SchLib>               (print every pin end the layout produces)
layout.json (mil):
  {"parts":  {"U1": {"lib_ref": "U_X", "x": 7300, "y": 8200, "o": 0, "m": false}},   o = 0..3 (x 90 deg CCW)
   "wires":  [[[x, y], [x, y], ...]],             polylines
   "ports":  [{"net": "GND", "x": .., "y": .., "style": "gnd_power", "o": 3}],
   "labels": [{"net": "FB", "x": .., "y": ..}],
   "boxes":  [{"title": "..", "x1": .., "y1": .., "x2": .., "y2": ..}]}
Pin ends come from the REAL library pins (altium_io), not from a hand table. check = grid, orthogonal wires,
a pin touching a wire mid-segment, then the same netlist / dots checks as conn_check.py on the planned geometry.
Exit 0 when the layout is clean, 1 otherwise.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_io import schlib_symbols, pin_tip, sheet_model
import conn_check, dots


def transform(dx, dy, o, m):
    if m:
        dx = -dx
    for _ in range(o % 4):
        dx, dy = -dy, dx
    return dx, dy


def part_pins(layout, syms):
    pins, errs = {}, []
    for ref, p in layout["parts"].items():
        s = syms.get(p["lib_ref"])
        if s is None:
            errs.append(f"{ref}: symbol {p['lib_ref']} not in the library")
            continue
        for pin in s["pins"]:
            tx, ty = pin_tip(pin)
            dx, dy = transform(tx * 10, ty * 10, p.get("o", 0), p.get("m", False))
            pins[(ref, pin["designator"])] = (p["x"] + dx, p["y"] + dy)
    return pins, errs


def model(layout, syms):
    pins, errs = part_pins(layout, syms)
    m = dict(pins=pins, wires=[[tuple(v) for v in w] for w in layout.get("wires", [])],
             labels=[(l["net"], (l["x"], l["y"])) for l in layout.get("labels", [])],
             ports=[(q["net"], (q["x"], q["y"]), q.get("o", 0)) for q in layout.get("ports", [])],
             junctions=[tuple(j) for j in layout.get("junctions", [])],
             designators=list(layout["parts"]))
    return m, errs


def check(layout, syms, plan, grid=100):
    m, errs = model(layout, syms)
    for w in m["wires"]:
        for a, b in zip(w, w[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                errs.append(f"diagonal wire {a}-{b}")
        for v in w:
            if v[0] % grid or v[1] % grid:
                errs.append(f"wire vertex {v} off the {grid} mil grid")
    for ref, p in layout["parts"].items():
        if p["x"] % grid or p["y"] % grid:
            errs.append(f"part {ref} origin off the grid")
    ends = {v for w in m["wires"] for v in (w[0], w[-1])} | {v for w in m["wires"] for v in w}
    segs = [(a, b) for w in m["wires"] for a, b in zip(w, w[1:])]
    for k, t in m["pins"].items():
        if t[0] % grid or t[1] % grid:
            errs.append(f"pin end {k[0]}.{k[1]} {t} off the grid")
        if any(conn_check.on_seg(t, a, b) for a, b in segs) and t not in ends:
            errs.append(f"pin {k[0]}.{k[1]} {t} touches a wire mid-segment (end the wire on the pin)")
    # stored dots are not in a plan: assume Altium adds one wherever 3+ items meet (rule SCH-Q)
    q = dots.analyse_model(dict(m, junctions=[]))
    pts = [line.split(":")[0] for line in q.get("dots", [])]
    m["junctions"] = [tuple(int(v) for v in s.strip("()").split(",")) for s in pts]
    lines, extra, s = conn_check.check(m, plan)
    errs += [f"{part}: {text}" for part, ok, text in lines if not ok] + extra
    q = dots.analyse_model(m)
    errs += [f"{k}: {line}" for k in ("overlap", "cross", "merge") for line in q.get(k, [])]
    return errs, s


def from_sheet(sheet):
    m = sheet_model(sheet)
    parts = {}
    for d, cs in m["comps"].items():
        c = cs[0]
        parts[d] = dict(lib_ref=c["lib_ref"], x=c["x"], y=c["y"], o=c["o"], m=c["mirrored"])
    return dict(parts=parts, wires=[[list(v) for v in w] for w in m["wires"]],
                ports=[dict(net=t, x=p[0], y=p[1], o=o) for t, p, o in m["ports"]],
                labels=[dict(net=t, x=p[0], y=p[1]) for t, p in m["labels"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("layout"); c.add_argument("schlib"); c.add_argument("plan")
    c.add_argument("--grid", type=int, default=100)
    f = sub.add_parser("from-sheet")
    f.add_argument("sheet"); f.add_argument("layout")
    p = sub.add_parser("pins")
    p.add_argument("layout"); p.add_argument("schlib")
    a = ap.parse_args(argv)
    if a.cmd == "from-sheet":
        lay = from_sheet(a.sheet)
        json.dump(lay, open(a.layout, "w"), indent=1)
        print(f"{len(lay['parts'])} parts, {len(lay['wires'])} wires written to {a.layout}")
        return 0
    lay = json.load(open(a.layout, encoding="utf-8"))
    syms = schlib_symbols(a.schlib)
    if a.cmd == "pins":
        pins, errs = part_pins(lay, syms)
        for k in sorted(pins):
            print(f"{k[0]}.{k[1]} {pins[k]}")
        for e in errs:
            print("FAIL", e)
        return 1 if errs else 0
    errs, s = check(lay, syms, json.load(open(a.plan, encoding="utf-8")), a.grid)
    for e in errs:
        print("FAIL", e)
    print(f"{s['pins_on_sheet']} pins, {s['nets']} named nets, {len(errs)} problems")
    print("RESULT", "FAIL" if errs else "PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
