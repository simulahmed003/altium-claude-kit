# Setup guide

Time: about 15 minutes plus downloads. Windows 10 or 11. Examples use `D:\EDA` as the workspace folder.

## 1. Install the requirements
| Tool | Check | Install |
|---|---|---|
| Python 3.11+ | `python --version` | `winget install Python.Python.3.12` |
| Git | `git --version` | `winget install Git.Git` |
| Claude Code | `claude --version` | follow the official Claude Code docs |
| Altium Designer 26 | opens, licence active | your Altium account |
| GitHub CLI (optional) | `gh --version` | `winget install GitHub.cli` |

Open a **new** terminal after installing, so the new PATH is used.

## 2. Clone
```
git clone https://github.com/simulahmed003/altium-claude-kit.git D:\EDA
cd D:\EDA
```

## 3. Run the installer
```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\setup.ps1
```
It installs the three MCP servers into `tools\mcp\`, writes `.mcp.json` and `.claude\settings.json` for **this** folder
(the guard hook and the deny rules for the safety files), creates a desktop shortcut "EDA KILL SWITCH", and prints a SUMMARY.
Fix every FAILED line and run it again; a failed server does not block the others. Both generated files are local
(git-ignored) because they contain your paths.

## 4. Allow the library tool to write
`altium-lib` may only write inside the folders listed in `allowed_paths` of
`%USERPROFILE%\.altium-designer-mcp\config.json`. `setup.ps1` creates this file if it is missing. If you already had one,
make sure it lists these three folders (forward slashes):
```
"allowed_paths": [ "D:/EDA/tools/libraries", "D:/EDA/projects", "D:/EDA/library" ],
```
Save the file and restart Claude Code.

## 5. Register the Altium scripts (manual, once)
In Altium Designer 26: DXP > Preferences > Scripting System > Global Projects > add the eda-agent script project
(the folder `setup.ps1` printed). The live loop itself is started later, when the bridge asks for it:
File > Run Script > StartMCPServer.

## 6. Start the agent and check
```
cd D:\EDA
claude
```
Type `/mcp`: `altium-lib`, `altium-coffee`, `altium-eda` should be listed (approve them if asked). If they are not,
exit and run `claude --continue` in the same folder. Then, in a normal terminal:
```
python tools\selftest.py
bridge.cmd status
```

## 7. First-run tests and first design
Do [FIRST_RUN_TESTS.md](FIRST_RUN_TESTS.md) once. Then create a design: `tools\newproject.ps1 -Name my-board`, and ask Claude to
follow playbook P1. Designs live in `projects\`, which is git-ignored; run `git init` inside each design folder.

## Update
`git pull`, then `tools\setup.ps1` again, `python tools\selftest.py`, and read `rules\CHANGELOG.md`. Existing designs keep the
rules version in their `project.json`.

## Troubleshooting
| Symptom | What to do |
|---|---|
| `claude` not found | Open a new terminal. Check the Claude Code install. |
| Servers missing in `/mcp` | Exit, run `claude --continue` from the workspace folder, approve the servers. |
| "KILL SWITCH IS ENGAGED" | Stop. Find out why it was pressed; run `REARM.cmd` only when it is safe. Never bypass it. |
| A tool call is blocked by the guard | Read the message. Only one live bridge (coffee or eda) runs at a time. Wait; do not retry in a loop. |
| Altium does not answer tool calls | Playbook P8 (`rules\playbooks\P8_recover_wedged_altium.md`). Often: Run > Stop (on laptops with media F-keys: Fn+Ctrl+F3). |
| A preview or PDF window is open in Altium | Close it. It blocks every tool call. |
| `setup.ps1` says Python is too old | Install Python 3.11 or newer and open a new terminal. |
| `selftest` fails after a pull | Open an issue with the output. |
| `altium-lib` cannot write a library | The file is open in Altium (close it), or the folder is not in `allowed_paths` (step 4). |

## Upgrading an install from altium-claude-workspace
Fastest way: close Altium and Claude Code, then run `python migrate_from_workspace.py` (from `tools\` of the kit, or downloaded on its own)
in an Administrator terminal. It does every step below, backs up each file it changes, and runs setup and selftest.
Use `--dry-run` first to see the plan.

The folders were renamed on 2026-10-17 (rules 1.1.1): `_rules` → `rules`, `_tools` → `tools`, `_global` → `library`,
`_guidelines` → `guidelines`, `_logs` → `logs`, `_tools/templates` → `templates`. Run `tools\setup.ps1` again so the hook,
`.mcp.json` and the kill-switch shortcut point to the new paths, change `allowed_paths` (step 4) to `.../library`, and move
your datasheet cache to `library\datasheets\`. Details: `library/README.md`. Existing designs keep working; their
`project.json` `global_root` must point to the new `library` folder.
