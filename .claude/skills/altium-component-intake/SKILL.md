---
name: altium-component-intake
description: Get a number about a part from the component database, or add a part met for the first time (datasheet download, extraction, check); use whenever a design needs a pin, rating, package or application value of a part.
---

## Goal
Every device number used in a design comes from the part's record in `library/parts/`, with its datasheet page and
quote (RQ-01). A part or fact that is missing is added first, then read from the record.

## Inputs
- the MPN or LCSC C-number, and what the design needs (a section, a fact key)
- `library/parts/README.md` (record format and the first-time workflow), `library/parts/taxonomy.json` (families, required facts, units)

## Rules to load
- `rules/02_REQUIREMENTS_CALCS_PARTS.md` (RQ-01 database first, RQ-03 C-numbers, RQ-04 stock at BOM time)
- `rules/03_LIBRARY.md` (LIB-05 footprint status) when the part goes on to the library

## Approach
1. `parts.py find <mpn or C-number>`. Found and PASS: read only the section needed (`parts.py get <mpn> --section abs_max`).
2. Not found: `parts.py new --lcsc C123` (or offline `--mpn --mfr --category`), `parts.py fetch <mpn> --project <p>`
   (maker's website first for the English original, LCSC second; downloads need no question), `parts.py locate <mpn>`, then extract per README step 5: every required fact, pins with the exposed pad,
   abs max, recommended, package and land pattern, application, layout and firmware notes, each with page and quote.
3. Found but the needed fact is missing: fetch the datasheet if it is not on disk, extract that fact into the record.
4. `parts.py check <mpn>` until PASS, then `parts.py index`. Read the number from the record, not from your notes.
5. Values the text layer lacks: read the page image, mark `visual`, add to `review.open`.
6. The project's PDFs stay local in `docs/datasheets/`: `parts.py datasheet <parts> --project <p>` (or `--manifest`)
   copies them from the library cache or `--search` folders, else downloads from the record's link. Never commit a PDF.
7. Extracted records may be used while designing. Before G1 the user checks pins, abs max, package and every visual
   value and records it with `parts.py verify`; `parts.py check --gate` must PASS.

## Stop and ask the user (do not guess) when
- `parts.py check` fails and the cause is in the datasheet itself (missing page, unreadable table)
- the datasheet contradicts itself, another datasheet, the supplier data or the catalog
- a downloaded datasheet has another sha256 than recorded (the maker revised it)
- the decision rests on an open `review.open` item or a `visual` value
- G1 is next and `parts.py check --gate` fails (pins, abs max, package or visual values not checked by the user)
State the part, the fact, the pages and the options, and wait.

## Exit checks
| Check | How | Pass when |
|---|---|---|
| record valid | `parts.py check <mpn>` | PASS |
| index current | `parts.py index` | the part is found by `parts.py find` |
| G1 ready | `parts.py check --gate` | PASS |

## Write back
- the record, `library/datasheets/index.json`, `library/parts/index.json` (never a PDF, in any repo)
- `PROJECT.md`: parts added and any open questions to the user
