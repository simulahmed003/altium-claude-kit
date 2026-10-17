# Roadmap

Built one module at a time and proven on the buck converter (12 V to 5 V, 3 A) before the next.
Status: ✅ done · 🔨 in progress · ⬜ not started

## How each module is built
1. **Rules first**: add or tighten rules in `rules/` (MUST, Why, Check, Source, Status). New rules start PROPOSED.
2. **Check second**: a script in `tools/scripts/` with a test, so the rule can be ENFORCED.
3. **Skill third**: a short skill in `.claude/skills/` from `docs/templates/SKILL_TEMPLATE.md`.
4. **Prove it** on the buck design. Record tokens, human corrections and datasheet opens per phase.
5. **Fix from evidence**: a correction made twice becomes a rule or a check (WF-04).
6. **Commit**: one PR per module; bump `rules/VERSION` when rules change.

## Done (from altium-claude-workspace, rules v1.1.0)
| Module | What exists |
|---|---|
| ✅ Workflow and gates | G1, S1, G2, G3, G4; `gate_check.py` evidence packs; rules WF-01..07 |
| ✅ Requirements, calcs, parts (base) | RQ-01..07; `calclib.py`, `calcs_run.py` |
| ✅ Library | LIB-01..08; `pin_match.py`, `gen_sym.py`; playbooks P2, P4 |
| ✅ Global library | catalog, category libs, promote / pull / update / status, content hashes; 16 buck parts |
| ✅ Schematic | SCH-A..S; `conn_check.py`, `dots.py`, `sch_overlap.py`, `sch_plan.py`; playbook P3 |
| ✅ Altium tooling | 3 MCP servers, guard hook, kill switch, popups; TOOL-01..17; playbook P8 |
| ✅ Docs and tests | setup guide, first-run tests, lessons learned, 56 tests + selftest, CI |
| ✅ Kit layer | skills folder + orchestrator draft, architecture, roadmap, AI-contributor guide |

## Next
### M1 Component facts database ⬜ (next)
`library/facts/` schema, `facts.py get / check / draft`, facts for the 16 buck parts, PROPOSED change to RQ-01.
Done when the buck schematic phase needs zero datasheet PDF opens for catalog parts.

### M2 Front of the flow ⬜
Requirements and architecture rules (with the planned G0 gate), part selection against facts, the first
`guidelines/` entries the user approves. Skills: requirements, architecture, part selection.

### M3 PCB rules from SEED to ENFORCED ⬜
PCB-01..12 checked by scripts (fab profile → Altium rules, `place.py` extensions), routing and copper pour rules,
silkscreen rules. Skills: pcb-setup, placement, routing. Done when the buck layout passes G2 with no rule left SEED.

### M4 Analysis ⬜
PDN / IR drop, thermal (beyond `junction_temp`), SI where it applies, SPICE runs through altium-eda. Skill: analysis.

### M5 Fab release ⬜
FAB-04 BOM approved, OutJob template, Gerber review checklist automated where possible. Skill: fab-release.

### M6 Wider support ⬜
Altium 25 and 24 tested (rules marked per version where they differ), more fab profiles, 4-layer stackups,
a second reference design by another contributor, `v1.0` release.

## Open (needs the maintainer)
- Approve the RQ-01 change in M1 once the facts DB works.
- Decide whether RQ-06 and RQ-07 move to `guidelines/` (see `guidelines/BACKLOG.md`).
