# Instructions for an AI assistant contributing to altium-claude-kit

Give this file to your AI (Claude, or any other) before it writes a contribution. It is short on purpose.

## Your job
Produce one focused change (one part, one rule file edit, one skill, or one tool) that a maintainer can review
in a few minutes. Do not restructure the repository or touch unrelated files.

## Hard rules
1. **Never invent data.** Every value in `part.yaml` needs `ref:` pointing to a datasheet page/table/figure you actually read. If you cannot read it, leave the field out and list it under `gaps:`.
2. **Keep absolute maximum and recommended operating conditions separate.**
3. **Units always explicit**, as `{value: X, unit: U}`, with `cond:` for test conditions when the datasheet gives them.
4. **New parts are `status: extracted_unreviewed`.** Only a human reviewer sets `verified`.
5. **Do not copy rule text into skills.** Cite the rule ID (`PL-03`).
6. **No PDFs, no CAD with a non-redistributable licence.** Record the source URL and SHA-256 in `source.yaml` instead.
7. **Stay small.** `SKILL.md` ≤ ~80 lines; `digest.md` ≤ 150 lines; tools print ≤ 15 lines and write logs to a file.

## Formats to follow
- Part: copy `components/_template/`; schema in `components/_schema/part.schema.json`.
- Skill: copy `skills/_template/SKILL.md`.
- Rule: `rules/_template.md`.

## Before you finish
Run `python tools/comp/comp.py validate --all` and fix every error. Then write the PR description:
what changed, which pages or sources you used, what you could not verify, and that it was AI-assisted (name the model).
