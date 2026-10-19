"""Tests for the global-library scripts on a temp library and temp projects (the real library is not touched).
The altium-lib copy is simulated by a file copy of a whole fixture library (same content hashes)."""
import contextlib, io, json, os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
G = os.path.join(HERE, "fixtures", "buck")
import libcat as lc, lib_promote, lib_pull, lib_status, lib_update, catalog_check, cad_register, cad_check
import datasheets_fetch
import altium_io

INFO = {"footprints": {n: {"status": "derived", "status_source": "test"} for n in
                       ("LMR33630_HSOIC8_DDA", "SOIC8_MS012", "IND_CDRH10D60", "CAPC3216_1206", "CAPC1608_0603",
                        "RESC1608_0603", "TB_MKDS1.5-2-5.08", "TP_PAD_D1.5")}, "components": {"J_MKDS1.5-2-5.08": {"family": "connectors/terminal_block"},
                           "U_LMR33630ADDA": {"family": "ics/power_buck"}, "Q_AO4407C": {"family": "discretes/mosfet"}}}


def run(mod, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mod.main(list(argv))
    return code, buf.getvalue()


class GlobalLib(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.g = os.path.join(self.t, "library")
        self.src = self.project("src", g1=True)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def project(self, name, g1):
        p = os.path.join(self.t, name)
        os.makedirs(os.path.join(p, "libs"))
        os.makedirs(os.path.join(p, "docs", "datasheets"))
        open(os.path.join(p, "gates.md"), "w").write(f"- [{'x' if g1 else ' '}] **G1 Footprints**\n")
        shutil.copyfile(os.path.join(G, "buck.SchLib"), os.path.join(p, "libs", f"{name}.SchLib"))
        shutil.copyfile(os.path.join(G, "buck.PcbLib"), os.path.join(p, "libs", f"{name}.PcbLib"))
        for s in altium_io.schlib_symbols(os.path.join(G, "buck.SchLib")).values():
            ds = lc.param(s, "Datasheet")
            if ds and ds != "-":
                open(os.path.join(p, "docs", "datasheets", ds), "wb").write(b"%PDF-1.4 stand-in " + ds.encode())
        return p

    def promote(self):
        info = os.path.join(self.t, "info.json")
        json.dump(INFO, open(info, "w"))
        return run(lib_promote, self.src, "--info", info, "--global-root", self.g)

    def write_global_libs(self):
        """stand-in for the altium-lib copies: whole-file copy gives the same content per item"""
        cat = lc.load_catalog(self.g)
        for lib in {c["global_lib"] for c in cat["components"]}:
            os.makedirs(os.path.dirname(os.path.join(self.g, lib)), exist_ok=True)
            shutil.copyfile(os.path.join(G, "buck.SchLib"), os.path.join(self.g, lib))
        for lib in {f["global_lib"] for f in cat["footprints"]}:
            os.makedirs(os.path.dirname(os.path.join(self.g, lib)), exist_ok=True)
            shutil.copyfile(os.path.join(G, "buck.PcbLib"), os.path.join(self.g, lib))

    def test_refused_without_g1(self):
        p = self.project("nog1", g1=False)
        code, out = run(lib_promote, p, "--global-root", self.g)
        self.assertEqual(code, 1)
        self.assertIn("G1 is not ticked", out)

    def test_status_requires_footprint_status(self):
        code, out = run(lib_promote, self.src, "--global-root", self.g)
        self.assertEqual(code, 1)
        self.assertIn("status", out)
        self.assertFalse(os.path.isfile(os.path.join(self.g, "catalog", "components.json")))

    def test_promote_then_check_and_status(self):
        code, out = self.promote()
        self.assertEqual(code, 0, out)
        cat = lc.load_catalog(self.g)
        self.assertEqual((len(cat["components"]), len(cat["footprints"])), (16, 8))
        self.assertEqual(run(catalog_check, "--global-root", self.g, "--project", self.src)[0], 0)
        code, out = run(catalog_check, "--global-root", self.g, "--strict")
        self.assertEqual(code, 1)                       # pending files + unverified LCSC
        code, out = run(lib_status, self.src, "--global-root", self.g)
        self.assertEqual(code, 0)
        self.assertIn("'OK': 24", out)
        code, out = self.promote()                      # second run: nothing changes
        self.assertIn("unchanged", out)
        self.assertEqual(lc.load_catalog(self.g)["components"][0]["rev"], 1)
        self.assertEqual(len(self.plan()), 24)          # still pending, so still planned

    def plan(self):
        return json.load(open(os.path.join(self.g, "catalog", "promote_plan.json")))["copies"]

    def test_plan_rebuilt_and_empty_plan_fails(self):
        self.promote()
        p = os.path.join(self.g, "catalog", "promote_plan.json")
        json.dump({"copies": []}, open(p, "w"))         # the bug seen on 2026-10-13
        code, out = run(catalog_check, "--global-root", self.g)
        self.assertEqual(code, 1)
        self.assertIn("24 pending items are not in promote_plan.json", out)
        for _ in range(2):                              # idempotent
            code, out = run(lib_promote, "-", "--plan", "--global-root", self.g, "--projects-root", self.t)
            self.assertEqual(code, 0, out)
        first = self.plan()
        self.assertEqual(len(first), 24)
        self.assertTrue(all(c["preserve_external_paths"] and c["source"].endswith(("src.SchLib", "src.PcbLib"))
                            for c in first))
        self.assertEqual(run(catalog_check, "--global-root", self.g)[0], 0)
        self.write_global_libs()                        # copies done -> plan empty, check clean
        run(lib_promote, "-", "--plan", "--global-root", self.g, "--projects-root", self.t)
        self.assertEqual(self.plan(), [])
        self.assertEqual(run(catalog_check, "--global-root", self.g)[0], 0)

    def test_pull_verify_and_drift(self):
        self.promote()
        self.write_global_libs()
        self.assertEqual(run(lib_promote, self.src, "--verify", "--global-root", self.g)[0], 0)
        dst = os.path.join(self.t, "dst")
        os.makedirs(os.path.join(dst, "libs"))
        code, out = run(lib_pull, dst, "R_10k_1%_0603", "--global-root", self.g)
        self.assertEqual(code, 0, out)
        plan = json.load(open(os.path.join(dst, "ai", "lib_pull_plan.json")))
        self.assertTrue(all(c["preserve_external_paths"] for c in plan["copies"]))
        self.assertEqual(run(lib_pull, dst, "--verify")[0], 1)     # copy not done yet
        tsch, tpcb = (c["target"] for c in plan["copies"])       # local family libraries: libs/passives/resistor.*
        self.assertTrue(tsch.endswith("libs/passives/resistor.SchLib") and tpcb.endswith("libs/passives/resistor.PcbLib"))
        os.makedirs(os.path.dirname(tsch))
        shutil.copyfile(os.path.join(self.g, "symbols", "passives", "resistor.SchLib"), tsch)
        shutil.copyfile(os.path.join(self.g, "footprints", "chip.PcbLib"), tpcb)
        code, out = run(lib_pull, dst, "--verify")
        self.assertEqual(code, 0, out)
        code, out = run(lib_status, dst, "--global-root", self.g)
        self.assertEqual(code, 0, out)
        self.assertIn("LOCAL ONLY", out)                # the other buck symbols came along in the file copy
        # drift: the local copy is replaced by a library with a different R_10k
        man = lc.load_manifest(dst)
        man["components"]["R_10k_1%_0603"]["symbol_hash"] = "0" * 16
        lc.save_manifest(dst, man)
        code, out = run(lib_status, dst, "--global-root", self.g)
        self.assertEqual(code, 1)
        self.assertIn("LOCAL CHANGED", out)
        self.assertEqual(run(lib_update, dst, "R_10k_1%_0603", "--global-root", self.g)[0], 1)

    def test_update_available(self):
        self.promote()
        self.write_global_libs()
        dst = os.path.join(self.t, "dst")
        os.makedirs(os.path.join(dst, "libs"))
        run(lib_pull, dst, "R_10k_1%_0603", "--global-root", self.g)
        shutil.copyfile(os.path.join(G, "buck.SchLib"), os.path.join(dst, "libs", "dst.SchLib"))
        shutil.copyfile(os.path.join(G, "buck.PcbLib"), os.path.join(dst, "libs", "dst.PcbLib"))
        run(lib_pull, dst, "--verify")
        cat = lc.load_catalog(self.g)
        lc.find(cat, "c", "R_10k_1%_0603")["rev"] = 2
        lc.save_catalog(cat, self.g)
        code, out = run(lib_status, dst, "--global-root", self.g)
        self.assertIn("UPDATE", out)
        code, out = run(lib_update, dst, "--global-root", self.g)
        self.assertEqual(code, 0, out)
        self.assertIn("R_10k_1%_0603", out)

    def test_datasheet_sha(self):
        self.promote()
        self.assertEqual(run(catalog_check, "--global-root", self.g)[0], 0)
        open(os.path.join(self.g, "datasheets", "0603WAF1002T5E_C25804.pdf"), "ab").write(b"changed")
        code, out = run(catalog_check, "--global-root", self.g)
        self.assertEqual(code, 1)
        self.assertIn("sha256 changed", out)

    def test_datasheet_not_fetched_is_a_note(self):
        self.promote()
        os.remove(os.path.join(self.g, "datasheets", "0603WAF1002T5E_C25804.pdf"))
        code, out = run(catalog_check, "--global-root", self.g)
        self.assertEqual(code, 0, out)
        self.assertIn("NOT FETCHED: 1 datasheet", out)

    def test_datasheets_fetch(self):
        self.promote()
        ds_dir = os.path.join(self.g, "datasheets")
        name = "0603WAF1002T5E_C25804.pdf"
        good = open(os.path.join(ds_dir, name), "rb").read()
        src = os.path.join(self.t, "src.pdf")
        open(src, "wb").write(good)
        cat = lc.load_catalog(self.g)
        for c in cat["components"]:
            if c["datasheet"]:
                c["datasheet"]["url"] = "file:///" + src.replace("\\", "/")
        lc.find(cat, "c", "R_100k_1%_0603")["datasheet"]["url"] = ""
        lc.save_catalog(cat, self.g)
        os.remove(os.path.join(ds_dir, name))
        code, out = run(datasheets_fetch, "--global-root", self.g, "--only", "R_10k_1%_0603")
        self.assertEqual(code, 0, out)                  # downloaded, sha256 matches
        self.assertIn("FETCHED", out)
        self.assertEqual(open(os.path.join(ds_dir, name), "rb").read(), good)
        code, out = run(datasheets_fetch, "--global-root", self.g, "--only", "R_10k_1%_0603")
        self.assertIn("OK", out)                        # good file is never downloaded again
        open(os.path.join(ds_dir, name), "ab").write(b"x")
        code, out = run(datasheets_fetch, "--global-root", self.g, "--only", "R_10k_1%_0603")
        self.assertEqual(code, 1)                       # present but wrong: reported, left untouched
        self.assertTrue(open(os.path.join(ds_dir, name), "rb").read().endswith(b"x"))
        other = "0603WAF5102T5E_C23196.pdf"             # source file has another part's hash
        os.remove(os.path.join(ds_dir, other))
        code, out = run(datasheets_fetch, "--global-root", self.g, "--only", "R_51k_1%_0603")
        self.assertEqual(code, 1)
        self.assertIn("differs from the catalog", out)
        self.assertFalse(os.path.exists(os.path.join(ds_dir, other)))
        os.remove(os.path.join(ds_dir, "0603WAF1003T5E_C25803.pdf"))
        code, out = run(datasheets_fetch, "--global-root", self.g, "--only", "R_100k_1%_0603")
        self.assertEqual(code, 1)
        self.assertIn("no datasheet.url", out)

    def test_cad(self):
        self.promote()
        os.makedirs(os.path.join(self.g, "models"), exist_ok=True)
        json.dump({"schema": 1, "models": []}, open(os.path.join(self.g, "models", "index.json"), "w"))
        self.assertEqual(run(cad_check, "--global-root", self.g)[0], 0)
        bad = os.path.join(self.t, "x.step")
        open(bad, "w").write("not a step file")
        self.assertEqual(run(cad_register, bad, "--footprint", "RESC1608_0603", "--source", "t", "--global-root", self.g)[0], 1)
        good = os.path.join(self.t, "r.step")
        open(good, "w").write("ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n")
        code, out = run(cad_register, good, "--footprint", "RESC1608_0603", "--source", "test", "--global-root", self.g)
        self.assertEqual(code, 0, out)
        self.assertEqual(run(cad_check, "--global-root", self.g)[0], 0)
        stored = os.path.join(self.g, "models", "step", "chip", "RESC1608_0603.step")
        self.assertTrue(os.path.isfile(stored))
        open(stored, "a").write("x")
        code, out = run(cad_check, "--global-root", self.g)
        self.assertEqual(code, 1)
        self.assertIn("sha256 changed", out)


if __name__ == "__main__":
    unittest.main()


class Readmes(unittest.TestCase):
    def test_create_keep_human_text_and_refresh(self):
        import lib_readmes
        t = tempfile.mkdtemp()
        try:
            g = os.path.join(t, "library")
            shutil.copytree(os.path.join(HERE, "..", "..", "library", "catalog"), os.path.join(g, "catalog"))
            os.makedirs(os.path.join(g, "parts"))
            shutil.copy(os.path.join(HERE, "..", "..", "library", "parts", "taxonomy.json"), os.path.join(g, "parts"))
            self.assertEqual(run(lib_readmes, "--check", "--global-root", g)[0], 1)
            self.assertEqual(run(lib_readmes, "--global-root", g)[0], 0)
            p = os.path.join(g, "symbols", "passives", "resistor.README.md")
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            self.assertIn("R_10k_1%_0603", txt)
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt.replace("Maintainer: (unassigned)", "Maintainer: Simul").replace("| R_10k_1%_0603 |", "| R_OLD |"))
            self.assertEqual(run(lib_readmes, "--check", "--global-root", g)[0], 1)
            run(lib_readmes, "--global-root", g)
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            self.assertIn("Maintainer: Simul", txt)
            self.assertIn("| R_10k_1%_0603 |", txt)
            self.assertNotIn("R_OLD", txt)
            self.assertTrue(os.path.isfile(os.path.join(g, "models", "step", "chip", "README.md")))
            self.assertEqual(run(lib_readmes, "--check", "--global-root", g)[0], 0)
        finally:
            shutil.rmtree(t)
