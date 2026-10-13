# EDA workspace rules (Altium Designer 26, three MCP servers)

Always start Claude Code from this workspace folder (D:\EDA in the examples). The hook, .mcp.json and permissions only apply here.
Projects live in `projects\<name>\`. Before touching a project read its `CLAUDE.md`, `PROJECT.md`,
`requirements.md`, `constraints.md` and `gates.md`. Rules: `_rules\` (VERSION, 79 rules). Index: `docs\README.md`.
Objective (user): automate the work an engineer does by hand in the tools. System-level design guidelines come later in `_guidelines\` (DRAFT, empty, not binding, separate from `_rules\`); never invent values for them.

## Non-negotiables
1. Human gates G1, S1, G2, G3, G4 (`gates.md`) need an explicit user sign-off. Never tick a gate yourself.
2. Datasheet first: every number about a part comes from a PDF in the project's `docs\datasheets\`. Missing -> ask.
3. Calculations in code (`_tools\scripts\calclib.py`, `calcs_run.py`), copied to `calcs.md`. Never mental arithmetic.
4. Reads before writes. Announce every destructive edit and get a yes first.
5. Never edit `_tools\bridge\`, `.mcp.json` or `.claude\` (the user controls those). Never bypass the guard hook.
6. "KILL SWITCH IS ENGAGED" in any result: stop all Altium work, tell the user, do not try to bypass it.
7. Never claim what is on the screen without evidence (tool result, file, capture). Run the checkers before "done".
8. New footprints go to the project's `libs\` first; the global library changes only via `lib_promote.py` after G1.
9. After each work session append decisions and open issues to the project's `PROJECT.md`.

## The three MCP servers
| Server | Use it for | Needs Altium open |
|---|---|---|
| `altium-lib` | create / edit / diff / validate .SchLib and .PcbLib (offline) | no |
| `altium-coffee` | live PCB: placement, check_placement, net classes, screenshots, output jobs | yes |
| `altium-eda` | live schematic, design review, audits, SPICE setup | yes |

Routing:
1. Library work -> `altium-lib`. Dry-run first (libs\_dryrun\). Never write a library that is open in Altium.
2. Schematic capture and review/audit -> `altium-eda`. Audits only on a COPY of the project.
3. PCB layout, screenshots, output jobs -> `altium-coffee`.
4. Only ONE live bridge (coffee or eda) at a time. A hook switches automatically and may show a popup.
   If a call is blocked, read the message, tell the user, and wait. Never retry in a loop.

## Read before each phase (full table: `_rules\00_INDEX.md`)
| Phase | Rule files | Playbook |
|---|---|---|
| Start a project | 01_WORKFLOW_GATES, 02_REQUIREMENTS_CALCS_PARTS, 08_COMMUNICATION | P1 |
| Library work | 03_LIBRARY, 07_TOOLING_ALTIUM | P2, P4 |
| Schematic | 04_SCHEMATIC, 07_TOOLING_ALTIUM | P3 |
| PCB layout | 05_PCB, 07_TOOLING_ALTIUM | P5 |
| Before any gate / fab output | 01_WORKFLOW_GATES, 06_FAB_OUTPUT | P6 |
| Commit / handoff | 01_WORKFLOW_GATES | P7 |
| Altium stuck | 07_TOOLING_ALTIUM | P8 |
Playbooks: `_rules\playbooks\`. Rule changes: only the user approves (propose with `_rules\RETRO_TEMPLATE.md`).

## Offline tools (`_tools\scripts\`, see its README.md; no Altium needed)
| Need | Script |
|---|---|
| New project | `new_project.py <name>` |
| Symbol pins = pads, style | `pin_match.py <SchLib> <PcbLib> --style` |
| Sheet connectivity + dots | `conn_check.py <sheet.SchDoc> ai\plan.json` |
| Sheet readability | `sch_overlap.py <sheet.SchDoc>` |
| Gate evidence | `gate_check.py <G1/S1/G2/G3/G4> projects\<name>` -> ai\review\ |
| Global library | `lib_pull.py`, `lib_status.py`, `lib_promote.py`, `catalog_check.py` (`_global\README.md`) |
| Everything still works | `python _tools\selftest.py` |

## Popups for problems the scripts cannot detect
When a tool error matches a symptom, run `bridge.cmd popup <id>` (from the workspace folder). Exit code 0 = user pressed Retry
(retry the call ONCE), 1 = Cancel (stop and ask).
| Symptom | id |
|---|---|
| coffee timeout / no reply while the eda-agent loop may be running | run `bridge.cmd status` FIRST. If the loop is "responding", it is the cause (Altium refuses a second script): do NOT press Ctrl+F3 and do NOT show `script_crashed`. Tell the user and release the loop through the guard's "release eda-agent loop" popup or with eda-agent `app_detach` (it SAVES all modified documents first - announce that and get a yes), then wait |
| timeout / no reply from Altium (loop not responding) | `script_crashed`, then `unknown_modal` if that did not help |
| `update_pcb` adds 0 components while not in sync | `eco_dialog` |
| "no active PCB/schematic document" | `wrong_document` |
| offline server cannot write a library (file locked) | `library_open` |
| unsaved documents block an operation | `unsaved_docs` |

Logs: bridge switches and failures in `_logs\MCP_LOG.md` (written by the scripts); lessons in `docs\LESSONS_LEARNED.md`.
