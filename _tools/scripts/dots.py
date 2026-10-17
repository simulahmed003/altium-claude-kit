"""dots.py - junction-dot analysis of a saved sheet (rules SCH-Q, SCH-E, TOOL-12). Read-only.

Usage:
  python dots.py <sheet.SchDoc | records.json>
Branches at a point = wire directions leaving it (a wire passing straight through counts 2, a wire end 1)
+ pin ends + power ports there. Altium draws an automatic dot at >= 3 branches; the rule wants a dot exactly there.
Reports (each one a problem):
  dot<3    stored junction with fewer than 3 connection items
  missing  3+ branches with no stored junction (close/reopen the sheet in Altium to rebuild them)
  overlap  two wires leaving a point in the same direction
  cross    wires crossing without a junction
  merge    two separate wires meeting end to end in a straight line
Exit 0 when there are no problems, 1 otherwise.
"""
import argparse, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_io import sheet_model

PROBLEMS = ("dot<3", "missing", "overlap", "cross", "merge")


def segments(wires):
    return [(w[k], w[k + 1], i) for i, w in enumerate(wires) for k in range(len(w) - 1)]


def branches(p, segs, pins, ports=()):
    dirs = []
    for a, b, i in segs:
        for q, o in ((a, b), (b, a)):
            if q == p:
                dirs.append(((o[0] > p[0]) - (o[0] < p[0]), (o[1] > p[1]) - (o[1] < p[1]), i))
        (x1, y1), (x2, y2) = a, b
        inside = (x1 == x2 == p[0] and min(y1, y2) < p[1] < max(y1, y2)) or \
                 (y1 == y2 == p[1] and min(x1, x2) < p[0] < max(x1, x2))
        if inside:
            d = (0, 1) if x1 == x2 else (1, 0)
            dirs += [(d[0], d[1], i), (-d[0], -d[1], i)]
    here = [k for k, t in pins.items() if t == p] + [("port", "")] * list(ports).count(p)
    return dirs, here


def analyse_model(m):
    wires, pins, junc = m["wires"], m["pins"], m["junctions"]
    ports = [p for _, p, _ in m["ports"]]
    segs = segments(wires)
    pts = {p for a, b, _ in segs for p in (a, b)} | set(pins.values()) | set(junc)
    out = defaultdict(list)
    for p in sorted(pts):
        dirs, ph = branches(p, segs, pins, ports)
        uniq = {(d[0], d[1]) for d in dirs}
        n = len(uniq) + len(ph)
        c = defaultdict(int)
        for d in dirs:
            c[(d[0], d[1])] += 1
        if any(v > 1 for v in c.values()):
            out["overlap"].append(f"{p}: overlapping wires leave in the same direction ({dict(c)})")
        if p in junc and n < 3:
            out["dot<3"].append(f"{p}: junction dot with only {n} connection items")
        if n >= 3 and p not in junc:
            out["missing"].append(f"{p}: {n} branches but no junction dot")
        if n >= 3:
            out["dots"].append(f"{p}: {n} branches" + (f" pins {ph}" if ph else ""))
        if n == 2 and not ph:
            wids = {d[2] for d in dirs}
            if len(wids) == 2 and len(uniq) == 2 and (sum(d[0] for d in uniq), sum(d[1] for d in uniq)) == (0, 0):
                out["merge"].append(f"{p}: two wires meet end to end in a straight line")
    for i, (a, b, _) in enumerate(segs):
        for c2, d, _ in segs[i + 1:]:
            if a[0] == b[0] and c2[1] == d[1]:
                x = (a[0], c2[1])
            elif a[1] == b[1] and c2[0] == d[0]:
                x = (c2[0], a[1])
            else:
                continue
            on1 = min(a[1], b[1]) < x[1] < max(a[1], b[1]) if a[0] == b[0] else min(a[0], b[0]) < x[0] < max(a[0], b[0])
            on2 = min(c2[1], d[1]) < x[1] < max(c2[1], d[1]) if c2[0] == d[0] else min(c2[0], d[0]) < x[0] < max(c2[0], d[0])
            if on1 and on2 and x not in junc:
                out["cross"].append(f"{x}: wires cross without a junction")
    return out


def analyse(path):
    return analyse_model(sheet_model(path))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("sheet")
    a = ap.parse_args(argv)
    res = analyse(a.sheet)
    for k in PROBLEMS + ("dots",):
        print(f"== {k}: {len(res.get(k, []))}")
        for line in res.get(k, []):
            print("  ", line)
    bad = sum(len(res.get(k, [])) for k in PROBLEMS)
    print(f"\n{len(res.get('dots', []))} junction dots, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
