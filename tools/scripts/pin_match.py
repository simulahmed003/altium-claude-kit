"""pin_match.py - every symbol against its footprint, read from the library files (rules LIB-01, LIB-02, LIB-03).

Usage:
  python pin_match.py <lib.SchLib> <lib.PcbLib> [--style] [--pcblib MORE.PcbLib ...]
Per symbol:
  - exactly one footprint link, and the footprint exists in the PcbLib(s)
  - pin numbers = pad numbers (same multiset), no hidden pins, no two pins on one connection point
  - every pin connection point on the 100 mil grid (body side may be off grid: 80 mil cap / 70 mil TP pins)
  - --style: visible text = Designator + Comment "=Value" only (every other parameter hidden)
Exit 0 when every symbol passes, 1 otherwise. Read-only.
"""
import argparse, os, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_io import schlib_symbols, pcblib_footprints, pin_tip


def check_symbol(sym, pads, style=False):
    why = []
    links = sym["footprints"]
    if len(links) != 1:
        why.append(f"{len(links)} footprint links")
    if pads is None:
        why.append(f"footprint {links[0] if links else '-'} not found")
    else:
        pn, pd = Counter(p["designator"] for p in sym["pins"]), Counter(pads)
        if pn != pd:
            why.append(f"pins {sorted(pn.elements())} vs pads {sorted(pd.elements())}")
    hidden = [p["designator"] for p in sym["pins"] if p["hidden"]]
    if hidden:
        why.append(f"hidden pins {hidden}")
    pos = Counter(pin_tip(p) for p in sym["pins"])
    stacked = [p["designator"] for p in sym["pins"] if pos[pin_tip(p)] > 1]
    if stacked:
        why.append(f"stacked pins {stacked}")
    off = [p["designator"] for p in sym["pins"] if any(v % 10 for v in pin_tip(p))]
    if off:
        why.append(f"pin ends off the 100 mil grid {off}")
    if style:
        vis = [(p["name"], p["text"]) for p in sym["params"] if not p["hidden"] and p["name"] != "Designator"]
        if vis != [("Comment", "=Value")]:
            why.append(f"visible parameters {vis} (want only Comment '=Value')")
    return why


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("schlib")
    ap.add_argument("pcblib")
    ap.add_argument("--pcblib", dest="more", action="append", default=[], help="extra PcbLib to search")
    ap.add_argument("--style", action="store_true", help="also check visible parameters (LIB-02)")
    a = ap.parse_args(argv)
    syms = schlib_symbols(a.schlib)
    fps = {}
    for p in [a.pcblib] + a.more:
        fps.update({k: v["pads"] for k, v in pcblib_footprints(p).items()})
    fails = 0
    print(f"{'symbol':24} {'footprint':22} result  detail")
    for s in sorted(syms):
        sym = syms[s]
        fp = sym["footprints"][0] if sym["footprints"] else "-"
        why = check_symbol(sym, fps.get(fp), a.style)
        fails += bool(why)
        detail = "; ".join(why) or f"{len(sym['pins'])} pins = {len(fps[fp])} pads"
        print(f"{s:24} {fp:22} {'FAIL' if why else 'PASS'}    {detail}")
    print(f"\n{len(syms)} symbols, {len(syms) - fails} PASS, {fails} FAIL")
    return 1 if fails or not syms else 0


if __name__ == "__main__":
    sys.exit(main())
