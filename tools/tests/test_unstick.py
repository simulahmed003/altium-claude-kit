"""Tests for the jam tools (TOOL-21, TOOL-22): altium_unstick (classification, duplicate choice, log count),
pas_lint and the new doctor checks. The window texts are the exact ones captured on AD26 26.11.1 (wedge study
2026-11-07). No Windows, no Altium needed."""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "scripts"))
import altium_unstick as au, pas_lint, doctor  # noqa: E402


def k(cls, title, text="", **kw):
    r = au.classify(dict(cls=cls, title=title, text=text, **kw))
    return r and r[:2]


class Classify(unittest.TestCase):
    def test_captured_dialogs(self):
        self.assertEqual(k("#32770", "X2", "Undeclared identifier: Free\r\n at Line:227, Char:15. \r\n\r\nContinue execution?"),
                         ("script_error", "cancel"))
        self.assertEqual(k("#32770", "X2", "Unknown identifier: \u00ef\r\n at Line:212, Char:10. \r\n\r\nContinue execution?"),
                         ("bom", "cancel"))
        self.assertEqual(k("TMessageForm", "Error", "Operation aborted"), ("aborted", "close"))
        self.assertEqual(k("TMessageForm", "Error"), ("aborted", "close"))
        self.assertEqual(k("TMessageForm", "Error", "Expression expected but % found"), ("template", "close"))
        self.assertEqual(k("TMessageForm", "Information", "There is another instance of running, but it is busy at "
                           "the moment. Cannot proceed with the request. Please try again later."),
                         ("second_instance", "close"))
        self.assertEqual(k("#32770", "X2", "... is not able to execute more than one script simultaneously"),
                         ("engine_busy", "close"))
        self.assertEqual(k("TForm_RunScriptParameters", "Run script"), ("run_params", "close"))
        self.assertEqual(k("TForm", "EDA Agent MCP"), ("eda_loop", "none"))

    def test_unknown_and_ignored(self):
        self.assertEqual(k("TMessageForm", "Confirm", "Save changes to Board.PcbDoc?"), ("unknown_modal", "none"))
        self.assertEqual(k("TFloatingPanel", "Properties", owned=True, owner_disabled=False), None)  # a panel, not modal
        self.assertEqual(k("TPreviewForm", "Preview SCH", owned=True, owner_disabled=True), ("unknown_modal", "none"))
        self.assertIsNone(k("TDXPMainForm", "Altium Designer (26.11.1)"))

    def test_duplicates(self):
        now = 10_000
        procs = [dict(pid=1, started=100), dict(pid=2, started=now - 30)]
        self.assertEqual(au.pick_duplicates(procs, {2}, now), ([2], []))
        self.assertEqual(au.pick_duplicates(procs, set(), now), ([], [2]))            # no proof: leave it
        old = [dict(pid=1, started=100), dict(pid=2, started=200)]
        self.assertEqual(au.pick_duplicates(old, {2}, now), ([], [2]))                # too old to be a handoff
        self.assertEqual(au.pick_duplicates(procs, {1}, now), ([], [2]))              # never the first Altium
        self.assertEqual(au.pick_duplicates(procs[:1], {1}, now), ([], []))

    def test_today_count(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "log")
            open(p, "w", encoding="utf-8").write(
                "2026-11-07T10:00:00 | RUN | stuck=0 | found=0\n2026-11-07T10:05:00 | RUN | stuck=1 | found=1\n"
                "2026-11-07T10:06:00 | ACT | script_error | cancel\n2026-11-06T09:00:00 | RUN | stuck=2 | found=2\n")
            self.assertEqual(au.stuck_runs_today(p, "2026-11-07"), 1)

    def test_cli_off_windows(self):
        if os.name != "nt":
            self.assertEqual(au.main([]), 0)


class PasLint(unittest.TestCase):
    def kinds(self, src, **kw):
        return [(lvl, msg.split(":")[0].split(" ")[0]) for lvl, _, msg in pas_lint.lint_text(src, **kw)]

    def test_bom_token_modal(self):
        res = pas_lint.lint_text(b"\xef\xbb\xbfProcedure Run; Begin ShowMessage('x'); End;")
        self.assertEqual([r[0] for r in res], ["FAIL", "FAIL"])
        self.assertIn("byte-order mark", res[0][2])
        res = pas_lint.lint_text(b"Begin SbxGuardUntil := Now + %GUARD_SECONDS% / 86400; End;")
        self.assertIn("%GUARD_SECONDS%", res[0][2])
        self.assertEqual(pas_lint.lint_text(b"Begin ShowMessage('x'); End;", allow_modal=True), [])

    def test_comments_and_strings_ignored(self):
        src = b"{ ShowMessage here is a comment } // StrictDelimiter\nBegin S := 'ShowMessage('; End;"
        self.assertEqual(pas_lint.lint_text(src), [])

    def test_bad_identifiers_and_stop(self):
        src = b"Begin L.StrictDelimiter := True; M.Rotation_X := 0; RunProcess('X2.exe -REditScript:Stop'); End;"
        msgs = " ".join(m for _, _, m in pas_lint.lint_text(src))
        self.assertIn("TOOL-06", msgs)
        self.assertIn("Rotation_X", msgs)
        self.assertIn("second Altium", msgs)

    def test_edit_without_try_and_pcblib_current(self):
        src = b"Begin Fp := Lib.GetComponentByName('A'); Body.MoveByXY(1, 2); Fp.AddPCBObject(Body); End;"
        msgs = [m for _, _, m in pas_lint.lint_text(src)]
        self.assertTrue(any("try/except" in m for m in msgs))
        self.assertTrue(any("SetState_CurrentComponent" in m for m in msgs))
        ok = (b"Begin Try Fp := Lib.GetComponentByName('A'); Lib.SetState_CurrentComponent(Fp); "
              b"Fp.AddPCBObject(Body); Finally End; End;")
        self.assertEqual(pas_lint.lint_text(ok), [])

    def test_pc_findings(self):
        # a token in a comment or string does not stop the compile; a BOM pasted mid-file does; template globals
        self.assertEqual(pas_lint.lint_text(b"{ %GUARD_SECONDS% } Begin S := '%LOG_PATH%'; End;"), [])
        res = pas_lint.lint_text("Begin\n\ufeffProcedure X; End;".encode("utf-8"))
        self.assertEqual([(r[0], r[1]) for r in res if "byte-order" in r[2]], [("FAIL", 2)])
        self.assertTrue(any("List1..List3" in m for _, _, m in pas_lint.lint_text(b"Begin List1.Free; End;")))

    def test_use_after_free(self):
        res = pas_lint.lint_text(b"Begin L.Free; L.Add('x'); End;")
        self.assertTrue(any("used again" in m for _, _, m in res))
        self.assertEqual(pas_lint.lint_text(b"Begin L.Free; L := TStringList.Create; L.Add('x'); End;"), [])

    def test_kit_scripts_pass(self):
        d = os.path.join(ROOT, "tools", "altium_scripts")
        for f in os.listdir(d):
            if f.lower().endswith(".pas"):
                res = pas_lint.lint_text(open(os.path.join(d, f), "rb").read())
                self.assertEqual([r for r in res if r[0] == "FAIL"], [], f)


class DoctorChecks(unittest.TestCase):
    def test_same_name_projects(self):
        paths = [r"D:\EDA\tools\mcp\altium-mcp\server\AltiumScript\Altium_API.PrjScr",
                 r"D:\EDA\tools\mcp\eda-agent\scripts\Altium_API.PrjScr",
                 r"D:\EDA\tools\mcp\altium-mcp\server\AltiumScript\AltiumCoffee.PrjScr"]
        paths = [p.replace("\\", os.sep) for p in paths]
        self.assertEqual(list(doctor.same_name_projects(paths)), ["altium_api.prjscr"])

    def test_mcp_code_dirty_and_skips(self):
        rep = doctor.Report()
        with tempfile.TemporaryDirectory() as t:
            repo = os.path.join(t, "tools", "mcp", "altium-mcp")
            for sub in (os.path.join("server", "AltiumScript"), os.path.join(".venv", "x"), "dev", "~cripts"):
                os.makedirs(os.path.join(repo, sub))
                open(os.path.join(repo, sub, "Altium_API.PrjScr"), "w").close()
            import subprocess
            subprocess.run(["git", "init", "-q", repo])
            subprocess.run(["git", "-C", repo, "add", "-A"])
            subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"])
            open(os.path.join(repo, "server", "AltiumScript", "Altium_API.PrjScr"), "w").write("changed")
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                doctor.check_mcp_code(rep, t)
        text = " ".join(w for _, w, _ in rep.rows)
        self.assertIn("(server/AltiumScript/Altium_API.PrjScr)", text)       # path not cut
        self.assertNotIn("two script projects", text)                         # .venv, dev, ~ copies skipped

    def test_stale_servers(self):
        procs = [(10, 1000.0, r"python D:\EDA\tools\mcp\altium-mcp\server\main.py"),
                 (11, 3000.0, r"python D:\EDA\tools\mcp\eda-agent\cli.py")]
        upd = {os.path.join("x", "altium-mcp"): 2000.0, os.path.join("x", "eda-agent"): 2000.0}
        self.assertEqual(doctor.stale_servers(procs, upd), [(10, os.path.join("x", "altium-mcp"))])


if __name__ == "__main__":
    unittest.main()
