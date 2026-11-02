# 09 Library standard

The component library standard v1.1 (Simul, 2026-11-02) is in `docs/LIBRARY_STANDARD.md`; these rules make it binding in the kit.
Decisions D1-D12 are at the top of that file. Decided 2026-11-02: D1 (IC pins 200 mil), D2 (2-pin geometry by convenience), D3 (capacitors show capacitance and voltage), D4 (standard parameter names; existing libraries renamed only with permission), D6 (unknown distributor number = blank, ask the user), D5 (standard Description), D7 (3D from the database library first), D8 and D9 (names and folders by the category tree; restructure briefed first), D11 (Datasheet URL from the maker, DigiKey/LCSC only when the maker has none), D12 (the standard is public in the kit). Still open: D10; until it is decided LIB-19 applies.

### LIB-21 The library standard applies to every library component
- MUST: build, copy, classify and check every component (kit global, project local and client libraries) to `docs/LIBRARY_STANDARD.md`; where it is silent, the other LIB rules apply; where a client's rules differ, LIB-20 applies.
- MUST: follow an older kit rule over the standard only for the items still listed open (D1-D12), and name the item in the report.
- Why: one written standard keeps every part of a kind correct and identical, for people and agents alike.
- Check: checklist (report names the standard version and any open item used)
- Source: user 2026-11-02 (draft standard; "integrate these rules with our existing workspace rules")
- Status: CHECKLIST

### LIB-22 One category per part, from the default tree
- MUST: give every component exactly one Type/Subtype from the standard's default tree, by its classification procedure and tie-breaks, copied exactly; never put package, value, rating, polarity, channel count, mounting, pitch or brand into a category.
- MUST: mark a part REVIEW (and ask the user) when two subtypes still fit, tie-break 6 was used, no subtype fits, or no datasheet was found; a new category only as a proposal that passes the five gates, after the user approves it.
- Why: one home per part makes parts findable; a category made to avoid a decision splits the library.
- Check: checklist (planned tool lib_std_check: category exists in the tree)
- Source: user 2026-11-02 (standard: core principles, classification, AI agent instructions)
- Status: CHECKLIST

### LIB-23 Common and electrical parameters, values from the datasheet
- MUST: give every component the standard's common parameters and its subtype's required electrical parameters, named exactly as the standard, in its value format (SI prefix, no space, ASCII u, decimal point, ranges with "to", one value each); take every value from the component database (RQ-01), unknown = empty.
- MUST NOT: store price, stock, MOQ or lead time, or a second manufacturer on a component (an alternate brand is its own component).
- Why: names and formats Altium's importer and ActiveBOM can read; values traceable to a datasheet page.
- Check: checklist (planned tool lib_std_check: names, required values, value format, Description pattern)
- Source: user 2026-11-02 (standard: Parameters tab)
- Status: CHECKLIST

### LIB-24 Legacy component names stay until the user approves a rename
- MUST: keep a component's existing name (for example a Workspace `CMP-xxx` ID) until the user approves the rename batch; meanwhile its manufacturer and MPN parameters must be correct and checked.
- MUST NOT: rename a component, symbol or footprint on the way, even when the standard (Name = MPN) asks for it.
- Why: other designs and the client's Workspace point to those names; the user decides when they change.
- Check: lib_audit.py (lists names that are not the MPN)
- Source: user 2026-11-02 ("right now we did not change any component name")
- Status: CHECKLIST

### LIB-25 Symbol pins: datasheet names, numbers and electrical types
- MUST: name each pin with the datasheet's primary name (ASCII; active-low as an overbar), number it as the package, draw every pin including NC, exposed pad (EP, pin count + 1 when unnumbered), shield and mounting tabs; alternate functions only in the pin Description; no hidden or stacked pins (SYM-01..05).
- MUST: set each pin's electrical type from the standard's pin type table (Power, Input, Output, I/O, Open Collector, HiZ, Passive).
- Why: ERC only finds real faults when pin types are right; a pin table that maps 1:1 to the package can be diffed.
- Check: pin_match.py (pins = pads); checklist (pin type table)
- Source: user 2026-11-02 (standard SYM-01..05, pin electrical types)
- Status: CHECKLIST

### LIB-26 Symbol layout and style from the class template
- MUST: draw each symbol from its class template and the standard's style values: pin ends on 100 mil, 2-pin parts 400 mil span, IC side layout (SYM-13), MCU and multi-part rules (SYM-14, 17, 18), IC pin length 200 mil (D1, not the standard's 300), bus order (SYM-15), text positions and linked Comment (SYM-20..22), colours and font, designator prefixes.
- Why: identical symbols can be swapped without moving wires and read the same everywhere.
- Check: pin_match.py --style (to be updated to the style values after D1-D3)
- Source: user 2026-11-02 (standard SYM-10..22, symbol style values); decided D1 (IC pins 200 mil, LIB-11), D2 (2-pin geometry where convenient), D3 (capacitors show capacitance and voltage, LIB-02)
- Status: CHECKLIST

### LIB-27 Footprints: maker's land first, IPC-7351B Nominal otherwise
- MUST: use the maker's recommended land pattern, else IPC-7351B Nominal (FP-01..05); build geometry, origin, zero orientation, through-hole holes, exposed-pad paste, mask and BGA pads to FP-10..17; polarity and pin 1 to the polarity table; marking, silkscreen, names and board features to FP-20..26; layers and courtyard to the layer map; record the source in `Package Drawing` and `Footprint Standard`.
- Why: a footprint is only as good as its source and its numbers; one layer map lets parts flip to the bottom correctly.
- Check: checklist (verification step 4 table per pad group); catalog_check.py (status)
- Source: user 2026-11-02 (standard FP-01..26, layer map, courtyard); open D8 against LIB-13, LIB-15
- Status: CHECKLIST

### LIB-28 3D bodies: STEP at datasheet maximum size, one per body
- MUST: give every footprint a STEP body at the datasheet's maximum length, width and height, seated on the board with pin 1 on pin 1, on Mechanical 1, shared by every footprint of that body, at most 2 MB, keeping the maker's colours (3D-02..07).
- Why: a wrong height or pin-1 corner shows up only at assembly or in the enclosure.
- Check: cad_fetch.py (box check against the record)
- Source: user 2026-11-02 (standard 3D-01..07); open D7 (source order) against LIB-13
- Status: CHECKLIST

### LIB-29 Verification checklist per component, author never releases
- MUST: fill the standard's nine-step checklist for every component and keep it with the component: source, pin table diff, pin types, footprint dimension table, polarity, 3D, automated checks, 1:1 print (person only), shared-item where-used.
- MUST: the author (the agent, or whoever built it) never releases its own part: the agent's check makes it "checked" (LIB-18, LIB-19); only the verifier (a person) fills Verified By and Verified Date and marks it "confirmed".
- Why: a second pair of eyes against a fixed checklist catches what the author missed.
- Check: lib_audit.py mark; checklist (verification record per component)
- Source: user 2026-11-02 (standard: verification and release); open D10
- Status: CHECKLIST

### LIB-30 Brief the user and get a yes before each part or step
- MUST: before each library part or work step (copying a symbol or footprint, creating one, filling or renaming parameters, writing a library), tell the user in a few lines what will be done, to which part and from which source, and wait for the user's yes; then do only that.
- MUST: copy symbols and footprints from the user's database library first, made consistent (LIB-17); create one from scratch only when none exists and the user permits it.
- Why: the user follows the library work from the phone and wants to approve each part before it changes.
- Check: checklist (each part's report starts with the brief and the user's yes)
- Source: user 2026-11-02 ("before next part or going to each work brief user what going to do then taking permission do the job"; "part need not be built from scratch, mainly copy symbol and footprint from that database library")
- Status: CHECKLIST
