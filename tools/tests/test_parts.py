"""Tests for parts.py on a temp library: page text comes from cache files, so no PDF and no pdftotext are needed."""
import contextlib, io, json, os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import parts as P

SHA = "ab" * 32
PAGES = {"layout": ["Title page\nPart XYZ1 buck converter", "Absolute Maximum Ratings\nVIN   -0.3   38   V\n0603 25V 50V"],
         "raw": ["Title page Part XYZ1 buck converter", "Absolute Maximum Ratings VIN -0.3 38 V 0603 75V 150V"],
         "table": ["Title page", "VIN  -0.3  38  V"]}


def run(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = P.main(list(argv))
    return code, buf.getvalue()


class Parts(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.old = os.environ.get("EDA_GLOBAL")
        os.environ["EDA_GLOBAL"] = self.t
        real = os.path.join(HERE, "..", "..", "library", "parts")
        os.makedirs(os.path.join(self.t, "parts"))
        for f in ("taxonomy.json", "manufacturers.json"):
            shutil.copy(os.path.join(real, f), os.path.join(self.t, "parts", f))
        P.save_json(P.p("datasheets", "index.json"), {"schema": 1, "datasheets": {SHA: {
            "file": "xyz1.pdf", "url": "", "source": "test", "mfr": "", "title": "", "revision": "", "added": "", "pages": 2,
            "covers": ["XYZ1"]}}})
        os.makedirs(P.p("datasheets", "_text"))
        for m, pages in PAGES.items():
            with open(P.p("datasheets", "_text", f"{SHA[:16]}.{m}.txt"), "w", encoding="utf-8") as f:
                f.write("\f".join(pages) + "\f")
        self.assertEqual(run("new", "--mpn", "XYZ1", "--mfr", "TI", "--category", "ics/power_buck", "--offline")[0], 0)
        self.f, self.r = P.one("XYZ1")
        self.r["datasheets"] = [{"sha256": SHA, "file": "xyz1.pdf"}]

    def tearDown(self):
        if self.old is None:
            os.environ.pop("EDA_GLOBAL", None)
        else:
            os.environ["EDA_GLOBAL"] = self.old
        shutil.rmtree(self.t)

    def check(self, **facts):
        self.r["facts"] = facts
        P.save_json(self.f, self.r)
        return P.check_record(self.f, self.r, P.taxonomy())

    def test_manufacturer_alias_gives_canonical_name_and_slug(self):
        self.assertEqual(self.r["mfr"], "Texas Instruments")
        self.assertTrue(self.f.endswith("XYZ1__ti.json"))

    def test_quote_must_be_on_the_cited_page(self):
        ok = {"abs_max": {"vin": {"min": -0.3, "max": 38, "unit": "V", "ref": {"page": 2, "quote": "VIN -0.3 38 V"}}}}
        self.assertEqual(self.check(**ok)[0], [])
        bad = {"abs_max": {"vin": {"max": 40, "unit": "V", "ref": {"page": 2, "quote": "VIN -0.3 40 V"}}}}
        self.assertIn("not found on page 2", " ".join(self.check(**bad)[0]))
        wrong_page = {"abs_max": {"vin": {"max": 38, "unit": "V", "ref": {"page": 1, "quote": "VIN -0.3 38 V"}}}}
        self.assertTrue(self.check(**wrong_page)[0])

    def test_mode_pins_the_quote_to_one_text_mode(self):
        # layout text puts 25V on the 0603 line (misaligned table); raw has the true row
        raw = {"abs_max": {"working_voltage": {"max": 75, "unit": "V", "ref": {"page": 2, "quote": "0603 75V 150V", "mode": "raw"}}}}
        self.assertEqual(self.check(**raw)[0], [])
        lay = {"abs_max": {"working_voltage": {"max": 75, "unit": "V", "ref": {"page": 2, "quote": "0603 75V 150V", "mode": "layout"}}}}
        self.assertTrue(self.check(**lay)[0])

    def test_units_order_and_abs_max_vs_recommended(self):
        unit = {"abs_max": {"vin": {"max": 38, "unit": "mV", "ref": {"page": 2, "quote": "38"}}}}
        self.assertIn("unit", " ".join(self.check(**unit)[0]))
        order = {"electrical": {"vref": {"min": 1.0, "typ": 0.9, "unit": "V", "ref": {"page": 2, "quote": "38"}}}}
        self.assertIn("min <= typ <= max", " ".join(self.check(**order)[0]))
        neg = {"electrical": {"vf": {"typ": -0.7, "max": -1, "unit": "V", "ref": {"page": 2, "quote": "38"}}}}
        self.assertEqual(self.check(**neg)[0], [])
        over = {"abs_max": {"vin": {"max": 38, "unit": "V", "ref": {"page": 2, "quote": "38"}}},
                "recommended": {"vin": {"max": 40, "unit": "V", "ref": {"page": 2, "quote": "38"}}}}
        self.assertIn("exceeds abs_max", " ".join(self.check(**over)[0]))

    def test_tagged_key_and_visual_reference(self):
        facts = {"electrical": {"rds_on@low_side": {"typ": 0.04, "unit": "ohm", "ref": {"page": 1, "quote": "not in text", "visual": True}}}}
        bad, notes = self.check(**facts)
        self.assertEqual(bad, [])
        self.assertIn("visual reference", " ".join(notes))

    def test_required_facts_once_extracted(self):
        self.r["review"]["status"] = "extracted"
        bad, notes = self.check()
        self.assertIn("required facts missing", " ".join(notes))
        self.r["review"]["status"] = "checked"
        self.assertIn("required facts missing", " ".join(self.check()[0]))

    def test_symbol_font_and_control_characters_normalize(self):
        page = "TCR 100PPM/C and tol \x0110%"
        self.assertTrue(P.quote_on_page("TCR ±100PPM/°C", page.translate(P.SYMBOL_PUA)))
        self.assertTrue(P.quote_on_page("tol 10%", page))

    def test_index_find_and_get(self):
        self.assertEqual(run("index")[0], 0)
        code, out = run("find", "xyz")
        self.assertEqual(code, 0)
        self.assertIn("XYZ1", out)
        self.assertEqual(run("find", "nothing-like-this")[0], 1)
        self.assertEqual(run("get", "XYZ1", "--section", "pins")[0], 0)

    def test_new_rejects_unknown_category_and_duplicates(self):
        self.assertEqual(run("new", "--mpn", "Q1", "--mfr", "AOS", "--category", "discretes/nope", "--offline")[0], 1)
        self.assertEqual(run("new", "--mpn", "XYZ1", "--mfr", "TI", "--category", "ics/power_buck", "--offline")[0], 1)

    def test_verify_and_gate(self):
        self.assertEqual(run("check", "XYZ1", "--gate")[0], 1)
        self.assertEqual(run("verify", "XYZ1", "--by", "tester", "--items", "pins", "abs_max")[0], 0)
        self.assertNotEqual(P.one("XYZ1")[1]["review"]["status"], "verified")
        self.assertEqual(run("verify", "XYZ1", "--by", "tester", "--items", "package", "visual")[0], 0)
        self.assertEqual(P.one("XYZ1")[1]["review"]["status"], "verified")
        self.assertEqual(run("verify", "XYZ1", "--by", "tester", "--items", "colour")[0], 1)

    def test_datasheet_into_project_by_hash(self):
        pdf = os.path.join(self.t, "elsewhere", "x.pdf")
        os.makedirs(os.path.dirname(pdf))
        with open(pdf, "wb") as f:
            f.write(b"%PDF-1.4 test")
        sha = P.sha256(pdf)
        idx = P.ds_index()
        idx["datasheets"][sha] = {"file": "xyz1_real.pdf", "covers": ["XYZ1"]}
        P.save_json(P.p("datasheets", "index.json"), idx)
        self.r["datasheets"] = [{"sha256": sha, "file": "xyz1_real.pdf"}]
        P.save_json(self.f, self.r)
        proj = os.path.join(self.t, "proj")
        self.assertEqual(run("datasheet", "XYZ1", "--project", proj)[0], 1)          # not found, no link
        code, out = run("datasheet", "XYZ1", "--project", proj, "--search", os.path.dirname(pdf))
        self.assertEqual(code, 0, out)
        self.assertEqual(P.sha256(os.path.join(proj, "docs", "datasheets", "xyz1_real.pdf")), sha)
        self.assertIn("already in the project", run("datasheet", "XYZ1", "--project", proj)[1])

    def test_url_order_maker_first(self):
        r = {"datasheet_urls": [{"source": "lcsc", "url": "https://datasheet.lcsc.com/a.pdf"}],
             "datasheets": [{"url": "https://www.ti.com/lit/ds/symlink/x.pdf"}]}
        self.assertEqual([s for s, _ in P.url_candidates(r)], ["maker", "lcsc"])


class RealLibrary(unittest.TestCase):
    def test_checked_in_records_pass(self):
        os.environ.pop("EDA_GLOBAL", None)
        recs = P.all_records()
        tax = P.taxonomy()
        for f, r in recs:
            self.assertEqual(P.check_record(f, r, tax)[0], [], os.path.basename(f))


if __name__ == "__main__":
    unittest.main()
