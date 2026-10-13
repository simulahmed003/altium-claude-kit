"""conn_check.py - every pin on the sheet against the planned net table (rule p).

   python conn_check.py <sheet.SchDoc> <plan.json>
Run after ANY library update, part move or rewire, on the SAVED sheet, before reporting.
Reads only the file (no Altium): pin ends, wires, net labels, power ports and manual junctions, and builds the
netlist the way Altium does:
  - wire vertices and segment ends join; a wire end / pin end / label / port on a wire's interior joins that wire
  - two wires that only cross do NOT join unless a manual junction sits on the crossing
  - net labels and power ports with the same text are one net
Prints PASS / FAIL per part (unconnected pin, wrong net, pin missing) and exits 1 on any mismatch.
Also runs the rule-q junction check (dots.py): a dot exactly where 3+ connection items meet, no crossings, no
overlapping wires, no straight end-to-end joins of separate wires.
"""
import json, sys
from collections import defaultdict
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0])
from schdoc_text import records, mil


def frac_len(r):
    return int(r.get("PINLENGTH", 0)) * 10 + int(r.get("PINLENGTH_FRAC", 0)) // 10000


def on_seg(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if x1 == x2 == x:
        return min(y1, y2) <= y <= max(y1, y2)
    if y1 == y2 == y:
        return min(x1, x2) <= x <= max(x1, x2)
    return False


def build(path):
    recs = records(path)[1:]
    comps = {i for i, r in enumerate(recs) if r.get("RECORD") == "1"}
    des = {int(r["OWNERINDEX"]): r.get("TEXT") for r in recs if r.get("RECORD") == "34"}
    pins, segs, named, junctions = {}, [], [], []
    for r in recs:
        rec = r.get("RECORD")
        if rec == "2" and int(r.get("OWNERINDEX", -1)) in comps:
            x, y, ln = mil(r, "X"), mil(r, "Y"), frac_len(r)
            dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][int(r.get("PINCONGLOMERATE", 0)) & 3]
            pins[(des[int(r["OWNERINDEX"])], r.get("DESIGNATOR"))] = (x + dx * ln, y + dy * ln)
        elif rec == "27":
            n = int(r.get("LOCATIONCOUNT", 0))
            pts = [(int(r.get(f"X{k}", 0)) * 10 + int(r.get(f"X{k}_FRAC", 0)) // 10000,
                    int(r.get(f"Y{k}", 0)) * 10 + int(r.get(f"Y{k}_FRAC", 0)) // 10000) for k in range(1, n + 1)]
            segs += [(pts[k], pts[k + 1]) for k in range(len(pts) - 1)]
        elif rec in ("25", "17"):
            named.append((r.get("TEXT", ""), (mil(r, "X"), mil(r, "Y"))))
        elif rec == "29":
            junctions.append((mil(r, "X"), mil(r, "Y")))
    parent = {}

    def f(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def u(a, b):
        parent[f(a)] = f(b)

    for i, (a, b) in enumerate(segs):
        u(("s", i), ("p", a))
        u(("s", i), ("p", b))
    ends = {p for s in segs for p in s}
    for p in ends | set(junctions):
        for i, (a, b) in enumerate(segs):
            if on_seg(p, a, b):
                u(("p", p), ("s", i))
    for k, t in pins.items():
        u(("pin",) + k, ("p", t))
        for i, (a, b) in enumerate(segs):
            if on_seg(t, a, b):
                u(("pin",) + k, ("s", i))
    for p in pins.values():            # pin end on another pin end
        u(("p", p), ("p", p))
    for name, p in named:
        u(("name", name), ("p", p))
        for i, (a, b) in enumerate(segs):
            if on_seg(p, a, b):
                u(("name", name), ("s", i))
    root_name = {}
    for name, _ in named:
        root_name[f(("name", name))] = name
    groups = defaultdict(list)
    for k in pins:
        groups[f(("pin",) + k)].append(k)
    got = {}
    for root, ks in groups.items():
        nm = root_name.get(root)
        for k in ks:
            got[k] = nm if nm else (None if len(ks) == 1 else "unnamed:" + "+".join(f"{a}.{b}" for a, b in sorted(ks)))
    return got


def main(sheet, plan_path):
    got = build(sheet)
    plan = json.load(open(plan_path))
    want = {(p["refdes"], p["pin"]): n["name"] for n in plan["nets"] for p in n["pins"]}
    parts = sorted({k[0] for k in want} | {k[0] for k in got}, key=lambda s: (s.rstrip("0123456789"), int(s[len(s.rstrip("0123456789")):] or 0)))
    bad = 0
    for part in parts:
        why = []
        for k in sorted(set(want) | set(got)):
            if k[0] != part:
                continue
            w, g = want.get(k), got.get(k, "missing")
            if k not in want:
                why.append(f"pin {k[1]} not in plan (on {g})")
            elif g is None:
                why.append(f"pin {k[1]} UNCONNECTED (plan {w})")
            elif g == "missing":
                why.append(f"pin {k[1]} missing on sheet (plan {w})")
            elif g != w:
                why.append(f"pin {k[1]} on {g} (plan {w})")
        bad += len(why)
        n = sum(1 for k in want if k[0] == part)
        print(f"{part:5} {'FAIL' if why else 'PASS'}  {'; '.join(why) or f'{n} pins on plan nets'}")
    nets = {v for v in got.values() if v}
    print(f"\n{len(got)} pins on sheet, {len(want)} in plan, {len(nets)} named nets, {bad} mismatches")
    from dots import analyse                     # rule q: junction dots
    q = analyse(sheet)
    keys = ("dot<3", "missing", "overlap", "cross", "merge")
    for k in keys:
        for line in q.get(k, []):
            print(f"rule q ({k}): {line}")
    qbad = sum(len(q.get(k, [])) for k in keys)
    print(f"rule q: {len(q.get('dots', []))} junction dots, {qbad} problems")
    return 1 if bad or qbad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
