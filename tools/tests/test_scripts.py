"""Fixture tests for tools/scripts: every checker PASSES its good fixture and FAILS its broken one.
Fixtures: tools/tests/fixtures (rebuild with make_fixtures.py). No Altium needed."""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)
G = os.path.join(HERE, "fixtures", "buck")
B = os.path.join(HERE, "fixtures", "broken")
f = lambda d, n: os.path.join(d, n)

import altium_io, pin_match, conn_check, dots, sch_overlap, merge_plan, sch_plan, gen_sym, calcs_run, place, jlc, \
    gate_check, rules_lint, first_run_test


def run(mod, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = mod.main(list(argv))
    return code, buf.getvalue()


class Help(unittest.TestCase):
    def test_every_script_has_help_and_docstring(self):
        for fn in sorted(os.listdir(SCRIPTS)):
            if fn.endswith(".py"):
                with self.subTest(fn):
                    src = open(f(SCRIPTS, fn), encoding="utf-8").read()
                    self.assertTrue(src.lstrip().startswith('"""'), "no module docstring")
                    r = subprocess.run([sys.executable, f(SCRIPTS, fn), "--help"], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, r.stderr[-300:])
                    self.assertIn("usage", r.stdout.lower())


class AltiumIO(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(altium_io.schlib_symbols(f(G, "buck.SchLib"))), 16)
        self.assertEqual(len(altium_io.pcblib_footprints(f(G, "buck.PcbLib"))), 8)
        m = altium_io.sheet_model(f(G, "buck__Buck.SchDoc"))
        self.assertEqual((len(m["comps"]), len(m["pins"])), (29, 66))

    def test_json_records_equal_binary(self):
        a, b = altium_io.sheet_model(f(G, "buck__Buck.SchDoc")), altium_io.sheet_model(f(G, "sheet.json"))
        self.assertEqual(a["pins"], b["pins"])
        self.assertEqual(a["wires"], b["wires"])

    def test_hash_survives_altium_lib_round_trip(self):
        s1, s2 = altium_io.schlib_symbols(f(G, "buck.SchLib")), altium_io.schlib_symbols(f(G, "roundtrip.SchLib"))
        p1, p2 = altium_io.pcblib_footprints(f(G, "buck.PcbLib")), altium_io.pcblib_footprints(f(G, "roundtrip.PcbLib"))
        for n in s2:
            self.assertEqual(altium_io.symbol_hash(s1[n]), altium_io.symbol_hash(s2[n]), n)
        for n in p2:
            self.assertEqual(altium_io.footprint_hash(p1[n]), altium_io.footprint_hash(p2[n]), n)

    def test_hash_sees_a_change(self):
        s = altium_io.schlib_symbols(f(G, "buck.SchLib"))["R_10k_1%_0603"]
        h = altium_io.symbol_hash(s)
        s["pins"][0] = dict(s["pins"][0], length=s["pins"][0]["length"] + 1)
        self.assertNotEqual(h, altium_io.symbol_hash(s))


class PinMatch(unittest.TestCase):
    def test_buck_16_of_16(self):
        code, out = run(pin_match, f(G, "buck.SchLib"), f(G, "buck.PcbLib"), "--style")
        self.assertEqual(code, 0)
        self.assertIn("16 symbols, 16 PASS, 0 FAIL", out)

    def test_missing_footprints_fail(self):
        code, out = run(pin_match, f(G, "buck.SchLib"), f(B, "missing_fp.PcbLib"))
        self.assertEqual(code, 1)
        self.assertIn("not found", out)

    def test_symbol_faults(self):
        sym = altium_io.schlib_symbols(f(G, "buck.SchLib"))["Q_AO4407C"]
        pads = altium_io.pcblib_footprints(f(G, "buck.PcbLib"))["SOIC8_MS012"]["pads"]
        self.assertEqual(pin_match.check_symbol(sym, pads, True), [])
        hid = dict(sym, pins=[dict(sym["pins"][0], hidden=True)] + sym["pins"][1:])
        self.assertTrue(any("hidden" in w for w in pin_match.check_symbol(hid, pads)))
        off = dict(sym, pins=[dict(sym["pins"][0], x=sym["pins"][0]["x"] + 5)] + sym["pins"][1:])
        self.assertTrue(any("grid" in w for w in pin_match.check_symbol(off, pads)))
        vis = dict(sym, params=[dict(p, hidden=False) for p in sym["params"]])
        self.assertTrue(any("visible" in w for w in pin_match.check_symbol(vis, pads, True)))
        self.assertTrue(any("pins" in w for w in pin_match.check_symbol(sym, pads[:-1])))


class ConnCheck(unittest.TestCase):
    def test_buck_pass(self):
        code, out = run(conn_check, f(G, "sheet.json"), f(G, "plan.json"))
        self.assertEqual(code, 0)
        self.assertIn("66 pins on sheet, 66 in plan, 11 named nets, 0 mismatches", out)
        self.assertIn("rule q: 37 junction dots, 0 problems", out)

    def test_wrong_net(self):
        code, out = run(conn_check, f(G, "sheet.json"), f(B, "plan_wrong_net.json"))
        self.assertEqual(code, 1)
        self.assertIn("R1    FAIL  pin 2 on FB (plan VOUT)", out)

    def test_duplicate_designator(self):
        code, out = run(conn_check, f(B, "sheet_dup_tp.json"), f(G, "plan.json"))
        self.assertEqual(code, 1)
        self.assertIn("duplicate designator TP3", out)

    def test_two_tps_on_one_net(self):
        m = altium_io.sheet_model(f(G, "sheet.json"))
        m["pins"][("TP9", "1")] = m["pins"][("TP4", "1")]
        m["designators"].append("TP9")
        plan = json.load(open(f(G, "plan.json")))
        _, extra, _ = conn_check.check(m, plan)
        self.assertTrue(any("test points" in e for e in extra))


class Dots(unittest.TestCase):
    def test_buck(self):
        self.assertEqual(run(dots, f(G, "sheet.json"))[0], 0)

    def test_moved_dot(self):
        code, out = run(dots, f(B, "sheet_moved_dot.json"))
        self.assertEqual(code, 1)
        self.assertIn("dot<3: 1", out)


class SchOverlap(unittest.TestCase):
    def test_buck_zero(self):
        code, out = run(sch_overlap, f(G, "sheet.json"))
        self.assertEqual(code, 0)
        self.assertIn("0 problems", out)

    def test_text_on_wire(self):
        code, out = run(sch_overlap, f(B, "sheet_text_on_wire.json"))
        self.assertEqual(code, 1)
        self.assertIn("on a wire: designator R1", out)

    def test_off_grid(self):
        code, out = run(sch_overlap, f(B, "sheet_off_grid.json"))
        self.assertEqual(code, 1)
        self.assertIn("grid: wire vertex", out)


class MergePlan(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(run(merge_plan, f(G, "sheet.json"))[0], 0)

    def test_removed_tp_joins_wires(self):
        res = merge_plan.plan(altium_io.sheet_model(f(G, "sheet.json")), ["TP5"])
        self.assertEqual(len(res["place_wires"]), 1)
        self.assertEqual(len(res["delete_junctions"]), 1)


class SchPlan(unittest.TestCase):
    def test_layout_from_sheet_passes(self):
        self.assertEqual(run(sch_plan, "check", f(G, "layout.json"), f(G, "buck.SchLib"), f(G, "plan.json"))[0], 0)

    def test_library_pins_match_sheet(self):
        m = altium_io.sheet_model(f(G, "sheet.json"))
        pins, errs = sch_plan.part_pins(json.load(open(f(G, "layout.json"))), altium_io.schlib_symbols(f(G, "buck.SchLib")))
        self.assertEqual(errs, [])
        self.assertEqual(pins, m["pins"])

    def test_missing_wire(self):
        code, out = run(sch_plan, "check", f(B, "layout_missing_wire.json"), f(G, "buck.SchLib"), f(G, "plan.json"))
        self.assertEqual(code, 1)
        self.assertIn("UNCONNECTED", out)


class GenSym(unittest.TestCase):
    def test_spec_reproduces_library(self):
        with tempfile.TemporaryDirectory() as t:
            code, out = run(gen_sym, f(G, "sym_spec.json"), f(t, "s.json"), "--check", f(G, "buck.SchLib"))
        self.assertEqual(code, 0, out)

    def test_off_grid_pin_fails(self):
        spec = json.load(open(f(G, "sym_spec.json")))
        u = next(s for s in spec["symbols"] if s["name"] == "U_LMR33630ADDA")
        u["pins"][0]["length"] = 7
        _, errs = gen_sym.build(spec)
        self.assertTrue(any("grid" in e for e in errs))


class Calcs(unittest.TestCase):
    def test_buck(self):
        code, out = run(calcs_run, f(G, "calc_inputs.json"))
        self.assertEqual(code, 0)
        self.assertIn("nom 5.008", out)
        self.assertIn("lo_pct -1.5,", out)
        self.assertIn("hi_pct 1.826", out)

    def test_limit_fails(self):
        self.assertEqual(run(calcs_run, f(B, "calc_fail.json"))[0], 1)


class Place(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(run(place, f(G, "place_ok.json"))[0], 0)

    def test_overlap_and_edge(self):
        code, out = run(place, f(B, "place_overlap.json"))
        self.assertEqual(code, 1)
        self.assertIn("U1 / U2: courtyards overlap", out)
        self.assertIn("U3: courtyard", out)


class Jlc(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(run(jlc, "parse", f(G, "bom_ok.csv"))[0], 0)
        code, out = run(jlc, "parse", f(B, "bom_bad.csv"))
        self.assertEqual(code, 1)
        self.assertIn("not a C-number", out)
        self.assertIn("designator R2 also", out)

    def test_bom_from_plan(self):
        rows, left, notes = jlc.bom_rows(json.load(open(f(G, "plan.json"))), exclude={"J1", "J2"},
                                         schlibs=[f(G, "buck.SchLib")])
        self.assertEqual(len(rows), 13)
        self.assertTrue(any(r["Designator"] == "C6,C7,C8,C9,C10,C11" for r in rows))
        self.assertTrue(notes)                     # nothing verified without a catalog


class GateCheck(unittest.TestCase):
    def make(self, t, gates):
        os.makedirs(f(t, "ai"))
        open(f(t, "gates.md"), "w").write("\n".join(f"- [{'x' if v else ' '}] **{k} x**" for k, v in gates.items()))
        json.dump({"rules_version": "1.0.0"}, open(f(t, "project.json"), "w"))

    def test_no_design_yet(self):
        with tempfile.TemporaryDirectory() as t:
            self.make(t, dict(G1=False, S1=False, G2=False, G3=False, G4=False))
            code, out = run(gate_check, "G1", t)
            self.assertEqual(code, 1)
            self.assertIn("no design yet", out)
            self.assertTrue(os.path.isfile(f(t, "ai/review/G1_evidence.md")))

    def test_g4_refused(self):
        with tempfile.TemporaryDirectory() as t:
            self.make(t, dict(G1=True, S1=True, G2=False, G3=True, G4=False))
            code, out = run(gate_check, "G4", t, "--no-write")
            self.assertEqual(code, 1)
            self.assertIn("G4 refused", out)

    def test_s1_on_buck_fixture(self):
        with tempfile.TemporaryDirectory() as t:
            self.make(t, dict(G1=True, S1=False, G2=False, G3=False, G4=False))
            os.makedirs(f(t, "libs")); os.makedirs(f(t, "hw/x"))
            for n in ("buck.SchLib", "buck.PcbLib"):
                shutil.copyfile(f(G, n), f(t, "libs/" + n))
            shutil.copyfile(f(G, "buck__Buck.SchDoc"), f(t, "hw/x/buck__Buck.SchDoc"))
            shutil.copyfile(f(G, "plan.json"), f(t, "ai/plan.json"))
            shutil.copyfile(f(G, "calc_inputs.json"), f(t, "ai/calc_inputs.json"))
            code, out = run(gate_check, "S1", t)
            self.assertEqual(code, 0, out)
            ev = open(f(t, "ai/review/S1_evidence.md"), encoding="utf-8").read()
            self.assertIn("rules VERSION", ev)
            self.assertIn("proj_run_erc", ev)


class RulesLint(unittest.TestCase):
    def test_broken_rule_fails(self):
        code, out = run(rules_lint, "--rules", f(B, "rules"))
        self.assertEqual(code, 1)
        self.assertIn("X-01: missing Status", out)


class FirstRunTest(unittest.TestCase):
    def test_parse_status(self):
        s = first_run_test.parse_status("Active bridge  : none\nAltium running : True\neda-agent loop : not responding\n")
        self.assertEqual(s["eda-agent loop"], "not responding")
        self.assertEqual(s["altium running"], "True")

    def test_tool_ran_needs_the_exact_line(self):
        self.assertTrue(first_run_test.tool_ran("ok\n" + first_run_test.DONE + "\n"))
        self.assertFalse(first_run_test.tool_ran("Bridge switch to 'eda' failed. Do NOT print " + first_run_test.DONE))

    def test_script_project_clash_between_servers(self):
        eda = ["u/EDA Agent/scripts/Altium_API.PrjScr"]
        coffee = ["m/server/AltiumScript/altium_api.PrjScr", "m/dev/sandbox/Sandbox.PrjScr",
                  "m/server/SandboxScript/Sandbox.PrjScr"]
        self.assertEqual(first_run_test.clashes(eda, coffee), ["altium_api.prjscr"])
        self.assertEqual(first_run_test.clashes(eda, coffee[1:]), [])

if __name__ == "__main__":
    unittest.main()
