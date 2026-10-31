"""Tests for the production tools: cpl_check.py, bom_check.py, fab_package.py, jlc_quote.py (FAB-04..08, RQ-08).
Each test builds its own small files in a temp folder. No Altium needed."""
import contextlib, io, json, os, shutil, sys, tempfile, unittest, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "scripts")))
import cpl_check, bom_check, fab_package, jlc_quote, new_project


def run(mod, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = mod.main(list(argv))
    return code, buf.getvalue()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


BOM_HDR = "Comment,Designator,Footprint,LCSC Part #,Quantity,Manufacturer,MPN,Mouser Part Number,DigiKey Part Number\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)


class Fit(Base):
    SOIC = [("1", -2.7, 1.905), ("2", -2.7, 0.635), ("3", -2.7, -0.635), ("4", -2.7, -1.905),
            ("5", 2.7, -1.905), ("6", 2.7, -0.635), ("7", 2.7, 0.635), ("8", 2.7, 1.905)]

    def test_recovers_rotation_and_shift(self):
        # JLC footprint = ours turned by -90 deg and moved; the fit must give theta 90 and the shift back
        jlc = []
        for n, x, y in self.SOIC:
            rx, ry = cpl_check.rot(-90, x - 0.3, y + 0.2)
            jlc.append((n, rx, ry))
        r = cpl_check.fit(self.SOIC, jlc)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["theta"], 90.0)
        self.assertAlmostEqual(r["shift_mm"][0], 0.3, places=3)
        self.assertAlmostEqual(r["shift_mm"][1], -0.2, places=3)

    def test_swapped_pin_numbers_fail(self):
        sot = [("1", -0.95, -1.0), ("2", 0.95, -1.0), ("3", 0.0, 1.0)]
        swapped = [("2", -0.95, -1.0), ("1", 0.95, -1.0), ("3", 0.0, 1.0)]   # E/B swapped in one library
        r = cpl_check.fit(sot, swapped)
        self.assertFalse(r["ok"])
        self.assertTrue(r["misfit_pads"])

    def test_kicad_mod_and_jlc_record(self):
        mod = write(os.path.join(self.d, "R.kicad_mod"),
                    '(footprint "R0603" (pad "1" smd rect (at -0.8 0) (size 0.8 0.9)) (pad "2" smd rect (at 0.8 0) (size 0.8 0.9)))')
        rec = write(os.path.join(self.d, "C1.json"), json.dumps({"jlc_footprint": {"pads": [
            {"number": "1", "x": 0.0, "y": 0.8}, {"number": "2", "x": 0.0, "y": -0.8}]}}))
        code, out = run(cpl_check, "fit", "--ours", mod, "--jlc", rec, "--save", os.path.join(self.d, "off.json"),
                        "--key", "R0603")
        self.assertEqual(code, 0, out)
        self.assertIn("rotation offset 270", out)   # JLC pad 1 below (y down file), ours left
        self.assertIn("R0603", json.load(open(os.path.join(self.d, "off.json"))))


class Convert(Base):
    def test_kicad_bottom_rule_and_offset(self):
        src = write(os.path.join(self.d, "pos.csv"),
                    "Ref,Val,Package,PosX,PosY,Rot,Side\n"
                    "U104,TFA,HVQFN-24,10,5,180,bottom\n"
                    "C101,10u,CP_Elec,1,1,0,bottom\n"
                    "R1,10k,R0603,2,2,90,top\n")
        off = write(os.path.join(self.d, "off.json"), json.dumps({"HVQFN-24": {"theta": 270, "shift_mm": [0, 0]}}))
        out = os.path.join(self.d, "cpl.csv")
        code, msg = run(cpl_check, "convert", src, out, "--src", "kicad", "--offsets", off)
        self.assertEqual(code, 0, msg)
        rows = {r["Designator"]: r for r in __import__("csv").DictReader(open(out))}
        self.assertEqual(rows["U104"]["Rotation"], "270")      # (180 - 180) + 270, as found on the Bondu board
        self.assertEqual(rows["C101"]["Rotation"], "180")      # 180 - 0
        self.assertEqual(rows["R1"]["Rotation"], "90")         # top: unchanged
        self.assertEqual(rows["U104"]["Layer"], "Bottom")

    def test_check_matches_bom(self):
        cpl = write(os.path.join(self.d, "cpl.csv"),
                    "Designator,Mid X,Mid Y,Layer,Rotation\nR1,1mm,1mm,Top,0\nR2,2mm,1mm,Top,400\n")
        bom = write(os.path.join(self.d, "bom.csv"), BOM_HDR + '10k,"R1,R3",R0603,C25804,2,UNI,X,-,-\n')
        code, out = run(cpl_check, "check", cpl, "--bom", bom, "--bbox", "0,0,1.5,5")
        self.assertEqual(code, 1)
        for want in ("rotation 400", "outside the board box", "in CPL, not in BOM: ['R2']", "in BOM, not in CPL: ['R3']"):
            self.assertIn(want, out)


class Bom(Base):
    def test_good(self):
        p = write(os.path.join(self.d, "b.csv"), BOM_HDR +
                  '10k,"R1,R2",R0603,C25804,2,UNI-ROYAL,0603WAF1002T5E,603-X,311-Y\n'
                  '100k,R3,R0603,C25803,1,UNI-ROYAL,0603WAF1003T5E,UNCONFIRMED,-\n')
        code, out = run(bom_check, p)
        self.assertEqual(code, 0, out)
        self.assertIn("UNCONFIRMED", out)

    def test_bad(self):
        p = write(os.path.join(self.d, "b.csv"),
                  "Comment,Designator,Footprint,LCSC Part #,Quantity,Manufacturer,MPN\n"
                  "825R,R101,R0603,C14675,1,Y,A\n"
                  "100K,R125-R127,R0603,C14675,3,Y,B\n"
                  "1.2K,R120,R0603,C1 / C2,1,Y,C\n")
        code, out = run(bom_check, p)
        self.assertEqual(code, 1)
        for want in ("Mouser Part Number' missing", "designator range", "used for different values",
                     "not one C-number"):
            self.assertIn(want, out)

    def test_lower_voltage_alternate(self):
        p = write(os.path.join(self.d, "b.csv"), BOM_HDR.strip() + ",Alternate note\n"
                  "10uF 25V X5R,C107,C0603,C76614,1,S,M,-,-,was C19702 10uF 6.3V\n")
        code, out = run(bom_check, p)
        self.assertEqual(code, 1)
        self.assertIn("below the line's 25 V", out)


class Package(Base):
    def make(self, extra=()):
        pkg = os.path.join(self.d, "Manufacturing_B_Rev1.0")
        os.makedirs(pkg)
        with zipfile.ZipFile(os.path.join(pkg, "B_Rev1.0_Gerber.zip"), "w") as z:
            for n in ("B.GTL", "B.GBL", "B.GTS", "B.GBS", "B.GTO", "B.GKO", "B.DRL"):
                z.writestr(n, "x")
        for n in ("B_BOM.csv", "B_CPL.csv") + tuple(extra):
            write(os.path.join(pkg, n), "x")
        return pkg

    def test_good_with_readme(self):
        pkg = self.make()
        self.assertEqual(run(fab_package, "readme", pkg, "--board", "B", "--rev", "1.0", "--layers", "2",
                             "--size", "15x13")[0], 0)
        code, out = run(fab_package, "check", pkg)
        self.assertEqual(code, 0, out)

    def test_schematic_and_reference_refused(self):
        pkg = self.make(("B.SchDoc", "B_Schematic.pdf", "B_CPL_before_rotation_fix.csv"))
        code, out = run(fab_package, "check", pkg)
        self.assertEqual(code, 1)
        self.assertIn("B.SchDoc", out)
        self.assertIn("B_Schematic.pdf", out)
        self.assertIn("reference file", out)
        self.assertIn("README.txt missing", out)


class Quote(Base):
    def test_shortfall(self):
        q = write(os.path.join(self.d, "q.json"), json.dumps({
            "board": "EXT01", "quantity": 1000, "quoted_total_usd": 1000.0,
            "rates": {"feeder_per_extended_type_usd": 1.55, "smt_per_joint_usd": 0.0017,
                      "tht_per_joint_usd": 0.0173, "tht_per_board_usd": 0.05},
            "short": [{"designator": "J102", "line_cost_usd": 220.8, "mount": "tht", "joints_per_board": 3},
                      {"designator": "U1", "unit_usd": 0.5, "qty_per_board": 1, "joints_per_board": 8}]}))
        r = jlc_quote.shortfall(json.load(open(q)))
        # J102: 220.8 + 1.55 + 3000*0.0173 + 1000*0.05 = 324.25 ; U1: 500 + 1.55 + 8000*0.0017 = 515.15
        self.assertAlmostEqual(r["added_usd"], 839.4, places=2)
        self.assertAlmostEqual(r["full_total_usd"], 1839.4, places=2)
        self.assertEqual(run(jlc_quote, "summary", q)[0], 0)


class Attach(Base):
    def test_attach_existing_folder(self):
        work = os.path.join(self.d, "Acme", "Board1")
        os.makedirs(work)
        write(os.path.join(work, "Board1.PrjPcb"), "x")
        write(os.path.join(work, "README.md"), "theirs")
        code, out = run(new_project, "board1", "--attach", work)
        self.assertEqual(code, 0, out)
        kit = os.path.join(work, "_eda")
        self.assertTrue(os.path.isfile(os.path.join(kit, "project.json")))
        self.assertEqual(json.load(open(os.path.join(kit, "project.json")))["design_dir"], "..")
        self.assertEqual(open(os.path.join(work, "README.md")).read(), "theirs")   # nothing of theirs touched
        self.assertEqual(sorted(os.listdir(work)), ["Board1.PrjPcb", "README.md", "_eda"])
        self.assertEqual(run(new_project, "board1", "--attach", work)[0], 1)      # never twice


if __name__ == "__main__":
    unittest.main()
