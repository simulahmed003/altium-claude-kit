# EDA workspace rules (Altium Designer 26, three MCP servers)

Always start Claude Code from this workspace folder (D:\EDA in the examples). The hook, .mcp.json and permissions only apply here.
A project in another folder is added to the session, never opened as its own session: `kit start "<folder>"` (WF-10).
First action of every session: `python tools\scripts\doctor.py` (WF-11); no FAIL, and pull before writing rules if it says behind.
Projects live in `projects\<name>\`, or stay in the user's own folder with the kit files in `<folder>\_eda\` (WF-09: never move or copy a work project into projects\). Before touching a project read its `CLAUDE.md`, `PROJECT.md`,
`requirements.md`, `constraints.md` and `gates.md`. Rules: `rules\` (VERSION, 129 rules). Index: `docs\README.md`.
Objective (user): automate the work an engineer does by hand in the tools. System-level design guidelines come later in `guidelines\` (DRAFT, empty, not binding, separate from `rules\`); never invent values for them.

## Non-negotiables
1. Human gates G1, S1, G2, G3, G4 (`gates.md`) need an explicit user sign-off. Never tick a gate yourself.
2. Datasheet first, through the component database (`library\parts\`, rule RQ-01): read part numbers with `parts.py get`.
   Part or value missing -> datasheet (maker's site first, LCSC second) into the project's `docs\datasheets\` (local, never
   committed) -> `parts.py fetch` + extract with page and quote -> `parts.py check` PASS -> read it from the database.
   A person checks pins, abs max, package and visual values (`parts.py verify`) before G1. Never from memory.
   A flaw (check fails, a contradiction, an open review item, a revised datasheet) -> ask the user.
3. Calculations in code (`tools\scripts\calclib.py`, `calcs_run.py`), copied to `calcs.md`. Never mental arithmetic.
4. Reads before writes. Announce every destructive edit and get a yes first.
5. Never edit `tools\bridge\`, `.mcp.json` or `.claude\` (the user controls those). Never bypass the guard hook.
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

Phase skills in `.claude\skills\` (start with `altium-orchestrator`) load the right rules and playbook for you.
Production files: `altium-fab-package`; JLC quotes: `altium-jlc-quote`; new library parts: `altium-local-library`.

## Tools for the user
Every tool must also be usable by the user directly from cmd.exe (`kit <tool> --help`, guide `docs\TOOLS_GUIDE.md`);
keep that guide current when a tool changes. When a task repeats or a CHECKLIST rule could be a script check,
propose a tool in one line (and add it to the guide's proposals table).

## Read before each phase (full table: `rules\00_INDEX.md`)
| Phase | Rule files | Playbook |
|---|---|---|
| Start a project | 01_WORKFLOW_GATES, 02_REQUIREMENTS_CALCS_PARTS, 08_COMMUNICATION | P1 |
| Any batch job (library, cleanup, fab package) | 01_WORKFLOW_GATES (WF-05, WF-12..14), 08_COMMUNICATION | - |
| Library work | LIBRARY_PACK (one line per rule; open 03 / 09 only for the rules you apply), 07_TOOLING_ALTIUM | P2, P4, P11, P12, P13 |
| Schematic | 04_SCHEMATIC, 07_TOOLING_ALTIUM | P3 |
| PCB layout | 05_PCB, 07_TOOLING_ALTIUM | P5 |
| Before any gate / fab output | 01_WORKFLOW_GATES, 06_FAB_OUTPUT | P6, P9 |
| BOM alternates, JLC quote | 02_REQUIREMENTS_CALCS_PARTS, 06_FAB_OUTPUT | P9, P10 |
| Commit / handoff | 01_WORKFLOW_GATES | P7 |
| Altium stuck | 07_TOOLING_ALTIUM | P8 |
| Library batch release to the Workspace | 09_LIBRARY_STANDARD, 03_LIBRARY, 07_TOOLING_ALTIUM | P13 |
Playbooks: `rules\playbooks\`. Rule changes: only the user approves (propose with `rules\RETRO_TEMPLATE.md`).

## Token budget (read less, run more)
- Read only the rule files of the current phase (table above). Library: `rules\LIBRARY_PACK.md` (9 kB) instead of 03 + 09 (39 kB). Never load `docs\LIBRARY_STANDARD.md` (76 kB, the standard's
  original text) or `docs\LIBRARY_PARAMETERS.md`; for a category's parameters run `lib_params.py "<Type>/<Subtype>"`.
- Prefer a tool's summary line over reading the files it checks; read a file only where the tool points.
- Long jobs: keep the batch `_decision_log.md` current after every step (WF-05), so a new session reads that file, not the history.
- A script you write that the next job will need goes into `tools\` with `--help` and a TOOLS_GUIDE row (WF-14).

## Offline tools (`tools\scripts\`, see its README.md; no Altium needed)
| Need | Script |
|---|---|
| Session preflight (servers, hook, git up to date, one Altium, stale MCP server, open dialogs) | `doctor.py` (`kit doctor`) |
| Before a live DelphiScript: BOM, modals, %TOKENS%, bad identifiers, try, current footprint | `pas_lint.py <script.pas>` (TOOL-21) |
| Altium stuck: find the cause, answer the safe dialogs, end a duplicate X2 | `altium_unstick.py --fix` (TOOL-21) |
| New project | `new_project.py <name>` |
| Symbol pins = pads, style | `pin_match.py <SchLib> <PcbLib> --style` |
| Sheet connectivity + dots | `conn_check.py <sheet.SchDoc> ai\plan.json` |
| Sheet readability | `sch_overlap.py <sheet.SchDoc>` |
| Gate evidence | `gate_check.py <G1/S1/G2/G3/G4> projects\<name>` -> ai\review\ |
| Parameter set of one category / check a SchLib against it | `lib_params.py "<Type>/<Subtype>"`, `lib_params.py --check <lib.SchLib>` |
| Workspace-ready SchLib (no "/" in types, Category, Symbol, description) | `ws_lib_check.py <lib.SchLib>` |
| Parameter values and Description format of a SchLib | `lib_std_check.py <lib.SchLib>` |
| Library geometry offline (pads mm, pins mil) / footprint review document | `lib_dump.py`, `fp_review.py` (LIB-33) |
| KiCad 3D models for standard footprints, then embed inside Altium | `kicad_models.py <PcbLib>`, `tools\altium_scripts\Swap3D.pas` |
| Batch library build from a plan (P13) | `kit lib_build <plan.json>` (`tools\library_build\`) |
| Global library | `lib_pull.py`, `lib_status.py`, `lib_promote.py`, `catalog_check.py` (`library\README.md`) |
| Library audit, check status, source | `lib_audit.py` (`mark`, `source`; LIB-17, LIB-19) |
| Production BOM / CPL / package | `bom_check.py`, `cpl_check.py` (convert, fit, check), `fab_package.py` (FAB-04..07) |
| JLC quote with stock shortfall | `jlc_quote.py shortfall` / `summary` (FAB-08) |
| Next free rule ID (after `git pull`) | `rules_lint.py --next-id LIB` |
| Everything still works | `python tools\selftest.py` |

## Popups for problems the scripts cannot detect
Any timeout, "script never started", "executor_wedged" or "busy": run `kit altium_unstick --fix` FIRST (TOOL-21); it frees
most jams without the user and names the cause. After `install.cmd /update` restart Claude Code (TOOL-22).
When it says "still stuck" and a tool error matches a symptom, run `bridge.cmd popup <id>` (from the workspace folder). Exit code 0 = user pressed Retry
(retry the call ONCE), 1 = Cancel (stop and ask).
| Symptom | id |
|---|---|
| coffee timeout / no reply while the eda-agent loop may be running | run `bridge.cmd status` FIRST. If the loop is "responding", it is the cause (Altium refuses a second script): do NOT press Ctrl+F3 and do NOT show `script_crashed`. Tell the user and release the loop through the guard's "release eda-agent loop" popup or with eda-agent `app_detach` (it SAVES all modified documents first - announce that and get a yes), then wait |
| timeout / no reply from Altium (loop not responding) | `script_crashed`, then `unknown_modal` if that did not help |
| `update_pcb` adds 0 components while not in sync | `eco_dialog` |
| "no active PCB/schematic document" | `wrong_document` |
| offline server cannot write a library (file locked) | `library_open` |
| unsaved documents block an operation | `unsaved_docs` |

Logs: bridge switches and failures in `logs\MCP_LOG.md` (written by the scripts); lessons in `docs\LESSONS_LEARNED.md`.
