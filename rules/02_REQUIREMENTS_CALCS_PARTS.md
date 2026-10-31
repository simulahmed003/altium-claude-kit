# 02 Requirements, calculations, parts

### RQ-01 Datasheet first, through the component database
- MUST: take every device number (pinout, rating, land pattern) from the component database (library\parts\, `parts.py get`), where each value cites a datasheet page and a quote that `parts.py check` finds on it. Part or value missing: get the datasheet first (maker's website first for a good English version, LCSC second), add it with `parts.py fetch`, extract with page and quote, `parts.py check` PASS, then read it from the database. Never use memory, distributor text (supplier_params) or symbol metadata as the source. Stop and ask the user on a flaw: `parts.py check` fails for a reason in the datasheet, the datasheet contradicts itself or another source, a decision rests on an open review item, or a downloaded datasheet has another sha256 than recorded (revised).
- MUST: keep datasheet PDFs local, in the project's docs\datasheets\ (from the library cache, another folder or the database link: `parts.py datasheet --project`) and library\datasheets\; never commit a PDF to the global or a project repository.
- MUST: extracted values may be used while designing; before G1 a person checks pins, abs max, package and every visual value against the PDF and records it (`parts.py verify`; `parts.py check --gate` PASS).
- Why: wrong numbers become wrong hardware; the database removes repeated PDF reading and keeps every number traceable to a page.
- Check: parts.py check (quote on the cited page, units, abs max vs recommended), parts.py check --gate (person checks), catalog_check.py (datasheet sha256 per catalog component)
- Source: workspace CLAUDE.md "Datasheet first"; user decisions 2026-10-17 (database first, person checks 1c, PDFs local, maker first)
- Status: ENFORCED

### RQ-02 Calculations in code
- MUST: compute in code (calclib.py functions), copy results to calcs.md. No mental arithmetic.
- Why: repeatable numbers, regression-checked.
- Check: calclib.py tests; gate_check.py runs the project calcs when ai\calc_inputs.json exists
- Source: workspace CLAUDE.md "Calculations are done in code"
- Status: ENFORCED

### RQ-03 C-number verification
- MUST: count an LCSC C-number only when a JLCPCB/LCSC page confirms MPN and package; else mark it NOT VERIFIED.
- MUST: when a part has no known LCSC number, look it up with `parts.py lcsc <MPN>` (exact MPN, the match with most stock) and record it with `--add` only after the LCSC page confirms MPN and package. No exact match: a similar part with the same package drawing may supply only its 3D model, as a marked substitute the user accepts at G1 (LIB-13); its facts, price, footprint and symbol never stand for the part.
- Why: memory C-numbers were wrong or unverified; parts without a C-number (TPS54302) had no supplier data and no 3D model.
- Check: catalog_check.py (lcsc_verified field); parts.py lcsc (exact match, LCSC page confirmation); checklist
- Source: LESSONS L9; user 2026-10-13; user 2026-10-19 (parts without an LCSC number)
- Status: ENFORCED

### RQ-04 Stock and Basic parts
- MUST: use LCSC/JLCPCB as the supplier unless requirements.md names another; prefer JLCPCB Basic parts; check stock at BOM upload, not before (it does not block design; `parts.py market` keeps a dated snapshot).
- Why: Basic parts are cheaper to place; stock changes daily.
- Check: checklist (BOM upload)
- Source: user 2026-10-13; default supplier: user 2026-10-17
- Status: CHECKLIST

### RQ-05 Deviations
- MUST: log every deviation from a requirement or rule in part_list.md / PROJECT.md and get user approval.
- Why: L1 DCR/size and Q1 "Preliminary" were accepted only after the user saw them.
- Check: checklist
- Source: LESSONS L8
- Status: CHECKLIST

### RQ-06 Capacitor rating and dielectric
- MUST: rate capacitors >= 2x working voltage, X7R or X5R.
- Why: DC-bias loss and margin.
- Check: checklist (part_list.md)
- Source: user unattended brief 2026-10-13
- Status: CHECKLIST

### RQ-07 Thermal target
- MUST: compute junction temperature with the datasheet method; write the layout target (e.g. RthJA) in constraints.md; check it at G2.
- Why: buck needed RthJA <= 55 C/W at 18 V in (calcs.md finding 3).
- Check: calclib.py thermal functions; G2 checklist
- Source: buck calcs.md; user decision 2026-10-13
- Status: CHECKLIST

### RQ-08 Alternate parts at BOM preparation
- MUST: accept an alternate (an LCSC or other supplier part that is not the designer's MPN, or a stock substitute) only when it keeps the footprint (same package and land), the same pinout and polarity mark, the same value, and every key rating equal or better: voltage and current/power not lower, tolerance not wider, dielectric or tempco not worse (C0G > X7R > X5R > Y5V), temperature range not narrower. Such an alternate is acceptable (not a BOM error), but it is applied only after the user approves it: list every proposed alternate (designator, designer MPN, proposed part, rating check, stock) and wait for the yes; one yes may cover the whole list shown. Pick in this order: the exact MPN in stock for the order quantity plus attrition; the same maker's other packaging or grade (-7 / -13 reel); a JLC Basic part that meets the ratings; an Extended part in stock with the most stock. A rating that cannot be met in stock: take the next higher rating in stock (a 25 V capacitor for a 16 V line), else ask.
- MUST NOT: apply any alternate, or keep one found in an existing BOM, without the user's approval; use a lower rating, another value, another package, or one LCSC number for lines with different values; substitute an IC, a module, a connector (mechanical fit) or any active part with another MPN without the user's yes; substitute silently to avoid a quote shortfall (FAB-08).
- MUST: record each alternate: the BOM keeps the designer's MPN, the LCSC Part # that will be placed and an "Alternate LCSC Part #" column (one number per cell); a BOM-changes table lists designator, old, new, reason and the rating check; the same change is written back into the schematic (or local library) parameters, so a BOM exported from the schematic equals the production BOM.
- Why: Bondu main board (2026-10-30): five resistor values carried the 100K part's LCSC number, two capacitor lines carried 6.3 V / 10 V parts for 25 V MPNs; the user: an LCSC number that differs from the MPN is fine when rating and footprint match, out-of-stock parts need an in-stock alternate without changing footprint and rating.
- Check: bom_check.py (shared LCSC on different values, lower voltage in an alternate note, one number per cell, changes table); rating comparison per line: checklist
- Source: user 2026-10-30 ("if lcsc part doesn't agree with mfn part we didn't treat them as big issue as long as both have same rating and footprint"; "take upper voltage component"; "switch to 25v if available in stock otherwise 16v"); user 2026-10-31 ("but always get approval for this")
- Status: ENFORCED

### RQ-09 Distributor part numbers
- MUST: store the LCSC, Mouser and DigiKey numbers of a part in its record (`suppliers[]`: name, sku, url, verified date) and carry all three into the library parameters and the BOM. Record a number only after its product page confirms the MPN and package; otherwise write UNCONFIRMED in its place.
- MUST NOT: build a distributor number from a prefix pattern (Mouser 603-, 187-, 855-) and present it as known.
- Why: Extention_01 BOM had four Mouser numbers made from the prefix pattern; the user needs Mouser and DigiKey numbers in every BOM.
- Check: bom_check.py (UNCONFIRMED listed); checklist (product page opened)
- Source: user 2026-10-30 ("why you remove mouser digikey partnumber from bom"); user 2026-10-31 ("we add their Mouser, DigiKey, LCSC part number")
- Status: CHECKLIST

