# P7 Commit and hand-off

Read with: 01_WORKFLOW_GATES, 08_COMMUNICATION.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Run the checkers for the stage (P6 offline part); `python tools\selftest.py` when scripts or rules changed. | TESTED (this phase) |
| 2 | Append decisions and open issues to PROJECT.md (dated). | TESTED (buck) |
| 3 | Stage only intended files: never .mcp.json, .claude\, bridge state; check `git status` for design files Altium saved unexpectedly. | TESTED (this phase) |
| 4 | Commit message: what changed + check results; one commit per numbered step of a brief. | TESTED (buck, this phase) |
| 5 | Update PROJECT.md / logs\WORKSPACE_PROGRESS.md resume notes so a new session can continue. | TESTED (this phase) |

5 of 5 steps TESTED.
