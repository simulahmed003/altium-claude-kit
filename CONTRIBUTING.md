# Contributing

Thanks for helping. This kit grows one part, one rule and one skill at a time. You can write your contribution
by hand or with your own AI assistant; both go through the same review.

## What you can contribute

| Type | Where | Typical size | Must include |
|---|---|---|---|
| **New part** | `components/<category>/<MPN>/` | 1 folder | `part.yaml` passing `comp validate`, `source.yaml` (datasheet URL, revision, SHA-256, CAD licence) |
| **Part fix** | existing `part.yaml` | 1–5 lines | the datasheet page that proves the fix |
| **Rule** | `rules/<topic>.md` | 1 line per rule | rule ID, the rule, a reason; a check script if one is possible |
| **Skill** | `skills/altium-<phase>/` | 1 folder | `SKILL.md` from `skills/_template/`, under ~80 lines, and one worked example or test |
| **Tool** | `tools/<area>/` | 1 script | short JSON output (`status`, `summary`, `issues`, `artifact`), `--help`, a test |
| **Fab profile** | `rules/fab-profiles/<fab>.yaml` | 1 file | link to the fab's capability page and the date you checked it |

## How

1. Fork the repo and create a branch: `part/TPS54331DR`, `rule/placement-PL-07`, `skill/altium-routing`.
2. Make the change. If an AI helps you, give it [docs/AI-CONTRIBUTOR.md](docs/AI-CONTRIBUTOR.md) first.
3. Run the checks locally:
   ```bash
   python tools/comp/comp.py validate --all
   python tools/comp/comp.py index
   ```
4. Open a pull request using the template. Say whether an AI wrote it and which one.

## Review

Every PR is reviewed by the maintainer (Simul) with AI assistance, and CI must pass.
Reviewers check, in this order:

1. **Evidence.** Every part fact has a datasheet page reference. Rules have a reason.
2. **No duplication.** A rule is written once; skills cite rule IDs instead of copying text.
3. **Size.** Skills stay short; part digests stay under 150 lines; tools print summaries, not logs.
4. **Licence.** No PDFs; CAD files only if their licence allows redistribution.

A part arrives as `status: extracted_unreviewed`. It becomes `verified` only after a reviewer has checked pins,
absolute maximum ratings and package dimensions against the cited pages.

## Style

- Units always explicit (`{value: 3, unit: A}`), SI prefixes, no bare numbers.
- One topic per rule file; rule IDs never reused after deletion (mark `deprecated` instead).
- Plain, short English. Write for a reader who skims.

## Code of conduct

Be kind, be specific, and assume good intent. Criticize the design, not the person.
