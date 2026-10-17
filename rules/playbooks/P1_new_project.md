# P1 New project

Read with: 01_WORKFLOW_GATES, 02_REQUIREMENTS_CALCS_PARTS, 08_COMMUNICATION.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Create the project: `python tools\scripts\new_project.py <name>` (lowercase, digits, hyphens). It copies the template, records the rules VERSION in project.json, writes libs\lib_manifest.json. | TESTED (selftest, temp project) |
| 2 | Fill requirements.md (numbers + who confirmed) and constraints.md (fab profile values, link, date checked). | TESTED (buck) |
| 3 | Choose parts: datasheet PDF into docs\datasheets\ before quoting any number (RQ-01). Prefer catalog parts (`library\catalog\components.md`). | TESTED (buck) |
| 4 | Calculations: write ai\calc_inputs.json, run `python tools\scripts\calcs_run.py ai\calc_inputs.json --md`, paste into calcs.md. | TESTED (buck fixture) |
| 5 | Pull global parts: `python tools\scripts\lib_pull.py <project> <component> ...` (local copies + manifest). | TESTED (selftest) |
| 6 | Check: `python tools\scripts\gate_check.py G1 projects\<name>` runs ("no design yet" is expected at this point). | TESTED (selftest) |
| 7 | Write the plan in PROJECT.md; commit (P7). | TESTED (buck) |

7 of 7 steps TESTED.
