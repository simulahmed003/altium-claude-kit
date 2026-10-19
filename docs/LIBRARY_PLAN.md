# Library plan: shared symbols, footprints and 3D models built from the component database

Status: PLAN (2026-10-19). The rules it adds (LIB-09 to LIB-15) are PROPOSED until the user approves them.
Source: user brief 2026-10-19 (library management and local library structure).

## 1. The idea in one paragraph

A part (one orderable MPN) is a record in the component database (`library/parts/`). Its drawing items are shared:
many parts point to one schematic symbol, one footprint and one 3D model. For example, every 0603 resistor uses the
symbol `RES`, the footprint `RESC1608_0603` and the model `RESC1608_0603.step`. The global library stores each shared
item once: symbols in one file per family inside a folder per category, footprints and 3D models in one file or folder per package type. A project's local library is built from the database. Each part used gets one
component, made from the shared symbol and footprint, with the part's parameters (MPN, maker, LCSC, value, key
ratings, datasheet link) copied from its record.

## 2. Structure

```
library/
  parts/<category>/<family>/<MPN>__<maker>.json   facts (exists); new "package" and "land" keys, see 5
  symbols/<category>/<family>.SchLib              shared symbols only, one per shape (see 3)
  footprints/<package type>.PcbLib                shared footprints, one per package and land
  models/step/<package type>/<footprint>.step     shared 3D models, one per body
  models/index.json                               model: footprint, source, sha256, body box, substitute flag
  catalog/components.json                         binding: part -> symbol, footprint, model (+ pin map)
                                                  plus "symbols", "footprints" and "models" lists
projects/<p>/libs/<category>/<family>.SchLib     local library, built by lib_build.py (one component per MPN)
projects/<p>/libs/<category>/<family>.PcbLib     the footprints those components use (copied from the global package files)
projects/<p>/libs/lib_manifest.json              rev + hash of every item used
```

Folders and files (user, 2026-10-19):
- Global symbols: one folder per database category, one SchLib per database family, named as in
  `library/parts/taxonomy.json` (`symbols/passives/resistor.SchLib`, `symbols/discretes/mosfet.SchLib`).
- Global footprints and 3D models: by package type, because one package serves several families (SOIC-8 is used by
  MOSFETs and ICs, 0603 by resistors, capacitors and LEDs). Each footprint exists once. Package types (as built in PR #16):
  `chip` (chip resistors, capacitors, inductors), `soic`, `sot`, `qfn_dfn`, `to`, `inductor_smd`, `terminal_block`,
  `header`, `usb`, `crystal_osc` and `test_point`. A new type is
  added by pull request, like a new family.
- Local project library: the same category folders with one SchLib and one PcbLib per family
  (`projects/<p>/libs/passives/resistor.SchLib` and `resistor.PcbLib`). The PcbLib holds copies of the global
  footprints that family uses, so one project can carry the same SOIC-8 in two family files; lib_status.py checks every
  copy against the one global footprint.
- A file is created when its first part comes in. Today's four category files (`passives.SchLib`, `passives.PcbLib`
  and so on) are moved by `lib_migrate_shared.py` (tool 7); catalog_check.py then checks the folders and file names.

## 3. What is shared, and the key used to find it

| Item | Shared by | Lookup key | Name pattern | Example |
|---|---|---|---|---|
| Symbol | all parts with the same pin list (number, name, type) and symbol kind | family kind + pin signature | `<KIND>` for 2-pin passives, `<KIND>_<n>P_<pin names>` for discretes, `<base part>_<package code>` for ICs | `RES`, `CAP`, `IND`, `IND_4P`, `PMOS_8P_SSSGDDDD`, `LMR33630_DDA` |
| Footprint | all parts with the same package and land | package code + pin count + pitch + body box | existing (README Naming) | `RESC1608_0603`, `SOIC8_MS012` |
| 3D model | all footprints of the same body | footprint name (+ body box check) | `<footprint>.step` | `RESC1608_0603.step` |

The pin map between symbol pins and pads stays 1:1 (LIB-01). A shared symbol is only reused when the pin list matches
exactly. A part with the same pins in another order gets its own symbol.

## 4. Workflow for one part (from part selection to the local library)

| Step | Do | Tool |
|---|---|---|
| 0 | The part record exists and `parts.py check` passes (RQ-01). If not, run component intake first. | parts.py |
| 1 | Look up all three items in the catalog by their keys. Report have / missing per item. | lib_find.py (new) |
| 2 | **Symbol** missing: build it from the record's pins under the drawing standard (LIB-02, LIB-03, LIB-11). Dry-run, then `pin_match.py --style`. | gen_sym.py --from-part (extend) |
| 3 | **Footprint** missing: build it from the record's `land` facts. If they are missing, fetch the datasheet and extract them into the record first. If the datasheet has no land drawing, use the IPC-7351 land from the `package` facts and mark the footprint "derived". | fp_build.py (new) |
| 4 | **3D model** missing: download it from JLC/EasyEDA by the LCSC number. If that fails, get it from the maker's site, then from a similar part with the same body (marked substitute). Check the model's box against the record's body size. | cad_fetch.py (new), cad_register.py |
| 5 | Build the local library: one component per part, using the shared symbol and footprint and the parameters from the record (LIB-14). | lib_build.py (new) |
| 6 | G1: a person checks the new symbol, the footprint against the datasheet, and the 3D model in place (pin 1, height). | gate_check.py G1 |
| 7 | After G1: promote new shared items to the global library. | lib_promote.py |

## 5. Database additions needed to build footprints and check 3D models

The current records have the body length, width and height only for passives. That is not enough to draw a land.
New fact keys in the `package` section of `taxonomy.json` (page + quote like every fact):

| Key | Meaning |
|---|---|
| `package.drawing_code` | maker's drawing or JEDEC code (DDA0008B, MS-012) |
| `package.length`, `width`, `height` | body size, min / nom / max |
| `package.pin_count`, `pitch` | pin count and pitch |
| `package.terminal_length`, `terminal_width` | lead or terminal size, for the IPC land |
| `package.lead_span` | toe-to-toe span for gull-wing parts |
| `package.ep_length`, `ep_width` | exposed pad |
| `land.source` | "datasheet" with page, or "ipc7351" when derived |
| `land.pad_length`, `pad_width`, `pad_span`, `pad_gap` | recommended land from the datasheet |
| `land.ep_length`, `ep_width`, `via` | exposed-pad land and vias |

Each family in `taxonomy.json` gets a `cad_required` list (the keys a footprint needs). `parts.py check --cad` reports what is missing.
For passives the size code alone is enough, because the IPC-7351 chip land follows from the body and terminal size.

## 6. Tools to build (in this order, the download tool together with the user)

| # | Tool | Does | Tested on |
|---|---|---|---|
| 1 | `lib_find.py <MPN or project>` | finds symbol, footprint and model for each part, prints have / missing, writes the lists in section 8 | 17 buck parts |
| 2 | `cad_fetch.py <MPN>` | 3D model download: EasyEDA/JLC by LCSC number (STEP), then maker URL, then substitute; saves to `models/step/<package type>/`, registers sha256, source and body box; also exports the EasyEDA symbol and footprint as a reference | user's PC (EasyEDA is blocked in the cloud session) |
| 3 | `step_box.py` (inside cad_fetch) | reads the STEP points and reports the body box, compared with `package.*` (pass when inside the datasheet min/max) | 17 buck parts |
| 4 | `gen_sym.py --from-part` | builds a symbol spec from the record's pins and family kind | buck symbols |
| 5 | `fp_build.py` | IPC-7351 chip and gull-wing land plus datasheet land into altium-lib JSON (dry-run) | buck footprints vs existing ones |
| 6 | `lib_build.py <project>` | local category folders with a SchLib and PcbLib per family from the database, shared symbols and footprints, parameters from LIB-14 | buck project |
| 7 | `lib_migrate_shared.py` | turns the 16 per-value symbols of the global library into shared symbols; old IDs stay as aliases | global library |

Also in this work: fix lesson B7 (an Altium save rewrites IDs, so `lib_status.py` reports LOCAL CHANGED). The hash should leave those fields out.

## 7. Decisions and open questions

Answered by the user (2026-10-19):
- IC symbols follow the datasheet's recommended pin grouping and are drawn symmetric (LIB-11).
- A standard body (chip size such as 0603, or a JEDEC package such as SOIC-8) has one shared 3D model, whatever the value: a 10 uF and a 22 uF 0603 capacitor use the same model (LIB-13). Resistor and capacitor chips keep separate models because their footprints and heights differ.
- The local library has one component per manufacturer part number, passives included (LIB-14).
- Global: symbols in a folder per category and a file per family; footprints and 3D models by package type. Local: a folder per category, a SchLib and a PcbLib per family (LIB-15).

Still open:
1. IC pin length: 200 or 300 mil? (Passives keep 100 mil, the capacitor 80 mil, from LIB-03.)

## 8. Lists for the 17 parts in the database

The lists are in `/mnt/project-files/altium-framework/LIBRARY_LISTS.md` for now. `lib_find.py` will generate them.
