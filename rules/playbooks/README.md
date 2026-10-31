# Playbooks

Status per step: TESTED = done successfully in the buck project or in a selftest (source given); UNTESTED = written from the tool docs, not yet run.

| Playbook | Read with | TESTED steps |
|---|---|---|
| [P1 New project](P1_new_project.md) | 01_WORKFLOW_GATES, 02_REQUIREMENTS_CALCS_PARTS, 08_COMMUNICATION | 7/7 |
| [P2 Add a component](P2_add_component.md) | 03_LIBRARY, 02_REQUIREMENTS_CALCS_PARTS | 6/7 |
| [P3 Build a schematic](P3_build_schematic.md) | 04_SCHEMATIC, 07_TOOLING_ALTIUM | 9/9 |
| [P4 Library change while the design is open in Altium](P4_library_change_in_altium.md) | 03_LIBRARY, 07_TOOLING_ALTIUM | 7/7 |
| [P5 PCB placement](P5_pcb_placement.md) | 05_PCB, 07_TOOLING_ALTIUM | 5/7 |
| [P6 Before presenting a gate (evidence pack)](P6_pre_gate_review.md) | 01_WORKFLOW_GATES | 5/5 |
| [P7 Commit and hand-off](P7_commit_handoff.md) | 01_WORKFLOW_GATES, 08_COMMUNICATION | 5/5 |
| [P8 Recover a wedged Altium](P8_recover_wedged_altium.md) | 07_TOOLING_ALTIUM | 5/6 |
| [P9 Production package, BOM and CPL](P9_production_package.md) | 06_FAB_OUTPUT, 02_REQUIREMENTS_CALCS_PARTS | 4/9 fully (3-7 by hand; tools new in 1.6.0) |
| [P10 JLCPCB assembly quotation](P10_jlc_quote.md) | 06_FAB_OUTPUT, 02_REQUIREMENTS_CALCS_PARTS | 7/7 by hand (jlc_quote.py new in 1.6.0) |
| [P11 New part in the local library (workflow)](P11_new_local_component.md) | 03_LIBRARY, 02_REQUIREMENTS_CALCS_PARTS | 10/11 (first version; placeholders for the user's detailed instructions) |
