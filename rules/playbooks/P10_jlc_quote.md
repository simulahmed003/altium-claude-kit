# P10 JLCPCB assembly quotation

Read with: 06_FAB_OUTPUT (FAB-06, FAB-08), 02_REQUIREMENTS_CALCS_PARTS (RQ-08). Skill: `altium-jlc-quote`.
Needs the browser (Claude in Chrome or Edge with the Claude extension); the user logs in to jlcpcb.com. Never type
a password, never add to cart, order or pay.

| # | Step | Status |
|---|---|---|
| 1 | Package passes P9 (`fab_package.py check`). Copy the upload files to the workspace `tmp\` folder only if the browser can upload only from the workspace (WF-09); delete that copy at the end. | TESTED (2026-10-30) |
| 2 | Upload the Gerber zip; check JLC's detected layers and size against the README. Set thickness, finish, via treatment and smallest via from the board's fab notes; keep the same options for every quantity. | TESTED (Bondu: epoxy filled and capped, lead-free HASL, 0.2 mm via) |
| 3 | PCB Assembly on, type Standard (or as asked), side as in the CPL. Upload BOM and CPL. Every BOM line matched; an unmatched or short line: propose an RQ-08 alternate and wait for the user's yes before selecting it. | TESTED (both boards) |
| 4 | Placement preview: check pin 1 / polarity of every polar and multi-pin part against our pad 1 (FAB-06); screenshot before and after any fix. | TESTED (2026-10-30; first Bondu look was wrong, then fixed by numbers) |
| 5 | For each quantity: record PCB cost and every assembly line with a screenshot. Lines short at that quantity: let JLC quote without them, write `ai\quote_<board>_<qty>.json` and run `python tools\scripts\jlc_quote.py shortfall ai\quote_<board>_<qty>.json`. | TESTED by hand (8 quotes); tool UNTESTED on a real quote |
| 6 | `python tools\scripts\jlc_quote.py summary ai\quote_*.json --csv <folder>\quote_summary.csv`, then build the workbook (Summary, JLC breakdown, Shortfall calculation with rate inputs and sources, Specs and BOM notes) and the screenshot document in the user's folder. Re-read the rates from today's quotes and update rules\fab-profiles\jlcpcb_assembly.json if they changed. | TESTED by hand (2026-10-30) |
| 7 | Report: table of totals per board and quantity (quoted and full), BOM substitutes needing a yes, the panel suggestion for small boards at volume, where the files are. | TESTED (2026-10-30) |
