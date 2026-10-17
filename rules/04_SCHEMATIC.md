# 04 Schematic

Letters follow the project schematic_standards.md (a-q). Source for all: buck S1 reviews, 2026-10-13.

### SCH-A Flow
- MUST: draw left to right (input, protection, input caps, IC, inductor, output caps, output); power rails on top, GND at the bottom.
- Why: a stranger traces VIN to VOUT quickly.
- Check: checklist (capture)
- Source: user S1 brief 2026-10-13
- Status: CHECKLIST

### SCH-B Blocks
- MUST: group parts into titled blocks with thin boxes (about 8 parts max). No box line through a symbol, text or GND glyph; wires may cross a box line only to enter or leave.
- Why: box lines cut U1's GND symbol and the FB wire.
- Check: sch_overlap.py (box-line checks)
- Source: LESSONS S4
- Status: ENFORCED

### SCH-C Grid and spacing
- MUST: place parts, wires and pin ends on the 100 mil grid with generous space; use the whole sheet.
- Why: off-grid parts give near-miss wires.
- Check: sch_overlap.py (grid check)
- Source: user S1 brief
- Status: ENFORCED

### SCH-D Text
- MUST: no overlapping text; designator and value outside the body, horizontal, never on a wire, pin or label; a value is closest to its own part and >= 200 mil from any test point.
- Why: C12's value read as TP8's; rotated and stacked text.
- Check: sch_overlap.py
- Source: LESSONS S6
- Status: ENFORCED

### SCH-E Wires
- MUST: straight orthogonal wires; no wire through a symbol or text; no overlapping wires; crossings only when unavoidable, never near a pin.
- Why: readability and false connections.
- Check: dots.py (overlap, crossing), sch_overlap.py
- Source: user S1 brief
- Status: ENFORCED

### SCH-F Connections
- MUST: prefer a direct short wire; net labels only for long or key nets; one label per net where first used; every decoupling cap beside its pin with its ground symbol below.
- Why: auto-named nets and scattered labels.
- Check: checklist
- Source: LESSONS S3
- Status: CHECKLIST

### SCH-G Power ports
- MUST: VIN symbol on top of each use; one GND symbol per cluster; one style; never on text.
- Why: 30 scattered ports on the first sheet.
- Check: checklist + sch_overlap.py (port text)
- Source: user S1 brief
- Status: CHECKLIST

### SCH-H Test points and DNP
- MUST: test points sit on the net they probe; DNP parts are marked DNP and drawn in a dashed box.
- Why: readability.
- Check: checklist
- Source: user S1 brief
- Status: CHECKLIST

### SCH-I Title block and notes
- MUST: fill title, revision, date, author, sheet x of y; notes in one box, one text per line, inside the border, numbers only from calcs.md.
- Why: the notes frame lost line breaks and ran over its border.
- Check: sch_overlap.py (frame fit); checklist (numbers vs calcs.md)
- Source: LESSONS S5
- Status: ENFORCED

### SCH-J Designators
- MUST: designators sorted by block, no gaps, no duplicates; all pin names and numbers visible on ICs and transistors.
- Why: readability; duplicate designators merge nets silently.
- Check: conn_check.py (duplicate designators)
- Source: user S1 brief
- Status: ENFORCED

### SCH-K ERC
- MUST: ERC 0 errors 0 warnings; the only allowed waiver is "Nets with no driving source" for resistor-fed inputs, each net listed in the project waivers.md.
- Why: EN, FB and a gate pull-down are driven by resistors only.
- Check: checklist (ERC counts in the evidence pack; MCP-sourced)
- Source: LESSONS T23
- Status: CHECKLIST

### SCH-L Pins = pads
- MUST: see LIB-01.
- Why: see LIB-01.
- Check: pin_match.py
- Source: LESSONS L1
- Status: ENFORCED

### SCH-M Identical parts in a row
- MUST: identical parts in a row keep their own designators and share ONE value line "<first>-<last>: <value> <voltage> <dielectric>".
- Why: six identical value texts crowded the output row.
- Check: checklist
- Source: user 2026-10-13
- Status: CHECKLIST

### SCH-N Pin numbers readable
- MUST: every pin number readable: never under a wire, dot or text; use 200 mil pins where pins fan into a bus.
- Why: Q1 numbers hidden under bus dots.
- Check: sch_overlap.py (pin number check)
- Source: LESSONS L2
- Status: ENFORCED

### SCH-O One test point per net
- MUST: one test point per probed net, no duplicates.
- Why: three GND test points were redundant.
- Check: conn_check.py (test points per net)
- Source: LESSONS S7; user rule o 2026-10-13
- Status: ENFORCED

### SCH-P Connectivity check after every change
- MUST: after any library update, part move or rewire, save the sheet and run conn_check.py (every pin vs plan.json) BEFORE reporting that it is fine.
- Why: claims were made from the plan, not the file.
- Check: conn_check.py
- Source: LESSONS S8, S10
- Status: ENFORCED

### SCH-Q Junction dots
- MUST: a dot exactly where 3 or more connection items meet (wire ends, a wire passing through, pin ends, a power port on a wire); merge straight end-to-end wires; corners are plain bends.
- Why: stale and unnecessary dots at corners and pin ends.
- Check: dots.py (also run by conn_check.py)
- Source: LESSONS S9, T21; user rule q 2026-10-13
- Status: ENFORCED

### SCH-R Build order
- MUST: library symbols -> plan.json -> coordinate plan on the 100 mil grid with blocks -> place by coordinates -> wires (merge collinear) -> text pass -> headings, boxes, title block, notes -> checkers -> captures -> own review -> user.
- MUST NOT: auto-place and then rework.
- Why: this order produced the clean sheet; auto-layout produced the unreadable one.
- Check: playbook P3
- Source: LESSONS S1
- Status: CHECKLIST

### SCH-S Read real coordinates
- MUST: read pin ends, wires and text from the saved sheet file, never from the plan.
- Why: plan coordinates went stale after library updates and moves.
- Check: conn_check.py, dots.py, sch_overlap.py all read the saved file
- Source: LESSONS S8
- Status: ENFORCED
