# passives / capacitor_mlcc

Multilayer ceramic capacitors.

Symbols of this family live in `capacitor_mlcc.SchLib` in this folder (rules LIB-10, LIB-11, LIB-15).

Maintainer: (unassigned)

## Contents

<!-- CONTENTS (lib_readmes.py refreshes this block; edit outside it) -->
| Symbol | MPN | Footprint | Rev |
|---|---|---|---|
| C_100n_50V_X7R_0603_CC0603KRX7R9BB104 | CC0603KRX7R9BB104 | CAPC1608_0603 | 2 |
| C_10u_50V_X7R_1206_1206B106K500NT | 1206B106K500NT | CAPC3216_1206 | 2 |
| C_1u_50V_X5R_0603_CL10A105KB8NNNC | CL10A105KB8NNNC | CAPC1608_0603 | 2 |
| C_220n_50V_X7R_0603_CC0603KRX7R9BB224 | CC0603KRX7R9BB224 | CAPC1608_0603 | 2 |
| C_22u_25V_X5R_1206_CL31A226KAHNNNE | CL31A226KAHNNNE | CAPC3216_1206 | 2 |
| C_DNP_0603 | - | CAPC1608_0603 | 1 |
<!-- /CONTENTS -->

## What goes in

- One symbol per pin list and kind, shared by every part with exactly that pin list (LIB-10). Values, MPNs and
  ratings are parameters, never a new symbol.
- Symbol name (also the Symbol parameter): the kind for discretes (Resistor, Capacitor, Capacitor Polarised,
  Diode, MOSFET P-Channel ...), drawn from the best-looking maker or content-vault symbol (LIB-19); the part's short
  name for ICs, connectors and modules (LMR33630, TPA3116D2).
- Component name: the MPN exactly as the maker writes it, one per MPN (LIB-14).

## Drawing standard (LIB-02, LIB-03, LIB-11)

- Pin ends on the 100 mil grid; line width 1 (small); discrete symbols blue (16711680); IC, connector and module boxes brown outline (128) on light-yellow fill; font size 10.
- Visible text: Designator and Comment (=Value) only; MPN, Manufacturer, LCSC, Datasheet and ratings hidden.
- One visible pin per pad, same number (LIB-01). Passive pins 100 mil (capacitor 80 mil), IC pins 200 mil.
- ICs: pins grouped as in the datasheet, power top, ground bottom, inputs left, outputs right, symmetric where
  the pinout allows, pin names exactly as in the datasheet.

## Facts the component database must hold for this family

`summary.capacitance`, `summary.tolerance`, `summary.rated_voltage`, `summary.dielectric`, `recommended.t_op`, `package.length`, `package.width`

## Adding or changing a symbol

By a person: close the library in Altium only when you are done, keep the drawing standard, then tell Claude in the
project. Claude runs `catalog_check.py` and `lib_status.py`, reports what changed and asks before adapting catalog
entries or project copies (LIB-16).

By Claude: build from the part record (`gen_sym.py`), dry-run into `libs/_dryrun/`, `pin_match.py --style`, user
check at G1, then `lib_promote.py` (LIB-09, LIB-11, P2).

## Notes and decisions

(add here)
