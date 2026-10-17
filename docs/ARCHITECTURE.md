# Claude + Altium Design Framework — Refined Plan

Status: approved plan (2026-10-17). What is built so far is tracked in [ROADMAP.md](ROADMAP.md).
Target: latest Altium Designer plus the two previous major versions.

---

## 1. What we are building (one paragraph)

A **global kit** that lives in one Git repo and a **local project** that copies only what it needs.
The kit has three parts: **skills** (how Claude approaches each design phase), **rules** (the engineering
standards a PCB designer must follow, written once), and a **component database + library** (datasheet
facts already extracted, plus symbol/footprint/3D/SPICE). Claude reads a small project state file to know
where it is, loads only the one skill and the few rules and component fields that phase needs, and
writes its decisions to files instead of keeping them in chat. That is where the token savings and the
reduced human feedback come from.

---

## 2. Key structural decisions

| # | Decision | Why |
|---|---|---|
| D1 | **Skills, rules and tools are separate.** A skill says *what to achieve and how to judge it*; a rule file says *what is acceptable*; a script does *anything deterministic*. | Rules are written once and referenced, never copied into skills. Calculations done by scripts cost no reasoning tokens and are repeatable. |
| D2 | **Skills are goal + gate, not step-by-step scripts.** Each SKILL.md is under ~80 lines: goal, inputs, which rules to load, exit checks, what to write back. | Claude evaluates instead of following a rigid recipe; short skills load cheaply. |
| D3 | **One component = one folder, keyed by exact MPN.** Facts in YAML with datasheet page refs, plus a short "digest" split by design phase. | Claude reads 30 lines of the right section instead of a 60-page PDF. |
| D4 | **Datasheet is read once, ever.** Ingest → extract → commit to global DB. Every later project and phase queries the DB. | Biggest single token waste today. |
| D5 | **Local project pulls a subset + lockfile.** `comp pull <MPN>` copies record + CAD into the project and pins the version. Global changes never silently change a project. | Small project folder, reproducible designs. |
| D6 | **Project state lives in files.** `project.yaml` (phase, status, open issues) + `decisions.md` (one line per decision with reason). | A new session resumes from 2 small files, not from replaying the conversation. |
| D7 | **Four human gates only:** requirements/architecture, critical parts + schematic freeze, layout freeze, fab release. Everything between runs autonomously and self-checks. | Cuts the "frequent human feedback" without losing control of irreversible choices. |
| D8 | **Workflow is dependency-driven, not linear.** If a check fails, go back to the earliest affected phase and redo only what depends on it. | No re-running the whole flow for a silkscreen fix. |
| D9 | **Build only what the buck converter pilot needs first.** Empty skill folders are not created. | Keeps the base small; others add skills later via a template. |

---

## 3. Repository layout

### 3.1 Global kit (one GitHub repo, e.g. `altium-claude-kit`)

```text
altium-claude-kit/
├── CLAUDE.md                  # ~40 lines: operating principles + how to find things (merged contract)
├── CONTRIBUTING.md
├── skills/                    # one folder per phase; only built when needed
│   ├── _template/SKILL.md
│   ├── altium-orchestrator/         # reads project.yaml, picks next phase/skill
│   ├── altium-requirements/
│   ├── altium-architecture/
│   ├── altium-component-selection/
│   ├── altium-library-cad/        # symbol, footprint, 3D, SPICE sourcing + creation
│   ├── altium-schematic-design/   # datasheet compliance + calculations + simulation
│   ├── altium-schematic-review/   # formatting + ERC + review vs requirements
│   ├── altium-pcb-setup/          # stackup, design rules, board outline
│   ├── altium-placement/
│   ├── altium-routing/            # routing + polygons
│   ├── altium-analysis/           # SI, PDN, thermal (load only what applies)
│   ├── altium-silkscreen-dfm/     # silkscreen, assembly, mechanical, DFM
│   └── 12-fab-release/        # outjob, Gerber/ODB++, BOM, PnP, release audit
├── rules/                     # engineering standards, one topic per file, referenced by skills
│   ├── core-invariants.md     # never-break rules (abs max, units, evidence, no invented specs)
│   ├── schlib.md
│   ├── pcblib-footprint.md    # IPC-7351 naming, courtyard, pin-1, paste
│   ├── cad-models.md
│   ├── schematic-design.md
│   ├── schematic-format.md
│   ├── placement.md
│   ├── design-rules.md
│   ├── routing-polygons.md
│   ├── pdn-thermal.md
│   ├── si.md
│   ├── silkscreen.md
│   └── fab-profiles/          # jlcpcb.yaml, pcbway.yaml, generic.yaml (numbers, not prose)
├── components/                # THE component database + library (see §5)
│   ├── index.json             # generated: MPN → category, key params, path
│   └── <category>/<MPN>/...
├── tools/                     # deterministic scripts (Python), each returns short JSON
│   ├── comp/                  # comp search | get | ingest | pull | push | validate
│   ├── calc/                  # buck, LDO, divider, RC, trace width, via current, thermal
│   ├── altium/                # DelphiScript/MCP wrappers: place, rules import, ERC/DRC parse
│   └── reports/               # parse ERC/DRC/sim logs into 10-line summaries
├── templates/
│   └── project/               # skeleton copied into every new local project
└── examples/
    └── buck-converter/        # the pilot, kept as regression test
```

### 3.2 Local Altium project (what the user actually works in)

```text
my-board/
├── CLAUDE.md                  # 10 lines: points to kit path, project rules overrides
├── project.yaml               # phase, status, gates, open issues, kit version
├── requirements.yaml
├── decisions.md               # one line per decision + reason + evidence ref
├── components.lock.yaml       # MPN → DB record version + hashes (written by `comp pull`)
├── components/                # ONLY the parts this board uses (copied by `comp pull`)
├── lib/
│   ├── Project.SchLib         # built from components/ (not hand-edited)
│   └── Project.PcbLib
├── calc/                      # calculation outputs (YAML/MD), one per circuit block
├── reports/                   # ERC/DRC/sim summaries; full logs in reports/raw/
└── altium/                    # .PrjPcb, .SchDoc, .PcbDoc, .OutJob
```

Rule of thumb: **the kit is read-only from a project's point of view**, except `comp push`, which sends a
newly ingested part back to the global DB through a Git branch/PR.

---

## 4. The workflow (phases, gates, what each loads)

Each phase = one skill. "Loads" is the context budget: Claude should not read more than this.

| Phase | Goal | Loads | Exit check | Gate |
|---|---|---|---|---|
| 01 Requirements | Measurable, testable requirements (V/I ranges, interfaces, size, env, cost) | user brief | every req has a number + verify method | **G1** |
| 02 Architecture | Block diagram, power tree, interface list, power budget | requirements.yaml | budget closes with margin; each req mapped to a block | **G1** |
| 03 Component selection | Exact MPNs for each block, 1 alternate for critical parts | DB `index.json`, `get --fields selection` | worst-case ratings met, in stock, lifecycle active | **G2** (critical parts) |
| 04 Library/CAD | Symbol, footprint, 3D, SPICE per part | rules/schlib, pcblib, cad-models; DB `package` fields | pin map matches datasheet; footprint matches drawing; models validated | — |
| 05 Schematic design | Circuit per block, datasheet-compliant, values calculated + simulated | rules/schematic-design; DB `pins`, `application`; tools/calc | every calc in calc/ passes vs requirement; sim within limits | — |
| 06 Schematic review | Formatting, net names, ERC clean, review vs requirements | rules/schematic-format | ERC 0 errors; traceability table complete | **G2** (freeze) |
| 07 PCB setup | Stackup, design rules, board outline, rule classes | rules/design-rules; fab-profile | rules imported; impedance/current widths calculated | — |
| 08 Placement | Critical loops first, then groups, thermal, mechanical | rules/placement; DB `layout` fields | loop areas/distances meet rules; 3D clearance | — |
| 09 Routing + polygons | Route by priority (power loops, sensitive, rest), pours, stitching | rules/routing-polygons | DRC 0; unrouted 0; current density ok | — |
| 10 Analysis | Only what applies: PDN/IR drop, thermal, SI | rules/pdn-thermal, si | results within limits or rework loop to 08/09 | **G3** (layout freeze) |
| 11 Silkscreen + DFM | Silkscreen, fiducials, assembly, DFM | rules/silkscreen; fab-profile | DFM report clean | — |
| 12 Fab release | Outjob, Gerber/ODB++, drill, BOM, PnP, release manifest | fab-profile | package audit script passes vs frozen revision | **G4** |

**Rework loop:** a failed exit check records an issue in `project.yaml` with the phase that must fix it.
The orchestrator goes back there and marks downstream checks as invalidated. Example: thermal fails →
back to 08 (spread copper) or 03 (lower-Rds part), not a full restart.

**On "Altium already has AI for requirements":** Altium 365 has a requirements/systems portal and
Copilot-style features depending on license. Treat it as an optional input source for phase 01; our
`requirements.yaml` stays the single source Claude reads. We should check what your license includes
before planning around it.

---

## 5. Component database (the most important part)

### 5.1 One folder per part

```text
components/power/buck/TPS54331DR/
├── part.yaml          # identity + structured facts (with datasheet page refs)
├── digest.md          # compact, sectioned for each phase (≤150 lines)
├── symbol/            # .SchLib (single component) or source for generator
├── footprint/         # .PcbLib + land-pattern source note
├── 3d/                # .step
├── sim/               # .lib/.cir SPICE, IBIS if needed
└── source.yaml        # datasheet URL, revision, SHA256, date; PDF stays in local cache, not Git
```

### 5.2 `part.yaml` — sections match phases, so a query loads one section

```yaml
id: TPS54331DR
mfr: Texas Instruments
package: SOIC-8
status: verified          # verified | extracted_unreviewed | conflicting | stale
datasheet: {rev: "SLVS839F", sha256: "…"}
selection:                # phase 03
  vin: {min: 3.5, max: 28, unit: V, ref: "p1"}
  iout_max: {value: 3, unit: A, ref: "p1"}
  fsw: {value: 570, unit: kHz, ref: "p5 table 7.5"}
  lifecycle: active
abs_max:                  # never merged with recommended
  vin: {value: 30, unit: V, ref: "p4"}
pins:                     # phase 04/05
  - {num: 1, name: BOOT, type: passive, fn: "bootstrap cap to PH, 0.1uF", ref: "p3"}
application:              # phase 05: equations + recommended values
  vout_eq: "Vout = 0.8 * (1 + R1/R2)"
  l_min_eq: "…"
layout:                   # phase 08/09
  - "Keep VIN cap within 2 mm of pin 2; minimize PH node area (p23 fig 32)"
thermal:                  # phase 10
  theta_ja: {value: 75, unit: C/W, cond: "JEDEC 2s2p", ref: "p4"}
cad:
  symbol: {status: verified}
  footprint: {status: verified, source: "IPC-7351 calc", ipc_name: SOIC127P600X175-8N}
  model_3d: {status: verified, source: "mfr"}
  spice: {status: available, source: "TI PSpice"}
```

`digest.md` repeats nothing from `part.yaml`; it holds the things that do not fit fields: design notes,
gotchas, errata, the recommended schematic in words.

### 5.3 The `comp` tool (the only way Claude touches the DB)

| Command | What it does | Typical output size |
|---|---|---|
| `comp search "buck 24V 3A"` | searches `index.json` by params | 5–10 lines |
| `comp get TPS54331DR --section pins` | returns one section only | 10–40 lines |
| `comp ingest <MPN> [--pdf path]` | download datasheet, extract to draft `part.yaml` + `digest.md`, status `extracted_unreviewed` | writes files, prints summary |
| `comp cad <MPN>` | fetch symbol/footprint/3D via adapters (see §6) | writes files, prints status |
| `comp validate <MPN>` | schema, units, refs present, pin count = footprint pads | pass/fail list |
| `comp pull <MPN...>` | copy into local project + write lockfile entry + rebuild Project.SchLib/PcbLib | summary |
| `comp push <MPN>` | create branch + PR to the global repo | PR link |

Datasheet rule (the core token saver): **Claude never opens a PDF if `comp get` can answer.** It opens
the PDF only during `ingest`, or to resolve a specific conflict, and then only the cited page.

### 5.4 Trust levels
A part used in a design must be `verified` for the fields that phase uses. `extracted_unreviewed` parts
can be used in selection and draft schematics, but phase 06 (schematic freeze) blocks until a human or a
second check verifies pins and critical limits. This keeps the DB growing fast without letting
unchecked data reach fab.

---

## 6. Tools and integrations (what exists vs what we build)

| Need | Option | Status |
|---|---|---|
| Drive Altium (place, wire, rules, run ERC/DRC) | Community Altium MCP servers (DelphiScript bridge); Altium scripting as fallback | **verify which one works with your Altium version** before building on it |
| JLC/LCSC CAD download | `easyeda2kicad` → KiCad libs → Altium's KiCad importer; or a direct EasyEDA → Altium converter we write | exists (KiCad route); Altium-direct to build |
| Other CAD | SnapEDA / Ultra Librarian / SamacSys (manual or API where allowed) | adapter later |
| Datasheet extraction | PDF text/table extraction script + Claude review of cited pages only | build in phase 1 |
| Calculations | `tools/calc/*.py` returning YAML | build per pilot need |
| Simulation | LTspice/ngspice batch run + result parser; Altium Mixed-Sim if available | build for buck pilot |
| Fab rules | `rules/fab-profiles/jlcpcb.yaml` → Altium rules import | build |

Every tool returns: `status`, 5–10 line `summary`, `issues[]`, `artifact` path. Full logs go to
`reports/raw/` and Claude reads them only when diagnosing.

---

## 7. Token and workload rules (applied everywhere)

1. Start every session by reading `project.yaml` + last 10 lines of `decisions.md`. Nothing else until needed.
2. Load one skill, the rules it names, and `comp get --section` for the parts in scope.
3. Numbers come from scripts, not from Claude doing arithmetic in prose.
4. Tool output is a summary; logs stay on disk.
5. A correction the user gives twice becomes a line in a rule file or a check in a script, not a longer prompt.
6. Measure per phase: tokens, human interventions, PDF opens, failed checks. The buck pilot gives the baseline.

---

## 8. Skill and rule file format (for contributors)

**SKILL.md** (target ≤80 lines):
```
---
name: altium-placement
description: Place components on PCB after setup; use when project.yaml phase = placement
---
Goal: …                       (2–3 lines)
Inputs: project.yaml, netlist, comp get --section layout
Rules to load: rules/placement.md, rules/fab-profiles/<fab>.yaml
Approach: priorities and judgment calls, not a click sequence
Exit checks: measurable list (each maps to a script or a review item)
Write back: project.yaml status, decisions.md lines, reports/placement.md
Escalate when: …
```

**Rule file:** numbered rules, each one line + reason + (optional) check script. Example:
`PL-03 Input cap of a buck within 2 mm of VIN pin — limits hot-loop inductance. check: tools/altium/loop_check.py`

Numbered IDs let skills, reviews and decisions reference `PL-03` instead of repeating the text.

---

## 9. Collaboration model

- **One repo, PR-only.** Main branch is protected; CI runs `comp validate` on changed parts, schema checks on skills/rules, and the buck example as a regression.
- **Contributions come in three sizes:** a new part (most common, via `comp push`), a rule fix (edit one line + reason), a new skill (copy `_template`, must include one example).
- **Versioned releases** (`v0.1`, `v0.2`). Each local project pins the kit version in `project.yaml`.
- **Licensing:** commit structured facts and CAD you are allowed to redistribute; keep PDFs and vendor-restricted models in a local cache with only the URL + hash in Git.

---

## 10. Build order (what we do first)

| Step | Build | Done when |
|---|---|---|
| 1 | Repo skeleton, merged `CLAUDE.md` (~40 lines), `project/` template, `part.yaml` schema | a new project can be created from template |
| 2 | `comp` tool: `search`, `get --section`, `ingest`, `validate`, `pull` | buck converter's ~10 parts are in the DB and pulled into the project |
| 3 | `comp cad` with the JLC route + Project.SchLib/PcbLib build | Altium opens the project libs with correct pin/pad mapping |
| 4 | Skills 05 + 06 and `tools/calc/buck.py` + one LTspice run | buck schematic redone from the DB with zero PDF opens |
| 5 | Rules + skills 07–09 + fab-profile import | buck layout redone; compare tokens and interventions vs your first attempt |
| 6 | Skills 10–12, then 01–03 and the orchestrator | full flow end to end on the pilot |
| 7 | CONTRIBUTING.md, CI, `v0.1` release | someone else can add a part or a skill without asking us |

Steps 1–2 are the foundation and directly attack your two problems (token use from datasheets, and
repeated feedback from Claude losing context).

---

## 11. Decisions taken (2026-10-17)
1. Altium: latest release, rules must also hold on the two previous major versions.
2. Altium automation: the three MCP servers used in the buck test, plus DelphiScript as fallback (names recorded in `project.yaml` → `tools:`).
3. Default fab profile: JLCPCB, with a conservative `generic` fallback.
4. Repo: public on GitHub, MIT licence. Built locally first, pushed later.
