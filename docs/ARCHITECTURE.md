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
| Component database | `library/parts/` (M1) | one record per orderable part, datasheet facts with page + quote | parts.py + extractor + review |
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

## Component database (roadmap M1, built 2026-10-17)

Problem: opening the datasheet PDF for every number, in every project, was the biggest token cost. Since rules 1.2.0, RQ-01 reads the part record first.

Design (details and workflow: `library/parts/README.md`):
- One record per orderable part: `library/parts/<category>/<family>/<MPN>__<mfr>.json`, keyed by manufacturer part
  number, so candidates that never reach the Altium library keep their facts too. Catalog components link by `catalog_ids`.
- `taxonomy.json` holds the category tree, the required facts per family and the unit of every fact key;
  `manufacturers.json` the canonical maker names. Field names and units only, no values.
- Sections match phases so a query returns only what a phase needs: summary, abs_max, recommended, electrical,
  thermal, package, compliance, ordering; pins; notes for application, layout, software, handling.
- Every value: `{min|typ|max|value, unit, cond, ref: {page, quote, mode}}`. `parts.py check` finds each quote on its
  page of the PDF text (three pdftotext modes), so an invented number fails. Values the text layer lacks are read
  from the page image and marked `visual` for a person to confirm.
- `review.status`: draft -> extracted -> checked -> verified (a person checked pins, abs max and package).
- `datasheets/index.json` (in git) ties each record to one PDF revision by sha256; PDFs and page text stay local.
- Price and stock are dated local snapshots (`parts.py market`), checked at BOM time (RQ-04).

RQ-01 (rules 1.2.0, approved by the user 2026-10-17): numbers come from the record, which cites the page, a quote and
the PDF hash. A missing part or fact is fetched and extracted into the record first; a flaw stops the work and goes to
the user. The PDF is opened only to extract, to verify, or for a disputed field.

## Token discipline
1. Start from `PROJECT.md` and `gates.md`, not from chat history.
2. One skill, one rule-file set, one playbook per phase (`rules/00_INDEX.md` "Read before each phase").
3. Facts by section, not PDFs.
4. Scripts print PASS/FAIL summaries; full output goes to `ai/review/`.
5. A correction made twice becomes a rule or a check (WF-04), not a longer prompt. Feedback is logged and harvested at each gate (WF-08, docs/RULE_FEEDBACK_LOOP.md).

## Contributions
Humans and their AI assistants contribute the same way: one topic per PR, evidence for every value, checks pass.
See [../CONTRIBUTING.md](../CONTRIBUTING.md) and [AI-CONTRIBUTOR.md](AI-CONTRIBUTOR.md).
