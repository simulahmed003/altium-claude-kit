"""dots.py - junction analysis of a saved .SchDoc (rule q). Read-only.
   python dots.py <sheet.SchDoc>
Branches at a point = wire directions leaving it (a wire passing straight through counts 2, a wire end 1)
+ pin ends + power ports there (a port on a wire is a connection item; Altium dots it). Altium draws an automatic dot at >= 3 branches; rule q wants a dot exactly there.
Reports: manual junctions with < 3 branches, overlapping / duplicate wire segments (they create false dots),
wires crossing without a junction, and straight end-to-end joins of separate wires (merge candidates)."""
import sys
from collections import defaultdict
PORTS = []
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0])
from schdoc_text import records, mil


def load(path):
    recs = records(path)[1:]
    comps = {i for i, r in enumerate(recs) if r.get("RECORD") == "1"}
    des = {int(r["OWNERINDEX"]): r.get("TEXT") for r in recs if r.get("RECORD") == "34"}
    wires, pins, junc = [], {}, []
    global PORTS
    PORTS = []
    for r in recs:
        rec = r.get("RECORD")
        if rec == "27":
            n = int(r.get("LOCATIONCOUNT", 0))
            wires.append([(int(r.get(f"X{k}", 0)) * 10, int(r.get(f"Y{k}", 0)) * 10) for k in range(1, n + 1)])
        elif rec == "2" and int(r.get("OWNERINDEX", -1)) in comps:
            x, y = mil(r, "X"), mil(r, "Y")
            ln = int(r.get("PINLENGTH", 0)) * 10
            dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][int(r.get("PINCONGLOMERATE", 0)) & 3]
            pins[(des[int(r["OWNERINDEX"])], r.get("DESIGNATOR"))] = (x + dx * ln, y + dy * ln)
        elif rec == "17":
            PORTS.append((mil(r, "X"), mil(r, "Y")))
        elif rec == "29":
            junc.append((mil(r, "X"), mil(r, "Y")))
    return wires, pins, junc


def segments(wires):
    return [(w[k], w[k + 1], i) for i, w in enumerate(wires) for k in range(len(w) - 1)]


def branches(p, segs, pins):
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
    pin_here = [k for k, t in pins.items() if t == p] + [("port", "")] * PORTS.count(p)
    return dirs, pin_here


def analyse(path):
    wires, pins, junc = load(path)
    segs = segments(wires)
    pts = {p for a, b, _ in segs for p in (a, b)} | set(pins.values()) | set(junc)
    out = defaultdict(list)
    for p in sorted(pts):
        dirs, ph = branches(p, segs, pins)
        uniq = {(d[0], d[1]) for d in dirs}
        n = len(uniq) + len(ph)
        if len(uniq) < len([d for d in dirs]):
            # two wires leaving in the same direction = overlap
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
            out["dots"].append(f"{p}: {n} branches -> dot ({'stored' if p in junc else 'not stored'})"
                               + (f" pins {ph}" if ph else ""))
        # straight end-to-end join of two separate wires with nothing else = merge candidate
        if n == 2 and not ph:
            wids = {d[2] for d in dirs}
            if len(wids) == 2 and len(uniq) == 2 and (sum(d[0] for d in uniq), sum(d[1] for d in uniq)) == (0, 0):
                out["merge"].append(f"{p}: two wires meet end to end in a straight line")
    # crossings without a junction
    for i, (a, b, wi) in enumerate(segs):
        for c, d, wj in segs[i + 1:]:
            if a[0] == b[0] and c[1] == d[1]:
                x = (a[0], c[1])
            elif a[1] == b[1] and c[0] == d[0]:
                x = (c[0], a[1])
            else:
                continue
            on1 = min(a[1], b[1]) < x[1] < max(a[1], b[1]) if a[0] == b[0] else min(a[0], b[0]) < x[0] < max(a[0], b[0])
            on2 = min(c[1], d[1]) < x[1] < max(c[1], d[1]) if c[0] == d[0] else min(c[0], d[0]) < x[0] < max(c[0], d[0])
            if on1 and on2 and x not in junc:
                out["cross"].append(f"{x}: wires cross without a junction")
    return out


if __name__ == "__main__":
    res = analyse(sys.argv[1])
    for k in ("dot<3", "missing", "overlap", "cross", "merge", "dots"):
        print(f"== {k}: {len(res.get(k, []))}")
        for line in res.get(k, []):
            print("  ", line)
