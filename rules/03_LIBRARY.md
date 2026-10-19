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

## Shared items and building from the component database (PROPOSED 2026-10-19, docs/LIBRARY_PLAN.md)

### LIB-09 Library first, then build
- MUST: for each part, look up the symbol, the footprint and the 3D model in the catalog first (lib_find.py); build or download only the missing items, in the order LIB-11, LIB-12, LIB-13.
- Why: the same land or symbol drawn twice drifts apart and doubles the review work.
- Check: checklist (planned tool lib_find, LIBRARY_PLAN section 6)
- Source: user brief 2026-10-19
- Status: PROPOSED

### LIB-10 One shared item per shape
- MUST: store one symbol per pin list and kind, one footprint per package and land, and one 3D model per body; parts point to them through the catalog binding. Part-specific data lives only in parameters taken from the part record.
- MUST NOT: add a symbol or footprint that differs from an existing one only in value, MPN or parameters.
- Why: thousands of parts share a few hundred shapes; one copy keeps them consistent.
- Check: catalog_check.py (duplicate keys, planned)
- Source: user brief 2026-10-19
- Status: PROPOSED

### LIB-11 Symbols built from the part record
- MUST: build a missing symbol from the record's pin list (number, name, type) with gen_sym.py, under the drawing standard of LIB-02 and LIB-03 (100 mil grid, line width 1, one line colour, font size 10). IC symbols follow the datasheet's recommended pin grouping (pin functions, as the datasheet groups them) and are drawn symmetric: a centred body, pins spread evenly on opposite sides.
- Why: pins typed from memory were wrong before; the record holds the checked pin list.
- Check: pin_match.py --style; gen_sym.py grid check
- Source: user brief 2026-10-19; user 2026-10-19 (IC symbols: datasheet recommendation, symmetric)
- Status: PROPOSED

### LIB-12 Footprints built from land data in the record
- MUST: build a missing footprint from the record's land facts (datasheet land with page and quote). If the record lacks them, fetch the datasheet and extract them into the record first. If the datasheet has no land drawing, derive the IPC-7351 land from the package facts and mark the footprint "derived" (LIB-05). When a family keeps lacking a fact a footprint needs, add that key to its cad_required list in taxonomy.json.
- Why: a footprint is only as good as its numbers, and the numbers belong in the database with their source.
- Check: parts.py check --cad (planned); catalog_check.py (status)
- Source: user brief 2026-10-19
- Status: PROPOSED

### LIB-13 3D models: source order and check
- MUST: take a missing 3D model from JLC/EasyEDA by the LCSC number first, the maker's site second; a standard body (a chip size such as 0603, or a JEDEC package such as SOIC-8) has one model shared by every part of that body and footprint, whatever the value (a 10 uF and a 22 uF 0603 capacitor use the same model). A part-specific body (an inductor, a connector) needs its own model; a similar part's model only as a marked substitute that the user accepts at G1. Check the model's box against the record's body length, width and height (inside the datasheet min/max) and record source and sha256 in models/index.json.
- Why: a wrong height or pin-1 corner shows up only at assembly.
- Check: cad_check.py; box check in the planned tool cad_fetch
- Source: user brief 2026-10-19; user 2026-10-19 (standard body = one shared model)
- Status: PROPOSED

### LIB-14 Local library parameters from the record
- MUST: build one local library component per manufacturer part number (MPN), from the part record: Comment (value), Description, MPN, Manufacturer, LCSC, Datasheet (URL from the record) and the family's key ratings, all hidden except Comment (LIB-02).
- Why: parameters typed by hand drift from the database the calculations used.
- Check: checklist (planned tool lib_build, LIBRARY_PLAN section 6)
- Source: user brief 2026-10-19; user 2026-10-19 (one local component per MPN)
- Status: PROPOSED

### LIB-15 Library files per category
- MUST: keep one SchLib and one PcbLib per database category (library/parts/taxonomy.json); never one file per part. Split a category by family only when it passes the size the user set.
- Why: few files are easy to share and pull; the category is already known from the record.
- Check: catalog_check.py (category matches file)
- Source: user brief 2026-10-19
- Status: PROPOSED
