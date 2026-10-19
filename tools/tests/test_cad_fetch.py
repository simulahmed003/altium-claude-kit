"""Offline tests for cad_fetch.py: STEP box from vertices, placement, KiCad parsing, body check (no download)."""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import cad_fetch as cf

STEP = """ISO-10303-21;
HEADER;
FILE_SCHEMA (( 'AUTOMOTIVE_DESIGN' ));
ENDSEC;
DATA;
#1 = SI_UNIT ( .MILLI., .METRE. ) ;
#2 = PRODUCT ( 'R0603', 'R0603', '', ( #3 ) ) ;
#10 = CARTESIAN_POINT ( 'NONE', ( -0.4, -0.8, 0.0 ) ) ;
#11 = CARTESIAN_POINT ( 'NONE', ( 0.4, 0.8, 0.45 ) ) ;
#12 = CARTESIAN_POINT ( 'NONE', ( 9.0, 9.0, -5.0 ) ) ;
#20 = VERTEX_POINT ( 'NONE', #10 ) ;
#21 = VERTEX_POINT ( 'NONE', #11 ) ;
ENDSEC;
END-ISO-10303-21;
"""
MOD = """(module "R0603" (layer F.Cu)
  (fp_line (start -1.59 -0.84) (end 1.59 -0.84) (layer F.CrtYd) (width 0.05))
  (fp_line (start -1.59 0.84) (end 1.59 0.84) (layer F.CrtYd) (width 0.05))
  (pad 2 smd rect (at 0.753366 0) (size 0.806477 0.864008) (layers F.Cu F.Mask F.Paste))
  (pad 1 smd rect (at -0.753366 0) (size 0.806477 0.864008) (layers F.Cu F.Mask F.Paste))
  (model packages3d/R0603.step
    (at (xyz -0.019565 -0.005 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 -90))
  )
)
"""
SYM = """(kicad_symbol_lib (symbol "0603WAF1002T5E" (property "Reference" "R" (id 0)) (property "LCSC" "C25804" (id 5))
  (symbol "0603WAF1002T5E_0_1"
    (pin input line (at 5.08 0 180) (length 2.54) (name "2" (effects)) (number "2" (effects)))
    (pin input line (at -5.08 0 0) (length 2.54) (name "1" (effects)) (number "1" (effects))))))
"""


def tmpfile(text, ext):
    fd, p = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return p


class CadFetch(unittest.TestCase):
    def test_step_box_uses_vertices_only(self):
        i = cf.step_info(tmpfile(STEP, ".step"))
        self.assertTrue(i["header_ok"] and i["mm"])
        self.assertEqual(i["product"], "R0603")
        self.assertEqual(i["box_from"], "vertices")
        self.assertEqual(i["bbox"], [[-0.4, 0.4], [-0.8, 0.8], [0.0, 0.45]])     # the (9, 9, -5) control point is ignored

    def test_rotation_turns_the_long_axis_onto_x(self):
        box = cf.rotate_box([[-0.4, 0.4], [-0.8, 0.8], [0.0, 0.45]], [0, 0, -90], [0, 0, 0])
        self.assertEqual([round(b[1] - b[0], 3) for b in box], [1.6, 0.8, 0.45])

    def test_kicad_footprint_and_symbol(self):
        fp = cf.kicad_footprint(tmpfile(MOD, ".kicad_mod"))
        self.assertEqual([p["number"] for p in fp["pads"]], ["2", "1"])
        self.assertEqual(fp["pads"][0]["w"], 0.806477)
        self.assertEqual(fp["courtyard"], [[-1.59, 1.59], [-0.84, 0.84]])
        self.assertEqual(fp["model"]["rotate_deg"], [0.0, 0.0, -90.0])
        sy = cf.kicad_symbol(tmpfile(SYM, ".kicad_sym"))
        self.assertEqual(sy["properties"]["LCSC"], "C25804")
        self.assertEqual(sorted(p["number"] for p in sy["pins"]), ["1", "2"])

    def test_body_check(self):
        rec = {"facts": {"package": {"length": {"min": 1.5, "typ": 1.6, "max": 1.7}, "width": {"min": 0.7, "max": 0.9},
                                     "height": {"min": 0.35, "max": 0.55}}}}
        lim = cf.body_limits(rec, 0.05)
        self.assertEqual(cf.check_box([[-0.81, 0.81], [-0.405, 0.405], [0, 0.45]], lim, 0.05), [])
        bad = cf.check_box([[-1.6, 1.6], [-0.8, 0.8], [0, 1.3]], lim, 0.05)
        self.assertEqual(len(bad), 3)
        only_max = cf.body_limits({"facts": {"package": {"height": {"max": 6.35}}}}, 0.05)
        self.assertEqual([round(v, 3) for v in only_max["z"][:2]], [-0.05, 6.4])
        self.assertIsNone(cf.body_limits({"facts": {}}, 0.05))


if __name__ == "__main__":
    unittest.main()
