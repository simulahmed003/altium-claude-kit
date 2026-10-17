# First-run tests (once, 15-30 minutes)

Do these before you trust the automatic bridge switching. Altium Designer must be installed; start it for tests 2-5.
Write each result as one line in `logs\MCP_LOG.md` (a local file, not in git).

1. `bridge.cmd status` prints without an error.
2. Start Altium, run `StartMCPServer` (File > Run Script), then `bridge.cmd status`: the eda-agent loop should say "responding".
   If it says the opposite, the loop check in `tools\bridge\lib.ps1` is wrong for your machine: use `bridge.cmd force eda` / `force coffee`
   instead of the automatic checks, and tell Claude.
3. With the loop running, ask Claude for one `altium-coffee` tool (for example `get_server_status`). Note whether the guard asked you to
   release the loop and whether Altium hung.
4. Ask Claude to call the eda-agent tool `app_detach` (it SAVES all modified Altium documents first). Then `bridge.cmd status`:
   the loop should now be "not responding".
5. Check that the two live servers do not fight over a script project with the same name (`Altium_API.PrjScr`).
6. Kill switch: double-click `KILL.cmd`, confirm the popup, check that `claude` shows the servers gone and Altium is untouched.
   Then double-click `REARM.cmd`.

If a test fails, do not work around it: write down what you saw and ask Claude to propose a fix for the scripts, then review the change.
