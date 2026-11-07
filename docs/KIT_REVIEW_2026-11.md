# Kit review, November 2026: what the first projects taught, and what changed

Rules 1.12.0. Written 2026-11-07 from every thread of the kit's first three weeks of real use (framework plan and
migration, the Extention_01 pulse board, the Bondu production package and JLC quotes, the D:\EDA cleanup, a 74-part
client library audit, parameter cleanup, footprint review document, the batch library build, the 3D-body fix and a
portfolio capture), the project memory, the decision logs and check reports, and the open PRs #30, #31 and #32.

## 1. What worked (keep it)

- **Tools over prose.** Every place a rule became a script (`pin_match`, `conn_check`, `bom_check`, `cpl_check`,
  `distributor_lookup`, `lib_audit`) the error stopped recurring. The CPL by numbers (FAB-06) found 43 wrong parts a
  look at the preview had passed.
- **Sample first, then scale.** The footprint review document was agreed on one footprint (SOT65P210X110-5N) and then
  generated for 68 footprints in one pass, with one round of fixes.
- **Datasheet-first with a database.** Part records with page and quote let later sessions reuse numbers without
  re-reading PDFs.
- **Offline file access.** Reading SchLib/PcbLib/SchDoc directly (`altium_io.py`) was fast and never wedged Altium.

## 2. Where time, tokens and the user's attention went (fix it)

| # | Pattern | Evidence | Cost |
|---|---|---|---|
| 1 | **Sessions started in the wrong folder** | The batch library session ran in the client folder: no Altium servers, 3D embedded offline (red boxes), the user moved the folder, still no servers | about an hour and three user actions |
| 2 | **Stale base, parallel branches** | PR #32 was written on a two-week-old base and reused LIB-17..20, P9 and version 1.6.0; LIB-33 was taken by two threads; 1.4.1 was merged after 1.5.0 | a PR that could not merge as-is; renumbering |
| 3 | **Asking per step instead of per batch** | Parameter update, footprint check, library build: each waited hours for a "yes"; the user then asked for "all permissions at once" | stalled threads |
| 4 | **Visual style decided late** | Symbol colours, resistor drawing, polarised capacitor and 3D colours redone across the whole library four times | four full passes, many Altium wedges |
| 5 | **Live Altium scripts for offline work** | Six Ctrl+F3 recoveries in one library session, four in one PCB session; a 3D swap put 26 bodies 1270 mm away | each one interrupts the user |
| 6 | **Extra or adjacent work** | A review spreadsheet nobody asked for; footprint checks started before the asked library package | tokens, then a "stop" from the user |
| 7 | **Job scripts left behind** | The review generator, Swap3D.pas and the batch builder exist only in the client folder | rebuilt in later sessions |
| 8 | **Claims not tied to the result** | "Datasheets deleted" (19 remained); "TPA3116 footprint has a wrong thermal pad" (figure misread); "1N4148W not on LCSC" (narrow search) | user corrections, lost trust |
| 9 | **Speed traded for a hard rule** | The S8550 datasheet check was skipped "for speed"; the user had already made it strict | a wrong current rating placed |
| 10 | **Big rule files for small needs** | Every library session loaded about 20 kB of parameter tables to use one category | tokens on every library task |
| 11 | **Usage limits mid-job** | The footprint check and the portfolio capture stopped at the limit | a new session re-reads history |
| 12 | **Setup by trial** | The migration took eight run-and-paste rounds (drive-letter crash, stale hook path, coffee pull failure) | the user's evening |

## 3. What this PR changes

| Change | Fixes pattern | Where |
|---|---|---|
| `kit doctor`: servers, guard hook, git behind/ahead, rules version, kill switch, Altium instance count, altium-lib paths; prints the start command | 1, 2, 12 | `tools/scripts/doctor.py`, WF-11 |
| `kit start "<folder>"`: Claude Code in the workspace with the project folder added, so the servers and the guard always load | 1 | `kit.cmd`, WF-10 |
| `rules_lint --next-id`, CHANGELOG order check, contributor note on numbering after `git pull` | 2 | `rules_lint.py`, CONTRIBUTING |
| PRs #30, #31, #32 consolidated on current main; #32 renumbered (LIB-35..38, P13) | 2 | rules 1.12.0 |
| One brief per batch with every permission and one sample per kind; final report with a by-hand list | 3, 4 | WF-12; LIB-30 decided |
| Asked scope at the asked pace; hard rules never dropped for speed | 6, 9 | WF-13 |
| Offline first, live Altium last; stop scripting a stage after 2 wedges | 5 | TOOL-20 (with TOOL-18/19 from #32) |
| Job scripts become kit tools in the same session | 7 | WF-14; TOOLS_GUIDE proposal to commit the three client-folder scripts |
| Facts from figures carry page and crop; negative claims list the search | 8 | RQ-10 |
| Counts and states from the tool output | 8 | COM-06 |
| Decision log after every step, so a stop resumes from one file | 11 | WF-05 |
| `kit lib_params "<Type>/<Subtype>"` and `--check <SchLib>`; tables only in the JSON and a generated doc; 09_LIBRARY_STANDARD.md from 37 kB to 22 kB | 10 | `lib_params.py`, LIB-23, LIB-34 |
| CLAUDE.md: preflight first, start command, token budget section, new tools | 1, 10 | CLAUDE.md |
| Orchestrator skill: doctor first, batch rule, library row names 09 and P13 | 1, 3 | `.claude/skills/altium-orchestrator` |
| Lessons K1..K10 | all | docs/LESSONS_LEARNED.md |

Tests: `tools/tests/test_kit_review.py` (17 tests: lib_params, doctor, rules_lint, ws_lib_check). Selftest also fails
when `docs/LIBRARY_PARAMETERS.md` no longer matches the JSON.

## 4. Decisions made for this PR (the user asked not to be disturbed)

1. **#32's rules keep their content but get new IDs** (LIB-35..38, P13). Main's LIB-17..20 are older, merged and
   referenced by tools (`lib_audit`), so the newcomer moves. Their new home is `09_LIBRARY_STANDARD.md`, because
   `03_LIBRARY.md` is at the 20-rule limit.
2. **LIB-13's 3D source order follows the user's latest words** (2026-11-04/05: KiCad models for standard packages,
   best-looking maker model for custom parts). D7's "Celestial first" now applies to symbols and footprints only.
3. **LIB-30 per-part briefs become a batch brief** (WF-12), as the user asked on 2026-11-04. Per-part stays available
   when the user asks for it.
4. **The parameter tables live in one place** (the JSON). The human-readable table is generated, so the two cannot drift.
5. **No change to `.mcp.json`, `.claude/` or `tools/bridge/`** (CLAUDE.md rule 5). `kit start` solves the folder problem
   without touching them.
6. **PRs #30, #31 and #32 are left open.** This branch contains #30 and #31 as merges, so merging this PR closes them in
   effect; #32 should be closed unmerged after this one, since its IDs collide.

## 5. Done in the follow-up (rules 1.13.0, the user approved everything left for later)

- The client-folder scripts are kit tools, without client data (WF-14): `fp_review.py` (review document, now reads
  the libraries offline through the new `lib_dump.py`, configured by a `review.json`), `tools/altium_scripts/Swap3D.pas`
  with `kicad_models.py` (KiCad models picked by pad matching, embedded inside Altium), and `tools/library_build`
  (batch builder driven by a plan JSON; the parameter sets come from `rules/library_parameters.json`; offline 3D
  embedding dropped because it gave red boxes). The client plan and override data stay in the client folder.
- `lib_std_check.py`: value format and Description pattern.
- Buck `lib_status` FAIL: an Altium re-save rewrote IDs only; now "OK (re-saved)" (22 of 23 items). One real
  difference remains for the user to look at: CAPC1608_0603, one pad flag byte differs from the global copy.
- Library rules: instead of moving 38 rules between files (every reference would break), `rules/LIBRARY_PACK.md`
  gives one line per rule (9 kB instead of 39 kB) and is generated by `rules_lint`, so it cannot go stale.
- Setup: `install.cmd` (prerequisites with winget, MCP servers, selftest, preflight, the remaining manual step);
  `install.cmd /update`.

## 6. Still open (decisions only the user can make)

- D10 (who verifies the user's own parts), LIB-20 client-rules placeholder, the restructure of the parts database to
  the 22-Type tree (planned after the client job).
- Description patterns for the Types the standard does not cover yet (R9): LED, crystals, filters, protection,
  switches, sensors, modules, board features. `lib_std_check` skips them until they exist.
