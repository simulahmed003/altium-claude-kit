# Documentation index

| Topic | File |
|---|---|
| Overview, requirements, quick start | ../README.md |
| Full setup guide, update, troubleshooting | SETUP.md |
| First-run tests of the bridge and kill switch | FIRST_RUN_TESTS.md |
| Contribute, fork, stay in sync | ../CONTRIBUTING.md |
| Workspace rules for the agent (non-negotiables, tools, phases) | ../CLAUDE.md |
| Rules (99, versioned), read-before-phase table, status counts | ../rules/00_INDEX.md |
| Rule files | ../rules/01_WORKFLOW_GATES.md ... 08_COMMUNICATION.md |
| Rule changes and versions | ../rules/CHANGELOG.md, ../rules/VERSION, ../rules/RETRO_TEMPLATE.md |
| System-level design guidelines (DRAFT, empty by design, separate from the rules; the user sets them later) | ../guidelines/README.md |
| Playbooks P1-P12 (TESTED / UNTESTED per step) | ../rules/playbooks/README.md |
| Offline scripts (checkers, generators, gate evidence) | ../tools/scripts/README.md |
| Tools guide for the user: cmd.exe commands per task, `kit.cmd` launcher, proposed next tools | TOOLS_GUIDE.md |
| Script tests and fixtures | ../tools/tests/ (run ../tools/selftest.py) |
| Fab profile (JLCPCB 2-layer, source + date) | ../rules/fab-profiles/jlcpcb_2layer.json |
| JLCPCB assembly: CPL side rule, observed assembly rates | ../rules/fab-profiles/jlcpcb_assembly.json |
| Global library, catalog, principles | ../library/README.md, ../library/catalog/components.md |
| Project template | ../templates/project/ |
| Lessons from the buck project | LESSONS_LEARNED.md |
| Architecture: layers, flow, facts database | ARCHITECTURE.md |
| Roadmap: done, next, how modules are built | ROADMAP.md |
| Design standards: rules, guidelines, fab profile, user standard, project; what is general vs user-specific | DESIGN_STANDARDS.md |
| Design feedback → rules loop (WF-08, skill altium-rule-harvest) | RULE_FEEDBACK_LOOP.md |
| Instructions for AI assistants that contribute | AI-CONTRIBUTOR.md |
| Phase skills (loaded by Claude Code) | ../.claude/skills/README.md |
| Skill template | templates/SKILL_TEMPLATE.md |
| Bridge / MCP log | ../logs/MCP_LOG.md (local, not in git) |
| Workspace phase progress | ../logs/WORKSPACE_PROGRESS.md (local, not in git) |
