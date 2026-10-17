---
name: altium-<phase>
description: <One sentence: what this phase produces and when to use it, e.g. "Place components on the PCB; use when project.yaml phase is placement.">
---
<!-- Target ≤80 lines. Say what to achieve and how to judge it, not a click-by-click script.
     Never copy rule text here: cite rule IDs. -->

## Goal
<2–3 lines: the outcome of this phase.>

## Inputs
- `project.yaml` (phase, fab_profile, tools)
- <files from earlier phases>
- `comp get <MPN> --section <section>` for parts in scope

## Rules to load
- `rules/<topic>.md`
- `rules/fab-profiles/<fab_profile>.yaml`

## Approach
<Priorities and judgment calls. What to decide first and why. Trade-offs to weigh.>

## Exit checks
| Check | How | Pass when |
|---|---|---|
| <id> | <script or review item> | <measurable condition> |

## Write back
- `project.yaml`: checks, issues, phase, next_action
- `decisions.md`: one line per decision
- `reports/<phase>.md`: ≤30-line summary; raw logs in `reports/raw/`

## Escalate when
<What breaks a gate, a rule or a requirement and needs a human.>
