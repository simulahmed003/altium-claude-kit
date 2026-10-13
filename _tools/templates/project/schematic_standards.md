# Schematic standards - {{NAME}}

Every schematic sheet must meet these rules before gate S1 (user approves it visually).
Check them on captures of the sheet (capwin.ps1 + crop.ps1) and with the checkers in _tools/scripts, never from coordinates alone. No PDF export through Altium (TOOL-07).

## a) Flow
- Left to right: input connector, reverse protection, input caps, IC, inductor, output caps, output connector.
- Power rails at the top, GND at the bottom. Signals flow one way.

## b) Blocks
- Group parts into labelled blocks, each drawn as a box with a title:
  "Input and reverse-polarity protection", "Buck converter (U1, L1, bootstrap)", "Output filter",
  "Feedback divider", "Enable and power-good", "Test points".
- No more than about 8 parts per block.

## c) Grid and spacing
- Every part on the 100 mil grid, pins on grid, one consistent orientation per part type.
- Generous space between parts and between blocks. Use the whole A3 sheet, or a larger one if needed.

## d) Text
- No overlapping text, ever.
- Designator and value sit outside the symbol body, never on a wire, a pin or another label.
- Text readable at 100 % zoom.

## e) Wires
- Straight and orthogonal. No wires through symbols or over text, no overlapping wires.
- Crossings only where unavoidable, with no junction dot, never near a pin.
- Junction dots only where nets connect.

## f) Connections
- Prefer a direct short wire. Use a net label only for long connections or key nets, placed clear of everything.
- Each decoupling capacitor sits directly beside the pin it serves, with its own ground symbol directly below it.

## g) Power ports
- VIN symbol at the top of each use, one GND symbol per cluster (not one per part).
- One consistent style, never overlapping text.

## h) Test points and DNP
- Test points sit at the net they probe, with a clear name.
- DNP parts are marked DNP and drawn dimmed or boxed.

## i) Title block and notes
- Fill the title block: title, revision, date, author.
- Notes go in one tidy box in its own free area inside the border: short lines, wrapped, no clipping, nothing over the border.
- Hot-loop and thermal notes sit next to U1.

## j) Designators and pins
- Designators sorted by block, no gaps, no duplicates.
- All pin names and numbers visible on the ICs and transistors (controller, MOSFETs).

## l) Symbol pins = footprint pads
- Every symbol has exactly the pins of its footprint: one visible pin per pad, same number, no hidden pins,
  no stacked pins. Checked by `_tools/scripts/pin_match.py <SchLib> <PcbLib> --style`; zero FAIL before a library goes to a sheet.

## m) Identical parts in a row
- Parts in a row with the same value keep their own designators but get ONE shared value line under (or beside)
  the row, format "<first>-<last>: <value> <voltage> <dielectric>" (e.g. "C6-C11: 22 uF 25 V X5R").
- The same value in two separate places (e.g. C4 and C12) is not a group: each part shows its own value.
- Every other part shows its designator once and its value once; test points show only their designator.

## n) Pin numbers readable
- Every pin number is readable: never under a wire, a junction dot or other text. Pins that fan into a bus
  wire are long enough (Q1 D/S: 200 mil) that the numbers sit clear between the body and the bus.
- Pin names stay inside the body and never touch each other; checked by _tools/scripts/sch_overlap.py.

## o) Test points
- One test point per net that needs probing, no duplicates (e.g. VIN, VOUT, SW, FB and one GND pad at the
  output). The planned net table (ai/plan.json) lists exactly these, so conn_check.py catches extras.

## p) Connectivity check after every change
- After ANY library update, part move or rewire: save the sheet and run
  `python ../../_tools/scripts/conn_check.py <sheet.SchDoc> ai/plan.json` (reads the saved file, every pin against the planned net
  table). It must report 0 mismatches before anything is reported as done. ERC must also run with unconnected
  pins / wires reported; the only waiver is "Nets with no driving source" (resistor-driven inputs).
- Update From Libraries resets per-instance Values (e.g. J1/J2 "12 V IN" / "5 V OUT"): re-apply them afterwards.

## q) Junction dots
- A junction dot only where 3 or more connection items meet at one point (wire ends, a wire passing through, pin
  ends, a power port on a wire). No dot where only 2 meet (pin + one wire, two wires end to end, a corner).
- Wires that meet end to end in a straight line are one wire; corners are plain bends.
- Every 3+ connection has a dot; wires never cross without one. Checked by _tools/scripts/dots.py, run inside conn_check.py.
- Altium keeps automatic dots as a cache that scripted edits do not refresh: after scripted wiring, close and reopen
  the sheet (Altium rebuilds the dots), save, then run conn_check.py.

## k) Acceptance
- ERC 0 violations.
- A stranger can trace VIN to VOUT in 30 seconds.
