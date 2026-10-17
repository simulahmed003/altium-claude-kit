"""conn_check.py - every pin on the saved sheet against plan.json (rules SCH-P, SCH-J, SCH-O, SCH-Q, LIB-08).

Usage:
  python conn_check.py <sheet.SchDoc | records.json> <plan.json> [--no-dots] [--tp-prefix TP]
Builds the netlist from the file the way Altium does (no Altium needed):
  - wire vertices and segment ends join; a wire end / pin end / label / port on a wire's interior joins it
  - two wires that only cross do NOT join unless a junction sits on the crossing
  - net labels and power ports with the same text are one net
Reports per part: unconnected pin, wrong net, pin missing on the sheet, pin not in the plan.
Also: duplicate designators (SCH-J), more than one test point on a net (SCH-O), and the dots.py junction check
(SCH-Q, skip with --no-dots). plan.json: {"nets": [{"name": .., "pins": [{"refdes": .., "pin": ..}]}]}.
Run after ANY library update, part move or rewire, on the SAVED sheet. Exit 0 when clean, 1 otherwise.
"""
import argparse, json, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_io import sheet_model
import dots


def on_seg(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if x1 == x2 == x:
        return min(y1, y2) <= y <= max(y1, y2)
    if y1 == y2 == y:
        return min(x1, x2) <= x <= max(x1, x2)
    return False


def netlist(m):
    """{(designator, pin): net name | None (unconnected) | 'unnamed:...'}"""
    segs = [(w[k], w[k + 1]) for w in m["wires"] for k in range(len(w) - 1)]
    named = m["labels"] + [(t, p) for t, p, _ in m["ports"]]
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
    for p in ends | set(m["junctions"]):
        for i, (a, b) in enumerate(segs):
            if on_seg(p, a, b):
                u(("p", p), ("s", i))
    for k, t in m["pins"].items():
        u(("pin",) + k, ("p", t))
        for i, (a, b) in enumerate(segs):
            if on_seg(t, a, b):
                u(("pin",) + k, ("s", i))
    for name, p in named:
        u(("name", name), ("p", p))
        for i, (a, b) in enumerate(segs):
            if on_seg(p, a, b):
                u(("name", name), ("s", i))
    root_name = {f(("name", n)): n for n, _ in named}
    groups = defaultdict(list)
    for k in m["pins"]:
        groups[f(("pin",) + k)].append(k)
    got = {}
    for root, ks in groups.items():
        nm = root_name.get(root)
        for k in ks:
            got[k] = nm if nm else (None if len(ks) == 1 else "unnamed:" + "+".join(f"{a}.{b}" for a, b in sorted(ks)))
    return got


def natural(s):
    m = re.match(r"(\D*)(\d*)", s)
    return (m.group(1), int(m.group(2) or 0), s)


def check(m, plan, tp_prefix="TP"):
    """Returns (per-part lines [(part, ok, text)], extra problem lines, summary dict)."""
    got = netlist(m)
    want = {(p["refdes"], str(p["pin"])): n["name"] for n in plan["nets"] for p in n["pins"]}
    lines, bad = [], 0
    for part in sorted({k[0] for k in want} | {k[0] for k in got}, key=natural):
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
        lines.append((part, not why, "; ".join(why) or f"{n} pins on plan nets"))
    extra = []
    for d, c in Counter(m["designators"]).items():
        if c > 1:
            extra.append(f"duplicate designator {d} ({c} parts)")
    tp_nets = defaultdict(list)
    for (d, _), net in got.items():
        if re.fullmatch(re.escape(tp_prefix) + r"\d+", d) and net:
            tp_nets[net].append(d)
    for net, tps in sorted(tp_nets.items()):
        if len(tps) > 1:
            extra.append(f"net {net} has {len(tps)} test points {sorted(tps, key=natural)} (rule: one per net)")
    summary = dict(pins_on_sheet=len(got), pins_in_plan=len(want), nets=len({v for v in got.values() if v}),
                   mismatches=bad)
    return lines, extra, summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("sheet")
    ap.add_argument("plan")
    ap.add_argument("--no-dots", action="store_true", help="skip the junction-dot check")
    ap.add_argument("--tp-prefix", default="TP")
    a = ap.parse_args(argv)
    m = sheet_model(a.sheet)
    plan = json.load(open(a.plan, encoding="utf-8"))
    lines, extra, s = check(m, plan, a.tp_prefix)
    for part, ok, text in lines:
        print(f"{part:5} {'PASS' if ok else 'FAIL'}  {text}")
    for e in extra:
        print("FAIL", e)
    print(f"\n{s['pins_on_sheet']} pins on sheet, {s['pins_in_plan']} in plan, {s['nets']} named nets, "
          f"{s['mismatches']} mismatches, {len(extra)} other problems")
    qbad = 0
    if not a.no_dots:
        q = dots.analyse_model(m)
        for k in dots.PROBLEMS:
            for line in q.get(k, []):
                print(f"rule q ({k}): {line}")
        qbad = sum(len(q.get(k, [])) for k in dots.PROBLEMS)
        print(f"rule q: {len(q.get('dots', []))} junction dots, {qbad} problems")
    ok = not (s["mismatches"] or extra or qbad)
    print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
