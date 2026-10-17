# 02 Requirements, calculations, parts

### RQ-01 Datasheet first, through the component database
- MUST: take every device number (pinout, rating, land pattern) from the component database (library\parts\, `parts.py get`), where each value cites a datasheet page and a quote that `parts.py check` finds on it. Part or value missing: get the datasheet first (maker's website first for a good English version, LCSC second), add it with `parts.py fetch`, extract with page and quote, `parts.py check` PASS, then read it from the database. Never use memory, distributor text (supplier_params) or symbol metadata as the source. A downloaded datasheet with another sha256 than recorded (revised): stop and ask the user.
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
- Why: memory C-numbers were wrong or unverified.
- Check: catalog_check.py (lcsc_verified field); checklist
- Source: LESSONS L9; user 2026-10-13
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
