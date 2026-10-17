# Instructions for an AI assistant contributing to altium-claude-kit

Give this file to your AI (Claude or any other) before it writes a contribution. Read `CONTRIBUTING.md` too.

## Your job
Make one focused change (a rule, a checker, a skill, a library part, a fab profile or a doc fix) that the maintainer
can review in a few minutes. Do not restructure folders or touch unrelated files.

## Hard rules
1. **Never invent values.** Every device number cites a datasheet page; every fab number cites the fab's page and the date checked. If you cannot read the source, leave the value out and say so in the PR.
2. **Rules use the house format**: ID, MUST / MUST NOT, Why, Check, Source, Status. A new rule is `PROPOSED`. Run `python _tools/scripts/rules_lint.py --write-index`.
3. **Skills cite rule IDs and playbooks**; they never copy rule text. Use `docs/templates/SKILL_TEMPLATE.md`, ≤ 80 lines.
4. **Scripts**: Python standard library only, `--help`, exit 0 = PASS / 1 = FAIL, a test in `_tools/tests/`, no project constants in code.
5. **Do not edit** `_tools/bridge/`, the hook or the kill switch unless the PR says how it was tested on a real Altium install.
6. **No PDFs, no designs, no personal paths or keys** in the diff. Library parts only through `lib_promote.py` after the design's G1.
7. **Units always explicit.** Abs max and recommended operating conditions are never mixed.

## Before you finish
Run `python _tools/selftest.py` and fix every FAIL. In the PR description write: what changed, the sources used,
what you could not verify, and that it was AI-assisted (name the model).
