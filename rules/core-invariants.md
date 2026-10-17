# Core invariants

Prefix: `CI`. These hold in every phase. A conflict with any of them goes to a human.

| ID | Rule | Why | Check |
|---|---|---|---|
| CI-01 | Part facts come only from the component DB or a cited datasheet page. | Invented specs cause silent failures. | review |
| CI-02 | Design to recommended operating conditions with margin; never to absolute maximum ratings. | Abs max is a damage limit, not an operating point. | review |
| CI-03 | Every quantity carries a unit and, for part facts, a datasheet ref. | Unit and source errors are the commonest data bugs. | `comp validate` |
| CI-04 | Calculations run in `tools/calc/` scripts and are saved in `calc/`. | Reproducible and cheap to re-check. | review |
| CI-05 | A part must be `verified` before schematic freeze (G2). | Unreviewed extraction must not reach fab. | `comp pull` warning |
| CI-06 | A check is `passed` only if a tool or a recorded review passed it. | Honest status. | review |
| CI-07 | Any rule override is written in the project `CLAUDE.md` with reason and approver. | Traceability. | review |
