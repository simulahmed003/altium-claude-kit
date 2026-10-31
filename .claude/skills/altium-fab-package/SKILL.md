---
name: altium-fab-package
description: Build and check the production package for the manufacturer (Gerber zip, BOM, CPL, README, optional assembly drawing) from an Altium or KiCad design, with BOM alternates and a CPL checked by numbers; use when the user asks for fab, production or assembly files.
---

## Goal
One folder `Manufacturing_<board>_Rev<x.y>\` next to the design that the user can send as it is: Gerber zip, BOM
and CPL as separate files, README, optional assembly drawing, never the schematic (FAB-05). The BOM matches the
design and every line is buildable (FAB-04, FAB-07, RQ-08); the CPL puts pin 1 where our pad 1 is (FAB-06).

## Inputs
- the design in the user's own folder (WF-09); `_eda\PROJECT.md` and `gates.md` when the project is attached
- the Gerber/drill output, the CAD placement file, the BOM exported from the design
- part records (`parts.py get`) for ratings when an alternate is needed

## Rules to load
- `rules/06_FAB_OUTPUT.md` (FAB-01, FAB-04..07), `rules/02_REQUIREMENTS_CALCS_PARTS.md` (RQ-08, RQ-09)
- playbook `rules/playbooks/P9_production_package.md`; `rules/fab-profiles/jlcpcb_assembly.json`

## Approach
1. Gates first (FAB-01). If the user asks for files before G1-G3 are ticked, ask for the sign-off in one line.
2. BOM before CPL: a wrong LCSC number on the BOM is a wrong part on the board; a wrong rotation is a reflow.
   Read every line: value, rating and footprint of the LCSC part against the MPN. Different number, same rating and
   footprint: acceptable, but list it with its rating check and get the user's yes before applying it (RQ-08). Lower rating, other value, shared number: fix it and write it back to the design.
3. Keep Mouser and DigiKey columns (FAB-04); numbers not confirmed on their page are UNCONFIRMED (RQ-09).
4. CPL by numbers only: convert, fit the JLC footprints by pin number, apply offsets, then the preview part by part.
   A misfit pad is a library bug, not a rotation.
5. Backups before changing any design file (name.ext.before_<what>.bak), reference files in `<pkg>\reference\`.

## Exit checks
| Check | How | Pass when |
|---|---|---|
| FAB-04, FAB-07, RQ-08 | `python tools\scripts\bom_check.py <bom> --cpl <cpl>` | PASS |
| FAB-06 | `cpl_check.py check <cpl> --bom <bom> --bbox ...` + preview screenshots | PASS, every polar/multi-pin part confirmed |
| FAB-05 | `python tools\scripts\fab_package.py check <pkg>` | PASS |

## Write back
- `PROJECT.md`: BOM changes (designator, old, new, why), CPL offsets found, open questions
- `_eda\ai\cpl_offsets.json` (or `ai\`): confirmed footprint offsets for reuse

## Escalate when
An IC, module or connector needs another MPN; a value in the design looks wrong (5.24K that no maker makes); a
DRC item below the fab's limit; a pad does not fit by pin number.
