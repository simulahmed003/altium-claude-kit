# Why Altium scripts jam, and what now handles it (wedge study, 2026-11-07)

Evidence came from the user's PC (AD26 26.11.1): `logs\MCP_LOG.md` (110 rows), the coffee and eda-agent server code,
the guard and bridge scripts, a list of every Altium window, and controlled script errors in the coffee Sandbox.
Raw files stay on the PC in `D:\EDA\logs\wedge_study\` (not committed).

## History

| Failure in MCP_LOG | Count |
|---|---|
| popup script_crashed (user pressed Ctrl+F3) | 10 (8 of them on 2026-11-05) |
| eda_loop_active | 9 |
| eda_loop_not_started | 6 |
| timeout | 3 |
| unknown_modal | 1 |

## Root causes

1. **Server older than its files.** An update pulled altium-mcp 0.6.2 while the coffee server from the old code kept
   running. The new `SandboxScript\Sandbox.pas` is a template whose `%GUARD_SECONDS%` only the new server fills, so every
   script failed to compile ("Expression expected but % found"). The old server closed that box after 6 s and reported
   "script never started / executor_wedged: run -REditScript:Stop": wrong advice, nothing was wedged.
2. **One script engine.** The eda-agent window (a timer pump) blocks every other script while open, even when paused
   ("...is not able to execute more than one script simultaneously"). It started by itself after an X2.exe
   command-line handoff. The guard only pings the loop; a paused or just-started pump does not answer.
3. **Name clash.** coffee's `AltiumScript\Altium_API.PrjScr` sits next to `AltiumCoffee.PrjScr` again (restored by a
   pull), and eda-agent's project has the same name.
4. **Command line during a dialog.** `X2.EXE -R...` while Altium shows a modal starts a second X2 ("There is another
   instance of running, but it is busy at the moment"). coffee (after a failed script) and eda-agent send
   `-REditScript:Stop` this way automatically.
5. **Script errors.** A `#32770` 'X2' box with "...Continue execution?": a freed object ("Undeclared identifier: Free"),
   or a file saved with a UTF-8 BOM ("Unknown identifier: ï").

## Recovery proven on the PC (no user, no -REditScript:Stop)

Cancel on the "Continue execution?" box (WM_COMMAND IDCANCEL), then close the "Operation aborted" box (WM_CLOSE). The next
Sandbox run started and finished at once. OK on the same box lets the script run on past the error. Altium's main window
has no Win32 menu, so Run > Stop has no command id. Not reached (the boxes were answered at the screen first): a paused
debugger without a box, and whether try/except avoids the box; those stay with `bridge.cmd popup script_crashed`.

## What the kit does now (rules 1.14.0)

| Cause | Tool | Rule |
|---|---|---|
| 1 | `kit doctor` check 9: server process older than its repo, tracked files changed in tools\mcp\*; `altium_unstick` names the compile box | TOOL-22 |
| 2 | `kit altium_unstick` and `kit doctor` check 10 show the eda-agent window and the "more than one script" box | TOOL-21 |
| 3 | `kit doctor` check 9: two script projects with the same name | TOOL-21 |
| 4 | `kit altium_unstick --fix` closes the "busy" box and ends the duplicate X2 (only one that showed it and is under 10 min old) | TOOL-18, TOOL-22 |
| 5 | `kit pas_lint` before every live script; `altium_unstick --fix` answers Cancel + closes "Operation aborted" | TOOL-21 |

## Changes that belong to other owners (proposed, not made)

`tools\bridge\` is the user's (TOOL-17); coffee and eda-agent are upstream projects. Text ready to use:

**tools\bridge (user):** (a) `Test-EdaLoop` in lib.ps1: besides the ping, look for a visible X2 window titled
"EDA Agent" and treat it as "loop active"; (b) `bridge.ps1 recover`: run `python tools\scripts\altium_unstick.py --fix`
first and show the script_crashed popup only when it exits 1.

**coffeenmusic/altium-mcp, issue "Do not send -REditScript:Stop automatically; it can start a second Altium":**
After a failed script, main.py (around lines 546-548) and sandbox.py (656-657) start `X2.EXE -REditScript:Stop`. When
Altium shows any dialog, that command line starts a second X2 ("There is another instance of running, but it is
busy"). On AD26 26.11.1, posting IDCANCEL to the "Continue execution?" `#32770` box and WM_CLOSE to the following
"Operation aborted" TMessageForm stops the script fully. Proposal: use that route, never the command line while a
dialog is open; report a compile error as a compile error (not "never started / wedged"); and rename
`AltiumScript\Altium_API.PrjScr`, which clashes with eda-agent's project of the same name.

**salitronic/eda-agent, issue "Agent loop starts by itself and blocks every other script":** after an X2.exe
command-line handoff the Dispatcher (Altium_API.PrjScr, StartProcName=Dispatcher.pas>StartMCPServer) started without
a request, and while its window is open (also when paused) Altium refuses every other script. Proposal: start the loop
only on an explicit request, answer the ping while paused (or report "paused"), and do not send -REditScript:Stop from
cli.py (around line 260) while a dialog may be open.
