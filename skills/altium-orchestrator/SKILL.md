---
name: altium-orchestrator
description: Decide the next step in an Altium board project built on altium-claude-kit; use at the start of every session in a project folder that has project.yaml.
---

## Goal
Pick the next valid task from `project.yaml` and hand it to the right phase skill, loading as little as possible.

## Inputs
- `project.yaml`, last 10 lines of `decisions.md`. Nothing else until a phase skill asks for it.

## Phase order and skills
requirements → architecture → component-selection → library-cad → schematic-design → schematic-review →
pcb-setup → placement → routing → analysis → silkscreen-dfm → fab-release.
Skill name = `altium-<phase>`. If that skill is not installed yet, say so, do the phase with the kit
`CLAUDE.md` principles and the phase's rule files, and note it in `decisions.md`.

## Approach
1. Open issues first: an open issue's `phase` is where work resumes, even if `phase` is later.
2. A failed or `invalidated` check sends work back to the phase that owns it; mark checks of later phases that depend on the change as `invalidated`.
3. Before moving past a gate with `required: true`, stop with a ≤10-line summary for approval.
4. If the user asks for something specific, do that, then re-check what it invalidated.

## Write back
`project.yaml`: phase, next_action. Nothing else unless a phase skill ran.

## Escalate when
A gate is reached, a requirement cannot be met, or a needed tool in `tools:` is missing.
