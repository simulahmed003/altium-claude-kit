"""gate_check.py - offline evidence pack for a gate (rules WF-01, WF-02, WF-03, FAB-01, TOOL-09, RQ-02).

Usage:
  python gate_check.py <G1|S1|G2|G3|G4> <project dir> [--out FILE] [--no-write]
Reads the project's gates.md, project.json (optional) and files; runs every offline checker that applies;
writes ai/review/<gate>_evidence.md (or --out). It never ticks a gate.
  every gate  earlier gates ticked (order G1, S1, G2, G3, G4); G4 is refused while any earlier gate is open
              rules VERSION recorded in project.json
  G1          pin_match.py --style per SchLib/PcbLib pair in libs\\; catalog_check.py when libs\\lib_manifest.json exists
  S1          + conn_check.py and sch_overlap.py per sheet against ai\\plan.json; calcs_run.py on ai\\calc_inputs.json
  G2, G3, G4  + .PrjPcb lists every SchDoc / PcbDoc in its folder; PCB part designators = sheet designators
Items that need Altium (ERC, DRC, check_placement, proj_get_differences, captures) are listed as MCP items
for the agent to fill in. Exit 0 when every offline item passes, 1 otherwise (also when there is no design yet).
"""
import argparse, datetime, glob, io, json, os, re, sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import altium_io, pin_match, conn_check, sch_overlap, calcs_run

ORDER = ["G1", "S1", "G2", "G3", "G4"]
MCP = {
    "G1": ["altium-lib validate_library: 0 errors, 0 warnings per library",
           "1:1 footprint prints compared with the datasheet (user)"],
    "S1": ["eda proj_run_erc: 0 errors / 0 warnings (waivers listed in waivers.md)",
           "captures left / centre / right reviewed by the agent (COM-01), then by the user"],
    "G2": ["coffee check_placement: no courtyard overlaps", "eda proj_get_differences: in sync",
           "capture of the placed board"],
    "G3": ["eda run_drc / pcb_run_drc: 0 violations or each waived", "eda design audit on a COPY of the project",
           "eda proj_get_differences: in sync"],
    "G4": ["Gerber viewer review: layers, outline, drills, silkscreen, mask, paste (user)"],
}


def gate_states(path):
    st = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*- \[( |x|X)\] \*\*(G\d|S\d)\b", line)
        if m and m.group(2) not in st:
            st[m.group(2)] = m.group(1).lower() == "x"
    return st


def run_tool(fn, argv):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = fn(argv)
    except SystemExit as e:
        code = e.code
    except Exception as e:                          # a crash is a FAIL with its message, never a traceback
        buf.write(f"ERROR {type(e).__name__}: {e}")
        code = 1
    return code == 0, buf.getvalue().strip().splitlines()


def collect(gate, proj):
    rows = []                                       # (item, ok | None for N/A, detail)
    gp = os.path.join(proj, "gates.md")
    if not os.path.isfile(gp):
        return [("gates.md", False, "missing")], None
    st = gate_states(gp)
    for g in ORDER[:ORDER.index(gate)]:
        rows.append((f"earlier gate {g} ticked", bool(st.get(g)), "ticked" if st.get(g) else "NOT ticked"))
    if gate == "G4" and not all(st.get(g) for g in ORDER[:4]):
        rows.append(("G4 refused", False, "earlier gates open (FAB-01)"))
    pj = os.path.join(proj, "project.json")
    pjd = json.load(open(pj, encoding="utf-8")) if os.path.isfile(pj) else {}
    rv = pjd.get("rules_version")
    rows.append(("rules VERSION recorded (WF-03)", bool(rv), rv or "project.json has no rules_version"))
    libs = sorted(glob.glob(os.path.join(proj, "libs", "*.SchLib")))
    sheets = sorted(p for p in glob.glob(os.path.join(proj, "hw", "**", "*.SchDoc"), recursive=True))
    plan = os.path.join(proj, "ai", "plan.json")
    if not libs and not sheets:
        rows.append(("design files", False, "no design yet (no libs\\*.SchLib, no hw\\**\\*.SchDoc)"))
        return rows, st
    for sl in libs:
        pl = sl[:-7] + ".PcbLib"
        if not os.path.isfile(pl):
            rows.append((f"pin_match {os.path.basename(sl)}", False, "no PcbLib with the same name"))
            continue
        ok, out = run_tool(pin_match.main, [sl, pl, "--style"])
        rows.append((f"pin_match --style {os.path.basename(sl)}", ok, out[-1] if out else ""))
    if os.path.isfile(os.path.join(proj, "libs", "lib_manifest.json")):
        try:
            import catalog_check
            ok, out = run_tool(catalog_check.main, ["--project", proj])
            rows.append(("catalog_check (manifest + catalog)", ok, out[-1] if out else ""))
        except ImportError:
            rows.append(("catalog_check", False, "catalog_check.py not installed"))
    if gate == "G1":
        return rows, st
    if not sheets:
        rows.append(("sheets", False, "no hw\\**\\*.SchDoc yet"))
    for sh in sheets:
        name = os.path.basename(sh)
        if os.path.isfile(plan):
            ok, out = run_tool(conn_check.main, [sh, plan])
            summary = next((l for l in out if "pins on sheet" in l), out[-1] if out else "")
            rows.append((f"conn_check {name}", ok, summary + ("" if ok else " | " + "; ".join(l for l in out if "FAIL" in l)[:300])))
        else:
            rows.append((f"conn_check {name}", False, "ai\\plan.json missing"))
        ok, out = run_tool(sch_overlap.main, [sh])
        rows.append((f"sch_overlap {name}", ok, out[-1] if out else ""))
    ci = os.path.join(proj, "ai", "calc_inputs.json")
    if os.path.isfile(ci):
        ok, out = run_tool(calcs_run.main, [ci])
        rows.append(("calcs_run ai\\calc_inputs.json", ok, out[-1] if out else ""))
    else:
        rows.append(("calcs_run", None, "N/A: no ai\\calc_inputs.json (calcs.md checked by hand)"))
    if gate == "S1":
        return rows, st
    for prj in glob.glob(os.path.join(proj, "hw", "**", "*.PrjPcb"), recursive=True):
        d = os.path.dirname(prj)
        listed = {os.path.basename(x.replace("\\", "/")).lower() for x in altium_io.prjpcb_documents(prj)}
        docs = [os.path.basename(x) for x in glob.glob(os.path.join(d, "*.SchDoc")) + glob.glob(os.path.join(d, "*.PcbDoc"))]
        miss = [x for x in docs if x.lower() not in listed]
        rows.append((f"{os.path.basename(prj)} lists every document (TOOL-09)", not miss,
                     f"missing {miss}" if miss else f"{len(docs)} documents listed"))
        sch_des = set()
        for sh in glob.glob(os.path.join(d, "*.SchDoc")):
            sch_des |= set(altium_io.sheet_model(sh)["designators"])
        for pcb in glob.glob(os.path.join(d, "*.PcbDoc")):
            pd = set(altium_io.pcbdoc_components(pcb))
            extra, missing = sorted(pd - sch_des), sorted(sch_des - pd)
            rows.append((f"{os.path.basename(pcb)} parts = sheet parts", not extra and not missing,
                         f"{len(pd)} on PCB, {len(sch_des)} on sheets" + (f"; only on PCB {extra}" if extra else "")
                         + (f"; only on sheets {missing}" if missing else "")))
    return rows, st


def write(gate, proj, rows, out):
    ver = open(os.path.join(ROOT, "_rules", "VERSION")).read().strip()
    ok = all(r[1] is not False for r in rows)
    L = [f"# {gate} evidence - {os.path.basename(os.path.abspath(proj))}", "",
         f"Generated {datetime.date.today().isoformat()} by `_tools/scripts/gate_check.py`. Workspace rules VERSION {ver}.",
         "The agent never ticks a gate: the user signs off in gates.md.", "",
         f"Offline result: **{'PASS' if ok else 'FAIL'}**", "", "## Offline checks", "", "| Item | Result | Detail |", "|---|---|---|"]
    for item, r, detail in rows:
        L.append(f"| {item} | {'N/A' if r is None else ('PASS' if r else 'FAIL')} | {str(detail).replace('|', '/')} |")
    L += ["", "## Items that need Altium (MCP) - the agent fills these in", "", "| Item | Result | Evidence |", "|---|---|---|"]
    L += [f"| {m} | TODO | |" for m in MCP[gate]]
    L += ["", "## Agent's own review (captures, COM-01)", "", "- TODO", ""]
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        open(out, "w", encoding="utf-8").write("\n".join(L))
    return ok, "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("gate", choices=ORDER)
    ap.add_argument("project")
    ap.add_argument("--out", help="evidence file (default <project>/ai/review/<gate>_evidence.md)")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv)
    rows, _ = collect(a.gate, a.project)
    out = None if a.no_write else (a.out or os.path.join(a.project, "ai", "review", f"{a.gate}_evidence.md"))
    ok, _ = write(a.gate, a.project, rows, out)
    for item, r, detail in rows:
        print(f"{'N/A ' if r is None else ('PASS' if r else 'FAIL')}  {item}: {detail}")
    if out:
        print("evidence:", out)
    print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
