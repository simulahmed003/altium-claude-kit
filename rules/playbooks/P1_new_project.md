# P1 New project

Read with: 01_WORKFLOW_GATES, 02_REQUIREMENTS_CALCS_PARTS, 08_COMMUNICATION.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Create the project: `python tools\scripts\new_project.py <name>` (lowercase, digits, hyphens). It copies the template, records the rules VERSION in project.json, writes libs\lib_manifest.json. | TESTED (selftest, temp project) |
| 2 | Fill requirements.md (numbers + who confirmed) and constraints.md (fab profile values, link, date checked). | TESTED (buck) |
| 3 | Choose parts from the component database first (`parts.py find`, `parts.py get`; prefer catalog parts in `library\catalog\components.md`). New part: P2 steps 2-3 before quoting any number (RQ-01). Put the datasheets of the chosen parts into docs\datasheets\ (local only): `parts.py datasheet <mpn ...> --project projects\<name>` (copies from the library cache, else downloads and checks the sha256). | TESTED (copy and download on a scratch project, 2026-10-17); database-first selection UNTESTED on a real project |
| 4 | Calculations: write ai\calc_inputs.json, run `python tools\scripts\calcs_run.py ai\calc_inputs.json --md`, paste into calcs.md. | TESTED (buck fixture) |
| 5 | Pull global parts: `python tools\scripts\lib_pull.py <project> <component> ...` (local copies + manifest). | TESTED (selftest) |
| 6 | Check: `python tools\scripts\gate_check.py G1 projects\<name>` runs ("no design yet" is expected at this point). | TESTED (selftest) |
| 7 | Write the plan in PROJECT.md; commit (P7). | TESTED (buck) |

6 of 7 steps TESTED (step 3 partly).
