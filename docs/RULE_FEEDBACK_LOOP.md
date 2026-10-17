# Design feedback → rules: the loop

People design with the kit; their AI agents follow the rules. When the user corrects the agent, suggests a better
option, or approves the work, that feedback is the raw material for better rules. This loop turns it into rules,
guidelines and user standards without letting one person's taste leak into the central repo. Layers and the
"general or specific" test: [DESIGN_STANDARDS.md](DESIGN_STANDARDS.md). Skill: `altium-rule-harvest`.

```
 design ──► user feedback ──► ai/feedback.jsonl ──► gate approved ──► harvest ──► user sorts each item
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

## 2. Harvest (when the user ticks a gate)
After a gate is signed off, the agent runs the `altium-rule-harvest` skill. It:
1. Reads `ai/feedback.jsonl` for that gate, and the earlier harvests of this project.
2. Groups lines that are the same problem.
3. For each group, decides which case it is:
   - **Rule existed and was not followed** → the fix is a better check or a clearer skill, not a new rule.
   - **Project only** (cause `requirement`) → nothing to harvest; it already lives in `requirements.md`.
   - **User standard** (cause `house-style`, `policy`, `equipment`, `preference`) → a line for `standards/local/<name>.md`.
   - **Central candidate** (cause `physics`, `standard`, `datasheet`, `fab`, `tool`, `process`, and passes the five tests) →
     a generalised rule or guideline in house format, Status PROPOSED, with the source and a check idea.
4. Writes `ai/review/harvest_<gate>.md` (one table, one row per group) and asks the user to sort each row:
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

## 5. Measure
Per rules version and per phase: feedback lines per project, corrections vs improvements, and how many came from a rule
that already existed. The goal is fewer corrections per board with every release.
