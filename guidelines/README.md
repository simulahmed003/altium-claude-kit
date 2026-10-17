# System-level design guidelines - DRAFT, EMPTY ON PURPOSE

Status: draft, created 2026-10-13. The user fills this in later. Nothing here is binding until the user approves it.
For Claude: do not invent values, do not apply a guideline that is not APPROVED, do not move rules into this folder.

## Objective
Automate the work an engineer does by hand in the tools. A guideline earns its place only when a script can apply it:
calculate it, check it, or show it in the gate evidence. So every guideline says how it is automated ("Automated by").
If no script exists yet, the topic is an automation candidate in BACKLOG.md.

## How this differs from the rules
| | `rules\` | `guidelines\` (this folder) | Project `requirements.md`, `constraints.md` |
|---|---|---|---|
| Holds | HOW we work: gates, tool use, file formats, checks | WHAT a good design needs: system-level limits and targets | The numbers of ONE project |
| Example | "Only the user ticks a gate" | "Inductor ripple current allowance" (value NOT SET) | "12 V in, 3 A out" |
| Today | in force, versioned (`rules\VERSION`) | empty, no value set | per project |
| Changed by | the user approves (rule WF-04) | the user sets and approves, one guideline at a time | the user, per project |

A project can take a guideline as its default, or deviate from it with the user's approval (rule RQ-05).
`rules_lint.py` and the rule index do not read this folder.

## Working method (proposal - the user approves it first)
1. No invented values. A value needs a source: datasheet, standard, fab profile, or a dated user decision. Otherwise it stays NOT SET.
2. One topic per file, written from TEMPLATE.md. IDs are `G-<AREA>-<NN>`.
3. The user approves one guideline at a time. Only then Status becomes APPROVED, with the date.
4. Each guideline names how it is automated: a `calclib.py` function, a checker script, or "none yet" (then it is listed in BACKLOG.md).
5. Every change goes in CHANGELOG.md.
6. Idea for later, not built: once guidelines are APPROVED, `calcs_run.py` and `gate_check.py` can read them, so the gate evidence
   shows which guideline each number was judged against.

## Files
| File | Purpose |
|---|---|
| TEMPLATE.md | block to copy for a new guideline, with one example that has no value |
| BACKLOG.md | candidate topics by area: names only, no values |
| CHANGELOG.md | history of this folder |
