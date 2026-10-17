---
name: altium-orchestrator
description: Pick the next step in an Altium board project under projects/<name>/; use at the start of a design session or when unsure which phase, rules or playbook apply.
---

## Goal
Find the next valid task for the project and load only what that task needs.

## Read first (nothing else yet)
- `projects/<name>/PROJECT.md`: pending lines and the latest decisions (rule WF-07: pending items first).
- `projects/<name>/gates.md`: which gates are ticked.
- `projects/<name>/project.json`: rules version, fab profile.

## Phase from gate state
| Ticked so far | Current work | Rules + playbook (see `_rules/00_INDEX.md`) |
|---|---|---|
| none, no requirements | requirements, calcs, parts | 01, 02, 08; P1, P2 |
| none, parts chosen | library | 03, 07; P2, P4 → present G1 |
| G1 | schematic | 04, 07; P3 → present S1 |
| G1, S1 | PCB layout | 05, 07; P5 → present G2 |
| G1, S1, G2 | DRC and audit | 05, 06; P6 → present G3 |
| G1, S1, G2, G3 | fab output | 06; P6 → present G4 |
Altium stuck at any point: 07 and P8.

## Approach
1. Pending items and failed checks come before new work. A failed check goes back to the phase that owns it.
2. Load one rule-file set and one playbook. Do not read the other rule files.
3. Before presenting a gate, run `gate_check.py <gate>` (playbook P6). Only the user ticks a gate (WF-01).
4. If a phase-specific skill exists in `.claude/skills/`, use it instead of the table above.

## Write back
Decisions and open issues in `PROJECT.md` at the end of the session (CLAUDE.md non-negotiable 9).

## Escalate when
A gate is reached, a requirement or rule cannot be met (RQ-05), or a tool is blocked (COM-05).
