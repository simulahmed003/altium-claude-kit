# P5 PCB placement

Read with: 05_PCB, 07_TOOLING_ALTIUM.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | G1 and S1 ticked (`gate_check.py G2` shows them). | TESTED (gate_check on buck, scratch output) |
| 2 | User runs Design > Update PCB; the ECO adds every part; the .PrjPcb lists the PcbDoc (gate_check TOOL-09 row). | TESTED (buck) |
| 3 | Release the eda loop (app_detach saves all: announce first); switch to coffee. | TESTED (buck) |
| 4 | Board outline; stackup 1.6 mm, 2 layers in Layer Stack Manager; rules from the fab profile. | UNTESTED |
| 5 | Write ai\place.json (mm, rot); `python tools\scripts\place.py ai\place.json --catalog library\catalog\components.json` PASS. | TESTED (fixtures) |
| 6 | Place with coffee set_component_position one part at a time; save; check_placement (courtyards may touch, not overlap). | TESTED (buck, first parts only) |
| 7 | `place.py ai\place.json --pcb hw\x\x.PcbDoc` 0 differences; capture; G2 checklist. | UNTESTED |

5 of 7 steps TESTED.
