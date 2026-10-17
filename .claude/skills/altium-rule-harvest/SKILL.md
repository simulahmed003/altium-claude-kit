---
name: altium-rule-harvest
description: Turn the user's design feedback from a project into rule, guideline and user-standard proposals; use right after the user ticks a gate, or when asked what the kit should learn from a design.
---

## Goal
Sort every piece of user feedback from one gate into: better check, project only, user standard, or central
candidate. Write the proposals; change nothing until the user has sorted them.

## Inputs
- `projects/<name>/ai/feedback.jsonl` (lines for this gate; WF-08 PROPOSED)
- `projects/<name>/ai/review/harvest_*.md` (earlier harvests: do not propose a dropped item again)
- `projects/<name>/project.json` (`standard`, `rules_version`), `PROJECT.md`
- the user standard named in `project.json`, if any

## Rules to load
- `rules/01_WORKFLOW_GATES.md` (WF-04 rule changes, WF-08 feedback log)
- `docs/DESIGN_STANDARDS.md` (layers, the five tests for "general")
- `docs/RULE_FEEDBACK_LOOP.md` (the loop)
- `rules/00_INDEX.md` and `guidelines/` to find existing rules before proposing new ones

## Approach
1. Group feedback lines that describe the same problem. One group = one row.
2. Search the existing rules and guidelines first. If one covers it, the row is "check fix": say which check or
   skill missed it and how a script could catch it next time.
3. Use the `cause` to choose the layer (DESIGN_STANDARDS.md). When unsure between user standard and central, choose
   user standard: it is cheap to promote later and costly to push one person's taste to everyone.
4. Central candidates must pass the five tests. Rewrite them in house format (ID, MUST, Why, Check, Source, Status
   PROPOSED) with project numbers removed. Never invent a value or a source; write NOT SET and say what is missing.
5. Write `ai/review/harvest_<gate>.md`, one table:
   | # | Feedback lines | Case | Proposed text | Source | Evidence | Your call |
   Leave "Your call" empty, then ask the user to fill each row: central / mine / project / drop.

## Exit checks
| Check | How | Pass when |
|---|---|---|
| every feedback line of the gate is in a row | count lines vs rows | none missing |
| central rows pass the five tests | DESIGN_STANDARDS.md | source, reach, evidence, checkable, no project data |
| new rule text is valid | `python tools/scripts/rules_lint.py` on a scratch copy | exit 0 |

## Write back (only after the user sorted the rows)
- **mine** → `standards/local/<name>.md`, from `standards/TEMPLATE.md`
- **central** → a branch in the user's clone with the rule or guideline (PROPOSED) and an evidence summary with no designs,
  customer names or paths. Ask before opening the PR (it is outward).
- **check fix** → an entry in `docs/LESSONS_LEARNED.md` and, if the user agrees, a checker task
- `PROJECT.md`: one line per decision; the harvest file keeps the "Your call" column as the record

## Escalate when
Feedback conflicts with a rule (the user may want the rule changed: WF-04), or a proposal would loosen a fab-profile limit.
