# P11 New part in the project's local library (workflow, first version 2026-10-31)

Read with: 03_LIBRARY (LIB-04, LIB-09..18), 02_REQUIREMENTS_CALCS_PARTS (RQ-01, RQ-03, RQ-08, RQ-09).
Skill: `altium-local-library`. Commands are for cmd.exe from the workspace folder (`kit <tool>` works too).
PLACEHOLDER marks the points the user's detailed local-library instructions will settle.

When: the user asks for a part that the project's local library does not have yet, or a schematic needs one.
Result: one local component per MPN, named by the MPN, with symbol, footprint and 3D model checked against the
datasheet, and every parameter (including LCSC, Mouser and DigiKey) taken from the part's database record.

## The user approves (the agent stops and asks)
- the part itself, when the request gives only a function or value (step 1)
- any footprint or symbol that differs from the datasheet, e.g. hole 1.10 mm vs maker's 1.02 mm (step 7)
- a 3D model taken from a similar part (a substitute, LIB-13) (step 6)
- any alternate MPN or LCSC part (RQ-08), and any change to the global library or the DbLib (step 11)

## Workflow

| # | Step | How | Done when | Status |
|---|---|---|---|---|
| 1 | Pin down the part | The MPN, or the LCSC number. Only a function or value was given: propose 1-3 candidates (rating, package, stock, Basic/Extended, price) and wait for the choice. | one MPN agreed | TESTED (Extention_01: S8550, 0.22 uF X7R, 3-pin header) |
| 2 | Part record and datasheet | `kit parts find <MPN>`; missing: `kit parts new --lcsc <C>` or `--mpn --mfr --category`, `kit parts fetch <MPN> --project <folder>` (maker's site first, LCSC second), extract pins, abs max, package and land with page and quote, `kit parts check <MPN>` PASS (RQ-01). | record PASS | TESTED (4 parts, 2026-10-30) |
| 3 | Distributor numbers | LCSC: `kit parts lcsc <MPN> --add <MPN>`. Mouser and DigiKey: from their product pages, written into the record's `suppliers[]` with the date; a page that cannot be opened: UNCONFIRMED (RQ-09). | 3 numbers or UNCONFIRMED | TESTED by hand |
| 4 | Look for existing items | In this order (LIB-17): the project's local library, the user's Altium DbLib (primary source, read-only: never change it), the kit global library (`library\symbols\<category>\<family>.SchLib`, `library\footprints\<package type>.PcbLib`, `library\models\step\`). Note what exists for symbol, footprint and 3D model (LIB-09, LIB-10). | each item: found where, or missing | TESTED (Celestial DbLib, 2026-10-30) |
| 5 | Symbol | Found with the same pin list: copy it and make it consistent (LIB-17: style, visible text, grid, pin length, parameters); record the source with `kit lib_audit source <id> --from dblib --ref <item>`. Missing: build from the record's pins with `kit gen_sym` under LIB-02, LIB-03, LIB-11 (IC: datasheet grouping, power top, ground bottom, 200 mil pins). A symbol of a similar part (S8050 for S8550) is only a starting point: every pin re-checked in step 7. | symbol in `libs\_dryrun\` | TESTED (copy); gen_sym TESTED on buck |
| 6 | Footprint and 3D model | Footprint found: copy it unchanged (geometry changes only after a step 7 mismatch and the user's decision). Missing: build from the record's land facts (LIB-12). 3D model: the shared model for the body, else `kit cad_fetch <part>` (JLC by LCSC number), else the maker's site; a similar part's model only as a marked substitute with the user's yes (LIB-13). | footprint + model in `libs\_dryrun\` | TESTED (copy, Extention_01); cad_fetch TESTED (C25804) |
| 7 | Datasheet check (the agent's own, every time: LIB-18) | Table per part: pin number to name (symbol) vs datasheet pin table; pad pitch, pad size, hole size, pin-1 position, body and courtyard vs datasheet drawing; polarity mark. Every mismatch: the datasheet value, the library value, a recommendation, and the user decides. | table written, mismatches decided | TESTED (S8550, DMG2301L-7, M20-9960345, 1N4148W) |
| 8 | Build the local component | Name = the MPN exactly (LIB-14). Parameters from the record: Comment (value, or MPN for an IC), Description ("R 10k 1% 0603"), Manufacturer, MPN, LCSC, Mouser, DigiKey, Datasheet URL, key ratings; all hidden except Comment. Close the library in Altium, dry-run, keep the .bak, validate 0/0, write (LIB-04). PLACEHOLDER: file layout (one `<project>.SchLib/.PcbLib`, as on Extention_01, or `libs\<category>\<family>` as LIB-15) and parameter names/order. | `kit pin_match <SchLib> <PcbLib> --style` PASS | TESTED (8 components, Extention_01) |
| 9 | Use it in the design | Place it, or re-link existing parts (Update from Libraries); then `kit conn_check <sheet> ai\plan.json`. | conn_check PASS | TESTED (Extention_01) |
| 10 | Report | Mark the component `checked` (`kit lib_audit mark <id> --status checked --by Claude --note <pages>`); the user marks `confirmed` (LIB-19). Short report: what was added, where each item came from (copied from / built), the step 7 table, numbers marked UNCONFIRMED, open decisions. Before G1 the user checks pins, abs max and package in the PDF (`kit parts_verify`). | user has the table | TESTED |
| 11 | Back to the database library | After G1 only: `kit lib_promote <project>` for the kit global library (LIB-06). Never into the user's DbLib: it is read-only for the kit (LIB-17). | user's yes | UNTESTED |

## Stop and ask when
- no datasheet can be found, or it contradicts the distributor data or itself
- the only symbol or footprint available differs from the datasheet
- the part chosen in step 1 is out of stock or not recommended for new designs
