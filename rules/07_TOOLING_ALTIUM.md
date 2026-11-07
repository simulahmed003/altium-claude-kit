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
- MUST: recover with `kit altium_unstick --fix` first (TOOL-21); only when it says "still stuck" with no dialog left, Run > Stop (Fn+Ctrl+F3 on this Lenovo) through `bridge.cmd popup script_crashed`, else Ctrl+S then End task X2.EXE.
- Why: two crashes wedged the debugger and needed the user; on AD26 Cancel on the "Continue execution?" dialog stops the script without the user (wedge study 2026-11-07).
- Check: altium_unstick.py; popup script_crashed
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
- MUST NOT: edit tools\bridge\, .mcp.json or .claude\ (user controls them).
- Why: they control the safety hook.
- Check: checklist
- Source: workspace CLAUDE.md
- Status: CHECKLIST

### TOOL-18 Scripting a library safely
- MUST: before a run_altium_script that edits a library: (1) check with Client.GetDocumentByPath / GetSchDocumentByPath that every document it uses is open and stop with a GUARD message if not; (2) skip the component shown on screen (CurrentSchComponent / CurrentComponent), or switch the view to an untouched part first; (3) use only properties already proven in an earlier script, and try a new one read-only on one object first; (4) SandboxLog before each risky step; (5) back the file up to History\ first and save only after a read-back.
- MUST NOT: run `X2.exe -REditScript:Stop` (it can start a second Altium and a license conflict); a wedge goes to `kit altium_unstick --fix` (TOOL-21), then `bridge.cmd popup script_crashed` (P8).
- Why: on 2026-11-05 six wedges came from a closed source library, the on-screen symbol, and guessed properties (Model.Rotation_X, LayerObject_V7, IsHidden on labels).
- Check: checklist; the run's step log
- Source: SpeakerSystemV1 batch 1, LESSONS L10-L13
- Status: CHECKLIST

### TOOL-19 PcbLib coordinates and embedded 3D models
- MUST: add footprint primitives in the footprint's own frame: only the footprint shown in the editor sits at Board.XOrigin/YOrigin, every other one at 0,0; before any edit make a footprint the script does not touch current, and never switch the current footprint after an edit (Altium drops that edit). Embed STEP models from inside Altium (Body.ModelFactory_FromFilename(path, False)), never from outside. After a batch edit, read back every footprint (pads vs body box, one body, model file name) and look at it in 3D before saving.
- Why: Swap3D.pas added the origin twice and put 26 bodies 1270 mm from their pads; externally embedded models fail Altium's checksum and show as red boxes; the on-screen footprint's edit was lost.
- Check: read-back script (pad box vs body box); 3D capture
- Source: SpeakerSystemV1 batch 1, LESSONS L10, L11
- Status: CHECKLIST


### TOOL-20 Offline first, live Altium last
- MUST: do library and document edits offline when a tool can (altium_io.py, altium-lib, the review generators) and keep live Altium scripts for what only Altium can do (embed STEP models, compile an IntLib, output jobs, 3D captures, a check that a file loads); each live script edits one object type, with nothing it touches open on screen (TOOL-18).
- MUST: after 2 script wedges in one stage, stop scripting that stage: finish it offline or give the user the menu path (COM-05); never make the user press Ctrl+F3 a third time for the same stage.
- Why: one library session needed six Ctrl+F3 recoveries and a PCB session four, each an interruption for the user; the offline route did the same edits without a wedge.
- Check: checklist; `kit altium_unstick --today` counts the stuck runs
- Source: threads 2026-10-30 (4 script crashes in one stage), 2026-11-04 (6 wedges); LESSONS L12, M17; kit review 2026-11-07 (docs/KIT_REVIEW_2026-11.md)
- Status: CHECKLIST

### TOOL-21 Unstick Altium automatically, write scripts that cannot jam it
- MUST: run `kit pas_lint <script.pas>` before every live DelphiScript (no FAIL): saved as UTF-8 without BOM, no unfilled %TOKEN%, no message box or other modal in an agent script (write a log file instead), try/except or try/finally around edits, PcbLib edits only on non-current footprints (TOOL-19).
- MUST: on any timeout, "script never started", "executor_wedged" or "busy" result, run `kit altium_unstick --fix` before anything else; act on its "next:" lines; never retry the script before it says "Altium is free".
- MUST NOT: answer a question dialog (save, confirm, overwrite) or release the eda-agent loop without the user (app_detach saves every document).
- Why: the jams of 2026-11-04..07 came from five causes: a server older than its files, the eda-agent loop holding the only script engine, two script projects named Altium_API.PrjScr, X2.exe command lines that started a second Altium, and script errors (one a BOM); each needed the user to press Ctrl+F3 or answer a dialog.
- Check: pas_lint.py; altium_unstick.py (logs\altium_unstick.log); doctor.py
- Source: wedge study on the user's PC 2026-11-07 (docs/WEDGE_STUDY_2026-11.md); LESSONS W1-W6
- Status: ENFORCED

### TOOL-22 Restart after an update, no X2.exe command line while a dialog shows
- MUST: after `install.cmd /update`, `git pull` of tools\mcp\* or any server update, exit Claude Code and start it again (`kit start`) before the next live Altium step; `kit doctor` warns when a server runs older code than its files.
- MUST: fix what `kit doctor` reports yourself when a kit tool or a restart fixes it (a Remote Control agent restarts its own session; `kit coffee_script_rename`; restore a template a stale server rewrote); leave the user only what needs their hands or a decision.
- MUST NOT: start X2.exe with a command line (RunScript, -REditScript) while Altium shows a dialog: run `kit altium_unstick` first, it must report no dialog.
- Why: an update under a running coffee server made every script fail to compile ("Expression expected but % found", reported as "wedged"); a command line sent while a dialog was open started a second Altium ("another instance ... busy").
- Check: doctor.py (check 9); altium_unstick.py
- Source: wedge study 2026-11-07 (docs/WEDGE_STUDY_2026-11.md)
- Status: CHECKLIST
