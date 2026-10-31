# P12 Rebuild the kit library to the library rules

Read with: 03_LIBRARY (LIB-05, LIB-06, LIB-10..19), 02_REQUIREMENTS_CALCS_PARTS (RQ-01, RQ-09).
Runs on the user's PC (needs the user's DbLib and altium-lib); Altium must not have the global libraries open (LIB-04).

| # | Step | Status |
|---|---|---|
| 1 | `kit lib_audit --md library\catalog\AUDIT.md`: the list of components to rebuild and why. | TESTED (cloud, 2026-10-31: 16 of 16 to rebuild) |
| 2 | Per part record: add Mouser and DigiKey numbers (RQ-09), datasheet URL from the maker; `kit parts check <MPN>`. | UNTESTED |
| 3 | Per component, P11 steps 4-8: find the same MPN (or the same shape) in the DbLib, copy it, make it consistent (LIB-17: name = MPN, style, parameters), keep the footprint geometry unless the datasheet check finds a mismatch; record the source. Old name goes to `former_ids` in the catalog so projects that use it still resolve. | UNTESTED |
| 4 | Footprints still `derived` or `unverified-accepted` (LIB-05): compare with the datasheet land, or with the DbLib footprint for the same package; upgrade the status with its source, or keep it and say why. Missing 3D models: `kit cad_fetch <part>` (LIB-13). | UNTESTED |
| 5 | Datasheet check per component (LIB-18), then `kit lib_audit mark <id> --status checked --by Claude --note <pages>`. | UNTESTED |
| 6 | Write the global libraries through `lib_promote.py - --adopt <id> --by <name>` (new revision, LIB-16), `kit pin_match <SchLib> <PcbLib> --style`, `kit catalog_check`, `kit lib_readmes`, `kit selftest`. | UNTESTED |
| 7 | The user reviews the table and marks each component confirmed (`kit lib_audit mark <id> --status confirmed --by <name>`). Commit as one pull request; projects that use old names update with `lib_update.py`. | UNTESTED |
