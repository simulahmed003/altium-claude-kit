"""merge_plan.py - wire clean-up plan for rule q (read-only, prints JSON).
   python merge_plan.py <sheet.SchDoc> [removed part ...]
Treats the pins of the removed parts as gone and drops wire stubs that end only at them, then joins every
pair of wires that meet end to end in a straight line at a point with exactly 2 branches. Collinear wire is
only joined, never extended, so connectivity cannot change. Output: wires to delete (their full vertex lists),
segments to place, junctions to delete (fewer than 3 branches afterwards)."""
import json, sys
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0])
from dots import load, segments, branches

path, removed = sys.argv[1], set(sys.argv[2:])
wires, pins, junc = load(path)
pins = {k: v for k, v in pins.items() if k[0] not in removed}
removed_tips = {v for k, v in load(path)[1].items() if k[0] in removed}

# 1. drop stubs that ended only on a removed pin (repeat until stable)
dropped = []
changed = True
while changed:
    changed = False
    segs = segments(wires)
    for i, w in enumerate(wires):
        if w is None or len(w) != 2:
            continue
        for end in (w[0], w[-1]):
            if end in removed_tips:
                dirs, ph = branches(end, segs, pins)
                if len(dirs) == 1 and not ph:          # nothing else there
                    dropped.append(w)
                    wires[i] = None
                    changed = True
                    break
    wires = [w for w in wires if w is not None] if changed else wires

# 2. break multi-point wires into 2-point segments where they take part in a straight join
segs = segments(wires)
explode = set()
for p in {q for a, b2, _ in segs for q in (a, b2)}:
    dirs, ph = branches(p, segs, pins)
    if not ph and len(dirs) == 2 and dirs[0][2] != dirs[1][2] and (dirs[0][0] + dirs[1][0], dirs[0][1] + dirs[1][1]) == (0, 0):
        explode |= {dirs[0][2], dirs[1][2]}
new = []
for i, w in enumerate(wires):
    if i in explode and len(w) > 2:
        new += [[w[k], w[k + 1]] for k in range(len(w) - 1)]
    else:
        new.append(w)
wires = new
# 3. join straight end-to-end pairs at 2-branch points
merged_from = []
while True:
    segs = segments(wires)
    pts = {p for a, b, _ in segs for p in (a, b)}
    done = False
    for p in sorted(pts):
        dirs, ph = branches(p, segs, pins)
        if ph or len(dirs) != 2:
            continue
        (dx1, dy1, i), (dx2, dy2, j) = dirs
        if i == j or (dx1 + dx2, dy1 + dy2) != (0, 0):
            continue
        wi, wj = wires[i], wires[j]
        if len(wi) != 2 or len(wj) != 2:
            continue                                     # only plain 2-point wires are joined
        a = wi[0] if wi[1] == p else wi[1]
        b = wj[0] if wj[1] == p else wj[1]
        merged_from += [wi, wj]
        wires = [w for k, w in enumerate(wires) if k not in (i, j)] + [[a, b]]
        done = True
        break
    if not done:
        break

orig = load(path)[0]
deleted = [w for w in orig if w not in wires]
placed = [w for w in wires if w not in orig]
segs = segments(wires)
bad_j = []
for p in junc:
    dirs, ph = branches(p, segs, pins)
    if len({(d[0], d[1]) for d in dirs}) + len(ph) < 3:
        bad_j.append(p)
print(json.dumps(dict(delete_wires=deleted, place_wires=placed, delete_junctions=bad_j, stubs_dropped=dropped)))
