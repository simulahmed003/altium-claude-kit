# library - managed global component library and database

There is one global library, and each project works on local copies of it. Python scripts manage the catalog, the hashes
and the copy plans. Only altium-lib writes .SchLib / .PcbLib files.

Shared symbols, footprints and 3D models built from the component database: see `docs/LIBRARY_PLAN.md` (plan, rules LIB-09 to LIB-15 PROPOSED).

## Layout

| Folder | Holds | Written by |
|---|---|---|
| `catalog/components.json` | single source of truth: every component and footprint (fields below) | lib_promote.py, cad_register.py |
| `catalog/components.md` | generated table, do not edit | libcat.py |
| `catalog/CHANGELOG.md` | one line per promotion or revision | lib_promote.py |
| `catalog/migrations/` | input files for promotions (statuses, caveats) | designer |
| `catalog/promote_plan.json` | altium-lib copies still to run for the last promotion | lib_promote.py |
| `symbols/<category>.SchLib` | schematic symbols, one library per category | altium-lib |
| `footprints/<category>.PcbLib` | footprints, one library per category | altium-lib |
| `models/step/`, `models/index.json` | 3D models (STEP) with sha256 and placement offsets | cad_register.py |
| `models/spice/` | simulation models (planned, roadmap M4) | - |
| `specs/` | gen_sym.py specs for generic symbols (generic passives) | designer |
| `parts/` | component database: one record per orderable part, datasheet facts with page + quote (see `parts/README.md`) | parts.py + extractor + review |
| `datasheets/index.json` | every datasheet by sha256: file, url, pages, covered MPNs (the PDFs themselves stay out of git) | parts.py |
| `datasheets/` | local cache of the PDFs the catalog points to (not in git, sha256 in the catalog) | datasheets_fetch.py |

## Categories

Each category has one SchLib and one PcbLib with the same name. The `category` field must match the file name
(catalog_check.py enforces this).

| Category | Holds | Designator prefix of the IDs |
|---|---|---|
| `passives` | resistors, capacitors, inductors, ferrites | R_, C_, L_, FB_ |
| `discretes` | diodes, MOSFETs, BJTs, LEDs | D_, Q_, LED_ |
| `ics` | regulators, MCUs, interface, analog, logic | U_ |
| `connectors` | connectors, terminals, test pads | J_, TP_ |

A new category comes in only when one of these four has outgrown a single file, for example when `ics` is split into
`power`, `mcu` and `interface`. It needs a catalog migration and its own pull request.

## Naming

| Item | Pattern | Examples |
|---|---|---|
| Component ID (symbol name) | `<prefix>_<value or MPN>_<key rating>_<package>` | `R_10k_1%_0603`, `C_10u_50V_X7R_1206`, `U_LMR33630ADDA` |
| Footprint, IPC-7351 chip parts | `<type><metric size>_<imperial size>` | `RESC1608_0603`, `CAPC3216_1206` |
| Footprint, IC or other package | `<package>_<drawing code>`, or `<part>_<package>_<code>` when the land is part-specific | `SOIC8_MS012`, `LMR33630_HSOIC8_DDA` |
| Footprint, connector | `<type>_<series>-<pins>-<pitch>` | `TB_MKDS1.5-2-5.08` |
| 3D model file | `<footprint name>.step` | `RESC1608_0603.step` |
| Datasheet cache file | `<MPN>_<LCSC>.pdf` | `1715721_C480516.pdf` |

## Principles

| | Rule |
|---|---|
| a | Projects open only their local copies in `projects/<p>/libs/`. Never open a global library in a design. |
| b | Run lib_promote.py only after the project's G1 is ticked. |
| c | Every item has a rev. A content change means rev + 1 and a CHANGELOG line. Old revs stay in "history". |
| d | Each project has `libs/lib_manifest.json`, with the rev and content hash of every local part. |
| e | components.json is the single source of truth. Component fields: id, category, symbol, global_lib, rev, symbol_hash, footprint, value, description, mfr, mpn, lcsc, lcsc_verified, jlc_tier, datasheet {path, sha256, url}, preferred, caveats, source_project, promoted {date, gate, rules_version}, history. Footprint fields: name, category, global_lib, rev, footprint_hash, status (datasheet-verified / derived / unverified-accepted), status_source, caveats, courtyard_mm, step, source_project, history. |
| f | Drift means the normalized content hash differs (altium_io.symbol_hash / footprint_hash, which drop the identity and path fields). lib_status.py reports it. |
| g | Copy footprints with `preserve_external_paths=true` so 3D links survive (LESSONS T26). |

Generic passives (R_GENERIC_0603, C_GENERIC_0603, C_GENERIC_1206) are specs in `specs/`. Preferred parts are catalog
entries with `preferred = true` (verified Basic parts and the TP pad).

## Scripts (`tools/scripts/`)

| Script | Use |
|---|---|
| `lib_promote.py <project> [--info file]` | Moves project parts into the catalog after G1 and writes promote_plan.json. `--plan` rebuilds the plan alone. `--verify` checks the global files. |
| `lib_pull.py <project> <id ...>` | Plans copies into the project. Run `--verify` after the copies. |
| `lib_update.py <project>` | Plans updates for parts with a newer global rev. Refuses parts changed locally. |
| `lib_status.py <project>` | Reports OK / UPDATE / LOCAL CHANGED / MISSING / LOCAL ONLY for each part. |
| `catalog_check.py [--project p] [--strict]` | Checks catalog fields, the category/file match, datasheet sha256, footprint status, global file hashes, and pending plan items. |
| `datasheets_fetch.py` | Downloads the catalog's PDFs into `datasheets/` and keeps only files whose hash matches. |
| `cad_register.py` / `cad_check.py` | Manages the 3D model store (structure only). |

## Moving an existing install to this layout (2026-10-17)

Folders were renamed: `_global/libs/*.SchLib` became `library/symbols/`, `*.PcbLib` became `library/footprints/`, `libs/specs/`
became `library/specs/`, and `cad/` became `library/models/`. Content hashes and revs did not change.
After `git pull`:
1. Run `tools/setup.ps1` again.
2. In `%USERPROFILE%\.altium-designer-mcp\config.json`, change the `allowed_paths` entry from `.../_global` to `.../library`.
3. Re-copy your downloaded datasheets from `_global/datasheets/` to `library/datasheets/`, or run `datasheets_fetch.py`.

## State on 2026-10-13
- First migration from buck-12v-5v-3a: 16 components and 8 footprints, all at rev 1. Caveats are in `catalog/migrations/buck_2026-10-13.json`.
- On 2026-10-13 altium-lib wrote the category library files (24 copies, `preserve_external_paths=true`) from the promote plan. `lib_promote.py --verify` passed, `catalog_check --strict` found 0 problems, and buck lib_status reported 24 OK.
