# _global\datasheets\

Vendor datasheet PDFs are **not stored in git** (they belong to their makers). `catalog\components.json` records, for each part, the
file name (`datasheet.path`) and the `sha256` of the PDF that was used, and `catalog_check.py` verifies it (rule RQ-01).

On a fresh clone the PDFs are missing:
- `python _tools\scripts\datasheets_fetch.py` downloads each one from the source link recorded in the catalog and checks its sha256.
- If a download fails, save the PDF by hand under the exact file name from the catalog; the hash check decides if it is the right file.
- A missing PDF is reported as NOT FETCHED, not as a broken catalog. A PDF whose hash differs is always an error.
