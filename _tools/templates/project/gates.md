# Human sign-off gates - {{NAME}}

Claude must stop and ask at each gate. Only the user ticks a box.

- [ ] **G1 Footprints** - every new footprint printed at 1:1 and compared with the datasheet land pattern and package drawing
- [ ] **S1 Schematic readability** - approved visually by the user against schematic_standards.md (captures with capwin.ps1 + evidence ai/review/S1_evidence.md from gate_check.py; no PDF export, TOOL-07)
- [ ] **G2 Layout** - placement, power loops, return paths, thermal copper and stackup reviewed on screen
- [ ] **G3 DRC and audit** - DRC clean (or each waiver explained), eda-agent audit reviewed, schematic/PCB net cross-check done
- [ ] **G4 Gerbers** - output opened in a Gerber viewer: layer count, outline, drills, silkscreen, mask, paste checked

Evidence for every gate: `python ../../_tools/scripts/gate_check.py <gate> .` writes ai/review/<gate>_evidence.md (playbook P6).
Nothing is sent to a fab until S1 and G1-G4 are all ticked. Layout (G2 work) starts only after S1.

## G1 checklist (fill per project)
- [ ] **G1 symbol-footprint check** - `python ../../_tools/scripts/pin_match.py libs/{{NAME}}.SchLib libs/{{NAME}}.PcbLib --style` reports PASS for every symbol (pins = pads one to one, none hidden, none stacked)
