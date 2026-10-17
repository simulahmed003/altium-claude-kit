# User standards

A user standard holds one person's or one company's design choices: house style, company or customer policy, the
industry rules they work under, and their own equipment and process. What belongs here and what belongs in the
central rules or guidelines: [docs/DESIGN_STANDARDS.md](../docs/DESIGN_STANDARDS.md).

- Your own standards go in `standards/local/` (git-ignored, never pushed to the central repo).
- Start one by copying `TEMPLATE.md` to `standards/local/<name>.md` and naming it in the project's `project.json`
  (`"standard": "standards/local/<name>.md"`).
- The `altium-rule-harvest` skill adds lines here when you sort a feedback item as "mine".
