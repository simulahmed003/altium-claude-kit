# 02 Requirements, calculations, parts

### RQ-01 Datasheet first
- MUST: take every device number (pinout, rating, land pattern) from a PDF saved in the project's docs\datasheets\ (catalog stores its sha256).
- MUST NOT: use memory, distributor text or symbol metadata as the source.
- Why: wrong numbers become wrong hardware.
- Check: catalog_check.py (datasheet path + sha256 present per component); checklist for each quoted number
- Source: workspace CLAUDE.md "Datasheet first"
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
- MUST: prefer JLCPCB Basic parts; check stock at BOM upload, not before (it does not block design).
- Why: Basic parts are cheaper to place; stock changes daily.
- Check: checklist (BOM upload)
- Source: user 2026-10-13
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
