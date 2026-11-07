"""Tests for the tools added by the 2026-11 kit review: lib_params, doctor, rules_lint (CHANGELOG order, --next-id),
ws_lib_check. No Altium needed."""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "scripts"))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, SCRIPTS)
import lib_params, doctor, rules_lint, ws_lib_check  # noqa: E402

BUCK_SCHLIB = os.path.join(HERE, "fixtures", "buck", "buck.SchLib")


def run(mod, *argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = mod.main(list(argv))
    return code, buf.getvalue()


class LibParams(unittest.TestCase):
    d = lib_params.load()

    def test_89_subtypes(self):
        self.assertEqual(len(lib_params.subtypes(self.d)), 89)

    def test_find_by_full_name_subtype_or_type(self):
        self.assertEqual(len(lib_params.find(self.d, "Capacitors/Ceramic (MLCC)")), 1)
        self.assertEqual(len(lib_params.find(self.d, "ceramic (mlcc)")), 1)
        self.assertGreater(len(lib_params.find(self.d, "Capacitors")), 3)
        self.assertEqual(lib_params.find(self.d, "No Such Thing"), [])

    def test_set_has_common_links_and_electrical(self):
        e = lib_params.find(self.d, "Capacitors/Ceramic (MLCC)")[0]
        s = lib_params.param_set(self.d, e)
        for n in ("Manufacturer Part Number 1", "LCSC Price/Stock", "Capacitance", "Voltage Rating", "Dielectric"):
            self.assertIn(n, s)
        self.assertNotIn("Category", s)            # import only
        self.assertEqual(len(s), len(set(s)))

    def test_check_component(self):
        e = lib_params.find(self.d, "Resistors/Chip")[0]
        good = [(n, "") for n in lib_params.param_set(self.d, e) if n != "Comment"] + [("Category", "Resistors/Chip")]
        self.assertEqual(lib_params.check_component(self.d, good)[1], [])
        bad = good[1:] + [("Value", "10k"), ("Resistance", "10k")]
        probs = " ".join(lib_params.check_component(self.d, bad)[1])
        self.assertIn("missing", probs)
        self.assertIn("Value", probs)
        self.assertIn("duplicate: Resistance", probs)
        self.assertIn("no Category", " ".join(lib_params.check_component(self.d, [("X", "")])[1]))
        self.assertIn("not in the tree", " ".join(lib_params.check_component(self.d, [("Category", "A/B")])[1]))

    def test_keep_list_is_not_extra(self):
        e = lib_params.find(self.d, "Resistors/Chip")[0]
        ps = [(n, "") for n in lib_params.param_set(self.d, e)] + [("Category", "Resistors/Chip"), ("Arrow Price/Stock", "x")]
        self.assertEqual(lib_params.check_component(self.d, ps)[1], [])

    def test_cli(self):
        code, out = run(lib_params, "Resistors/Chip")
        self.assertEqual(code, 0)
        self.assertIn("Resistance", out)
        code, out = run(lib_params, "--list", "--json")
        self.assertEqual(len(json.loads(out)), 89)
        self.assertEqual(run(lib_params, "Nope")[0], 1)
        code, out = run(lib_params, "--check", BUCK_SCHLIB)   # buck parts predate the standard: no Category
        self.assertEqual(code, 1)
        self.assertIn("no Category", out)

    def test_doc_is_current(self):
        with tempfile.TemporaryDirectory() as t:
            got = lib_params.write_doc(self.d, os.path.join(t, "x.md"))
        self.assertEqual(got, open(lib_params.DOC_PATH, encoding="utf-8").read(), "run kit lib_params --write-doc")


class Doctor(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.t)

    def rows(self, fn, *a):
        rep = doctor.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            fn(rep, *a)
        return rep.rows

    def test_mcp_missing_fails_and_complete_passes(self):
        self.assertEqual(self.rows(doctor.check_mcp, self.t)[0][0], "FAIL")
        with open(os.path.join(self.t, ".mcp.json"), "w") as f:
            json.dump({"mcpServers": {"altium-lib": {}, "altium-eda": {}}}, f)
        r = self.rows(doctor.check_mcp, self.t)[0]
        self.assertEqual(r[0], "WARN")
        self.assertIn("altium-coffee", r[1])
        with open(os.path.join(self.t, ".mcp.json"), "w") as f:
            json.dump({"mcpServers": {s: {} for s in doctor.SERVERS}}, f)
        self.assertEqual(self.rows(doctor.check_mcp, self.t)[0][0], "OK")

    def test_hook_old_path_fails(self):
        os.makedirs(os.path.join(self.t, ".claude"))
        with open(os.path.join(self.t, ".claude", "settings.json"), "w") as f:
            f.write('{"hooks": "powershell -File D:/EDA/_tools/bridge/guard.ps1"}')
        self.assertEqual(self.rows(doctor.check_hook, self.t)[0][0], "FAIL")

    def test_altium_instances(self):
        self.assertEqual(self.rows(doctor.check_altium, 1)[0][0], "OK")
        self.assertEqual(self.rows(doctor.check_altium, 2)[0][0], "FAIL")
        self.assertEqual(self.rows(doctor.check_altium, None)[0][0], "OK")

    def test_kill_switch(self):
        os.makedirs(os.path.join(self.t, "tools", "bridge"))
        open(os.path.join(self.t, "tools", "bridge", "KILLED.lock"), "w").close()
        r = self.rows(doctor.check_kill, self.t)[0]
        self.assertEqual(r[0], "WARN")
        self.assertIn("KILL SWITCH IS ENGAGED", r[1])

    def test_altium_lib_paths(self):
        cfg = os.path.join(self.t, "config.json")
        with open(cfg, "w") as f:
            json.dump({"allowed_paths": [self.t.replace("\\", "/")]}, f)
        self.assertEqual(self.rows(doctor.check_altium_lib, self.t, cfg)[0][0], "OK")
        with open(cfg, "w") as f:
            json.dump({"allowed_paths": ["D:/Elsewhere"]}, f)
        self.assertEqual(self.rows(doctor.check_altium_lib, self.t, cfg)[0][0], "WARN")

    def test_cli_prints_start_command(self):
        _, out = run(doctor, "--offline", "--folder", r"D:\Work\Board1")
        self.assertIn(r'--add-dir "D:\Work\Board1"', out)
        self.assertIn("doctor:", out)


class RulesLint(unittest.TestCase):
    def test_real_rules_clean_and_next_id(self):
        rules = rules_lint.parse(os.path.join(ROOT, "rules"))
        self.assertEqual(rules_lint.changelog_errors(os.path.join(ROOT, "rules")), [])
        ids = {r["id"] for r in rules}
        for p in ("LIB", "WF", "TOOL"):
            self.assertNotIn(rules_lint.next_id(rules, p), ids)

    def test_changelog_order_and_version(self):
        with tempfile.TemporaryDirectory() as t:
            with open(os.path.join(t, "CHANGELOG.md"), "w") as f:
                f.write("| Version | Date |\n|---|---|\n| 1.5.0 | x |\n| 1.4.1 | x |\n| 1.6.0 | x |\n")
            with open(os.path.join(t, "VERSION"), "w") as f:
                f.write("1.7.0\n")
            errs = rules_lint.changelog_errors(t)
        self.assertTrue(any("1.4.1" in e for e in errs))
        self.assertTrue(any("VERSION 1.7.0" in e for e in errs))


class WsLibCheck(unittest.TestCase):
    def sym(self, **p):
        return {"params": [{"name": k.replace("_", " "), "text": v} for k, v in p.items()], "records": []}

    def test_slash_in_type_fails(self):
        why = ws_lib_check.check("J1", self.sym(Component_Type="FFC / FPC", Category="Connectors/FFC / FPC", Symbol="Conn"))
        self.assertTrue(why)

    def test_good_passes(self):
        why = ws_lib_check.check("J1", self.sym(Component_Type="FFC & FPC", Category="Connectors/FFC & FPC", Symbol="Conn"))
        self.assertEqual(why, [])


if __name__ == "__main__":
    unittest.main()
