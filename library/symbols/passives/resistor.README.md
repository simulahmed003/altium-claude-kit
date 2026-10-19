# passives / resistor

Fixed resistors: chip, thin film, current sense, through hole.

Symbols of this family live in `resistor.SchLib` in this folder (rules LIB-10, LIB-11, LIB-15).

Maintainer: (unassigned)

## Contents

<!-- CONTENTS (lib_readmes.py refreshes this block; edit outside it) -->
| Symbol | MPN | Footprint | Rev |
|---|---|---|---|
| R_100k_1%_0603_0603WAF1003T5E | 0603WAF1003T5E | RESC1608_0603 | 2 |
| R_10k_1%_0603_0603WAF1002T5E | 0603WAF1002T5E | RESC1608_0603 | 2 |
| R_20k0_0.1%_0603_PTFR0603B20K0P9 | PTFR0603B20K0P9 | RESC1608_0603 | 2 |
| R_4k99_0.1%_0603_PTFR0603B4K99P9 | PTFR0603B4K99P9 | RESC1608_0603 | 2 |
| R_51k_1%_0603_0603WAF5102T5E | 0603WAF5102T5E | RESC1608_0603 | 2 |
<!-- /CONTENTS -->

## What goes in

- One symbol per pin list and kind, shared by every part with exactly that pin list (LIB-10). Values, MPNs and
  ratings are parameters, never a new symbol.
- Symbol name: `<KIND>` for two-pin passives (RES, CAP, IND), `<KIND>_<n>P_<pin names>` for discretes
  (PMOS_8P_SSSGDDDD), `<base part>_<package code>` for ICs (LMR33630_DDA).
- Local project component name: `<prefix>_<value>_<key rating>_<package>_<MPN>`, one per MPN (LIB-14).

## Drawing standard (LIB-02, LIB-03, LIB-11)

- Pin ends on the 100 mil grid; line width 1 (small); one line colour; font size 10.
- Visible text: Designator and Comment (=Value) only; MPN, Manufacturer, LCSC, Datasheet and ratings hidden.
- One visible pin per pad, same number (LIB-01). Passive pins 100 mil (capacitor 80 mil), IC pins 200 mil.
- ICs: pins grouped as in the datasheet, power top, ground bottom, inputs left, outputs right, symmetric where
  the pinout allows, pin names exactly as in the datasheet.

## Facts the component database must hold for this family

`summary.resistance`, `summary.tolerance`, `summary.rated_power`, `abs_max.working_voltage`, `summary.tcr`, `recommended.t_op`, `package.length`, `package.width`

## Adding or changing a symbol

By a person: close the library in Altium only when you are done, keep the drawing standard, then tell Claude in the
project. Claude runs `catalog_check.py` and `lib_status.py`, reports what changed and asks before adapting catalog
entries or project copies (LIB-16).

By Claude: build from the part record (`gen_sym.py`), dry-run into `libs/_dryrun/`, `pin_match.py --style`, user
check at G1, then `lib_promote.py` (LIB-09, LIB-11, P2).

## Notes and decisions

(add here)
