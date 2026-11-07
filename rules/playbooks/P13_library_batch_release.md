# P13 Library batch: build, check and release to the Workspace

Read with: 09_LIBRARY_STANDARD, 03_LIBRARY, 07_TOOLING_ALTIUM.

Status per step: TESTED = done successfully in a project (source given); UNTESTED = written from the tool docs, not yet run.

| # | Step | Status |
|---|---|---|
| 1 | Plan the batch: one SchLib + PcbLib + LibPkg; per part the Type/Subtype (names without "/"), MPN as component name (LIB-14), Symbol name per kind (LIB-37), one IPC-7351B footprint per package (LIB-35, LIB-36). Datasheets local. | TESTED (SpeakerSystemV1 batch 1) |
| 2 | Back up the libraries to `History\` before every write step; one Altium instance only, opened by the user. | TESTED (SpeakerSystemV1 batch 1) |
| 3 | 3D models: KiCad models for standard packages, best-looking maker STEP for ICs and custom parts, recoloured to KiCad colours if off-standard; embed from inside Altium; read back pad box vs body box and look at each in 3D top view (TOOL-19). | TESTED (SpeakerSystemV1 batch 1) |
| 4 | Symbols: one drawing per kind of discrete from the best-looking maker or content-vault symbol, blue; IC, connector and module boxes brown outline on light yellow; pins renumbered to the datasheet (diode 1 = cathode); value text placed by the symbol (capacitance + voltage on capacitors, resistance on resistors), pin numbers hidden on R/C, all text navy (LIB-02, LIB-37). Review pictures rendered offline from the SchLib, not by switching symbols in Altium. | TESTED (SpeakerSystemV1 batch 1) |
| 5 | Scripts follow TOOL-18 (guard open documents, skip the on-screen part, proven properties only); a wedge goes to P8, never `X2.exe -REditScript:Stop`. | TESTED (SpeakerSystemV1 batch 1) |
| 6 | Checks, all green before upload: `pin_match.py <SchLib> <PcbLib>` (NPTH holes need no pin), `ws_lib_check.py <SchLib>`, `validate_library` on the PcbLib (0 errors; warnings explained), symbols and footprints of one size side by side. | TESTED (SpeakerSystemV1 batch 1) |
| 7 | Compile the LibPkg to an IntLib for the review document; Reviewer 1 and Reviewer 2 sign; then the Library Importer. A refused item (for example "Invalid tag HRID ... /") is fixed in the library and in every document that names it (category tree, parameter list, proposal, build plan), then the import is run again. | TESTED (SpeakerSystemV1 batch 1: FFC / FPC -> FFC & FPC) |
| 8 | Log decisions and open items in the batch `_decision_log.md`; new lessons go to docs\LESSONS_LEARNED.md and, after the user's yes, to the rules. | TESTED (SpeakerSystemV1 batch 1) |

8 of 8 steps TESTED.
