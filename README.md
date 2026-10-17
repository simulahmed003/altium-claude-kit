# altium-claude-kit

Rules, checkers and a managed component library for AI-assisted PCB design with Altium Designer 26 and Claude Code.
The agent works under written rules and human sign-off gates, scripts check its work, and you stay in control.

> Status: first public version. Built and tested on Windows 10 with one design (a 12 V to 5 V, 3 A buck converter).
> Expect rough edges. Fixes and better rules are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

## What is in this repo
| Part | What it does |
|---|---|
| `.claude/skills/` | Phase skills Claude Code loads automatically: goal, what to read, how to judge. Draft; see the roadmap. |
| `_rules/` | Versioned rules (workflow, requirements, library, schematic, PCB, fab output, tooling, communication) and playbooks P1-P8. Every rule says how it is checked. Index: `_rules/00_INDEX.md`. |
| `_tools/scripts/` | Offline checkers and generators: pins = pads, connectivity, text overlaps, calculations, gate evidence, BOM. Python standard library only. No Altium needed. |
| `_tools/bridge/`, `.claude` hook | A guard that lets only one live Altium bridge run at a time, plus a kill switch. |
| `_global/` | Managed global component library: catalog, category libraries, hashes, promote / pull / update scripts. Projects work on local copies. |
| `_guidelines/` | Draft area for system-level design guidelines. Empty by design; set per team. |
| `_tools/templates/project/` | Template for a new design (requirements, constraints, gates). |
| `docs/` | Setup guide, first-run tests, lessons learned, architecture, roadmap, guide for AI contributors. |

Your designs are **not** part of this repo. `projects/` is git-ignored: keep each design in its own (private) git repo inside it.

## Requirements (install before running setup)
| Need | Version | Why |
|---|---|---|
| Windows | 10 or 11 | The live Altium bridge, guard and kill switch use PowerShell and Win32. The Python checkers also run elsewhere. |
| Altium Designer | 26 (commercial licence) | Only for the live schematic / PCB bridges. Offline libraries and checkers do not need it. |
| Python | 3.11 or newer | `setup.ps1` builds the MCP servers' virtual environments with it. The workspace scripts need nothing extra. |
| Git | any recent | Clone this repo; `setup.ps1` clones two MCP servers. |
| Claude Code | current | The agent. Needs a Claude account that can run Claude Code. See the official docs for install. |
| Internet to github.com and PyPI | | `setup.ps1` downloads three MCP servers (see Third-party tools). |
| GitHub CLI `gh` | optional | Only if you contribute pull requests. |

PowerShell 5.1 is built into Windows. Example installs: `winget install Python.Python.3.12`, `winget install Git.Git`, `winget install GitHub.cli`.

## Quick start
```
git clone https://github.com/simulahmed003/altium-claude-kit.git D:\EDA
cd D:\EDA
powershell -NoProfile -ExecutionPolicy Bypass -File _tools\setup.ps1
```
Read the SUMMARY at the end of the script. Re-running it is safe. Then:
1. Do the one manual Altium step (register the eda-agent scripts). See [docs/SETUP.md](docs/SETUP.md).
2. Open a new terminal: `cd D:\EDA`, `claude`, then type `/mcp`. You should see `altium-lib`, `altium-coffee`, `altium-eda`.
3. Check the install: `python _tools\selftest.py` (all steps PASS; the buck design regression is SKIPPED because designs are not in this repo).
   Vendor datasheet PDFs are not in git either: `python _tools\scripts\datasheets_fetch.py` downloads and hash-checks them.
4. Do the first-run tests once: [docs/FIRST_RUN_TESTS.md](docs/FIRST_RUN_TESTS.md).

You can clone to another folder; the examples use `D:\EDA`. Always start `claude` from the workspace folder, because the hook and permissions only apply there.

## Start a design
```
powershell -NoProfile -ExecutionPolicy Bypass -File _tools\newproject.ps1 -Name my-board
```
Then ask Claude to start the project following playbook P1 (`_rules/playbooks/P1_new_project.md`).
The agent reads `CLAUDE.md` and the rules, works through the gates G1, S1, G2, G3, G4, and stops at each one. **Only you tick a gate.**
Put the design under its own git repo: `cd projects\my-board`, `git init`.

## Everyday commands
| Command | What it does |
|---|---|
| `bridge.cmd status` | active bridge, health, kill switch, Altium and loop state |
| `bridge.cmd use coffee` / `use eda` | switch the live bridge by hand (the hook does it automatically) |
| `bridge.cmd force eda` | skip the checks if a check misbehaves |
| `bridge.cmd recover` | popup for a crashed Altium script engine |
| `KILL.cmd` / `REARM.cmd` | emergency stop / re-enable |
| `python _tools\selftest.py` | run every checker and test |
| `python _tools\scripts\rules_lint.py` | check the rule files |

## Update
`git pull`, run `_tools\setup.ps1` again, run `python _tools\selftest.py`, and read `_rules/CHANGELOG.md`. A design keeps the rules version it was started with (`project.json`).

## Roadmap
What exists and what comes next (component facts database, front-of-flow phases, PCB rules, analysis): [docs/ROADMAP.md](docs/ROADMAP.md). Design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contribute
Found a better rule, a bug, a new checker or a footprint? See [CONTRIBUTING.md](CONTRIBUTING.md). Using an AI assistant? Give it [docs/AI-CONTRIBUTOR.md](docs/AI-CONTRIBUTOR.md) first. Rules change only through a reviewed pull request that bumps `_rules/VERSION` and the changelog.

## Known limits
- The live bridge, guard and kill switch cover Claude Code started from the workspace folder only.
- A crashed Altium script engine can only be noticed by a missing reply; fixing it needs you. See playbook P8.
- Never export PDF or open print preview through Altium while the agent works: the preview window blocks every tool.
- Vendor datasheet PDFs are not stored here. The catalog keeps their path and sha256 (see `_global/datasheets/README.md`).

## Third-party tools (installed by `setup.ps1`, not bundled)
[embedded-society/altium-designer-mcp](https://github.com/embedded-society/altium-designer-mcp) (offline libraries),
[coffeenmusic/altium-mcp](https://github.com/coffeenmusic/altium-mcp) (live PCB),
[salitronic/eda-agent](https://github.com/salitronic/eda-agent) (live schematic, review, audit).
Each keeps its own licence. This project is not affiliated with Altium or Anthropic; product names belong to their owners.

## Licence
Apache-2.0. See `LICENSE` and `NOTICE`.
