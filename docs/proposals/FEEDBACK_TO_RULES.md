# Proposal: design standards, user feedback and how rules grow

Status: PROPOSAL, 2026-10-17. Nothing here is binding until the maintainer approves it, one part at a time (WF-04).
Nothing in `rules\` is changed by this file.

## 1. The goal in one paragraph
People design boards with their own AI agent. The agent follows the kit's rules. While it works, the user corrects it
("this is wrong", "this would be better") and finally approves each gate. After approval the agent looks back at the
corrections, decides which ones are worth keeping, writes them in a general form, and offers them to the right place:
the user's own standard, or the central repo (this kit) as a rule or guideline proposal. The next design starts better.

## 2. What "the design standard" is: five layers
An agent never works from one list. It works from five layers, each with its own owner and its own change process.

| Layer | Where | Holds | Example | Owner, change process |
|---|---|---|---|---|
| L1 Core rules | `rules\` (central) | How any design is done safely and checkably with this toolchain: gates, evidence, tool quirks, file checks | "Pin ends on the 100 mil grid" (LIB-03), "Only the user ticks a gate" (WF-01) | Maintainer, by PR (WF-04) |
| L2 Guidelines | `guidelines\` (central) | Engineering targets with a source, for a class of circuit | "Inductor ripple ratio k range" (NOT SET today) | Maintainer, one guideline at a time |
| L3 Fab profiles | `rules\fab-profiles\` (central) | What a fab can make, with source and date | JLCPCB 2-layer min trace/space | Maintainer, from the fab's published page |
| L4 User / company standard | `standards\<owner>\` (new, local; never pushed to central) | House style and preferences | Sheet size A3, silk 1.0 mm, preferred fab, preferred parts, block titles | The user |
| L5 Project | `projects\<name>\` requirements, constraints, schematic_standards | The numbers and choices of ONE design | 12 V in, 5 V 3 A out, AP63300 | The user, per project |

How they combine:
- L1 MUST lines are the floor. A lower layer can add to them, never remove them. A project may deviate only with a
  recorded, user-approved deviation (RQ-05).
- For values: L3 fab limits are hard limits. Inside them, L5 project beats L4 user standard beats L2 guideline default.
- The agent says which layer every number came from, in the gate evidence next to its source.

## 3. Is a piece of feedback general or specific to that user? The test
Ask these questions in order. The first "yes" decides.

| # | Question | If yes, it goes to |
|---|---|---|
| 1 | Is it about this design's requirements or one part choice ("use 4.99k here")? | L5 project only |
| 2 | Is it taste, house style or a company policy, with no source beyond "we prefer"? (sheet size, fonts, colors, naming, vendor choice) | L4 user standard |
| 3 | Is it a number that depends on the fab or assembly house? | L3 fab profile (if the fab publishes it), else L4 |
| 4 | Is it an engineering target with a source (datasheet, standard, app note, measurement) that holds for a class of circuit? | L2 guideline proposal |
| 5 | Is it about correctness, safety, manufacturability or tool behaviour that would bite any user of this toolchain? | L1 rule proposal |
| - | None of the above, or a one-off accident | lesson only (`docs\LESSONS_LEARNED.md`), no rule |

Extra conditions before anything goes to the central repo (L1, L2, L3):
- **Generalizable**: it can be written without this project's names, designators or values (values become parameters
  or sourced numbers).
- **Sourced**: it cites a datasheet page, standard, fab page, or reproduced tool behaviour. "The user said so" is
  enough for L4, never for L1 or L2.
- **Repeated or severe**: seen twice (WF-04 already says this), or once if it could damage hardware, cost a fab
  run, or corrupt files.
- **Checkable**: it names how it is checked: an existing script, a new script (then it starts CHECKLIST with a script
  planned), or a checklist step.
- **Not already covered**: no existing rule says the same thing (then the proposal edits that rule instead).
- **No private data**: no design files, no customer names, no PDFs, no personal paths (AI-CONTRIBUTOR.md rule 6).

## 4. The loop, step by step
1. **Capture (during design).** Every correction or suggestion the user gives is written at once to
   `projects\<name>\ai\feedback.md`, one entry per item:
   `F-<nn> | date | phase/gate | kind: defect / better option / preference | user's words | what the agent changed | evidence (file, capture, check output)`.
   The agent never edits rules here. It only records.
2. **Retro (at the end of every stage, section 4a).** When the user approves the end of a stage, the agent runs the retro:
   groups the F- entries, applies the test in section 3, and fills `rules\RETRO_TEMPLATE.md` (extended with a
   "layer" and "generalized wording" column). It checks for duplicates against `rules\00_INDEX.md`.
3. **User decision (local).** The agent shows the retro as a short table: each item with its proposed layer and
   wording. The user marks each one: accept / change layer / drop.
   - L5 and L4 items are applied right away (they are the user's own files).
   - L1, L2, L3 items become a proposal package.
4. **Proposal to the central repo.** One PR per topic, from the user's fork, in the house format (ID, MUST, Why,
   Check, Source, Status PROPOSED), with the anonymized evidence: what went wrong, the generalized rule, the source,
   how often it was seen. CI runs `rules_lint.py` and the selftest.
5. **Maintainer review.** The maintainer approves, edits or rejects. On approval: VERSION bump, CHANGELOG line with the
   approval date. Status goes PROPOSED -> CHECKLIST, and later -> ENFORCED when a checker script lands.
6. **Distribution.** Users pull the new version. Each project pins `rules_version` (WF-03), so a running design is not
   changed under it; the user upgrades a project on purpose, at a gate boundary.

## 4a. Feedback at every stage, not only at gates
The loop runs at the end of every design stage, and capture (step 1) runs all the time. A stage is the work between
two checkpoints; the five human gates are only some of them.

| Stage | Ends with | Retro point |
|---|---|---|
| 1 Requirements and architecture | user OK on requirements.md (planned gate G0) | yes |
| 2 Calculations and part selection | user OK on calcs.md and the part list | yes |
| 3 Library | G1 | yes |
| 4 Schematic | S1 | yes |
| 5 Layout | G2 | yes |
| 6 Analysis (thermal, PDN, SI, SPICE as the domain needs) | user OK on the analysis report | yes |
| 7 DRC and audit | G3 | yes |
| 8 Fab release | G4 | yes |
| 9 After the board is built (bring-up, measurements, rework) | user's bring-up notes | yes: the most valuable feedback |

A domain pack (section 4b) may add stages, for example "stackup and impedance" before layout for high-speed boards.
Each retro is short: only the entries since the last retro. Stage 9 feedback is the strongest evidence for L1/L2,
because it was measured on a real board.

## 4b. More domains without an unmanageable rule set
When power-electronics, high-speed, RF or server/computer designers join, one flat `rules\` folder would grow into
rules that most projects never need. Proposal:

- **Core plus domain packs.** `rules\core\` holds what every board needs (today's 01, 02, 03, 07, 08 and the general
  parts of 04, 05, 06). Each domain gets `rules\domains\<domain>\` with its own rule files, playbooks, guideline
  topics, checker scripts and any extra stages or gates. ID prefixes per domain (for example PWR-, HS-, RF-).
- **A project declares its domains** in `project.json` (`"domains": ["power"]`). The agent loads core plus only
  those packs, and only the files of the current stage (the phase table in `00_INDEX.md` already does this for
  stages). This keeps the agent's reading short however big the repo gets.
- **The layer test gets one more question.** Between questions 4 and 5 of section 3: "Does it hold only for one
  domain?" Then it goes to that domain pack, not to core.
- **Domain reviewers.** Each pack names who reviews its PRs (someone who designs in that domain). Core stays with
  the maintainer.

## 4c. The AI keeps the rule set manageable
Next to rule proposals, the agent proposes housekeeping, always as a PR the maintainer approves, never as a
direct edit. A `rules_health.py` report (an extension of `rules_lint.py`) gives it the evidence:
- **Too big**: a file or pack past a size limit -> propose a split. (The limit is NOT SET; the maintainer picks it.)
- **Overlap**: two rules that say nearly the same thing -> propose a merge.
- **Wrong home**: a core rule that only domain projects ever trigger -> propose a move to that pack; a rule that
  several packs copy -> propose a move to core.
- **Never used**: a rule that no check and no feedback has touched over a number of projects -> propose retiring it.
  (The number is NOT SET.)
- **Often broken CHECKLIST rule** -> propose a checker script so it becomes ENFORCED.
- **Old SEED or PROPOSED** -> remind the maintainer to decide.
- **Conflicts** between a domain pack and core, or between two packs -> flag for the maintainer.
IDs are never reused. A moved or merged rule keeps its old ID as an alias in the index, so old projects, lessons and
feedback entries still resolve. A structure change bumps the minor version; projects pinned to the old version
keep working.

## 5. What to build (each item is its own small PR, after approval of this proposal)
| # | Piece | Type |
|---|---|---|
| 1 | Rule WF-08 "Capture feedback" and WF-09 "Retro after each stage" (text below), status PROPOSED | rule |
| 2 | `templates\project\ai\feedback.md` and an extended `rules\RETRO_TEMPLATE.md` (layer + generalized wording columns) | template |
| 3 | `standards\` folder with `README.md` and a `TEMPLATE.md` for a user/company standard (L4); `.gitignore` keeps `standards\*` local except the README and template | folder |
| 4 | `feedback_triage.py`: reads feedback.md, finds duplicates against the rule index (by keywords and IDs), drafts the retro table; never decides the layer on its own | script + test |
| 5 | A `rule-feedback` skill (retro and proposal steps; cites WF-08, WF-09, this file). Drafted in `docs\templates\`; the user copies it into `.claude\skills\` (Claude may not edit `.claude\`) | skill |
| 6 | Move the user-specific parts of today's rules to L4 or L5 (see section 6); each move is a rule change the maintainer approves | rule review |
| 7 | `rules\core\` + `rules\domains\` layout, `domains` key in project.json, loader and index support; first pack: `power` (from the buck work) | structure |
| 8 | `rules_health.py` housekeeping report (section 4c) | script + test |

Draft rule text (PROPOSED):
- **WF-08 Capture feedback.** MUST: write every user correction or suggestion to `ai\feedback.md` when it is given,
  with phase, kind, the user's words, the change made and the evidence. MUST NOT change any rule, guideline or
  standard file at that moment. Why: feedback is the raw material for better rules; lost feedback is repeated work.
  Check: gate_check.py lists feedback entries with no retro decision (planned).
- **WF-09 Retro after each stage.** MUST: when the user approves the end of a stage (section 4a), classify each new feedback entry with the
  layer test (FEEDBACK_TO_RULES.md section 3), show the table, and apply only what the user accepts. Central
  proposals are PRs in the house format, never direct edits of `rules\`. Why: rules grow from evidence, with the
  user in control. Check: checklist (retro file per gate in `ai\review\`).

## 6. Going through the existing rules, step by step
One rule file per session, in this order: 01, 02, 03, 04, 07, 08, 05, 06 (05 and 06 last: they are mostly SEED and
will be rewritten in roadmap M3 and M5). For each rule we decide together:
1. **Layer**: L1 core, or should it move to L2 / L3 / L4 / L5?
2. **Still right?** Keep, reword, split, merge or retire.
3. **Status and check**: can a CHECKLIST rule become ENFORCED, and with which script?
4. **Source**: is the source good enough for L1?

First-pass observations, to be confirmed in those sessions (not decisions):
- 01, 02, 03, 07: almost all L1 (process, datasheet discipline, library checks, Altium tool behaviour).
  RQ-06 and RQ-07 carry design numbers and are already flagged as L2 candidates (ROADMAP "Open").
- 04 Schematic: the checks (grid, overlaps, dots, connectivity) are L1. Several details came from one user's S1 brief
  and look like L4 house style: whole A3 sheet, five titled blocks, about 8 parts per block, grouped value text,
  one GND symbol per cluster. The template `schematic_standards.md` also names buck-specific blocks (L5).
- 05 PCB: SEED, all from one board. Fab numbers belong in L3; silk size and via tenting choices look L4 unless a
  source makes them L1. The 8 items in `projects\buck-12v-5v-3a\ai\RULE_PROPOSALS.md` go through the section 3
  test first.
- 06 Fab: FAB-04 (JLCPCB BOM columns) is fab-specific, so L3, not L1.
- 08 Communication: L1 for the agent's honesty duties (COM-01 evidence); report style (COM-02) could be L4.

## 7. Decisions needed from the maintainer
1. Approve the five layers and the precedence in section 2?
2. Approve the layer test and the central-repo conditions in section 3?
3. Location and privacy of L4: `standards\<owner>\`, local only (git-ignored), or its own private repo?
4. Should WF-08 and WF-09 enter as PROPOSED now?
5. Start the rule-by-rule review with 01_WORKFLOW_GATES?
6. Approve retros at every stage (section 4a), including stage 9 after the board is built?
7. Approve core plus domain packs (section 4b)? Which domains first after `power`?
8. Approve AI housekeeping proposals (section 4c), and set the size and "never used" limits?
