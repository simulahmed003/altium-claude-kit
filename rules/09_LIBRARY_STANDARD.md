# 09 Library standard

The component library standard v1.1 (Simul, 2026-11-02) is in `docs/LIBRARY_STANDARD.md`; these rules make it binding in the kit.
Decisions D1-D12 are at the top of that file. Decided 2026-11-02: D1 (IC pins 200 mil), D2 (2-pin geometry by convenience), D3 (capacitors show capacitance and voltage), D4 (standard parameter names; existing libraries renamed only with permission), D6 (unknown distributor number = blank, ask the user), D5 (standard Description), D7 (3D from the database library first), D8 and D9 (names and folders by the category tree; restructure briefed first), D11 (Datasheet URL from the maker, DigiKey/LCSC only when the maker has none), D12 (the standard is public in the kit). Still open: D10; until it is decided LIB-19 applies.
Parameter set frozen 2026-11-03 (LIB-31, LIB-32): the parameters below are the complete list until the user asks to change or add one.

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
- Check: lib_params.py --check (Category exists in the tree); ws_lib_check.py
- Source: user 2026-11-02 (standard: core principles, classification, AI agent instructions)
- Status: CHECKLIST

### LIB-23 Common and electrical parameters, values from the datasheet
- MUST: give every component the 25 common parameters and its subtype's required electrical parameters (rules/library_parameters.json; one category: `kit lib_params "<Type>/<Subtype>"`), named exactly as written, in its value format (SI prefix, no space, ASCII u, decimal point, ranges with "to", one value each); take every value from the component database (RQ-01), unknown = empty.
- MUST NOT: store price, stock, MOQ or lead time values, or a second manufacturer on a component (an alternate brand is its own component); the Price/Stock product links of LIB-31 are links, not values, and are allowed.
- Why: names and formats Altium's importer and ActiveBOM can read; values traceable to a datasheet page.
- Check: lib_params.py --check (names per category); checklist (values, value format, Description pattern)
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
- Decided by the user 2026-11-04: in a batch the brief and the yes cover the whole batch (WF-12); per-part briefs only when the user asks to go part by part.
- Status: CHECKLIST

### LIB-31 The parameter set is frozen until the user changes it
- MUST: give each component exactly the parameters in the tables below and nothing new: the stored common ones, its subtype's electrical ones and the links `Mouser Price/Stock`, `DigiKey Price/Stock`, `LCSC Price/Stock`; names without the hint in brackets (`Dielectric`, not `Dielectric (X7R, X5R, C0G)`); `Supplier 1` and `Supplier Part Number 1` present but empty.
- MUST: Description in the component field and as a hidden `Description` parameter; Comment = the value (`100nF`, `10k`, `10R`, `4.7uH`) or the short part name for ICs; resistance below 1k as `10R`, `49.9R`, from 1k as `1k`; other ohm values as `22mOhm`; manufacturer short name as on the datasheet cover.
- MUST NOT: add price/stock parameters or remove existing ones; keep an old-name duplicate of a standard parameter (`Manufacturer_Name`, `MP`, `Datasheet Link`, `Pins`, `Case/Package`...) once the standard one has its value: remove it and log the old value.
- Why: one fixed parameter list, decided with the user, keeps every library and BOM export identical; duplicates disagree sooner or later.
- Check: lib_params.py --check (names); checklist (change log per component: added, updated, removed, kept)
- Source: user 2026-11-03 (answers on the SpeakerSystemV1 parameter update: "do not kept duplicate", "follow the standard", "use 10R", "do not add like supplier 1 ... leave blank", "lets fixed the parameter rules ... until i asked to change it")
- Status: CHECKLIST

### LIB-32 Parameter values: datasheet wins, distributor numbers from the official APIs
- MUST: values from the datasheet: maker's PDF first, DigiKey second, LCSC third; Height = the datasheet's maximum seated height (nominal + tolerance); on a conflict with the library write the datasheet value only when confirmed on the page, else keep the old value and list it for the user.
- MUST: Mouser and DigiKey numbers and product links from the official APIs (Mouser Search API, DigiKey Product Information V4; Nexar optional) by exact MPN and manufacturer; list every packaging variation, store DigiKey Cut Tape (else the only listing), keep an existing link.
- MUST NOT: type API keys or secrets: they stay in the user's own key file (`%USERPROFILE%\.distributor_keys.json`) or environment variables.
- Why: distributor sites block scripts; the APIs give the real purchasing number and URL for the exact part.
- Check: distributor_lookup.py (all listings with exact-MPN and manufacturer flags); checklist
- Source: user 2026-11-03 ("datasheet first priority mfn second digikey third lcsc", "take height from datasheet", "where conflict keep data sheet", "as your script is blocked by digikey use their api", "add those partnumber and links as parameter")
- Status: CHECKLIST

### LIB-33 Footprint review document for human review
- MUST: one editable A4 Word document for the whole library, report only (never edit the footprint or symbol). Page 1: a short introduction; a note naming the library footprints that no symbol uses (skipped, no section); one outline table: # | footprint name linked to its section | components (MPN) | Result | Datasheet (local + online, or what is missing) | Reviewer 1 | Reviewer 2 | Decision (Edit / Keep). Reviewer cells are taken from the sign-off lines: OK when the reviewer wrote ok (note kept), Not OK when the comment says otherwise, blank when empty. Then one section per footprint: header with component(s), MPN, package, datasheet title and pages, a clickable local datasheet link and the maker's online link (DigiKey/Mouser link when the maker has none), tolerances and the overall result in bold.
- MUST: every section shows four pieces of evidence a person can check without opening another file: (1) Pins: each symbol drawn from the SchLib (captioned "name (MPN)", pin numbers, names, electrical-type arrows) beside a datasheet crop that validates it (pin assignment or pin table; for 2-terminal parts the terminal or polarity drawing); (2) Package: a datasheet crop that ties the exact MPN to the package (ordering table, part-number key or package code); (3) Land pattern: a datasheet crop with the footprint dimensions (recommended land pattern, or the package drawing when the maker gives no land pattern); (4) Footprint: the footprint drawn from the PcbLib data, never from live Altium, with every checked dimension marked (arrows centre to centre for pitch and row spacing, edge to edge for sizes and spans; label `<DS letter> <name> <footprint value> | DS <value>` coloured green Pass, red Fail, orange Check; labels never cover pads or each other), on the same page as crop 3. A piece the datasheet does not have is replaced by a highlighted "not in the datasheet" box and the part is listed in the Datasheet column. Crops are real page images (150 dpi or more), cropped tight, captioned "Datasheet p.<n>: <what>", readable on A4. The section ends with the check table on its own page (Check | Datasheet | Footprint | Diff | Tol | Result) and two sign-off lines "Reviewer 1 / Reviewer 2: name, date, OK / Not OK, comment" (LIB-29).
- MUST: differences computed in code; tolerance ±0.01 mm on every dimension (a datasheet min to max range passes inside the range); courtyard and paste/mask are Check until their rules are decided. Missing datasheets: maker first, then DigiKey, Mouser and LCSC (API links), then ask the user with component name, MPN and maker.
- Why: the reviewer signs what the pages show; the four pieces of evidence let a person check each symbol and footprint against the datasheet page by page (SpeakerSystemV1 review, 2026-11-03/04).
- Check: checklist (render the .docx to PDF; count the four pieces of evidence in every section before sending)
- Source: user 2026-11-03 ("this format is final document this format in rules how human review doc will prepared"; "most important keep all tollerence0.01 mm"; "for symble add mfn part number in the doc in bracket"; "make the editable document in A4"); 2026-11-04 (outline with links and reviewer columns; note on unused footprints; "for every symble screnshot of library i add a screenshot from datasheet which balidate this symbel ... a screenshot from datasheet which validate the package ... screenshot from datasheet which have the foopprint dimention and add the footprint screenshot with proper dimention marked ... update your rules about review document creation")
- Status: CHECKLIST

### LIB-34 One parameter set per category: no duplicates, no blank extras
- MUST: give every component of a category (Type/Subtype) the same parameter set: the stored common parameters, the three Price/Stock links, and all Required and Optional electrical parameters of its subtype; a parameter whose value is unknown stays present and empty.
- MUST: remove every component-level parameter that is not in that set, blank or valued (old Altium content, SnapEDA and database leftovers such as `Value`, `Schedule B`, `Lifecycle Status`, `Length`), and log its old value; where it duplicates a standard parameter that is empty, move its value into the standard one first; keep only one parameter per name; when `Value` goes, `Comment` becomes the visible value text in its place and font.
- MUST NOT: touch parameters owned by a model or implementation (`OwnerIndex` set, e.g. SIM fields, `altium.hash`) or the price/stock parameters of LIB-31 (`Arrow Part Number`, `Arrow Price/Stock`, `Price`, `Check_prices`).
- Why: parts of one category compare and export the same way; duplicates disagree sooner or later and blank extras are noise once the full set is there.
- Check: lib_params.py --check (every category's parameter names identical, no duplicates or extras); checklist (change log per component)
- Source: user 2026-11-03 ("remove the duplicate keep the authentic", "whats the point of those duplicate and blank parameter", "in each category components should have same parameters", "go ahead and do this make all consistent")
- Status: CHECKLIST

## Batch library build (approved 2026-11-05, Library_Management_Work_Proposal v1.2)

### LIB-35 Footprint names follow IPC-7351B
- MUST: name every footprint of an IPC family by IPC-7351B, as the Altium IPC Footprint Wizard does: `RESC1005X40N` (chip resistor, body 1.0 x 0.5 mm = 0402, height 0.40 mm, Nominal), `CAPC1608X90N`, `SOIC127P600X175-8N`, `QFN50P400X400X100-25N`. Density N by default, M or L only where the board needs it, and the letter stays in the name. Parts without an IPC family are named `<Manufacturer>_<Series or MPN>` (`JST_B2B-XH-A`, `Molex_526101471`). Footprints taken from Celestial or a maker are renamed to these names.
- MUST NOT: name a footprint by imperial size only (`RESC1608_0603`) or by a maker's drawing code.
- Why: one standard name per land lets every library and every engineer read the package and the density from the name.
- Check: catalog_check.py (planned name pattern); checklist
- Source: user 2026-11-05 ("update kits rule to follow the standard")
- Status: CHECKLIST

### LIB-36 One generic land and courtyard per package
- MUST: give all parts with the same standard package one generic IPC-7351B land and one 3D body, sized for the tallest and largest body that uses it; chip resistors and chip capacitors of one size follow the same land rule (pad size, toe, gap, courtyard line width). Courtyard = outermost of pads and body (assembly outline and 3D body) plus 0.25 mm (0.15 mm for chips smaller than 0603, 0.5 mm for connectors), each edge rounded outward to a 0.05 mm grid. Silkscreen 0.15 mm, kept off the pads. A part-specific footprint only where the datasheet land cannot be met by the generic one.
- Why: eight different 0402 lands for one body made boards inconsistent; a 0402 resistor built by another generator than the 0402 capacitor showed at once in 3D.
- Check: checklist (3D view of every footprint of one size side by side); validate_library
- Source: user 2026-11-04/05 (SpeakerSystemV1 batch 1 review)
- Status: CHECKLIST

### LIB-37 One best-looking symbol per kind of discrete
- MUST: give every kind of discrete part one symbol (Resistor, Capacitor, Capacitor Polarised, Inductor, Ferrite Bead, Diode, Diode Zener, Diode TVS Unidirectional, BJT NPN, MOSFET N-Channel, MOSFET P-Channel, Crystal 4-Pad, Test Point) and record its name in the component's Symbol parameter. Choose the drawing from the best-looking symbol found among the makers' and Altium content-vault symbols, not a plain generic one; renumber its pins to the datasheet (diode pin 1 = cathode). Parts with their own pinout (ICs, connectors, modules) keep one symbol each.
- Why: the user wants one clean, recognisable look across the schematic, with the same drawing for the same kind.
- Check: render the symbols of each kind side by side; pin_match.py
- Source: user 2026-11-05 ("pick the gorgeous symbol where found for the discrete component, not the generic")
- Status: CHECKLIST

### LIB-38 Library ready for the Workspace before upload
- MUST: before the Altium 365 Library Importer runs, pass `ws_lib_check.py` (Component Type without / \ : * ? " < > |, Category exactly Type/Subtype ending in the Component Type, Symbol parameter set, descriptions at most 256 characters), `pin_match.py` (all PASS) and `validate_library` on the PcbLib (0 errors). A name in the category tree never contains "/": use "&" (FFC & FPC). Follow playbook P13.
- Why: the importer stopped on "FFC / FPC" with "Invalid tag HRID"; it refuses long descriptions without naming the part.
- Check: ws_lib_check.py; pin_match.py; validate_library
- Source: user 2026-11-05 (SpeakerSystemV1 batch 1 upload; "update our workflow rules ... so we could do this type of work more efficiently")
- Status: CHECKLIST

## Parameter tables (part of LIB-23)

The tables are kept in one place, `rules/library_parameters.json` (28 common parameters, the three Price/Stock links and the
required and optional electrical parameters of all 89 subtypes). Read the set of one category with
`kit lib_params "<Type>/<Subtype>"` (a few lines), check a SchLib against it with `kit lib_params --check <lib.SchLib>`,
and see the full tables for people in `docs/LIBRARY_PARAMETERS.md` (generated; selftest fails when it is stale).
Names exactly as written, without the hint in brackets (LIB-31); values in the format below; unknown = empty.

#### Value format

| Rule | Write | Never |
|---|---|---|
| SI prefix, no space, unit symbol | `10k`, `100nF`, `4.7``u``H`, `50V` | `10 K`, `0.1uF `, `100 nano` |
| u for micro, ASCII only | `4.7``u``F` | `4.7``µF, 4.7``mfd` |
| Decimal point, no trailing zeros | `2.2``u``F` | `2,2``u``F`, `2.20``u``F` |
| Ranges with "to" | `-40°C to 85°C`, `2.7V to 5.5V` | `-40~85` |
| Tolerance as ± percent | `1%` | `F`, `±1 %` |
| Resistance below 1k with R, from 1k with k | `10R`, `49.9R`, `1k`, `4.7k` | `10`, `10Ω`, `1000R` |
| Ohm in other values as Ohm | `22mOhm`, `50Ohm` | `22mΩ`, `22m` |
| One value per parameter | `Channels` = `2` | `2 (dual)` |
| Unknown = empty | *(blank)* | `N/A`, `-`, `TBD` |
