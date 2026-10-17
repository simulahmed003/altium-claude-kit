"""merge_plan.py - wire clean-up plan for rule SCH-Q (read-only, prints JSON).

Usage:
  python merge_plan.py <sheet.SchDoc | records.json> [--removed REF ...] [--out plan.json]
Treats the pins of the removed parts as gone and drops wire stubs that end only at them, splits polylines
that take part in a straight join, then joins every pair of 2-point wires that meet end to end in a straight
line at a point with exactly 2 branches. Wire is only joined, never extended, so connectivity cannot change.
Output keys: delete_wires (full vertex lists - delete each by its polyline start), place_wires,
delete_junctions (fewer than 3 branches afterwards), stubs_dropped.
Exit 0 when the plan is empty (nothing to clean), 1 when there is work to do.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_io import sheet_model
from dots import segments, branches


def plan(m, removed=()):
    removed = set(removed)
    orig = [list(w) for w in m["wires"]]
    wires = [list(w) for w in orig]
    pins = {k: v for k, v in m["pins"].items() if k[0] not in removed}
    ports = [p for _, p, _ in m["ports"]]
    removed_tips = {v for k, v in m["pins"].items() if k[0] in removed}
    dropped, changed = [], True
    while changed:
        changed = False
        segs = segments(wires)
        for i, w in enumerate(wires):
            if len(w) != 2:
                continue
            for end in (w[0], w[-1]):
                if end in removed_tips:
                    dirs, ph = branches(end, segs, pins, ports)
                    if len(dirs) == 1 and not ph:
                        dropped.append(w)
                        wires = wires[:i] + wires[i + 1:]
                        changed = True
                        break
            if changed:
                break
    segs = segments(wires)
    explode = set()
    for p in {q for a, b, _ in segs for q in (a, b)}:
        dirs, ph = branches(p, segs, pins, ports)
        if not ph and len(dirs) == 2 and dirs[0][2] != dirs[1][2] and \
                (dirs[0][0] + dirs[1][0], dirs[0][1] + dirs[1][1]) == (0, 0):
            explode |= {dirs[0][2], dirs[1][2]}
    new = []
    for i, w in enumerate(wires):
        new += [[w[k], w[k + 1]] for k in range(len(w) - 1)] if i in explode and len(w) > 2 else [w]
    wires = new
    while True:
        segs = segments(wires)
        done = False
        for p in sorted({q for a, b, _ in segs for q in (a, b)}):
            dirs, ph = branches(p, segs, pins, ports)
            if ph or len(dirs) != 2:
                continue
            (dx1, dy1, i), (dx2, dy2, j) = dirs
            if i == j or (dx1 + dx2, dy1 + dy2) != (0, 0) or len(wires[i]) != 2 or len(wires[j]) != 2:
                continue
            a = wires[i][0] if wires[i][1] == p else wires[i][1]
            b = wires[j][0] if wires[j][1] == p else wires[j][1]
            wires = [w for k, w in enumerate(wires) if k not in (i, j)] + [[a, b]]
            done = True
            break
        if not done:
            break
    segs = segments(wires)
    bad_j = [p for p in m["junctions"]
             if len({(d[0], d[1]) for d in branches(p, segs, pins, ports)[0]}) + len(branches(p, segs, pins, ports)[1]) < 3]
    return dict(delete_wires=[w for w in orig if w not in wires], place_wires=[w for w in wires if w not in orig],
                delete_junctions=bad_j, stubs_dropped=dropped)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("sheet")
    ap.add_argument("--removed", nargs="*", default=[], help="designators of parts being deleted")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = plan(sheet_model(a.sheet), a.removed)
    txt = json.dumps(res)
    if a.out:
        open(a.out, "w").write(txt)
    print(txt)
    work = any(res[k] for k in res)
    print("RESULT", "work to do" if work else "clean", file=sys.stderr)
    return 1 if work else 0


if __name__ == "__main__":
    sys.exit(main())
