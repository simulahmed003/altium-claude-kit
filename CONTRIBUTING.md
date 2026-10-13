# Contributing

This repo holds the **process**: rules, playbooks, checkers, the guard, the managed global library and the project template.
It does not hold designs, vendor datasheet PDFs, logs, personal paths, keys or machine-specific config.
Do not commit: `projects/`, `.mcp.json`, `.claude/settings.json`, `_logs/`, `*.pdf`.

## Use it for your own work (fork)
1. Fork on GitHub and clone your fork (see `docs/SETUP.md`).
2. Do your designs in `projects/<name>/`, each with its own `git init`. They never enter this repo.
3. Improve rules, scripts and the library in your fork as you learn from your designs.
4. Stay in sync: `git remote add upstream <original repo url>`, then `git fetch upstream` and merge or rebase.
5. Send the improvements that help everyone back as pull requests.

## Before a pull request
- `python _tools\selftest.py` passes on a fresh clone (all steps).
- If you touched `_rules/`: `python _tools\scripts\rules_lint.py --write-index` and commit the regenerated `00_INDEX.md`.
- No design files, PDFs, personal paths, e-mail addresses or keys in the diff.
- One topic per pull request, with a short description of the problem it solves and how you checked it.

## Rule changes
A rule is a contract, so the rules have a process (rule WF-04):
- Propose a rule when a check fails twice or the same correction is made twice. Use `_rules/RETRO_TEMPLATE.md`.
- A rule block has: ID, `MUST` / `MUST NOT`, `Why`, `Check`, `Source`, `Status`. A new rule starts as `PROPOSED` (not binding).
- The maintainer approves it in the pull request; the same change bumps `_rules/VERSION` and adds a row to `_rules/CHANGELOG.md`.
- A rule that names a script as its check must name a script that exists (`rules_lint.py` enforces this).
- Designs keep the rules version they were started with.

## Scripts
Python standard library only. Each script has a docstring that describes usage, `--help`, exit code 0 = PASS and 1 = FAIL, and a test in
`_tools/tests/`. No project constants in code: values come from the project's `ai/*.json` or the fab profile. Add it to
`_tools/scripts/README.md`.

## Guard and safety files
`_tools/bridge/`, the hook and the kill switch protect a live Altium session. Changes there need a description of how you tested them
on a real Altium install, and a maintainer review.

## Global library
`_global/libs/*.SchLib` and `*.PcbLib` are binary, so git cannot merge them. Rules of thumb:
- Promote a part only after your design's G1 gate (`lib_promote.py`), and include its catalog entry with the datasheet sha256 and source link.
- Library pull requests are merged one at a time by the maintainer; if two touch the same library file, rebase and re-run the promotion.
- Never commit vendor PDFs. See `_global/datasheets/README.md`.

## System-level design guidelines
`_guidelines/` is a draft area. A guideline needs a source for every value and a stated way a script applies it. See `_guidelines/README.md`.
