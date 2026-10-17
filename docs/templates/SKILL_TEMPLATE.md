---
name: altium-<phase>
description: <One sentence: what this phase produces and when to use it, e.g. "Place components on the PCB; use after gate S1 is ticked.">
---
<!-- Target ≤80 lines. Say what to achieve and how to judge it, not a click-by-click script.
     Never copy rule text here: cite rule IDs. -->

## Goal
<2–3 lines: the outcome of this phase.>

## Inputs
- `projects/<name>/PROJECT.md`, `gates.md`, `project.json`
- <files from earlier phases, e.g. ai/plan.json>
- part facts for the parts in scope (component facts DB, roadmap M1)

## Rules to load
- `_rules/0X_<TOPIC>.md` (cite IDs)
- playbook `_rules/playbooks/PX_*.md`
- fab profile from `project.json`

## Approach
<Priorities and judgment calls. What to decide first and why. Trade-offs to weigh.>

## Exit checks
| Check | How | Pass when |
|---|---|---|
| <rule ID> | <script in _tools/scripts, or checklist> | <measurable condition> |

## Write back
- `PROJECT.md`: decisions and open issues
- `ai/review/`: evidence (gate_check.py)
- `calcs.md`: calculation results (RQ-02)

## Escalate when
<What breaks a gate, a rule or a requirement and needs a human.>
