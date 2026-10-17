# Usage guide

How to design a board with this kit. Altium Designer runs on Windows, so commands below work in
PowerShell or Git Bash; paths use `/` for brevity.

## 1. One-time setup

1. Install Python 3.10+, Git, Altium Designer, and Claude Code.
2. Clone the kit somewhere permanent and install its Python dependencies:
   ```bash
   git clone https://github.com/<owner>/altium-claude-kit.git C:/tools/altium-claude-kit
   pip install -r C:/tools/altium-claude-kit/requirements.txt
   ```
3. Make the skills visible to Claude Code by copying (or symlinking) `skills/*` into `~/.claude/skills/`:
   ```bash
   cp -r C:/tools/altium-claude-kit/skills/altium-* ~/.claude/skills/
   ```
   Re-copy after `git pull` when skills change.
4. Optional, per the tool you use: connect an Altium MCP server and the CAD download tools listed in
   `docs/ARCHITECTURE.md` §6. Record what you have in your project's `project.yaml` → `tools:` so Claude does not
   assume a tool exists.

## 2. Start a project

```bash
python C:/tools/altium-claude-kit/tools/comp/comp.py new-project D:/designs/my-board
```

This copies `templates/project/` and writes the kit path into the project's `CLAUDE.md`. You get:

| File | You edit? | Purpose |
|---|---|---|
| `project.yaml` | rarely | phase, gate status, open issues, fab profile, available tools |
| `requirements.yaml` | yes, with Claude | the numbers the design must meet |
| `decisions.md` | Claude appends | one line per decision with reason and evidence |
| `components.lock.yaml` | no (tool writes) | exact DB version of every part used |
| `components/` | no (tool writes) | only the parts this board uses |
| `lib/` | no (tool builds) | `Project.SchLib` / `Project.PcbLib` built from `components/` |
| `calc/`, `reports/` | Claude writes | calculation results and check summaries |
| `altium/` | Claude + you | the Altium project files |

## 3. Work with Claude

Open Claude Code in the project folder and describe what you want, e.g.
"Design a 24 V to 5 V / 3 A buck converter on a 2-layer board for JLCPCB."
The `altium-orchestrator` skill reads `project.yaml`, picks the current phase, and loads that phase's skill.

Claude works autonomously between gates and stops at each gate with a short summary for you to approve:

| Gate | You approve |
|---|---|
| G1 | requirements and architecture |
| G2 | critical parts and the frozen schematic |
| G3 | the frozen layout after analysis |
| G4 | the fab package |

To change which gates need you, edit `gates:` in `project.yaml`.

## 4. Components

| Task | Command |
|---|---|
| Find a part in the global DB | `comp search "buck 24V 3A"` |
| Read only what you need | `comp get TPS54331DR --section pins` |
| Add a new part (datasheet read once) | `comp ingest <MPN> --pdf path/to/datasheet.pdf` |
| Fetch symbol / footprint / 3D | `comp cad <MPN>` |
| Check a part record | `comp validate <MPN>` |
| Use a part in this project | `comp pull <MPN>` |
| Share a new part with everyone | `comp push <MPN>` (opens a pull request) |

`comp` here means `python <kit>/tools/comp/comp.py`. Which commands are working today is in `docs/ROADMAP.md`.

Parts pulled into a project are pinned in `components.lock.yaml`. Updates to the global DB never change a
project silently; run `comp pull <MPN> --update` to take a newer version on purpose.

## 5. Keeping the kit current

`git pull` in the kit folder. Your projects stay on the part versions in their lockfile and on the kit version
in `project.yaml` → `kit_version` until you choose to move.
