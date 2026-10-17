"""make_fixtures.py - (re)build the test fixtures in _tools/tests/fixtures/ from the buck project (read-only there).

Usage:
  python make_fixtures.py [--project D:/EDA/projects/buck-12v-5v-3a]
Good fixtures (fixtures/buck/): copies of buck.SchLib, buck.PcbLib, buck__Buck.SchDoc, ai/plan.json, the sheet
records as JSON, the sheet layout (sch_plan from-sheet), and the round-trip library copies written by altium-lib.
Broken fixtures (fixtures/broken/): each one changes ONE thing so a checker must FAIL:
  plan_wrong_net.json      R1 pin 2 planned on VOUT instead of FB              -> conn_check FAIL
  sheet_dup_tp.json        TP4 designator renamed TP3 (duplicate designator)   -> conn_check FAIL
  sheet_moved_dot.json     one junction moved 100 mil off its point            -> dots FAIL
  sheet_text_on_wire.json  R1 designator moved onto the VOUT wire              -> sch_overlap FAIL
  sheet_off_grid.json      one wire vertex moved 50 mil                        -> sch_overlap (grid) + conn_check FAIL
  layout_missing_wire.json one wire removed from the layout                    -> sch_plan FAIL
  missing_fp.PcbLib        library with 2 of the 8 footprints                  -> pin_match FAIL
  place_overlap.json       two courtyards overlap, one part near the edge      -> place FAIL
  bom_bad.csv              a non-C-number and a duplicate designator           -> jlc parse FAIL
  calc_fail.json           FB divider with 1 % resistors against a 1 % limit   -> calcs_run FAIL
  rules/                   a rule without Status                               -> rules_lint FAIL
Run after the buck design changes on purpose; commit the result with the reason.
"""
import argparse, copy, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_tools", "scripts"))
import altium_io, sch_plan

FIX = os.path.join(HERE, "fixtures")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--project", default=os.path.join(ROOT, "projects", "buck-12v-5v-3a"))
    a = ap.parse_args(argv)
    good, bad = os.path.join(FIX, "buck"), os.path.join(FIX, "broken")
    os.makedirs(good, exist_ok=True)
    os.makedirs(os.path.join(bad, "rules"), exist_ok=True)
    p = a.project
    for src, dst in (("libs/buck.SchLib", "buck.SchLib"), ("libs/buck.PcbLib", "buck.PcbLib"),
                     ("hw/buck/buck__Buck.SchDoc", "buck__Buck.SchDoc"), ("ai/plan.json", "plan.json")):
        shutil.copyfile(os.path.join(p, src), os.path.join(good, dst))
    rt = os.path.join(ROOT, "_tools", "libraries", "_rt")
    if os.path.isdir(rt):
        shutil.copyfile(os.path.join(rt, "g1.SchLib"), os.path.join(good, "roundtrip.SchLib"))
        shutil.copyfile(os.path.join(rt, "g1.PcbLib"), os.path.join(good, "roundtrip.PcbLib"))
        shutil.copyfile(os.path.join(rt, "g1.PcbLib"), os.path.join(bad, "missing_fp.PcbLib"))
    sheet = os.path.join(good, "buck__Buck.SchDoc")
    recs = altium_io.sch_records(sheet)[1:]
    json.dump(recs, open(os.path.join(good, "sheet.json"), "w"), indent=0)
    lay = sch_plan.from_sheet(sheet)
    json.dump(lay, open(os.path.join(good, "layout.json"), "w"), indent=1)

    plan = json.load(open(os.path.join(good, "plan.json")))
    b = copy.deepcopy(plan)
    for n in b["nets"]:
        n["pins"] = [q for q in n["pins"] if not (q["refdes"] == "R1" and str(q["pin"]) == "2")]
        if n["name"] == "VOUT":
            n["pins"].append(dict(refdes="R1", pin="2"))
    json.dump(b, open(os.path.join(bad, "plan_wrong_net.json"), "w"), indent=1)

    def mutate(name, fn):
        r = copy.deepcopy(recs)
        fn(r)
        json.dump(r, open(os.path.join(bad, name), "w"), indent=0)

    def dup(r):
        next(x for x in r if x.get("RECORD") == "34" and x.get("TEXT") == "TP4")["TEXT"] = "TP3"
    mutate("sheet_dup_tp.json", dup)

    def move_dot(r):
        j = next(x for x in r if x.get("RECORD") == "29")
        j["LOCATION.X"] = str(int(j["LOCATION.X"]) + 10)
    mutate("sheet_moved_dot.json", move_dot)

    m = altium_io.sheet_model(sheet)
    vout = next(w for w in m["wires"] if len(w) >= 2 and w[0][1] == w[1][1] and abs(w[0][0] - w[1][0]) >= 600)

    def text_on_wire(r):
        d = next(x for x in r if x.get("RECORD") == "34" and x.get("TEXT") == "R1")
        d["LOCATION.X"], d["LOCATION.Y"] = str(min(vout[0][0], vout[1][0]) // 10 + 20), str(vout[0][1] // 10 - 3)
        d.pop("LOCATION_FRAC.X", None); d.pop("LOCATION_FRAC.Y", None)
    mutate("sheet_text_on_wire.json", text_on_wire)

    def off_grid(r):
        w = next(x for x in r if x.get("RECORD") == "27")
        w["X1_FRAC"] = "500000"                       # +50 mil
    mutate("sheet_off_grid.json", off_grid)

    l2 = copy.deepcopy(lay)
    l2["wires"] = l2["wires"][1:]
    json.dump(l2, open(os.path.join(bad, "layout_missing_wire.json"), "w"), indent=1)

    json.dump(dict(board=dict(w=20, h=15), courtyards={"A": [4, 3]},
                   parts={"U1": dict(x=5, y=5, rot=0, footprint="A"), "U2": dict(x=7, y=5, rot=90, footprint="A"),
                          "U3": dict(x=18.5, y=10, rot=0, footprint="A")}),
              open(os.path.join(bad, "place_overlap.json"), "w"), indent=1)
    json.dump(dict(board=dict(w=20, h=15), courtyards={"A": [4, 3]},
                   parts={"U1": dict(x=5, y=5, rot=0, footprint="A"), "U2": dict(x=9, y=5, rot=0, footprint="A"),
                          "U3": dict(x=15, y=10, rot=90, footprint="A")}),
              open(os.path.join(good, "place_ok.json"), "w"), indent=1)
    open(os.path.join(bad, "bom_bad.csv"), "w", newline="").write(
        "Comment,Designator,Footprint,LCSC Part #\r\n10k,\"R1,R2\",RESC1608_0603,C25804\r\n10k,R2,RESC1608_0603,25804\r\n")
    open(os.path.join(good, "bom_ok.csv"), "w", newline="").write(
        "Comment,Designator,Footprint,LCSC Part #\r\n10k,\"R1,R2\",RESC1608_0603,C25804\r\n100nF,C1,CAPC1608_0603,C14663\r\n")
    json.dump({"checks": [{"name": "divider 1 % parts", "fn": "divider_worst", "ref": 5.0,
                           "args": {"vref3": [0.985, 1.0, 1.015], "rt": 20000, "rb": 4990, "r_tol": 0.01},
                           "limits": {"lo_pct": [-1, 1], "hi_pct": [-1, 1]}}]},
              open(os.path.join(bad, "calc_fail.json"), "w"), indent=1)
    open(os.path.join(bad, "rules", "01_X.md"), "w").write(
        "# X\n\n### X-01 Broken rule\n- MUST: do a thing.\n- Why: test.\n- Check: checklist\n- Source: test\n")
    open(os.path.join(bad, "rules", "VERSION"), "w").write("0.0.0\n")
    print("fixtures written to", FIX)
    return 0


if __name__ == "__main__":
    sys.exit(main())
