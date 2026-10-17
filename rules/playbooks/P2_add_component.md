# P2 Add a component

Read with: 03_LIBRARY, 02_REQUIREMENTS_CALCS_PARTS.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Look in the catalog first: `library\catalog\components.md`. If found, `lib_pull.py` it; stop here. | TESTED (selftest) |
| 2 | Component database: `parts.py find <mpn or C-number>`. Not there: `parts.py new --lcsc C123`, then `parts.py fetch <mpn> --url <maker PDF> --project projects\<name>` (maker first, LCSC second; never committed). Record path + sha256 in the catalog entry at promotion (catalog_check.py checks it). | TESTED (17 buck parts with fetch --file; TI maker download on a scratch project 2026-10-17) |
| 2a | Extract: `parts.py locate`, `parts.py text --mode raw/table`, write facts, pins and notes with page + quote (visual: true when the text layer lacks a value); `parts.py check` PASS. Before G1 a person checks pins, abs max, package, visual values: `parts.py verify --by <name> --items ...`. | TESTED (17 buck parts extracted 2026-10-17); verify UNTESTED |
| 3 | Write a symbol spec (ai\sym_spec.json); run `python tools\scripts\gen_sym.py ai\sym_spec.json libs\_dryrun\sym.json`: pin ends on the 100 mil grid. | TESTED (buck spec reproduces the library 16/16) |
| 4 | Footprint from the datasheet land pattern (mm): altium-lib write_pcblib into libs\_dryrun\ first, then the real libs\ file (library closed in Altium). | TESTED (buck G1) |
| 5 | altium-lib validate_library 0 errors 0 warnings; `pin_match.py libs\x.SchLib libs\x.PcbLib --style` all PASS. | TESTED (buck) |
| 6 | Record the footprint status (datasheet-verified / derived / unverified-accepted) for G1 (LIB-05). | TESTED (buck G1 list) |
| 7 | After G1: `lib_promote.py` to the global library. | TESTED (buck migration 2026-10-13: 24 altium-lib copies from promote_plan.json, then `--verify` PASS, catalog_check --strict 0 problems) |

7 of 8 steps TESTED (step 2a verify part untested).
