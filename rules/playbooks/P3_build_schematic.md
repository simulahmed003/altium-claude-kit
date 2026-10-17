# P3 Build a schematic

Read with: 04_SCHEMATIC, 07_TOOLING_ALTIUM.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Write ai\plan.json (parts + nets) from the part list and calcs. | TESTED (buck) |
| 2 | Write ai\layout.json on the 100 mil grid with blocks; `python tools\scripts\sch_plan.py check ai\layout.json libs\x.SchLib ai\plan.json` until PASS. | TESTED (buck sheet read back: PASS) |
| 3 | Start the eda loop (user: File > Run Script > Altium_API > Dispatcher.pas > StartMCPServer); app_ping. | TESTED (buck) |
| 4 | Place parts and wires by coordinates (sch_place_*), merge collinear wires. | TESTED (buck); design_execute_plan UNTESTED |
| 5 | Save (app_save_document, check the file time); close and reopen the sheet (junction cache); save. | TESTED (buck) |
| 6 | conn_check.py (includes dots), sch_overlap.py on the saved file: all 0. | TESTED (buck) |
| 7 | Text pass, headings, boxes, title block, notes from calcs.md; rerun the checkers. | TESTED (buck) |
| 8 | ERC 0/0 (only waiver: nets with no driving source, listed in waivers.md). | TESTED (buck) |
| 9 | Captures (capwin.ps1 + crop.ps1), own review, `gate_check.py S1`, present (P6). | TESTED (buck captures; gate_check fixture) |

9 of 9 steps TESTED.
