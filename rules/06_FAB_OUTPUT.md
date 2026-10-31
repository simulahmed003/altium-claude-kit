# 06 Fab output

### FAB-01 No output before all gates
- MUST NOT: generate or send Gerbers, drill, BOM or pick-and-place to a fab before S1 and G1-G4 are ticked.
- Why: the gates exist to stop bad fabs.
- Check: gate_check.py G4 (refuses when earlier gates are open)
- Source: gates.md "Nothing is sent to a fab until G1-G4 are all ticked"
- Status: ENFORCED

### FAB-02 Gerber review
- MUST: open the output in a Gerber viewer and check layer count, outline, drills, silkscreen, mask, paste (G4).
- Why: output settings errors are invisible in Altium.
- Check: G4 checklist
- Source: gates.md G4
- Status: CHECKLIST

### FAB-03 Output through an OutJob
- MUST: generate outputs with an OutJob run by coffee (run_output_jobs), never with Altium print/PDF preview.
- Why: preview windows block the bridge (LESSONS T8).
- Check: checklist (at G4 confirm the files came from run_output_jobs, not from a preview)
- Source: LESSONS T8; approved by user 2026-10-13 (chat)
- Status: CHECKLIST

### FAB-04 BOM columns
- MUST: write the production BOM with the JLC upload columns Comment, Designator, Footprint, LCSC Part #, and keep the kit columns Quantity, Manufacturer, MPN, Mouser Part Number, DigiKey Part Number (plus "Alternate LCSC Part #" when RQ-08 applies); list every designator by itself (R125,R126,R127, never R125-R127); one part number per cell; hand-soldered and DNP parts marked, not dropped silently.
- Why: JLC could not read designator ranges (Bondu, 2026-10-30); the user needs Mouser and DigiKey numbers for other suppliers; JLC ignores the extra columns.
- Check: bom_check.py; jlc.py parse
- Source: user 2026-10-30 ("why you remove mouser digikey partnumber from bom"); JLC BOM upload of two boards 2026-10-30
- Status: ENFORCED

### FAB-05 Production package for the manufacturer
- MUST: build one folder `Manufacturing_<board>_Rev<x.y>\` next to the design (WF-09) holding only: `<board>_Rev<x.y>_Gerber.zip` (copper, mask, paste, silk, outline, PTH and NPTH drill), the BOM (FAB-04) and the CPL (FAB-06) as separate .csv (or .xlsx) files, an optional assembly drawing PDF, and README.txt with the board spec (layers, size, thickness, copper, finish, via treatment, assembly side, through-hole parts, notes).
- MUST NOT: put the schematic (in any form), design sources, libraries, backups or reference files (old CPL, correction lists) in it; those go to a `reference\` sub-folder that is never uploaded.
- MUST: regenerate the Gerbers when the copper, outline or drill changed after they were made (a stackup-only change does not need it) and refill zones before export.
- Why: the user's manufacturer format (Extention_01 and Bondu, 2026-10-30); a schematic leaves the company only by the user's choice.
- Check: fab_package.py check
- Source: user 2026-10-30 ("do not share schematic there, create required format like separate bom and cpl ... all gerber in zip file ... optionally add draftsman assembly doc")
- Status: ENFORCED

### FAB-06 CPL rotation and position, checked by numbers
- MUST: convert the CAD placement file to the assembler's convention with `cpl_check.py convert` (KiCad bottom side: JLC rotation = (180 - rotation) mod 360; Altium bottom side: not confirmed yet, see rules/fab-profiles/jlcpcb_assembly.json).
- MUST: for every polar or multi-pin part, find the assembler's footprint for its LCSC number (`cad_fetch.py`, library\models\jlc\<C>.json) and fit it onto our footprint by pin number (`cpl_check.py fit`); apply the rotation offset and centre shift through the offsets table; a pad that does not land on its same-numbered pad means wrong pin numbering in a library: fix the library or ask, never only rotate.
- MUST: upload the corrected CPL and confirm pin 1 (or polarity) of every polar and multi-pin part in the assembler's preview against our pad 1, part by part; keep before and after screenshots and the corrections table (designator, old, new, offset, shift) in the project's reference folder; record each confirmed footprint offset in the offsets table for reuse. Never call a CPL checked or verified because the preview "looks right" as a whole.
- Why: Bondu (2026-10-30): every bottom part at 0 or 180 deg came out flipped because the KiCad rotation was used raw, and 13 library footprints differed from JLC's (90/180/270 deg, up to 1.9 mm shift); the first look called it fine. Extention_01: J102 turned 180 deg and D101 reversed.
- Check: cpl_check.py (convert, fit, check against the BOM and the board box); preview check: checklist with screenshots
- Source: user 2026-10-30 ("most of the component got rotated ... we need to follow a procedure to identify how much each component got rotated ... just need the final proper CPL file"); memory rule "never call a CPL verified by eye"
- Status: ENFORCED

### FAB-07 BOM, CPL and design agree
- MUST: check before every upload: BOM designators = CPL designators (DNP and hand-soldered parts on neither, or on both and marked), every CPL position inside the board outline, no LCSC number shared by different values, and a BOM exported again from the design equals the production BOM after any change (RQ-08).
- Why: Bondu: LCSC fields in the schematic disagreed with the MPN on 14 lines; designators were in ranges.
- Check: bom_check.py --cpl; cpl_check.py check --bom --bbox
- Source: Bondu and Extention_01 packages, 2026-10-30
- Status: ENFORCED

### FAB-08 Assembly quotation (JLCPCB)
- MUST: quote from the final production package (the same Gerber zip, BOM and CPL that will be sent), with the board options taken from the README and the board's own fab notes (layers, size, thickness, finish, via treatment such as epoxy filled and capped, smallest via), the same options for every quantity, the assembly type and side matching the CPL. Before taking any price, every BOM line is matched (RQ-08 for stock alternates) and the placement preview passes FAB-06.
- MUST: record per board and quantity: PCB cost, every assembly line (setup, stencil, parts, feeder/loading, SMT joints, hand soldering, surcharges, other) and the total without shipping, with a screenshot. When the assembler cannot place lines at a quantity because of stock, quote without them AND compute the full cost as if nothing were short with `jlc_quote.py shortfall` (JLC's own rates read from the quotes, rules/fab-profiles/jlcpcb_assembly.json), shown next to the quoted figure with the method. Then deliver an Excel workbook (Summary with total and per-board cost per quantity, JLC breakdown, shortfall calculation with rate inputs and sources, specs and BOM notes) and a document with every preview and quote screenshot, in the user's project folder (WF-09); propose a panel when a small board carries a single-board surcharge at volume.
- MUST NOT: type passwords (the user logs in), add to cart, order or pay; substitute an IC or connector to avoid a shortfall without asking.
- Why: two-board quote of 2026-10-30 (5/10/1000/3000 pcs): the user wanted totals as if nothing were short, a boss-ready workbook and screenshots for checking rotations.
- Check: jlc_quote.py (shortfall and summary arithmetic, RQ-02); checklist (screenshots, workbook sheets)
- Source: user 2026-10-30 ("if you see part shortfall understand their billing pattern and calculate yourself"; "in summary make a table as the total cost if no shortfall happen"; Excel to submit to the boss)
- Status: CHECKLIST
