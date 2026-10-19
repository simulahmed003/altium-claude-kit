# library - managed global component library and database

There is one global library, and each project works on local copies of it. Python scripts manage the catalog, the hashes
and the copy plans. Only altium-lib writes .SchLib / .PcbLib files.

Shared symbols, footprints and 3D models built from the component database: see `docs/LIBRARY_PLAN.md` (plan) and rules LIB-09 to LIB-16 in `rules/03_LIBRARY.md`.

Every symbol family has a `symbols/<category>/<family>.README.md`, every footprint package type a `footprints/<type>.README.md`, and every 3D model folder a `models/step/<type>/README.md`. Each one says what belongs there, the naming, the drawing or land standard, how to add an item, and who maintains it. `tools/scripts/lib_readmes.py` creates missing READMEs and refreshes only their Contents block, so text people add stays.

## Layout

| Folder | Holds | Written by |
|---|---|---|
| `catalog/components.json` | single source of truth: every component and footprint (fields below) | lib_promote.py, cad_register.py |
| `catalog/components.md` | generated table, do not edit | libcat.py |
| `catalog/CHANGELOG.md` | one line per promotion or revision | lib_promote.py |
| `catalog/migrations/` | input files for promotions (statuses, caveats) | designer |
| `catalog/promote_plan.json` | altium-lib copies still to run for the last promotion | lib_promote.py |
| `symbols/<category>/<family>.SchLib` | schematic symbols: one folder per category, one library per family | altium-lib |
| `footprints/<package type>.PcbLib` | footprints sorted by package type (`chip`, `soic`, `sot`, `qfn_dfn` ...): each footprint exists once | altium-lib |
| `models/step/<package type>/` | 3D models (STEP), one per footprint body, same package types as `footprints/` | cad_fetch.py, cad_register.py, people |
| `models/index.json` | every 3D model: footprint, source, sha256, placement offset and rotation | cad_register.py |
| `models/spice/` | simulation models (planned, roadmap M4) | - |
| `specs/` | gen_sym.py specs for generic symbols (generic passives) | designer |
| `parts/` | component database: one record per orderable part, datasheet facts with page + quote (see `parts/README.md`) | parts.py + extractor + review |
| `datasheets/index.json` | every datasheet by sha256: file, url, pages, covered MPNs (the PDFs themselves stay out of git) | parts.py |
| `datasheets/` | local cache of the PDFs the catalog points to (not in git, sha256 in the catalog) | datasheets_fetch.py |

## Categories, families and package types (user decision 2026-10-19)

Symbols: one folder per category, one library file per family. Category and family are the same as in the component
database (`parts/taxonomy.json`), and the catalog takes them from the part's database record (by MPN). A part with no
record uses the prefix default in `libcat.DEFAULT_FAMILY` (R, C, L, FB, TP, LED) or `"family"` in `lib_promote.py --info`.

| Category folder | Family files today |
|---|---|
| `symbols/passives/` | `resistor`, `capacitor_mlcc`, `inductor_power` |
| `symbols/discretes/` | `mosfet` |
| `symbols/ics/` | `power_buck` |
| `symbols/connectors/` | `terminal_block`, `test_point` |

A new family file appears when the first part of that family is promoted; the folder tree follows the taxonomy.

Footprints: sorted by package type, because one package serves many families (SOIC-8: MOSFETs and ICs; 0603: resistors,
capacitors, LEDs). The type comes from the footprint name (`libcat.PACKAGE_TYPES`) or `"package_type"` in `--info`.

| File | Holds today |
|---|---|
| `footprints/chip.PcbLib` | `RESC1608_0603`, `CAPC1608_0603`, `CAPC3216_1206` |
| `footprints/soic.PcbLib` | `SOIC8_MS012`, `LMR33630_HSOIC8_DDA` |
| `footprints/inductor_smd.PcbLib` | `IND_CDRH10D60` |
| `footprints/terminal_block.PcbLib` | `TB_MKDS1.5-2-5.08` |
| `footprints/test_point.PcbLib` | `TP_PAD_D1.5` |

3D models belong to the footprint, so every component on the same footprint shares one model: a 10 uF and a 22 uF 0603
capacitor use the same `CAPC1608_0603` body.

Projects (local copies): `projects/<p>/libs/<category>/<family>.SchLib` and `.PcbLib`, footprints per family
(`lib_pull.py` plans the copies there). Older projects with one flat `<p>.SchLib` / `.PcbLib` still work; the scripts
read every library under `libs/` except `_dryrun`.

## Naming

| Item | Pattern | Examples |
|---|---|---|
| Component ID (one per MPN, LIB-14) | by value (passives, connectors): `<prefix>_<value>_<key rating>_<package>_<MPN>`; by part number (ICs, discretes): `<prefix>_<MPN>`; parts with no MPN keep a plain name | `R_10k_1%_0603_0603WAF1002T5E`, `J_MKDS1.5-2-5.08_1715721`, `U_LMR33630ADDAR`, `Q_AO4407C`, `C_DNP_0603`, `TP_PAD`. Renamed parts keep their old ID in `former_ids`, so older projects still find them |
| Shared symbol (LIB-10) | `<KIND>` two-pin passives, `<KIND>_<n>P_<pin names>` discretes, `<base part>_<package code>` ICs | `RES`, `CAP`, `PMOS_8P_SSSGDDDD`, `LMR33630_DDA` |
| Footprint, IPC-7351 chip parts | `<type><metric size>_<imperial size>` | `RESC1608_0603`, `CAPC3216_1206` |
| Footprint, IC or other package | `<package>_<drawing code>`, or `<part>_<package>_<code>` when the land is part-specific | `SOIC8_MS012`, `LMR33630_HSOIC8_DDA` |
| Footprint, connector | `<type>_<series>-<pins>-<pitch>` | `TB_MKDS1.5-2-5.08` |
| 3D model file | `models/step/<package type>/<footprint name>.step` | `models/step/chip/RESC1608_0603.step` |
| Datasheet cache file | `<MPN>_<LCSC>.pdf` | `1715721_C480516.pdf` |

## Working on the library: people and Claude

| Who | Does |
|---|---|
| A person (the user, or a maintainer named in a README) | adds or improves symbols, footprints and 3D models by hand in Altium, keeps the standard in the README, writes decisions under "Notes and decisions" |
| Claude | builds missing items from the component database (LIB-09 to LIB-13), keeps the catalog and READMEs current, and after a hand edit runs `catalog_check.py` and `lib_status.py`, reports what changed and asks before adapting catalog entries, hashes or project copies (LIB-16) |

The global library grows from projects: a part new to a project is built in the project's local library
(`projects/<p>/libs/<category>/<family>.SchLib` / `.PcbLib`), checked at G1, then promoted with `lib_promote.py`.
New footprints go to `footprints/<package type>.PcbLib`, new symbols to their family file, new 3D models to
`models/step/<package type>/`. Run `python tools/scripts/lib_readmes.py` after a promotion.

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
| `cad_fetch.py` | Downloads a part's 3D model from JLC/EasyEDA by LCSC number and files it (LIB-13). |
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
- 2026-10-19: the 4 category files were split into family symbol libraries and package-type footprint libraries
  (24 altium-lib copies, `lib_promote.py --verify` PASS, `catalog_check --strict` 0 problems).
- On 2026-10-13 altium-lib wrote the category library files (24 copies, `preserve_external_paths=true`) from the promote plan. `lib_promote.py --verify` passed, `catalog_check --strict` found 0 problems, and buck lib_status reported 24 OK.
