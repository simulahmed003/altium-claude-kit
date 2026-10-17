# library\parts - component database

One record per orderable part (manufacturer part number), with every number tied to a page of its datasheet.
Built to hold thousands of parts. The tool is `tools\scripts\parts.py` (`--help` for all commands).

## Parts database vs. the Altium library
| | `library\parts\` (this folder) | `library\catalog\` + `symbols\`, `footprints\` |
|---|---|---|
| Holds | every part we have researched: facts, pins, supply data | the parts that have an Altium symbol and footprint |
| Key | manufacturer + MPN | catalog id (`R_10k_1%_0603`) |
| Grows | each time a project meets a new part | only after G1, through `lib_promote.py` |
| Link | `catalog_ids` in the part record | the catalog's `mpn` |

A part can be in the database without being in the Altium library (a candidate that was not chosen). A catalog
component normally points to exactly one part record.

## Layout
| Path | Holds | In git |
|---|---|---|
| `parts\taxonomy.json` | categories, families, required facts per family, allowed fact keys and their units | yes |
| `parts\manufacturers.json` | canonical manufacturer names, aliases (`TI` = `Texas Instruments`), file slugs | yes |
| `parts\<category>\<family>\<MPN>__<mfr slug>.json` | one part record | yes |
| `parts\index.json` | generated search index (`parts.py index`) | yes |
| `datasheets\index.json` | every datasheet PDF by sha256: file, url, source, pages, which MPNs it covers | yes |
| `datasheets\*.pdf` | the PDFs (vendor copyright) | no |
| `datasheets\_text\` | page text cache, three pdftotext modes | no |
| `market\` | price and stock snapshots with their date (`parts.py market`) | no |

Folders stay small because parts are spread over category and family. A family folder that grows past a few
hundred parts can be split by a taxonomy change (new family), never by renaming one.

## Categories
The tree lives in `taxonomy.json`: `passives` (resistor, capacitor_mlcc, capacitor_electrolytic, capacitor_polymer,
inductor_power, ferrite_bead), `discretes` (mosfet, diode_*, led, bjt), `ics` (power_buck, power_boost, power_ldo,
power_switch, mcu, interface, analog, sensor, logic, memory, clock), `connectors`, `frequency`, `protection`,
`electromechanical`. Each family lists the facts that must be extracted before a part leaves `draft`, and the
LCSC category names that map to it (so `parts.py new --lcsc C123` can file the part by itself).
A new family or key is a pull request to `taxonomy.json`: field names and units only, never values.

## A part record
```
mpn, mfr, category, description, package, lifecycle
datasheets[]      sha256, file, url (one PDF can cover many MPNs; one MPN can have several PDFs)
suppliers[]       name, sku (LCSC C-number, ...), url, verified date         - stable ids only
supplier_params   the distributor's parameter list: for search only, NEVER a source (rule RQ-01)
facts             summary, abs_max, recommended, electrical, thermal, package, compliance, ordering
                  each key -> {min|typ|max|value, unit, cond, derivation, ref}
pins[]            number, name, type, description, ref
notes             application (circuit design), layout, software (firmware), handling: [{text, ref}]
catalog_ids[]     Altium catalog components that use this part
review            status draft -> extracted -> checked -> verified, extracted_by, open[] questions
```
`ref` = `{page, quote, mode?, visual?, ds?}`: the PDF page (as the PDF numbers it, not the printed footer),
a short quote copied word for word from that page, the text mode the quote comes from, and `visual: true` when the
value was read from the page image because the PDF text layer does not contain it.

Conventions:
- Units are the SI unit named in `taxonomy.json` (`0.0115` ohm, not `11.5 mOhm`); the quote keeps the datasheet's unit.
- min / typ / max are stored as the datasheet's columns print them. P-channel negative values are ordered by magnitude.
- One quantity under several conditions: `rds_on`, `rds_on@vgs_4v5`, `rds_on@low_side`.
- A value decoded from the part number gives the decoding rule as the quote and the arithmetic in `derivation`.
- Abs max and recommended never mix. `check` fails a recommended max above the abs max.

## Workflow: the first time a project meets a part
1. `parts.py find <mpn or C-number>` - already there? Use it (read sections with `parts.py get <mpn> --section abs_max`).
2. `parts.py new --lcsc C123` (or `--mpn --mfr --category` offline). LCSC gives MPN, maker, package, description,
   parameters and the datasheet link; the maker name is mapped to its canonical name.
3. `parts.py fetch <mpn>` downloads the datasheet (or `--file` for a PDF you already have), records its sha256 and
   pages, and builds the page text. Prefer the maker's PDF over a distributor copy when both exist (`--url`).
4. `parts.py locate <mpn>` lists the pages per section. `parts.py text <mpn> --pages 5-6 --mode table` shows them.
   Read tables in `raw` or `table` mode: `layout` mode can move a value onto the wrong row.
5. The extractor (an AI agent or a person) writes facts, pins and notes with page and quote. What to extract:
   - every `required` fact of the family, plus pins (with the exposed pad), abs max, recommended, key electrical,
     thermal, package dimensions and the datasheet's recommended land pattern;
   - application notes: required external parts, equations and the maker's example values;
   - layout notes: placement and routing rules from the layout section;
   - software notes for parts with an interface: address, registers, timing.
   When the text layer lacks a value, read the page image, mark `visual: true`, and add it to `review.open`.
   Do not take a table that only looks like a land pattern (YAGEO's bend-test board): say so in a note.
6. `parts.py check <mpn>` until PASS: schema, units, every quote found on its page, abs max vs recommended,
   required facts. Set `review.status` to `extracted`.
7. A person verifies pins, abs max and package against the PDF (and every `visual` value), then sets `verified`
   with name and date. Only `verified` facts may later replace opening the PDF (rule RQ-01 change, PROPOSED).
8. `parts.py index`. Commit the record, `datasheets\index.json` and `parts\index.json` (never the PDF).
9. Price and stock: `parts.py market <mpn>` at BOM time (rule RQ-04). The snapshot is local and dated.

## Status on 2026-10-17
17 parts from the buck-12v-5v-3a datasheets (12 PDFs), all `extracted`, `parts.py check` 17 PASS, 65 values marked
`visual` (RESI datasheet text has no digits; drawings in the Sumida, Codaca, Samsung and AOS PDFs). None is `verified` yet.
