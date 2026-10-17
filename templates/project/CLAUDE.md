# Project {{NAME}}

Created {{DATE}}. Workspace rules in ../../CLAUDE.md apply. Rules snapshot: rules VERSION {{RULES_VERSION}}
(recorded in project.json; a newer workspace VERSION does not change this project silently - WF-03).

@requirements.md
@constraints.md
@schematic_standards.md
@PROJECT.md

Before each phase read the files in ../../rules/00_INDEX.md "Read before each phase" and the playbook named there.
Checkers and generators: ../../tools/scripts (README.md there). Evidence per gate: ai/review/ (gate_check.py).
Libraries: local copies only (libs/), recorded in libs/lib_manifest.json; global parts via lib_pull.py.

Folders: `hw\` Altium project, `libs\` project libraries, `docs\datasheets\` project-only datasheets (part numbers come from `library\parts\` records first, RQ-01),
`outputs\` Gerbers/BOM, `ai\` plans, reports and session notes.
Current phase: see PROJECT.md. Gates: see gates.md.
