# Skills

Claude Code loads every skill in this folder automatically when it is started from the repo folder.
A skill is a short entry point for one phase: its goal, what to read, how to judge the result. It cites rule IDs
and playbooks; it never copies rule text. Template: `docs/templates/SKILL_TEMPLATE.md` (target ≤ 80 lines).

| Skill | Status |
|---|---|
| altium-orchestrator | draft |
| altium-component-intake | draft: numbers from the component database; first-time parts: fetch, extract, check (RQ-01) |
| altium-rule-harvest | draft: design feedback → rule, guideline and user-standard proposals (docs/RULE_FEEDBACK_LOOP.md) |
| phase skills (requirements, architecture, part selection, library, schematic, layout, analysis, fab) | planned, see `docs/ROADMAP.md` |
