# P9 Production package, BOM and CPL for the manufacturer

Read with: 06_FAB_OUTPUT (FAB-04..07), 02_REQUIREMENTS_CALCS_PARTS (RQ-08, RQ-09), 01_WORKFLOW_GATES (WF-09).
Skill: `altium-fab-package`. All commands are for cmd.exe, run from the workspace folder (D:\EDA). Quote paths
that contain spaces. The design stays in the user's folder (WF-09); `<pkg>` below is
`<design folder>\Manufacturing_<board>_Rev<x.y>`.

Status per step: TESTED = done on a real board (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Gates G1-G3 ticked by the user (FAB-01). Regenerate Gerbers and drill with zones refilled if copper, outline or drill changed after the last output (FAB-05). Altium: the OutJob containers; KiCad: kicad-cli. | TESTED (Extention_01 Altium, Bondu KiCad, 2026-10-30) |
| 2 | Make `<pkg>` and `<pkg>\reference\`. Zip the Gerber and drill files into `<board>_Rev<x.y>_Gerber.zip`. | TESTED (both boards) |
| 3 | BOM: export from the design, then add the kit columns (FAB-04) and one designator per entry. Fix every LCSC number that is not the line's value or rating; pick stock alternates by RQ-08, show the list (designator, MPN, proposed part, rating check, stock) and apply them only after the user's yes, then write them back into the schematic. `python tools\scripts\bom_check.py "<pkg>\<board>_BOM.csv"` until PASS. | TESTED by hand (Bondu: 14 lines fixed); bom_check UNTESTED on a real BOM |
| 4 | CPL: `python tools\scripts\cpl_check.py convert <cad placement file> "<pkg>\<board>_CPL.csv" --src kicad\|altium --offsets "<design folder>\_eda\ai\cpl_offsets.json"`. | rule TESTED by hand (Bondu bottom side, 2026-10-30); tool UNTESTED on a real board |
| 5 | Offsets for polar and multi-pin parts: get the JLC footprint for the LCSC number (`python tools\scripts\cad_fetch.py <part>` writes `library\models\jlc\<C>.json`; a JLC2KiCadLib .kicad_mod works too), then `python tools\scripts\cpl_check.py fit --ours <our footprint> --jlc <JLC record> --save "...\cpl_offsets.json" --key <footprint name>`; a misfit pad = wrong pin numbering, fix the library or ask. Re-run step 4. | method TESTED (Bondu, 13 footprints); tool UNTESTED on a real board |
| 6 | `python tools\scripts\cpl_check.py check "<pkg>\<board>_CPL.csv" --bom "<pkg>\<board>_BOM.csv" --bbox xmin,ymin,xmax,ymax`. | UNTESTED |
| 7 | `python tools\scripts\fab_package.py readme "<pkg>" --board <B> --rev <x.y> --layers <n> --size <WxH> ...`, add the optional assembly drawing PDF, then `python tools\scripts\fab_package.py check "<pkg>"` until PASS. Old CPLs and correction tables go to `<pkg>\reference\`. | format TESTED (both boards); tool UNTESTED on a real board |
| 8 | Upload to the assembler and confirm the preview part by part (FAB-06; P10 steps 3-4). Fix and re-upload until every polar and multi-pin part has pin 1 on our pad 1. | TESTED (Extention_01: J102, D101 fixed; Bondu: 43 parts fixed) |
| 9 | Report: the folder path, what changed in the BOM (changes table), what the user must still decide. Write the decisions into PROJECT.md. | TESTED (both boards) |

Steps tested by hand: 1, 2, 8, 9 fully; 3-7 by hand, their tools new in rules 1.6.0.
