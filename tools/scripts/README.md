# tools\scripts - workspace checkers and generators

All scripts are pure Python (standard library), read-only on design files unless stated, and need no Altium.
Each has a docstring, `--help`, and exit code 0 = PASS / 1 = FAIL. Tests: `tools\tests\` (fixtures in
`tools\tests\fixtures\`, rebuilt with `make_fixtures.py`). Run everything with `python tools\selftest.py`.

| Script | Does | Rules | Typical call |
|---|---|---|---|
| altium_io.py | shared reader: SchLib, PcbLib, SchDoc, PcbDoc, PrjPcb; content hashes | - | `python altium_io.py libs\x.SchLib` |
| pin_match.py | symbol pins = footprint pads, no hidden/stacked pins, pin ends on grid, `--style` visible text | LIB-01..03 | `python pin_match.py libs\x.SchLib libs\x.PcbLib --style` |
| conn_check.py | every pin on the saved sheet vs plan.json; duplicate designators; one TP per net; junction dots | SCH-J, O, P, Q | `python conn_check.py hw\x\x.SchDoc ai\plan.json` |
| dots.py | junction dots, overlaps, crossings, merge candidates | SCH-E, Q, TOOL-12 | `python dots.py hw\x\x.SchDoc` |
| sch_overlap.py | text overlaps, box lines, pin numbers, frames, nearest part, grid | SCH-B, C, D, I, N | `python sch_overlap.py hw\x\x.SchDoc` |
| merge_plan.py | wire clean-up plan after part removal (JSON) | SCH-Q | `python merge_plan.py sheet.SchDoc --removed TP6` |
| sch_plan.py | coordinate plan check with real library pins; read a plan back from a sheet | SCH-R | `python sch_plan.py check ai\layout.json libs\x.SchLib ai\plan.json` |
| gen_sym.py | symbol JSON for altium-lib write_schlib from a short spec (R, C, L, testpoint, connector, ic) | LIB-01..03 | `python gen_sym.py ai\sym_spec.json libs\_dryrun\sym.json` |
| calclib.py | divider, ripple, Isat, derating, EN UVLO, TJ, IPC-2221 (import it) | RQ-02 | `from calclib import divider_worst` |
| calcs_run.py | runs ai\calc_inputs.json with limits; `--md` table for calcs.md | RQ-02 | `python calcs_run.py ai\calc_inputs.json --md` |
| place.py | placement plan: courtyards, board edge (fab profile), plan vs saved PcbDoc | PCB-02, 12 | `python place.py ai\place.json --pcb hw\x\x.PcbDoc` |
| jlc.py | JLCPCB BOM / CPL from plan + PcbDoc; BOM parse check (only after G4) | FAB-01, 04, RQ-03 | `python jlc.py bom ai\plan.json out\bom.csv --catalog ...` |
| gate_check.py | evidence pack ai\review\<gate>_evidence.md; gate order; never ticks a gate | WF-01..03, FAB-01, TOOL-09 | `python gate_check.py S1 projects\x` |
| first_run_test.py | runs docs\FIRST_RUN_TESTS.md on Windows (live calls through `claude -p`, so the guard decides); log lines to logs\MCP_LOG.md | TOOL-01 | `python tools\scripts\first_run_test.py` |
| coffee_script_rename.py | gives altium-coffee its own script project name (AltiumCoffee.PrjScr) and sets its config script_path; run by setup.ps1 | TOOL-01 | `python tools\scripts\coffee_script_rename.py --check` |
| libcat.py | shared catalog / manifest code for the lib scripts (import it) | LIB-05, 06 | - |
| lib_promote.py | project parts -> global catalog after G1; plans the altium-lib copies (catalog vs libs, idempotent; `- --plan` rebuilds); `--verify` | LIB-06 | `python lib_promote.py projects\x --info info.json` |
| lib_pull.py | plan global -> project copies; `--verify` records them in lib_manifest.json | LIB-06 | `python lib_pull.py projects\x R_10k_1%_0603` |
| lib_update.py | plan updates to newer global revs; refuses locally changed parts | LIB-06 | `python lib_update.py projects\x` |
| lib_status.py | drift report by content hash: OK / UPDATE / LOCAL CHANGED / MISSING / LOCAL ONLY | LIB-06 | `python lib_status.py projects\x` |
| datasheets_fetch.py | download the catalog's datasheet PDFs (not in git) from `datasheet.url`; keeps a file only if its sha256 matches; never overwrites a good file | RQ-01 | `python datasheets_fetch.py` |
| parts.py | component database: new part (LCSC), datasheet fetch, page text for extraction, facts with page + quote, `check` verifies every quote on its page, index, find, price/stock | RQ-01, 03, 04 | `python parts.py new --lcsc C25804`, `python parts.py check` |
| parts_verify.py | walks a person through the person checks (pins, abs max, package, visual values) part by part, opens each PDF, records yes answers with parts.py verify, ends with check --gate | RQ-01 | `python tools\scripts\parts_verify.py` |
| catalog_check.py | catalog fields, datasheet sha256 (PDF not on disk = NOT FETCHED note), LCSC verified, footprint status, global file hashes | RQ-01, 03, LIB-05, 06 | `python catalog_check.py --project projects\x` |
| cad_register.py, cad_check.py | 3D model store (STEP header, sha256, index), structure only | LIB phase 2 | `python cad_check.py` |
| rules_lint.py | rule-file format; ENFORCED rules name existing scripts; `--write-index` | WF-04 | `python rules_lint.py --write-index` |

Inputs that drive the scripts (no project constants in code):
- `ai\plan.json` - parts and nets (eda DesignPlan format: `nets[].pins[].refdes/pin`).
- `ai\layout.json` - sheet coordinate plan (see sch_plan.py --help).
- `ai\sym_spec.json` - symbol spec (see gen_sym.py --help).
- `ai\calc_inputs.json` - calculations with limits and sources.
- `ai\place.json` - PCB placement plan (mm).
- `project.json` - name, rules_version, fab profile.
- `rules\fab-profiles\jlcpcb_2layer.json` - fab limits (published) and workspace defaults (design), with source and date.

Units: sheet scripts use mil; library pin coordinates are schematic units (10 = 100 mil); PCB scripts use mm.
