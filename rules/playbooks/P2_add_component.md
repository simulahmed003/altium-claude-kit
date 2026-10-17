# P2 Add a component

Read with: 03_LIBRARY, 02_REQUIREMENTS_CALCS_PARTS.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Look in the catalog first: `library\catalog\components.md`. If found, `lib_pull.py` it; stop here. | TESTED (selftest) |
| 2 | Get the datasheet PDF; record path + sha256 in the catalog entry (catalog_check.py checks it). | TESTED (buck datasheets; catalog_check selftest) |
| 3 | Write a symbol spec (ai\sym_spec.json); run `python tools\scripts\gen_sym.py ai\sym_spec.json libs\_dryrun\sym.json`: pin ends on the 100 mil grid. | TESTED (buck spec reproduces the library 16/16) |
| 4 | Footprint from the datasheet land pattern (mm): altium-lib write_pcblib into libs\_dryrun\ first, then the real libs\ file (library closed in Altium). | TESTED (buck G1) |
| 5 | altium-lib validate_library 0 errors 0 warnings; `pin_match.py libs\x.SchLib libs\x.PcbLib --style` all PASS. | TESTED (buck) |
| 6 | Record the footprint status (datasheet-verified / derived / unverified-accepted) for G1 (LIB-05). | TESTED (buck G1 list) |
| 7 | After G1: `lib_promote.py` to the global library. | TESTED (buck migration 2026-10-13: 24 altium-lib copies from promote_plan.json, then `--verify` PASS, catalog_check --strict 0 problems) |

6 of 7 steps TESTED.
