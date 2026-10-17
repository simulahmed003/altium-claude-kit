# Design feedback → rules: the loop

People design with the kit; their AI agents follow the rules. When the user corrects the agent, suggests a better
option, or approves the work, that feedback is the raw material for better rules. This loop turns it into rules,
guidelines and user standards without letting one person's taste leak into the central repo. Layers and the
"general or specific" test: [DESIGN_STANDARDS.md](DESIGN_STANDARDS.md). Skill: `altium-rule-harvest`.

```
 design stage ──► user feedback ──► ai/feedback.jsonl ──► stage done ──► harvest ──► user sorts each item
                                                                                   │
                       ┌─────────────────────────┬──────────────────────┬─────────┴────────────┐
                       ▼                         ▼                      ▼                      ▼
                   project only            user standard        central candidate         drop / check fix
              (requirements.md)      (standards/local/)        (PR to central repo)    (rule existed: improve
                                                                       │                 its check or skill)
                                                                       ▼
                                                     maintainer + AI review ──► PROPOSED ──► ENFORCED when a check exists
```

## 1. Capture (during design, every phase)
Every time the user corrects the agent, rejects an option, or picks a better one, the agent appends one line to
`projects/<name>/ai/feedback.jsonl` before it continues (proposed rule WF-08). It records what the user said, not a judgement.

| Field | Meaning |
|---|---|
| `date`, `phase`, `gate` | when, and the gate the work belonged to (G1, S1, G2, G3, G4) |
| `kind` | `correction` (something was wrong), `improvement` (it worked, a better option exists), `preference`, `approval` |
| `what` | what the agent did, in one line |
| `feedback` | what the user said or changed, in one line |
| `fix` | what was done about it |
| `rules` | rule or guideline IDs involved, or `[]` if none covered it |
| `cause` | `physics`, `standard`, `datasheet`, `fab`, `tool`, `process`, `house-style`, `policy`, `equipment`, `preference`, `requirement` |
| `evidence` | a file under `ai/review/`, a capture, or a checker output |

The agent proposes the `cause`; the user can change it at harvest. Example: `templates/project/ai/feedback.example.jsonl`.

## 2. Harvest (at the end of every design stage)
Feedback comes in every stage, not only at gates: requirements, architecture, calculations, part choice, library,
schematic, placement, routing, analysis and fab output, and after the board is built (bring-up, measurements,
rework). Feedback from the built board weighs most, because it was measured on real hardware. So the agent runs the `altium-rule-harvest` skill when a stage
ends: when the user ticks its gate, or, for a stage with no gate, when the user accepts its result. A small harvest
per stage is quicker for the user to sort and keeps the context fresh. The skill:
1. Reads `ai/feedback.jsonl` for that stage, and the earlier harvests of this project.
2. Groups lines that are the same problem.
3. For each group, decides which case it is:
   - **Rule existed and was not followed** → the fix is a better check or a clearer skill, not a new rule.
   - **Project only** (cause `requirement`) → nothing to harvest; it already lives in `requirements.md`.
   - **User standard** (cause `house-style`, `policy`, `equipment`, `preference`) → a line for `standards/local/<name>.md`.
   - **Central candidate** (cause `physics`, `standard`, `datasheet`, `fab`, `tool`, `process`, and passes the five tests) →
     a generalised rule or guideline in house format, Status PROPOSED, with the source and a check idea.
4. Writes `ai/review/harvest_<stage>.md` (one table, one row per group) and asks the user to sort each row:
   **central / mine / project / drop**. Nothing is written anywhere else before that.

## 3. Apply (after the user sorts)
- **mine** → the agent adds the line to `standards/local/<name>.md`. It binds that user's next projects.
- **central** → the agent prepares one contribution per topic in the user's clone (branch, rule text, evidence summary
  with no designs, customer names or paths). Opening the PR to the central repo is outward, so it waits for the user's yes.
- **drop** → recorded in the harvest file so it is not proposed again.

## 4. Review in the central repo (maintainer + AI)
1. Duplicate or conflict with an existing rule? Merge into that rule instead.
2. Source checked? Values without a source are removed or stay NOT SET.
3. Evidence: one project = PROPOSED; two projects or two users, or a cited standard = can be approved.
4. Approved → status CHECKLIST, `rules/VERSION` and `CHANGELOG.md` bumped (WF-04). It becomes ENFORCED only when a
   checker script exists and names it.
5. Users get it by pulling the kit; each project keeps the rules version it started with (WF-03) until it chooses to move.

## 5. Keeping the rules manageable as more fields join
Today the rules cover one kind of board (a small 2-layer power board). When power-electronics, high-speed or server
designers join, the rules would grow past what an agent can load per stage. Three mechanisms keep them small:

1. **Core plus domain packs.** `rules/` keeps only what every board needs (gates, evidence, library, schematic basics,
   tooling). Field-specific rules go in a domain pack, `rules/domains/<domain>/`, with its own ID prefix
   (for example `PWR-`, `HS-`, `SRV-`) and its own guidelines. A project lists its domains in `project.json`
   (`"domains": ["power"]`), and the agent loads only core plus those packs. A rule moves from a pack to core only
   when two or more packs need it.
2. **Stages per domain.** A domain pack may add stages and checks (for example impedance and length matching for
   high-speed, creepage and thermal for power). It adds them to the stage table in its own README; the core gates stay.
3. **The harvest also proposes upkeep.** Each harvest ends with a "rules health" row, as a proposal the user sorts like the rest:
   - a rule file over the size limit (`rules_lint.py` warns above 20 rules per file): split it or move rules to a pack
   - duplicate or overlapping rules: merge them
   - a CHECKLIST rule a script could check: name the script to write
   - a rule nobody has needed in several projects: retire it, or move it to a pack
   - a PROPOSED rule with no new evidence after several projects: drop it

IDs are never reused. A rule that is moved or merged keeps its old ID as an alias, so older projects still resolve.

The limits (rules per file, how many projects without use before a rule is retired) are the maintainer's decision.
`rules_lint.py` starts with 20 rules per file as a warning only, until the maintainer sets the number.

Domain packs are created when the first contributor from that field arrives. Until then everything stays in core.
Each pack gets a maintainer from that field (CODEOWNERS), and the core maintainer approves changes to core.

## 6. Measure
Per rules version and per phase: feedback lines per project, corrections vs improvements, and how many came from a rule
that already existed. The goal is fewer corrections per board with every release.
