# Architecture

How the kit is organised and why. Status of each piece: [ROADMAP.md](ROADMAP.md).

## Goal
Let Claude carry an embedded board from requirements to fab files in Altium Designer with few human corrections and
low token use, while a human keeps control at gates. Target: Altium Designer 26, and the two previous major versions
once someone tests them.

## Layers (each concern lives in one place)

| Layer | Folder | Owns | Changed by |
|---|---|---|---|
| Agent contract | `CLAUDE.md` | non-negotiables, MCP routing, where to look | maintainer |
| Rules | `rules/` | HOW we work: MUST, Why, Check, Source, Status; versioned | reviewed PR (WF-04) |
| Playbooks | `rules/playbooks/` | tested step lists for recurring tasks | reviewed PR |
| Skills | `.claude/skills/` | per-phase entry points: goal, what to load, how to judge | reviewed PR |
| Guidelines | `guidelines/` | WHAT a good design needs (system-level limits), draft | maintainer approves each |
| User standards | `standards/local/` (git-ignored) | one user's or company's house style and policies | that user (docs/DESIGN_STANDARDS.md) |
| Checkers and generators | `tools/scripts/` | anything deterministic: checks, calcs, plans, BOM | PR with tests |
| Altium bridge | `tools/bridge/`, hook | one live script engine, kill switch, popups | PR tested on real Altium |
| Global library | `library/` | catalog, category libraries, revisions, hashes | `lib_promote.py` after G1 |
| Component facts | `library/facts/` (planned M1) | datasheet facts per catalog part, with page refs | ingest + review |
| Projects | `projects/<name>/` (git-ignored) | one design, its own git repo, local library copies | the designer |

Rules say how to work, guidelines say what good looks like, the project says the numbers for one board.
Skills point to rules by ID and never copy them.

## Design flow and gates

| Phase | Rules | Playbook | Gate (only the user ticks) |
|---|---|---|---|
| Requirements, architecture | 01, 02, `guidelines/` | P1 | (planned: G0 requirements) |
| Calculations, part choice | 02 | P1, P2 | |
| Library (symbols, footprints, 3D) | 03, 07 | P2, P4 | G1 footprints |
| Schematic | 04, 07 | P3 | S1 schematic readability |
| PCB setup, placement, routing | 05, 07 | P5 | G2 layout |
| DRC, audit, analysis | 05, 06 | P6 | G3 DRC and audit |
| Fab output | 06 | P6 | G4 Gerbers |

Every gate needs an evidence pack from `gate_check.py` (WF-02). A failed check returns work to the phase that owns it.

## Three MCP servers

| Server | Source | Use |
|---|---|---|
| `altium-lib` | embedded-society/altium-designer-mcp | offline SchLib/PcbLib read, write, validate |
| `altium-coffee` | coffeenmusic/altium-mcp | live PCB: placement, rules, screenshots, output jobs |
| `altium-eda` | salitronic/eda-agent | live schematic, review, audit, SPICE |

Only one live bridge at a time (TOOL-01). The guard hook enforces it.

## Component facts database (planned, roadmap M1)

Problem: RQ-01 makes Claude open the datasheet PDF for every number, in every project. That is the biggest token cost.

Design:
- One file per catalog part: `library/facts/<catalog id>.json`. Standard-library JSON, like every other workspace file.
- Sections match phases so a query returns only what a phase needs: `selection`, `abs_max`, `recommended`, `pins`,
  `application`, `layout`, `thermal`, `package`.
- Every value: `{"value"|"min"|"typ"|"max", "unit", "ref": "p12 table 7.5", "cond"}`. Abs max never mixed with recommended.
- `status`: `extracted_unreviewed` → `verified` (a human checked pins, abs max and package against the cited pages).
- The datasheet sha256 in the catalog ties every fact to one PDF revision.
- Script `facts.py`: `get <id> --section pins`, `check` (schema, units, refs, pin count = catalog footprint pads),
  `draft <id>` (extract a first draft from the PDF for review).
- Projects read facts from the global DB by catalog id and revision recorded in `lib_manifest.json`.

Rule change this needs (PROPOSED, the user approves through WF-04): RQ-01 accepts a number from a `verified` facts
entry, because the entry cites the page and the PDF hash; the PDF is opened only for a missing or disputed field.

## Token discipline
1. Start from `PROJECT.md` and `gates.md`, not from chat history.
2. One skill, one rule-file set, one playbook per phase (`rules/00_INDEX.md` "Read before each phase").
3. Facts by section, not PDFs.
4. Scripts print PASS/FAIL summaries; full output goes to `ai/review/`.
5. A correction made twice becomes a rule or a check (WF-04), not a longer prompt. Feedback is logged and harvested at each gate (WF-08, docs/RULE_FEEDBACK_LOOP.md).

## Contributions
Humans and their AI assistants contribute the same way: one topic per PR, evidence for every value, checks pass.
See [../CONTRIBUTING.md](../CONTRIBUTING.md) and [AI-CONTRIBUTOR.md](AI-CONTRIBUTOR.md).
