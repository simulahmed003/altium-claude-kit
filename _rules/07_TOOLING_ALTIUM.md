# 07 Tooling (Altium, MCP servers, bridge)

### TOOL-01 One script engine
- MUST: use the eda loop OR coffee, never both; the guard checks the eda loop before every coffee call.
- Why: Altium refuses a second script while the loop runs.
- Check: guard.ps1 (PreToolUse hook)
- Source: LESSONS T1
- Status: ENFORCED

### TOOL-02 Loop check is a read-only ping
- MUST NOT: use `eda-agent doctor` as a loop check (its canary runs save_all).
- Why: every check silently saved all documents.
- Check: lib.ps1 (Test-EdaLoop pings)
- Source: LESSONS T2
- Status: ENFORCED

### TOOL-03 Detach saves
- MUST: list open documents and announce before `app_detach` (it saves all modified documents).
- Why: saving is a write the user must expect.
- Check: checklist
- Source: LESSONS T3
- Status: CHECKLIST

### TOOL-04 Loop idle stop
- MUST: expect the eda loop to stop after 10 min idle; tell the user at once and give the restart path (File > Run Script > Altium_API > Dispatcher.pas > StartMCPServer).
- Why: calls failed silently after pauses.
- Check: checklist (app_ping before a batch)
- Source: LESSONS T4
- Status: CHECKLIST

### TOOL-05 Scripts that can wedge Altium
- MUST NOT: run blind exploratory DelphiScript. Prefer eda tools; stop after 2 crashes in one stage.
- MUST: recover with Run > Stop (Fn+Ctrl+F3 on this Lenovo), else Ctrl+S then End task X2.EXE.
- Why: two crashes wedged the debugger and needed the user.
- Check: checklist; popup script_crashed
- Source: LESSONS T5, T6, T7
- Status: CHECKLIST

### TOOL-06 DelphiScript limits
- MUST NOT: use TStringList.StrictDelimiter / DelimitedText or unverified rule API identifiers.
- Why: they crash the script engine in this Altium.
- Check: checklist
- Source: LESSONS T5, T6
- Status: CHECKLIST

### TOOL-07 No PDF export through Altium
- MUST NOT: call proj_export_image / print preview.
- Why: "Preview SCH" opens modal and blocks every tool.
- Check: checklist
- Source: LESSONS T8
- Status: CHECKLIST

### TOOL-08 Hook fail-closed
- MUST: keep `"onFailure":"block"` on the PreToolUse hook in .claude\settings.json (user edits it).
- Why: a timed-out hook lets the call through.
- Check: setup.ps1 writes it on new installs
- Source: LESSONS T9
- Status: ENFORCED

### TOOL-09 Verify the project file on disk
- MUST: after adding documents, check that the .PrjPcb on disk lists every document (DocumentPath= lines); a new PcbDoc may land in "Free Documents".
- Why: proj_save said success while the file listed nothing.
- Check: gate_check.py (project file check)
- Source: LESSONS T10, T11
- Status: ENFORCED

### TOOL-10 Saves are verified
- MUST: save with app_save_document and check the file time; `obj_modify ... saved:true` does not write the file.
- Why: checks ran on a stale file.
- Check: checklist
- Source: LESSONS T12
- Status: CHECKLIST

### TOOL-11 Update From Libraries
- MUST: the user runs the wizard; the ECO may show only symbol/parameter changes, never Add/Remove; afterwards re-apply instance Values, run conn_check.py and proj_get_differences, compare PCB positions to the last commit, and press End if the screen did not redraw.
- Why: J1/J2 values reset; U1/Q1 re-added off-board; a non-redrawn screen looked disconnected.
- Check: conn_check.py + checklist (playbook P4)
- Source: LESSONS T18, T19, T20
- Status: CHECKLIST

### TOOL-12 Junction cache
- MUST: after scripted wiring, close and reopen the sheet, save, run dots.py.
- Why: Altium keeps stale automatic dots.
- Check: dots.py
- Source: LESSONS T21
- Status: ENFORCED

### TOOL-13 Ghost ERC entries
- MUST: when ERC reports an object that is not in the sheet or the file, reload the sheet from disk and recompile before acting.
- Why: a ghost "Unconnected wire" survived three recompiles.
- Check: checklist
- Source: LESSONS T22
- Status: CHECKLIST

### TOOL-14 eda tool quirks
- MUST: use obj_modify (not obj_batch_modify with "|" in set); sch_mirror_component (not IsMirrored); delete wires by polyline start read from the file; designators only via a verified offline patch of the closed sheet.
- Why: each of these silently did nothing or the wrong thing.
- Check: checklist
- Source: LESSONS T13-T17
- Status: CHECKLIST

### TOOL-15 Screen evidence
- MUST: capture with capwin.ps1 and crop.ps1; ask the user for exact zoom/area when detail is needed.
- Why: eda zoom and screenshot do not work here.
- Check: checklist
- Source: LESSONS T16
- Status: CHECKLIST

### TOOL-16 Kill switch
- MUST: stop all Altium work when a result says "KILL SWITCH IS ENGAGED"; never bypass it.
- Why: user safety stop.
- Check: guard.ps1
- Source: workspace CLAUDE.md
- Status: ENFORCED

### TOOL-17 Protected files
- MUST NOT: edit _tools\bridge\, .mcp.json or .claude\ (user controls them).
- Why: they control the safety hook.
- Check: checklist
- Source: workspace CLAUDE.md
- Status: CHECKLIST
