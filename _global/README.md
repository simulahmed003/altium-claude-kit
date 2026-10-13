# _global - managed global library

One global library, local copies per project. Python scripts manage the catalog, hashes and plans;
only altium-lib writes .SchLib / .PcbLib files.

| Folder | Holds |
|---|---|
| catalog\components.json | single source of truth: every component and footprint (fields below) |
| catalog\components.md | generated table (do not edit) |
| catalog\CHANGELOG.md | one line per promotion / revision |
| catalog\migrations\ | input files for promotions (statuses, caveats) |
| catalog\promote_plan.json | altium-lib copies still to run for the last promotion |
| libs\<category>.SchLib / .PcbLib | category libraries: passives, ics, discretes, connectors (written by altium-lib) |
| libs\specs\ | gen_sym.py specs (generic passives) |
| datasheets\ | PDFs used by catalog parts, sha256 in the catalog |
| cad\step\, cad\index.json | 3D models (cad_register.py, cad_check.py) |

## Principles
| | Rule |
|---|---|
| a | Projects open only their local copies in projects\<p>\libs\. Never open a global library in a design. |
| b | lib_promote.py only after the project's G1 is ticked. |
| c | Every item has a rev; a content change = rev + 1 + CHANGELOG line. Old revs stay in "history". |
| d | Each project has libs\lib_manifest.json: rev and content hash of every local part. |
| e | components.json is the single source of truth: id, category, symbol, global_lib, rev, symbol_hash, footprint, value, description, mfr, mpn, lcsc, lcsc_verified, jlc_tier, datasheet {path, sha256}, preferred, caveats, source_project, promoted {date, gate, rules_version}, history; footprints: name, category, global_lib, rev, footprint_hash, status (datasheet-verified / derived / unverified-accepted), status_source, caveats, courtyard_mm, step, source_project, history. |
| f | Drift = normalized content hash (altium_io.symbol_hash / footprint_hash: identity and path fields dropped) differs. lib_status.py reports it. |

Generic passives (R_GENERIC_0603, C_GENERIC_0603, C_GENERIC_1206) are specs in libs\specs\; preferred
parts are catalog entries with preferred = true (verified Basic parts and the TP pad).

## Scripts (_tools\scripts)
| Script | Use |
|---|---|
| lib_promote.py <project> [--info file] | project parts -> catalog (after G1); writes promote_plan.json (always derived from catalog vs libs; `- --plan` rebuilds it alone); `--verify` checks the global files |
| lib_pull.py <project> <id ...> | plan copies into the project; `--verify` after the copies |
| lib_update.py <project> | plan updates for parts with a newer global rev (refuses locally changed parts) |
| lib_status.py <project> | OK / UPDATE / LOCAL CHANGED / MISSING / LOCAL ONLY per part |
| catalog_check.py [--project p] [--strict] | catalog fields, datasheet sha256, footprint status, global file hashes, pending items missing from promote_plan.json |
| cad_register.py / cad_check.py | 3D model store, structure only |

## State on 2026-10-13
- First migration from buck-12v-5v-3a: 16 components, 8 footprints, rev 1, caveats in catalog\migrations\buck_2026-10-13.json.
- Category library files written 2026-10-13 by altium-lib (24 copies, preserve_external_paths=true) from
  catalog\promote_plan.json; `lib_promote.py --verify` PASS, catalog_check --strict 0 problems, buck lib_status 24 OK.
  promote_plan.json is now empty because nothing is pending.
- The altium-lib round trip was tested (D:\EDA\_tools\libraries\_rt\): symbols and footprints copied with
  preserve_external_paths=true have identical content hashes.
