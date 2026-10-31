# Tools guide (for you, in cmd.exe)

Every kit tool runs by itself from cmd.exe, without Claude and without Altium (except where noted). Two ways:

```
cd /d D:\EDA
python tools\scripts\<tool>.py --help
```
or, from any folder, with the `kit.cmd` launcher in the workspace root (add D:\EDA to PATH once, or type
`D:\EDA\kit`):
```
kit                          lists every tool
kit <tool> --help            full help of one tool
kit <tool> <arguments>       runs it
```
Every tool prints PASS / FAIL lines and ends with exit code 0 (PASS) or 1 (FAIL). Put paths with spaces in quotes.
The examples use `"D:\Work\Acme\Board1"` for a design that lives in your own (employer) folder.

## Production files and quotes (new in rules 1.6.0)

| Task | Command | Rules |
|---|---|---|
| Check a production BOM (columns incl. Mouser/DigiKey, no designator ranges, one LCSC number per cell, no LCSC number shared by two values, no lower-voltage alternate) | `kit bom_check "D:\Work\Acme\Board1\Manufacturing_B1_Rev1.0\B1_BOM.csv"` | FAB-04, FAB-07, RQ-08 |
| Same, plus BOM = CPL designators and a BOM-changes table | `kit bom_check B1_BOM.csv --cpl B1_CPL.csv --changes bom_changes.csv` | FAB-07 |
| Turn a KiCad position file into a JLC CPL (bottom side: 180 - rotation) | `kit cpl_check convert board-all-pos.csv B1_CPL.csv --src kicad` | FAB-06 |
| Turn an Altium Pick Place file into a JLC CPL | `kit cpl_check convert "Pick Place for B1.csv" B1_CPL.csv --src altium` | FAB-06 |
| Find how much JLC's footprint is rotated/shifted against ours (by pin number) and save it | `kit cpl_check fit --ours U104.kicad_mod --jlc library\models\jlc\C2838168.json --save "D:\Work\Acme\Board1\_eda\ai\cpl_offsets.json" --key HVQFN-24` | FAB-06 |
| Apply the saved offsets while converting | `kit cpl_check convert pos.csv B1_CPL.csv --src kicad --offsets "...\cpl_offsets.json"` | FAB-06 |
| Check a CPL (columns, rotation 0-359, inside the board, same parts as the BOM) | `kit cpl_check check B1_CPL.csv --bom B1_BOM.csv --bbox 0,0,80,70` | FAB-06, FAB-07 |
| Write the README for the manufacturer folder | `kit fab_package readme "<pkg>" --board B1 --rev 1.0 --layers 2 --size 15.4x13.2 --side Top --tht J102` | FAB-05 |
| Check the manufacturer folder (no schematic, no design files, Gerber zip complete, BOM, CPL, README) | `kit fab_package check "D:\Work\Acme\Board1\Manufacturing_B1_Rev1.0"` | FAB-05 |
| Full JLC cost when parts are short on stock at a quantity | `kit jlc_quote shortfall quote_B1_1000.json` (input format: `kit jlc_quote --help`) | FAB-08 |
| Table of all quotes (quoted and full totals, per-board price) | `kit jlc_quote summary quote_*.json --csv quote_summary.csv` | FAB-08 |
| Older JLC BOM/CPL from a kit project (plan.json + PcbDoc) | `kit jlc bom ai\plan.json out\bom.csv`, `kit jlc cpl hw\B1\B1.PcbDoc out\cpl.csv` | FAB-04 |

JLC rates used by `jlc_quote` and the CPL side rule live in `rules\fab-profiles\jlcpcb_assembly.json` (observed
2026-10-30; re-read them from a fresh quote).

## Projects

| Task | Command | Rules |
|---|---|---|
| New project inside the workspace | `kit new_project my-board` | P1 |
| Use the kit on a design that stays in your own folder (adds only `_eda\`) | `kit new_project board1 --attach "D:\Work\Acme\Board1"` | WF-09 |
| Gate evidence pack | `kit gate_check G1 projects\my-board` or `kit gate_check S1 "D:\Work\Acme\Board1\_eda"` | WF-01, WF-02 |
| Everything still works | `kit selftest` | - |

## Parts and libraries

| Task | Command | Rules |
|---|---|---|
| Find a part in the component database | `kit parts find DMG2301L` | RQ-01 |
| Add a part by LCSC number, get its datasheet | `kit parts new --lcsc C25804`, `kit parts fetch <MPN> --project <folder>` | RQ-01 |
| Find a part's LCSC number | `kit parts lcsc <MPN>` | RQ-03 |
| Check a part record | `kit parts check <MPN>` | RQ-01 |
| Walk through your person checks (pins, abs max, package) | `kit parts_verify` | RQ-01 |
| Symbol pins = footprint pads, style | `kit pin_match libs\x.SchLib libs\x.PcbLib --style` | LIB-01..03 |
| Download and file a 3D model (also writes the JLC footprint record used by `cpl_check fit`) | `kit cad_fetch <part>` | LIB-13 |
| Global library: status, pull, promote, catalog | `kit lib_status <project>`, `kit lib_pull`, `kit lib_promote`, `kit catalog_check` | LIB-06 |

## Schematic and PCB checks

| Task | Command | Rules |
|---|---|---|
| Sheet connectivity against the net plan | `kit conn_check hw\B1\Sheet1.SchDoc ai\plan.json` | SCH-P |
| Sheet readability | `kit sch_overlap hw\B1\Sheet1.SchDoc` | SCH-B..N |
| Junction dots | `kit dots hw\B1\Sheet1.SchDoc` | SCH-Q |
| Placement plan check | `kit place ai\place.json --pcb hw\B1\B1.PcbDoc` | PCB-12 |
| Calculations | `kit calcs_run ai\calc_inputs.json --md` | RQ-02 |

The full list with every option: `tools\scripts\README.md`.

## Tools worth building next (proposals, not made yet)

These steps were done by hand more than once; a tool would save time and tokens. Say which to build.

| Proposal | Saves | Why now |
|---|---|---|
| `bom_build.py`: production BOM straight from an Altium/KiCad BOM export + part records (kit columns, designators one by one, Mouser/DigiKey from `suppliers[]`, changes table) | the hand-built BOM step in P9 | both boards' BOMs were assembled by hand; columns were dropped once |
| `lcsc_stock.py`: stock and price of every BOM line at a given quantity, with in-stock alternates that pass RQ-08 | the shortfall hunt during quotes | 6 to 9 Bondu lines were short at 1000/3000 pcs |
| `gerber_check.py`: layers, outline, drill sizes and counts from the Gerber zip | FAB-02 review by eye | listed in the kit inventory as missing |
| `kicad_export.cmd`: Gerbers, drill, positions and BOM through kicad-cli with zones refilled | KiCad output step | stale zone fills gave 62 false DRC errors on Bondu |
| `quote_book.py`: the Excel quote workbook from `jlc_quote` JSON files (needs openpyxl) | building the workbook by hand | the workbook was rebuilt three times for the final look |
