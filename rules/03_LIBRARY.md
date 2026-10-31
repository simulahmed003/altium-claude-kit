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

## Shared items and building from the component database (approved 2026-10-19, docs/LIBRARY_PLAN.md)

### LIB-09 Library first, then build
- MUST: for each part, look up the symbol, the footprint and the 3D model in the catalog first (lib_find.py); build or download only the missing items, in the order LIB-11, LIB-12, LIB-13.
- Why: the same land or symbol drawn twice drifts apart and doubles the review work.
- Check: checklist (planned tool lib_find, LIBRARY_PLAN section 6)
- Source: user brief 2026-10-19
- Status: CHECKLIST

### LIB-10 One shared item per shape
- MUST: store one symbol per pin list and kind, one footprint per package and land, and one 3D model per body; parts point to them through the catalog binding. Part-specific data lives only in parameters taken from the part record.
- MUST NOT: add a symbol or footprint that differs from an existing one only in value, MPN or parameters.
- Why: thousands of parts share a few hundred shapes; one copy keeps them consistent.
- Check: catalog_check.py (duplicate keys, planned)
- Source: user brief 2026-10-19
- Status: CHECKLIST

### LIB-11 Symbols built from the part record
- MUST: build a missing symbol from the record's pin list (number, name, type) with gen_sym.py, under the drawing standard of LIB-02 and LIB-03 (100 mil grid, line width 1, one line colour, font size 10). IC symbols follow the datasheet's pin grouping and functional block order (power top, ground bottom, inputs left, outputs right), symmetric where the pinout allows, pin names exactly as in the datasheet, pin length 200 mil.
- Why: pins typed from memory were wrong before; the record holds the checked pin list.
- Check: pin_match.py --style; gen_sym.py grid check
- Source: user brief 2026-10-19; user 2026-10-19 (IC symbols: datasheet grouping, symmetric, 200 mil pins)
- Status: CHECKLIST

### LIB-12 Footprints built from land data in the record
- MUST: build a missing footprint from the record's land facts (datasheet land with page and quote). If the record lacks them, fetch the datasheet and extract them into the record first. If the datasheet has no land drawing, derive the IPC-7351 land from the package facts and mark the footprint "derived" (LIB-05). When a family keeps lacking a fact a footprint needs, add that key to its cad_required list in taxonomy.json.
- Why: a footprint is only as good as its numbers, and the numbers belong in the database with their source.
- Check: parts.py check --cad (planned); catalog_check.py (status)
- Source: user brief 2026-10-19
- Status: CHECKLIST

### LIB-13 3D models: source order and check
- MUST: take a missing 3D model from JLC/EasyEDA by the LCSC number first, the maker's site second; a standard body (a chip size such as 0603, or a JEDEC package such as SOIC-8) has one model shared by every part of that body and footprint, whatever the value (a 10 uF and a 22 uF 0603 capacitor use the same model). A part-specific body (an inductor, a connector) needs its own model; a similar part's model only as a marked substitute that the user accepts at G1. A part with no LCSC number (or whose JLC model fails the check): find the same part, or one with the same body, on LCSC and use its model (`cad_fetch.py <part> --lcsc <its C-number>`), stored marked as a substitute that the user accepts at G1. Downloaded models are committed to the global library so others can use and extend it (unlike datasheet PDFs). Check the model's box against the record's body length, width and height (inside the datasheet min/max) and record source and sha256 in models/index.json.
- Why: a wrong height or pin-1 corner shows up only at assembly.
- Check: cad_check.py; cad_fetch.py (box check against the record, placement, register)
- Source: user brief 2026-10-19; user 2026-10-19 (standard body = one shared model); user 2026-10-19 (no LCSC number: same or similar part on LCSC; STEP models committed)
- Status: CHECKLIST

### LIB-14 Local library parameters from the record
- MUST: build one local library component per manufacturer part number (MPN), whose library reference (name) is exactly the MPN (0603WAF1002T5E, LMR33630ADDAR), with parameters from the part record: Comment (value, or the MPN for an IC), Description (prefix, value, key rating, package: "R 10k 1% 0603"), Manufacturer, MPN, LCSC, Mouser, DigiKey (RQ-09), Datasheet (URL from the record) and the family's key ratings, all hidden except Comment (LIB-02).
- Why: parameters typed by hand drift from the database the calculations used; a bare MPN name is found by search and matches the BOM.
- Check: checklist (planned tool lib_build, LIBRARY_PLAN section 6)
- Source: user brief 2026-10-19; user 2026-10-31 (decision: library reference = bare MPN; Mouser, DigiKey and LCSC numbers in every component)
- Status: CHECKLIST

### LIB-15 Library files: symbols by category and family, footprints by package type
- MUST: keep global symbols in library/symbols/<category>/<family>.SchLib (names from library/parts/taxonomy.json), global footprints in library/footprints/<package type>.PcbLib and 3D models in library/models/step/<package type>/, each footprint once. Build a project's local library as libs/<category>/<family>.SchLib and .PcbLib, copying the global footprints a family uses into its PcbLib. Never one file per part; create a file when its first part comes in.
- Why: the record knows its category and family, so symbols are found without a lookup table; one package serves several families, so the global footprint and 3D model live once per package; local family files keep a project's library small and readable.
- Check: catalog_check.py (folders and file names, after the migration); lib_status.py (local footprint copies match the global one)
- Source: user brief 2026-10-19; user 2026-10-19 ("for each category a folder, for each family a library file"; global footprints by package type, local one footprint file per family)
- Status: CHECKLIST

### LIB-16 People may edit the global library
- MUST: accept edits a person makes directly to the global library (symbols, footprints, 3D models, READMEs). Before building on a changed item, run lib_status.py / catalog_check.py, tell the user what changed, and ask before adapting catalog entries, hashes or project copies to it; after a yes, record the edit with `lib_promote.py - --adopt <id> --by <name>` (new revision).
- Why: the user improves the library by hand from time to time; the tools must follow those changes, not overwrite them.
- Check: catalog_check.py (global file hashes); lib_promote.py --verify / --adopt
- Source: user 2026-10-19 ("I may update the global library from time to time ... then adapt after asking")
- Status: CHECKLIST

## New components in a local library (2026-10-31)

### LIB-17 New component copied from the DbLib, made consistent
- MUST: take a missing component from the user's Altium database library (DbLib) first: copy its symbol, footprint and 3D model into the local library (and, after G1, into the kit global library); the kit global library comes second; build (LIB-11..13) only what neither has. Record where each item came from (`lib_audit.py source <id> --from dblib --ref <DbLib item>`).
- MUST: make every copy consistent before use: name = MPN (LIB-14); symbol style, visible text, pin grid and pin length to LIB-02, LIB-03, LIB-11; parameters and their names to LIB-14 from the part record; footprint geometry kept as copied unless the datasheet check (LIB-18) finds a mismatch, which the user decides; 3D model attached and checked (LIB-13).
- MUST NOT: change, add to or write back into the DbLib or its database in any way; it is read-only for the kit, even when the tool would allow a write.
- Why: the DbLib holds many checked parts and saves building them again; it is not ours to change; copies from several sources drift apart unless each one is brought to one standard.
- Check: lib_audit.py (name, parameters, source, check status); pin_match.py --style
- Source: user 2026-10-31 ("DbLib will be our primary source but we must keep things consistent high"; "we do not modify or contribute in the DB library"); Extention_01 2026-10-30 (Celestial DbLib read-only)
- Status: ENFORCED

### LIB-18 Every new or copied symbol and footprint checked against the datasheet
- MUST: before reporting a part placed or a library item done, check its symbol pin map, footprint pads (pitch, pad size, hole size, pin-1 position) and package against the part's datasheet through the component database (RQ-01), and write what was checked and any mismatch (e.g. "holes 1.10 mm, maker recommends 1.02") in the report. This applies equally to a symbol or footprint copied from a similar part or from a database library.
- MUST NOT: hand this check back to the user, even when the user asks for speed; the user's own check before G1 (RQ-01) comes on top of it.
- Why: Extention_01 (2026-10-30): an S8550 copied from an S8050 was placed with a wrong current rating and an unchecked pinout; the user had already made this a strict instruction.
- Check: checklist (report lists pins, pads and package checked per part); pin_match.py
- Source: user 2026-10-30 ("you check the sch and footprint symbol against datasheet ... I already give you instructions strictly about that")
- Status: CHECKLIST

### LIB-19 Check status of every library component
- MUST: give every component in the kit global library and in a local library a check status: unchecked -> checked (the agent's datasheet check, LIB-18, with date and pages) -> confirmed (a person confirmed pins, pads and package). Record it with `lib_audit.py mark`; only a person marks confirmed. Use only confirmed components without a warning; an unchecked or checked one is named in every report that uses it.
- MUST: rebuild a component that `lib_audit.py` lists as REBUILD before it goes into a new design, through P11 (copy from the DbLib, make consistent, check).
- Why: the existing kit library was built before the current rules (descriptive names, no Mouser/DigiKey, datasheet file names, no check record); the user wants every component visibly checked or confirmed.
- Check: lib_audit.py (audit table library/catalog/AUDIT.md; mark, source)
- Source: user 2026-10-31 ("rebuild kit library according to our complete library creation rules and mark each component confirmed or checked")
- Status: ENFORCED

### LIB-20 Library work for a client under the client's rules
- MUST: when building components for a client's library (their Altium workspace or DbLib), keep the client's library rules in `standards/local/clients/<client>/` (never pushed), build the parts locally as a local library that follows those rules, and deliver them the way the client asks; the kit rules fill only what the client's rules leave open, and the datasheet check (LIB-18) always applies.
- MUST: after each client job, list where the client's rules differ from the kit rules and sort each difference with the user (altium-rule-harvest, WF-08) before any kit rule changes.
- PLACEHOLDER: filled when the client's rules arrive.
- Why: the user will build libraries for a company that pushes them to its own Altium workspace; their rules govern their parts, and good ideas from them should improve the kit.
- Check: checklist (client rules file present; harvest table sorted)
- Source: user 2026-10-31 ("what they will push we will create that locally as our local library under their rules ... and update our rules accordingly")
- Status: PROPOSED

