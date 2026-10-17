# P4 Library change while the design is open in Altium

Read with: 03_LIBRARY, 07_TOOLING_ALTIUM.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Announce the change; the user closes the library documents in Altium (altium-lib never writes an open library). | TESTED (buck) |
| 2 | Dry-run into libs\_dryrun\, compare (altium-lib diff_libraries / compare_components), then write the real file (.bak kept). | TESTED (buck) |
| 3 | validate_library 0/0; pin_match.py --style all PASS; pin ends unchanged unless a rewire is planned (LIB-08). | TESTED (buck) |
| 4 | User runs Tools > Update From Libraries; the ECO shows only symbol/parameter changes, never Add/Remove. | TESTED (buck) |
| 5 | Re-apply instance Values reset by the update (J1/J2 lesson); press End if the screen did not redraw. | TESTED (buck) |
| 6 | Save; conn_check.py PASS; proj_get_differences; PCB positions vs plan: `place.py ai\place.json --pcb hw\x\x.PcbDoc`. | TESTED (buck conn_check); place.py --pcb UNTESTED on a live board |
| 7 | Global copy: `lib_status.py <project>` shows the drift; promote only after G1 (`lib_promote.py`). | TESTED (selftest) |

7 of 7 steps TESTED.
