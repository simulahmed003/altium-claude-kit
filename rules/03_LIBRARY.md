# 03 Library

### LIB-01 Pins = pads
- MUST: give every symbol exactly the pins of its footprint: one visible pin per pad, same number.
- MUST NOT: stack or hide pins.
- Why: Q1 showed only D/S/G and hid five pads.
- Check: pin_match.py
- Source: LESSONS L1; user rule 2026-10-13
- Status: ENFORCED

### LIB-02 One style, only Designator and Comment visible
- MUST: one style per symbol type (line width 1, one colour, one font size 10); visible text = Designator + Comment "=Value" only; MPN, Manufacturer, LCSC, JLCPCB Type, Datasheet hidden.
- Why: duplicate value text and mixed styles made the sheet unreadable.
- Check: pin_match.py --style (visible parameters per symbol)
- Source: LESSONS L3, L4
- Status: ENFORCED

### LIB-03 Pin ends on the 100 mil grid
- MUST: put every pin connection point on the 100 mil grid. Exceptions (body side off-grid only): cap pin 80 mil, test-pad pin 70 mil.
- Why: off-grid pins make wires miss pins.
- Check: pin_match.py (grid check)
- Source: buck library v2 (gen_sym2.py), user accepted exceptions 2026-10-13
- Status: ENFORCED

### LIB-04 Writing libraries
- MUST: close the library in Altium, dry-run into libs\_dryrun\, keep the .bak, validate 0 errors 0 warnings, then run pin_match.py.
- Why: open libraries get locked or overwritten.
- Check: checklist + pin_match.py
- Source: LESSONS T24
- Status: CHECKLIST

### LIB-05 Footprint verification status
- MUST: verify each footprint 1:1 against the datasheet at G1 and record its status: datasheet-verified / derived (with source) / unverified-accepted (who, when). Carry the status into every reuse.
- Why: passive lands were derived; the SOIC8 land had no manufacturer drawing.
- Check: catalog_check.py (status field)
- Source: LESSONS L6, L7
- Status: ENFORCED

### LIB-06 Global library and local copies
- MUST: open only the project's local copies (projects\<p>\libs\); change the global library only through lib_promote after G1; record used revs in libs\lib_manifest.json; copy footprints with preserve_external_paths=true.
- Why: one source of truth without silent drift.
- Check: lib_status.py; catalog_check.py
- Source: user brief 2026-10-13; LESSONS T26, T27
- Status: ENFORCED

### LIB-07 Pin-name spacing
- MUST: keep pin names from touching; widen or heighten the body (altium-lib cannot set the pin-name offset).
- Why: U1 PGND/AGND names touched VCC/FB.
- Check: checklist (capture) + sch_overlap.py on the sheet
- Source: LESSONS T25
- Status: CHECKLIST

### LIB-08 Edit placed symbols without moving pin ends
- MUST: keep every pin connection point fixed when restyling a symbol that is already on a sheet, unless the rewire is planned.
- Why: moved pin ends disconnect wires after Update From Libraries.
- Check: conn_check.py after the update
- Source: LESSONS L5
- Status: ENFORCED

## PCB footprint and 3D models (phase 2, waiting for the user's ideas)

(Intentionally empty.)
