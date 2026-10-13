"""selftest.py - prove the workspace tooling works (part 7 of the workspace brief). No Altium needed.

Usage:
  python _tools\\selftest.py [--no-buck]
Steps (each PASS / FAIL, exit 1 if any FAIL):
  1 unit and fixture tests (_tools\\tests\\test_*.py)
  2 rules_lint.py: rule files well formed, every ENFORCED rule names an existing script
  3 every script answers --help (part of step 1) and catalog_check.py / cad_check.py on the real _global
  4 new_project.py into _tools\\tests\\_tmp\\ (recreated each run, git-ignored), then gate_check.py G1 on it:
    must not crash and must report "no design yet"
  5 buck regression, read-only on projects\\buck-12v-5v-3a: pin_match 16/16, conn_check 66 pins / 11 nets PASS,
    dots 0, sch_overlap 0, calcs 5.008 V and -1.50 % / +1.83 % (fixture calc_inputs), lib_status 24 OK,
    gate_check S1 offline items (written to _tools\\tests\\_tmp\\, never into the project).
    SKIPPED (not FAIL) when projects\\buck-12v-5v-3a is absent, as on a fresh clone of the public repo.
"""
import argparse, contextlib, io, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
S = os.path.join(HERE, "scripts")
TMP = os.path.join(HERE, "tests", "_tmp")
BUCK = os.path.join(ROOT, "projects", "buck-12v-5v-3a")
sys.path.insert(0, S)


def call(mod, *argv):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = mod.main(list(argv))
    except Exception as e:
        return 99, f"CRASH {type(e).__name__}: {e}"
    return code, buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--no-buck", action="store_true")
    a = ap.parse_args(argv)
    import rules_lint, catalog_check, cad_check, new_project, gate_check, pin_match, conn_check, dots, sch_overlap, \
        calcs_run, lib_status
    res = []

    def step(name, ok, detail=""):
        res.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f": {detail}" if detail else ""))

    r = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", os.path.join(HERE, "tests")],
                       capture_output=True, text=True, cwd=os.path.join(HERE, "tests"))
    last = [l for l in r.stderr.splitlines() if l.startswith("Ran ") or l in ("OK",) or l.startswith("FAILED")]
    step("1 unit + fixture tests", r.returncode == 0, " / ".join(last))
    if r.returncode:
        print(r.stderr[-2000:])
    code, out = call(rules_lint)
    step("2 rules_lint", code == 0, out.strip().splitlines()[-1])
    code, out = call(catalog_check)
    step("3 catalog_check (_global)", code == 0, out.strip().splitlines()[-1])
    code, out = call(cad_check)
    step("3 cad_check (_global)", code == 0, out.strip().splitlines()[-1])
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    code, out = call(new_project, "selftest-board", "--root", TMP)
    proj = os.path.join(TMP, "selftest-board")
    step("4 new_project into _tools/tests/_tmp", code == 0 and os.path.isfile(os.path.join(proj, "project.json")),
         out.strip().splitlines()[0])
    leftovers = [f for f in ("{{NAME}}", "{{RULES_VERSION}}", "{{DATE}}")
                 for d, _, fs in os.walk(proj) for n in fs if n.endswith((".md", ".json"))
                 if f in open(os.path.join(d, n), encoding="utf-8").read()]
    step("4 template placeholders filled", not leftovers, f"left: {sorted(set(leftovers))}" if leftovers else "")
    code, out = call(gate_check, "G1", proj)
    step("4 gate_check G1 on the new project (no design yet, no crash)", code == 1 and "no design yet" in out,
         f"exit {code}")
    if not a.no_buck and not os.path.isdir(BUCK):
        print("SKIPPED  5 buck regression: projects/buck-12v-5v-3a not present (designs are not in the public repo)")
    elif not a.no_buck:
        L, H = os.path.join(BUCK, "libs"), os.path.join(BUCK, "hw", "buck")
        sheet, plan = os.path.join(H, "buck__Buck.SchDoc"), os.path.join(BUCK, "ai", "plan.json")
        code, out = call(pin_match, os.path.join(L, "buck.SchLib"), os.path.join(L, "buck.PcbLib"), "--style")
        step("5 buck pin_match", code == 0 and "16 symbols, 16 PASS, 0 FAIL" in out, out.strip().splitlines()[-1])
        code, out = call(conn_check, sheet, plan)
        step("5 buck conn_check", code == 0 and "66 pins on sheet, 66 in plan, 11 named nets, 0 mismatches" in out,
             next((l for l in out.splitlines() if "pins on sheet" in l), ""))
        code, out = call(dots, sheet)
        step("5 buck dots", code == 0, out.strip().splitlines()[-1])
        code, out = call(sch_overlap, sheet)
        step("5 buck sch_overlap", code == 0, out.strip().splitlines()[-1])
        code, out = call(calcs_run, os.path.join(HERE, "tests", "fixtures", "buck", "calc_inputs.json"))
        step("5 buck calcs", code == 0 and "nom 5.008" in out and "lo_pct -1.5," in out and "hi_pct 1.826" in out,
             next((l for l in out.splitlines() if "divider" in l), "")[:110])
        code, out = call(lib_status, BUCK)
        step("5 buck lib_status", code == 0, out.strip().splitlines()[-2])
        code, out = call(gate_check, "S1", BUCK, "--out", os.path.join(TMP, "buck_S1_evidence.md"))
        offline = [l for l in out.splitlines() if l.startswith(("PASS", "FAIL", "N/A"))]
        bad = [l for l in offline if l.startswith("FAIL") and "rules VERSION" not in l]
        step("5 buck gate_check S1 (only known gap: no project.json)", not bad and code != 99,
             f"{len(offline)} items, {len(bad)} other FAIL")
    n = len(res) - sum(res)
    print(f"\nselftest: {len(res)} steps, {n} FAIL" + (", buck regression SKIPPED" if not a.no_buck and not os.path.isdir(BUCK) else ""))
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
