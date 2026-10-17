# P8 Recover a wedged Altium

Read with: 07_TOOLING_ALTIUM.

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Stop calling tools. `bridge.cmd status` (in the workspace folder). Loop responding + coffee timeout = the loop is the cause: release it (popup or app_detach after announcing). | TESTED (buck) |
| 2 | Timeout with no loop: `bridge.cmd popup script_crashed`; user presses Run > Stop (Fn+Ctrl+F3). Exit 0 = retry once, 1 = stop and ask. | TESTED (buck) |
| 3 | Still stuck: `bridge.cmd popup unknown_modal` (hidden dialog); user closes it. | TESTED (buck: Preview SCH) |
| 4 | Last resort, user only: Ctrl+S in Altium, End task X2.EXE, restart Altium, reopen the project. | UNTESTED (LESSONS T7) |
| 5 | After recovery: check file dates on disk, rerun conn_check / gate_check, log in logs\MCP_LOG.md. Two crashes in one stage = stop and ask (TOOL-05). | TESTED (buck) |
| 6 | KILL SWITCH IS ENGAGED in any result: stop all Altium work, tell the user; only the user runs REARM.cmd. | TESTED (bridge setup) |

5 of 6 steps TESTED.
