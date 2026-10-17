# 05 PCB (SEED - enriched in the layout phase)

Fab values: JLCPCB 2-layer capabilities page https://jlcpcb.com/capabilities/pcb-capabilities, checked 2026-10-13
(copied in rules\fab-profiles\jlcpcb_2layer.json and the buck constraints.md). Design values keep margin.

### PCB-01 Stackup
- MUST: 2 layers, 1.6 mm FR-4, 1 oz outer copper unless the project says otherwise; set the core in Layer Stack Manager.
- Why: a new PcbDoc had 0.07 mm total thickness.
- Check: checklist (get_pcb_layer_stackup)
- Source: buck constraints.md; LESSONS B3
- Status: SEED

### PCB-02 Copper to board edge
- MUST: >= 0.5 mm.
- Why: stays legal if JLCPCB V-cut panelises (V-cut 0.4 mm).
- Check: checklist (DRC rule)
- Source: JLCPCB capabilities page, checked 2026-10-13
- Status: SEED

### PCB-03 Vias
- MUST: 0.3 mm drill / 0.6 mm pad; vias in a thermal pad tented both sides.
- Why: fab margin; solder wicking.
- Check: checklist (DRC rule)
- Source: JLCPCB page 2026-10-13; user G1 decision (6 tented EP vias)
- Status: SEED

### PCB-04 Trace and space
- MUST: design >= 0.20 mm trace / 0.20 mm space (0.30 where room allows).
- Why: margin over 0.10/0.10 mm (1 oz).
- Check: checklist (DRC rule)
- Source: JLCPCB page 2026-10-13
- Status: SEED

### PCB-05 Power path width
- MUST: >= 1.4 mm for 3 A (1 oz outer, 10 C rise) or a copper pour.
- Why: IPC-2221 width for the current.
- Check: calclib.py trace_width_ipc2221
- Source: buck calcs.md (1.37 mm at 3 A)
- Status: SEED

### PCB-06 Silkscreen
- MUST: text height >= 1.0 mm, line >= 0.15 mm, off pads.
- Check: checklist (DRC rule)
- Why: legibility at the fab.
- Source: JLCPCB page 2026-10-13
- Status: SEED

### PCB-07 Solder mask web
- MUST: >= 0.10 mm (green, 1 oz).
- Why: fab capability.
- Check: checklist (DRC rule)
- Source: JLCPCB page 2026-10-13
- Status: SEED

### PCB-08 Hole to hole
- MUST: >= 0.5 mm.
- Why: margin over 0.45 mm pad hole-hole.
- Check: checklist (DRC rule)
- Source: JLCPCB page 2026-10-13
- Status: SEED

### PCB-09 PTH annular ring
- MUST: >= 0.25 mm.
- Why: hand-soldered connectors.
- Check: checklist (footprint)
- Source: JLCPCB page 2026-10-13
- Status: SEED

### PCB-10 Ground and hot loop
- MUST: solid bottom GND plane with minimal slots under the power stage; input caps and IC form the smallest hot loop; SW copper small.
- Why: switching noise and EMI.
- Check: G2 checklist
- Source: buck constraints.md; lmr33630.pdf layout section
- Status: SEED

### PCB-11 Thermal gate
- MUST: meet the project's thermal target (buck: RthJA <= 55 C/W at the IC pad, else derate Vin max to 15 V).
- Why: junction temperature margin.
- Check: G2 checklist; calclib.py junction_temp
- Source: buck calcs.md; user decision 2026-10-13
- Status: SEED

### PCB-12 Placement method
- MUST: place with set_component_position one part at a time, then check_placement; read flags by type (courtyards may touch, not overlap).
- MUST NOT: place with a batch DelphiScript.
- Why: the batch script wedged Altium; check_placement flags touching outlines.
- Check: checklist
- Source: LESSONS B1, B2, T5
- Status: SEED
