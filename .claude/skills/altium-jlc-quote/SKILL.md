---
name: altium-jlc-quote
description: Get JLCPCB PCB + assembly quotes for one or more boards at several quantities through the browser, including the full cost when parts are short on stock, and deliver an Excel workbook and a screenshot document; use when the user asks for a JLC (PCBA) quotation or price.
---

## Goal
For every board and quantity: the JLC quote with its full breakdown, and the total as if nothing were short, from
the same files that will be sent (FAB-08). The user can forward the workbook as it is.

## Inputs
- a production package that passes `fab_package.py check` (skill altium-fab-package, P9)
- the quantities, assembly type (default Standard) and anything the board's fab notes ask for
- the browser: Claude in Chrome or Edge with the Claude extension; the user logs in to jlcpcb.com

## Rules to load
- `rules/06_FAB_OUTPUT.md` (FAB-06, FAB-08), `rules/02_REQUIREMENTS_CALCS_PARTS.md` (RQ-08)
- playbook `rules/playbooks/P10_jlc_quote.md`; rates in `rules/fab-profiles/jlcpcb_assembly.json`

## Approach
1. Never type a password, never add to cart, order or pay. Stop at the quote page.
2. Board options come from the README and the board's own notes (via filling, finish), the same for every quantity.
3. The BOM match and the placement preview come before any price: a quote of the wrong parts is worthless.
   Short or unmatched lines: stock alternate per RQ-08, ask before changing an IC or connector.
4. Shortfall at a quantity: let JLC quote without the short lines, then add them back with `jlc_quote.py shortfall`
   using today's rates read from the quotes. Arithmetic in code only (RQ-02).
5. Screenshot every preview and every quote; name them board_qty_what.png.
6. Small boards at 1000+: point out the single-board surcharge and propose a panel.

## Exit checks
| Check | How | Pass when |
|---|---|---|
| FAB-06 | preview, part by part | every polar/multi-pin part confirmed, before/after screenshots kept |
| FAB-08 | `python tools\scripts\jlc_quote.py summary ai\quote_*.json --csv ...` | every board x quantity has quoted and full totals |
| deliverables | workbook (Summary, JLC breakdown, Shortfall calc, Specs and BOM notes) + document | both in the user's folder |

## Write back
- `PROJECT.md`: totals, BOM substitutes, open questions; `rules/fab-profiles/jlcpcb_assembly.json` if a rate changed
  (date and source)

## Escalate when
Login needed; a part has no in-stock alternate with the same rating and footprint; JLC asks to confirm a part or
order; a price breakdown line cannot be explained.
