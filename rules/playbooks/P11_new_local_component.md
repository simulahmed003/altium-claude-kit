# P11 New component in a project's local library (first version; user's detailed instructions pending)

Read with: 03_LIBRARY (LIB-10..18), 02_REQUIREMENTS_CALCS_PARTS (RQ-01, RQ-09). Skill: `altium-local-library`.
PLACEHOLDER: the user will send detailed local library instructions; steps marked (pending) change then.

| # | Step | Status |
|---|---|---|
| 1 | Part record first: `python tools\scripts\parts.py find <MPN>`; missing: P2 steps 2-3 (datasheet, extraction, `parts.py check` PASS). | TESTED (Extention_01: S8550, DMG2301L-7, 1N4148W, M20-9960345) |
| 2 | Distributor numbers: LCSC (`parts.py lcsc <MPN>`), Mouser and DigiKey from their product pages, into the record's `suppliers[]`; a number not confirmed on its page is UNCONFIRMED (RQ-09). | TESTED by hand (Extention_01) |
| 3 | Find the symbol, footprint and 3D model in the database library (kit global library, or the user's DbLib) (pending: source order). Copy them into the local library; build only what is missing (LIB-11..13). | TESTED (Extention_01, from the Celestial DbLib) |
| 4 | Name the component exactly by its MPN; fill Comment, Description, Manufacturer, MPN, LCSC, Mouser, DigiKey, Datasheet and key ratings, hidden except Comment (LIB-14). | TESTED (Extention_01, 8 components) |
| 5 | Check against the datasheet (LIB-18): pin map, pads (pitch, size, holes), pin 1, package; `python tools\scripts\pin_match.py <SchLib> <PcbLib> --style`. Report every mismatch with the datasheet value. | TESTED (Extention_01) |
| 6 | Point the schematic part at the local component (Update from Libraries), then `conn_check.py`. | TESTED (Extention_01) |
| 7 | (pending) Flow back to the database / global library: `lib_promote.py` after G1 (LIB-06). | UNTESTED |
