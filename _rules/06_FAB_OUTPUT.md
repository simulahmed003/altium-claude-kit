# 06 Fab output

### FAB-01 No output before all gates
- MUST NOT: generate or send Gerbers, drill, BOM or pick-and-place to a fab before S1 and G1-G4 are ticked.
- Why: the gates exist to stop bad fabs.
- Check: gate_check.py G4 (refuses when earlier gates are open)
- Source: gates.md "Nothing is sent to a fab until G1-G4 are all ticked"
- Status: ENFORCED

### FAB-02 Gerber review
- MUST: open the output in a Gerber viewer and check layer count, outline, drills, silkscreen, mask, paste (G4).
- Why: output settings errors are invisible in Altium.
- Check: G4 checklist
- Source: gates.md G4
- Status: CHECKLIST

### FAB-03 Output through an OutJob
- MUST: generate outputs with an OutJob run by coffee (run_output_jobs), never with Altium print/PDF preview.
- Why: preview windows block the bridge (LESSONS T8).
- Check: checklist (at G4 confirm the files came from run_output_jobs, not from a preview)
- Source: LESSONS T8; approved by user 2026-10-13 (chat)
- Status: CHECKLIST

### FAB-04 BOM columns for JLCPCB
- MUST: BOM with Comment, Designator, Footprint, LCSC part number; hand-soldered parts excluded from the SMT order.
- Why: JLCPCB assembly upload format; J1/J2 are hand-soldered.
- Check: checklist
- Source: buck part_list.md (J1/J2 not in SMT order); JLCPCB BOM format not yet re-checked
- Status: PROPOSED
