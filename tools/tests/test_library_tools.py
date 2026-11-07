"""Tests for the library tools brought in from the batch library job (2026-11): lib_std_check, lib_dump,
kicad_models, fp_review (CLI only), library_build (plan + component step), altium_io.same_content, the rule pack.
No Altium, no pywin32 needed."""
import contextlib, io, json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "scripts"))
BUILD = os.path.abspath(os.path.join(HERE, "..", "library_build"))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, BUILD)
import altium_io, lib_std_check, lib_dump, kicad_models, fp_review, rules_lint, lib_params  # noqa: E402
import build as lib_build  # noqa: E402

G = os.path.join(HERE, "fixtures", "buck")
SCH, PCB = os.path.join(G, "buck.SchLib"), os.path.join(G, "buck.PcbLib")


def run(mod, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = mod.main(list(argv))
    return code, buf.getvalue()


class StdCheck(unittest.TestCase):
    def test_values(self):
        ok = ["10k", "100nF", "4.7uH", "50V", "-40°C to 85°C", "1%", "", "=Value", "22mOhm", "0.05"]
        for v in ok:
            self.assertEqual(lib_std_check.value_problems("Value", v), [], v)
        bad = {"4.7 uF": "space", "2,2uF": "comma", "2.20uF": "trailing", "N/A": "empty", "4.7µH": "non-ASCII",
               "-40~85": "to", "2 (dual)": "one value", "1mfd": "mfd"}
        for v, why in bad.items():
            self.assertIn(why, " ".join(lib_std_check.value_problems("Value", v)), v)

    def test_resistance(self):
        r = lambda v: lib_std_check.value_problems("Resistance", v)
        self.assertEqual(r("10R") + r("4.7k") + r("49.9R"), [])
        self.assertTrue(r("10") and r("1000R") and r("10K"))

    def test_free_text_not_checked(self):
        self.assertEqual(lib_std_check.value_problems("Description", "RES 10k 1% 0.1W 0603 (thin film)"), [])
        self.assertTrue(lib_std_check.value_problems("Manufacturer 1", "N/A"))     # unknown is still empty

    def test_description(self):
        d = lib_std_check.description_problems
        self.assertEqual(d("Resistors", "RES 10k 1% 0.1W 0603", "RES 10k 1% 0.1W 0603"), [])
        self.assertIn("start with RES", " ".join(d("Resistors", "R 10k", "R 10k")))
        self.assertIn("differ", " ".join(d("Capacitors", "CAP 1u", "CAP 2u")))
        self.assertIn("no hidden", " ".join(d("Sensors", "TEMP SENSOR", None)))
        self.assertEqual(d("Sensors", "anything goes", "anything goes"), [])      # no pattern yet (R9)

    def test_cli(self):
        code, out = run(lib_std_check, SCH)
        self.assertEqual(code, 1)                 # the buck parts predate the standard
        self.assertIn("16 components", out)
        self.assertEqual(run(lib_std_check, "--value", "100nF")[0], 0)
        self.assertEqual(run(lib_std_check, "--value", "100 nF")[0], 1)


class Dump(unittest.TestCase):
    def test_footprint_mm(self):
        fp = altium_io.pcblib_footprints(PCB)["CAPC1608_0603"]
        pads = sorted(lib_dump.footprint_geometry(fp)["pads"], key=lambda p: p["n"])
        self.assertAlmostEqual(pads[0]["x"], -0.725, places=3)
        self.assertAlmostEqual(pads[1]["sx"], 0.95, places=3)
        self.assertEqual(pads[0]["layer"], "Top Layer")

    def test_symbol_mil(self):
        s = lib_dump.symbol_geometry(altium_io.schlib_symbols(SCH)["U_LMR33630ADDA"])
        vin = next(p for p in s["pins"] if p["name"] == "VIN")
        self.assertEqual((vin["x"], vin["L"], vin["el"]), (-500, 100, 7))
        self.assertTrue(s["rects"])

    def test_dump_files(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(run(lib_dump, PCB, SCH, "--out", t)[0], 0)
            pcb = open(os.path.join(t, "_pcblib_dump.txt"), encoding="utf-8").read()
            self.assertEqual(pcb.count("FP|"), 8)
            fs = json.load(open(os.path.join(t, "fpsum.json"), encoding="utf-8"))
            self.assertEqual(fs["C_100n_50V_X7R_0603"]["footprint"], "CAPC1608_0603")


class KicadModels(unittest.TestCase):
    MOD = ('(footprint "R_0603_1608Metric"\n (pad "1" smd roundrect (at -0.825 0) (size 0.8 0.95))\n'
           ' (pad "2" smd roundrect (at 0.825 0) (size 0.8 0.95))\n)\n')

    def test_best_rotation(self):
        ours = [("1", 0, 0.8), ("2", 0, -0.8)]                    # our footprint stands upright
        err, a, dx, dy, n, no = kicad_models.best_rotation(ours, kicad_models.kicad_pads(self.MOD))
        self.assertIn(a, (90, 270))
        self.assertLess(err, 0.05)
        self.assertEqual((n, no), (2, 2))

    def test_plan_and_csv(self):
        with tempfile.TemporaryDirectory() as t:
            fpd = os.path.join(t, "footprints", "Resistor_SMD.pretty")
            stp = os.path.join(t, "3dmodels", "Resistor_SMD.3dshapes")
            os.makedirs(fpd)
            os.makedirs(stp)
            open(os.path.join(fpd, "R_0603_1608Metric.kicad_mod"), "w").write(self.MOD)
            open(os.path.join(stp, "R_0603_1608Metric.step"), "w").write("ISO-10303-21;\n")
            mp = os.path.join(t, "map.json")
            json.dump({"RESC1608_0603": "Resistor_SMD/R_0603_1608Metric",
                       "SOIC8_MS012": "Resistor_SMD/R_0603_1608Metric"}, open(mp, "w"))
            out = os.path.join(t, "out")
            code, txt = run(kicad_models, PCB, "--kicad", t, "--map", mp, "--out", out)
            self.assertEqual(code, 0)
            self.assertIn("MISMATCH  SOIC8_MS012", txt)
            self.assertEqual(open(os.path.join(out, "models.csv")).read().strip(),
                             "RESC1608_0603,R_0603_1608Metric.step,0,0.0,0.0")
            self.assertTrue(os.path.isfile(os.path.join(out, "R_0603_1608Metric.step")))


class SameContent(unittest.TestCase):
    def test_ids_ignored_content_not(self):
        fp = altium_io.pcblib_footprints(PCB)["SOIC8_MS012"]
        other = dict(fp, prims=[])
        for typ, blocks in fp["prims"]:
            blocks = list(blocks)
            if typ == 12:
                blocks[0] = blocks[0].replace(b"MODELID={", b"MODELID={0")
            if typ == 2 and len(blocks[4]) >= 158:
                b = bytearray(blocks[4])
                b[130] ^= 0xFF                                    # a pad unique-ID byte
                blocks[4] = bytes(b)
            other["prims"].append((typ, blocks))
        self.assertTrue(altium_io.same_content("f", fp, other))
        moved = dict(fp, prims=[(t, [b[0][:13] + bytes([b[0][13] ^ 1]) + b[0][14:]] + list(b[1:])) if t == 4 else (t, b)
                                for t, b in fp["prims"]])
        self.assertFalse(altium_io.same_content("f", fp, moved))
        s = altium_io.schlib_symbols(SCH)["R_10k_1%_0603"]
        s2 = dict(s, records=[dict(r, DESCRIPTION="") if r.get("RECORD") == "45" else r for r in s["records"]])
        self.assertTrue(altium_io.same_content("c", s, s2))


class ReviewAndBuild(unittest.TestCase):
    def test_fp_review_help_without_packages(self):
        code, out = run(fp_review, "--help")
        self.assertEqual(code, 0)
        self.assertIn("review.json", out)

    @unittest.skipUnless(__import__("importlib").util.find_spec("olefile"), "olefile not installed (install.cmd /full)")
    def test_build_example_plan_and_component(self):
        code, out = run(lib_build, "--example")
        plan = json.loads(out)
        self.assertIn("parts", plan)
        from buildsch import components
        lib_build.log.clear()
        new, sk, recs, pins, desc, h = lib_build.build_component(
            {"symbols": {}}, components(SCH), lib_params.load(), "R_10k_1%_0603",
            {"type": "Resistors", "sub": "Chip", "fp": "RESC1608X55N"})
        items = {(r[1], r[2]) for r in lib_build.log}
        self.assertIn(("parameter added", "Category"), items)
        self.assertIn(("footprint", "RESC1608_0603"), items)
        self.assertTrue(any(r[1] == "parameter removed" and r[2] == "LCSC" for r in lib_build.log))
        with self.assertRaises(SystemExit):
            lib_build.allowed_params(lib_params.load(), "No", "Such", {})


class Pack(unittest.TestCase):
    def test_library_pack_is_current(self):
        rules = rules_lint.parse(os.path.join(ROOT, "rules"))
        self.assertEqual(rules_lint.pack_errors(rules, os.path.join(ROOT, "rules")), [])
        text = rules_lint.pack_text(rules, "LIBRARY_PACK.md")
        self.assertIn("| LIB-01 |", text)
        self.assertIn("| LIB-38 |", text)


if __name__ == "__main__":
    unittest.main()
