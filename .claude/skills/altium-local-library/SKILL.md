---
name: altium-local-library
description: Add a part that the project's local library does not have yet: named by its MPN, symbol, footprint and 3D model copied from the database library, parameters with LCSC, Mouser and DigiKey numbers, checked against the datasheet; use whenever a schematic needs a new component. First version, the user's detailed instructions will follow.
---

## Goal
A local library component per MPN that the BOM can be built from directly, whose symbol and footprint have been
checked against the datasheet by the agent before it is reported placed (LIB-14, LIB-17, LIB-18).

## Inputs
- the MPN (or LCSC number) and the project's local library (`libs\` or the project's LIB folder)
- the part record (`parts.py get <MPN>`), the database library (kit global library, or the user's DbLib)

## Rules to load
- `rules/03_LIBRARY.md` (LIB-04, LIB-10..18), `rules/02_REQUIREMENTS_CALCS_PARTS.md` (RQ-01, RQ-03, RQ-09)
- playbook `rules/playbooks/P11_new_local_component.md` (and P2, P4 for writing libraries)

## Approach
1. Record first (RQ-01): no record, no component. Datasheet from the maker first, LCSC second.
2. Reuse before build (LIB-10): copy the symbol, footprint and 3D model from the database library; a similar part's
   item is only a starting point and is checked like a new one.
3. Name = MPN exactly. Parameters from the record, all hidden except Comment (LIB-14). LCSC, Mouser, DigiKey
   confirmed on their pages or written UNCONFIRMED (RQ-09).
4. The datasheet check is yours, every time, even under time pressure (LIB-18): pins, pads, holes, pin 1, package.
   Say what you checked and any mismatch in the report.
5. PLACEHOLDER (user instructions pending): source order DbLib vs kit library, local file layout for work projects,
   parameter names and order, flow back to the database. Until then: ask once if the choice matters.

## Exit checks
| Check | How | Pass when |
|---|---|---|
| LIB-01..03 | `python tools\scripts\pin_match.py <SchLib> <PcbLib> --style` | PASS |
| LIB-18 | report lists pins, pads and package checked against datasheet pages | every new or copied item |
| RQ-01 | `python tools\scripts\parts.py check <MPN>` | PASS |

## Write back
- `PROJECT.md`: components added, their source (copied from / built), mismatches found and their decision

## Escalate when
The datasheet and the copied footprint disagree (hole size, pitch, pin order); no record can be built (no
datasheet); a DbLib is read-only and the user wants the change in the database itself.
