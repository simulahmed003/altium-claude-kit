# P6 Before presenting a gate (evidence pack)

Read with: 01_WORKFLOW_GATES.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Save everything; `python _tools\scripts\gate_check.py <gate> projects\<name>`. | TESTED (selftest + buck scratch) |
| 2 | Fix every FAIL in ai\review\<gate>_evidence.md; rerun until the offline result is PASS. | TESTED (fixtures) |
| 3 | Fill the MCP rows (ERC / DRC / differences / check_placement) with tool results, never from memory. | TESTED (buck, by hand before gate_check existed) |
| 4 | Own capture review in the evidence file (COM-01): what was checked, where. | TESTED (buck) |
| 5 | Present: short report, user actions first. The user ticks gates.md; the agent never does. | TESTED (buck G1, S1) |

5 of 5 steps TESTED.
