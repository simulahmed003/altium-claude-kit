# 02 Requirements, calculations, parts

### RQ-01 Component database first
- MUST: take every device number (pinout, rating, package, land pattern) from the part's record in library\parts\ (`parts.py get`); each fact cites its datasheet page, quote and PDF sha256.
- MUST: if the part or the fact is missing, fetch the datasheet and extract it into the record until `parts.py check` passes, then read it from the record. If the record fails check, contradicts its datasheet or another source, or the fact rests on an open review item, stop and ask the user.
- MUST NOT: use memory, distributor text or symbol metadata as the source; pins, abs max and package are used for G1 only when the record is verified by the user.
- Why: wrong numbers become wrong hardware; one checked record per part saves opening the PDF in every project.
- Check: parts.py check (page + quote per fact, units, abs max vs recommended); catalog_check.py (datasheet sha256)
- Source: workspace CLAUDE.md "Datasheet first"; user 2026-10-17 (database first, fetch and extract when missing, ask on a flaw)
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
