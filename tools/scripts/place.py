"""place.py - check a PCB placement plan before and after placing (rules PCB-02, PCB-12). Offline.

Usage:
  python place.py <place.json> [--fab rules/fab-profiles/jlcpcb_2layer.json] [--catalog components.json]
                  [--pcb board.PcbDoc] [--tol 0.05]
place.json (mm, origin bottom-left):
  {"board": {"w": 40, "h": 30},
   "parts": {"U1": {"x": 19.0, "y": 14.6, "rot": 180, "side": "top", "footprint": "LMR33630_HSOIC8_DDA"}},
   "courtyards": {"LMR33630_HSOIC8_DDA": [6.2, 5.4]}}        (optional; else from the catalog)
Courtyard = [w, h] mm at rotation 0, centred on the part origin; 90 / 270 swap w and h.
Checks: rotation a multiple of 90; courtyard inside the board minus the fab copper-to-edge margin;
no two courtyards on the same side overlap (touching is allowed); every part has a courtyard.
--pcb: also compare the plan with the saved PcbDoc (position within --tol mm, rotation, missing / extra parts),
e.g. to verify that U1 and Q1 are back where the plan puts them.
Exit 0 when clean, 1 otherwise.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import altium_io

MIL = 0.0254


def courtyard_map(plan, catalog):
    cy = dict(plan.get("courtyards", {}))
    if catalog:
        for c in json.load(open(catalog, encoding="utf-8")).get("footprints", []):
            if c.get("courtyard_mm") and c["name"] not in cy:
                cy[c["name"]] = c["courtyard_mm"]
    return cy


def boxes(plan, cy):
    out, errs = {}, []
    for ref, p in plan["parts"].items():
        if p.get("rot", 0) % 90:
            errs.append(f"{ref}: rotation {p['rot']} is not a multiple of 90")
        size = cy.get(p.get("footprint"))
        if not size:
            errs.append(f"{ref}: no courtyard for footprint {p.get('footprint')} (add courtyard_mm to the catalog)")
            continue
        w, h = size if p.get("rot", 0) % 180 == 0 else size[::-1]
        out[ref] = (p["x"] - w / 2, p["y"] - h / 2, p["x"] + w / 2, p["y"] + h / 2, p.get("side", "top"))
    return out, errs


def check(plan, cy, edge):
    b, errs = boxes(plan, cy)
    W, H = plan["board"]["w"], plan["board"]["h"]
    for ref, (x1, y1, x2, y2, _) in b.items():
        if x1 < edge or y1 < edge or x2 > W - edge or y2 > H - edge:
            errs.append(f"{ref}: courtyard ({x1:.2f}, {y1:.2f})-({x2:.2f}, {y2:.2f}) closer than {edge} mm to the board edge")
    refs = sorted(b)
    for i, a in enumerate(refs):
        for c in refs[i + 1:]:
            A, C = b[a], b[c]
            if A[4] == C[4] and A[0] < C[2] and C[0] < A[2] and A[1] < C[3] and C[1] < A[3]:
                errs.append(f"{a} / {c}: courtyards overlap")
    return errs


def compare_pcb(plan, pcb, tol):
    errs = []
    have = altium_io.pcbdoc_components(pcb)
    for ref, p in plan["parts"].items():
        h = have.get(ref)
        if h is None:
            errs.append(f"{ref}: in the plan, not on the PCB")
            continue
        x, y = h["x"] * MIL, h["y"] * MIL
        if abs(x - p["x"]) > tol or abs(y - p["y"]) > tol or round(h["rotation"]) % 360 != p.get("rot", 0) % 360:
            errs.append(f"{ref}: PCB ({x:.2f}, {y:.2f}) rot {h['rotation']:.0f} vs plan ({p['x']}, {p['y']}) rot {p.get('rot', 0)}")
    for ref in sorted(set(have) - set(plan["parts"])):
        errs.append(f"{ref}: on the PCB, not in the plan")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("plan")
    ap.add_argument("--fab", default=os.path.join(ROOT, "rules", "fab-profiles", "jlcpcb_2layer.json"))
    ap.add_argument("--catalog")
    ap.add_argument("--pcb")
    ap.add_argument("--tol", type=float, default=0.05)
    a = ap.parse_args(argv)
    plan = json.load(open(a.plan, encoding="utf-8"))
    edge = json.load(open(a.fab, encoding="utf-8"))["design"]["copper_to_edge_mm"]
    errs = check(plan, courtyard_map(plan, a.catalog), edge)
    if a.pcb:
        errs += compare_pcb(plan, a.pcb, a.tol)
    for e in errs:
        print("FAIL", e)
    print(f"{len(plan['parts'])} parts, edge margin {edge} mm, {len(errs)} problems")
    print("RESULT", "FAIL" if errs else "PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
