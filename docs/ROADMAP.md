# Roadmap

How this kit gets built: one skill at a time, each proven on the buck-converter pilot before the next.
Status: ✅ done · 🔨 in progress · ⬜ not started

## How we build each module (the cycle)

1. **Rules first.** Write or update the rule file(s) the phase needs, numbered, one line + reason each.
2. **Tool second.** Write any script that turns a rule into a check or a calculation.
3. **Skill third.** Write `SKILL.md` from the template: goal, inputs, rules to load, exit checks, write-back.
4. **Prove it on the pilot.** Run the phase on `examples/buck-converter/` and log: tokens, human interventions, PDF opens, failed checks.
5. **Fix from evidence.** A correction needed twice becomes a rule or a check, not more prompt text.
6. **Commit and tag.** One PR per module; tag a release when a milestone closes.

## Defaults until decided

| Question | Default used | Change it in |
|---|---|---|
| Altium version | Latest Altium Designer release; rules and scripts must also work on the two previous major versions | `project.yaml` → `altium_version` |
| Altium 365 features | not assumed | `project.yaml` → `tools:` |
| Altium automation | The three MCP servers already used in the buck test, DelphiScript fallback; confirmed in M3 | `docs/ARCHITECTURE.md` §6 |
| Fab house | JLCPCB (cheapest prototype route, LCSC parts) with a `generic` conservative fallback | `project.yaml` → `fab_profile` |
| Licence | MIT for code and docs | `LICENSE` |

## Milestones

### M0 Skeleton ✅
Repo layout, `CLAUDE.md`, README, usage, contributing, AI-contributor guide, project template, part schema,
skill/rule templates, `comp` with `new-project`, `index`, `search`, `get`, `validate`, `pull`.

### M1 Component database ⬜ (next)
| Item | Done when |
|---|---|
| `comp ingest` (PDF → draft `part.yaml` + `digest.md`) | a datasheet becomes a valid draft record with page refs |
| Buck pilot parts in DB (~10) | all `comp validate` clean, critical ones `verified` |
| `comp push` (branch + PR) | a new part reaches GitHub without manual git |
| Measure | buck schematic data needs 0 PDF opens |

### M2 Library and CAD ⬜
`rules/schlib.md`, `rules/pcblib-footprint.md`, `rules/cad-models.md`; `comp cad` via the JLC/LCSC route
(easyeda2kicad → Altium import, or a direct converter); `lib/` build into `Project.SchLib`/`Project.PcbLib`;
skill `altium-library-cad`. Done when Altium opens the pilot libs with correct pin-to-pad mapping.

### M3 Altium bridge ⬜
Pick and test the Altium automation route; wrappers in `tools/altium/` for: place part, connect, import rules,
run ERC/DRC, export reports. `tools/reports/` parsers return 10-line summaries.

### M4 Schematic ⬜
`rules/schematic-design.md`, `rules/schematic-format.md`; `tools/calc/buck.py` and an LTspice/ngspice batch run;
skills `altium-schematic-design`, `altium-schematic-review`. Done when the buck schematic passes ERC with all
calcs in `calc/` and no human correction.

### M5 PCB layout ⬜
`rules/design-rules.md`, `rules/placement.md`, `rules/routing-polygons.md`, `rules/fab-profiles/jlcpcb.yaml`;
skills `altium-pcb-setup`, `altium-placement`, `altium-routing`. Done when buck layout passes DRC; compare
tokens and interventions against the original manual attempt.

### M6 Analysis, silkscreen, release ⬜
`rules/pdn-thermal.md`, `rules/si.md`, `rules/silkscreen.md`; skills `altium-analysis`,
`altium-silkscreen-dfm`, `altium-fab-release`; release audit script. Done when the buck produces a complete,
audited fab package.

### M7 Front of the flow ⬜
Skills `altium-requirements`, `altium-architecture`, `altium-component-selection`; full orchestrator routing
and rework loop. Done when the buck runs end to end from a one-paragraph brief.

### M8 Open for contributors ⬜ → release v0.1
CI running `validate` + pilot regression, issue templates in use, `v0.1` tag, a second example design by
someone other than the maintainer.

## Later (open to contributors)
EMC pre-check, DFT/testability, high-speed interfaces (USB, DDR), mixed-signal, more fab profiles,
more CAD sources (SnapEDA, Ultra Librarian, SamacSys), part-sourcing and lifecycle checks.

## Metrics we track per phase
Tokens used · human interventions · datasheet PDF opens · failed checks · rework loops.
The buck pilot's first manual run is the baseline.
