# Lessons learned

Workspace-level record. One row per incident or finding. Newest project first, oldest row first inside it.
Rule IDs point to `rules\` (see `rules\00_INDEX.md`). Sources: `logs\MCP_LOG.md`, git log, buck project `ai\*`,
`PROJECT.md`, `gates.md`, user reviews (`projects\buck-12v-5v-3a\ai\review\`).

## Project buck-12v-5v-3a (2026-10-13)

### Tooling (Altium, MCP, bridge)

| # | Symptom | Cause | Fix | Rule |
|---|---|---|---|---|
| T1 | coffee call timed out; Altium said it cannot run another script | Altium has ONE script engine; the eda loop held it | Guard checks the eda loop on every coffee call and asks to release it | TOOL-01 |
| T2 | Every loop check silently saved all open documents | `eda-agent doctor` canary sends `application.save_all` | Loop check is a read-only ping, never `doctor` | TOOL-02 |
| T3 | `app_detach` saved documents | Detach runs `save_all` first | Announce it, get a yes, list open docs first | TOOL-03 |
| T4 | eda calls failed after a pause | eda loop stops itself after 10 min idle | Keep it busy or tell the user to restart it (File > Run Script > StartMCPServer) | TOOL-04 |
| T5 | Coffee placement script wedged Altium in the debugger | DelphiScript has no `TStringList.StrictDelimiter` / `DelimitedText` | One explicit block per object; no string parsing in scripts | TOOL-06 |
| T6 | Read-only rule probe wedged Altium again | Some rule API identifiers are invalid in this Altium | No blind exploratory scripts; stop after 2 crashes; use eda tools | TOOL-05 |
| T7 | Recovery needed after a wedge | Debugger paused | Run > Stop (Fn+Ctrl+F3 on this Lenovo); else Ctrl+S, then End task X2.EXE | TOOL-05 |
| T8 | PDF export opened "Preview SCH" and blocked every tool | `proj_export_image` runs Altium print preview (modal) | Never export PDF through Altium; review with window captures | TOOL-07 |
| T9 | A PreToolUse hook timeout let the call through | Hooks are fail-open by default | `"onFailure":"block"` in `.claude\settings.json` (user edit); setup.ps1 writes it on new installs | TOOL-08 |
| T10 | Update PCB said "no primary PCB document" | New PcbDoc attached to "Free Documents" | Add it to the project, save the project, check the .PrjPcb on disk | TOOL-09 |
| T11 | `proj_save` said success; .PrjPcb on disk listed no documents | Project save does not write the file in this build | User saves the project in Altium; script checks `DocumentPath=` lines | TOOL-09 |
| T12 | `obj_modify` said `saved:true`; file on disk was old | It does not write the file | `app_save_document`, then check the file time | TOOL-10 |
| T13 | `obj_batch_modify` matched nothing | It mis-parses a `set` that contains `|` | Use `obj_modify` per object | TOOL-14 |
| T14 | `IsMirrored=true` did not mirror J1 | The property only sets a flag | `sch_mirror_component` | TOOL-14 |
| T15 | Wire deletes by start point missed wires | Altium merges connected segments into polylines | Read wires from the saved file, filter by the polyline start | TOOL-14 |
| T16 | `app_screenshot` failed; `obj_zoom` did not move the view | No pywin32/Pillow; zoom calls are ignored | `capwin.ps1` (PrintWindow) + `crop.ps1`; ask the user for exact zooms | TOOL-15 |
| T17 | Designators could not be moved or rotated | Designator location is not writable through eda | Offline patch of the closed sheet (`patch_designators.py`, verified, backup) | TOOL-14 |
| T18 | After Update From Libraries J1/J2 showed "MKDS..." again | The update resets per-instance Values | Re-apply instance Values after every update | TOOL-11 |
| T19 | U1 and Q1 came back off-board, U1 at 0 deg | PCB ECOs at 12:58/12:59 re-added them (new unique IDs) | ECO must show only symbol/parameter changes; restore positions; compare PCB to the last commit | TOOL-11 |
| T20 | User saw a gap at Q1's pins; file and netlist were fine | Screen not redrawn after the update | Press End; trust the file + conn_check, not the screen | TOOL-11 |
| T21 | Dots at 2-wire corners and pin ends | Altium caches automatic dots; scripted edits do not refresh them | Close and reopen the sheet, save, run dots.py | TOOL-12 |
| T22 | ERC kept an "Unconnected wire" that was in neither the sheet nor the file | Stale compile memory | Reload the sheet from disk, recompile | TOOL-13 |
| T23 | No-ERC markers did not clear "Nets with no driving source" | The check is net-level | Project waiver (Error Reporting > No Report), listed in waivers | SCH-K |
| T24 | altium-lib refused / risked writing an open library | File is locked or Altium would overwrite it | Close the library in Altium first; dry run; .bak; validate 0/0 | LIB-04 |
| T25 | Pin names touched (PGND vs VCC) | altium-lib cannot set the pin-name offset | Widen the body; keep pin ends fixed | LIB-07 |
| T26 | Cross-library copy dropped the footprint's 3D model reference | Default `preserve_external_paths=false` | Always copy footprints with `preserve_external_paths=true` | LIB-06 |
| T27 | altium-lib cannot write `D:\EDA\library` | Not in `allowed_paths` of `%USERPROFILE%\.altium-designer-mcp\config.json` | User adds the path and restarts Claude | LIB-06 |
| T28 | Usage limit interrupted long runs | Session budget | Progress file + one commit per part | WF-05 |
| T29 | Footprint hash differed after an altium-lib round trip that compare_components called identical | The last 2 bytes of pad block 6 (size-and-shape block) are the corner radius % (uint16) of the pad's one entry in the newer per-layer table at the end of the block (entry = 15 bytes: layer, shape 9 = rounded rectangle, size X, size Y, corner radius). The legacy 32-layer corner radius array earlier in the same block says 25 % in both writers; altium-lib writes 50 (0x32) into the newer entry, Altium writes 25 (0x19). Only rounded-rectangle pads with an extended block carry it (TB, TP and the IC/MOSFET pin-1 pads have none). Evidence: buck.PcbLib b6d1e54 (written by altium-lib) = (25, 50); bb608e7 (after Altium saved it) = (25, 25), so Altium takes the legacy 25 % and rewrites the entry. altium-lib read_pcblib also reports 25 %. | `altium_io.footprint_hash` drops those 2 bytes (Altium ignores them). Not yet seen in Altium 26 on a file Altium has not re-saved: open library\libs\passives.PcbLib, footprint RESC1608_0603, pad 1, Properties > Corner Radius must read 25 %. If it reads 50 %, the hash must keep the bytes and the copies must be re-saved in Altium. | LIB-06 |
| T30 | Shell heredoc / sed broke Windows paths in generated files (\r became a carriage return, \c a control byte) | Git Bash escape handling | Write generator scripts to a file with the Write tool; use forward slashes in docs paths | - (no rule yet) |

### Library

| # | Symptom | Cause | Fix | Rule |
|---|---|---|---|---|
| L1 | Q1 showed only D, S, G | Stacked pins (one visible per group) | Pins = pads, one visible pin per pad, `pin_match.py` | LIB-01 |
| L2 | Pin numbers 2, 3, 6, 7 hidden under bus dots | 100 mil pins too short for a bus | 200 mil pins where pins fan into a bus | SCH-N |
| L3 | Every value showed twice | Instance Value visible + library Comment `=Value` visible | Only Designator + Comment `=Value` visible; hide all other parameters | LIB-02 |
| L4 | Heavy red cap plates, mixed styles | Line width 2, default colours | One style per symbol type, line width 1, one colour | LIB-02 |
| L5 | Symbol edit would break wiring | Pin ends moved | Keep pin connection points fixed when editing a placed symbol | LIB-08 |
| L6 | Passive datasheets had no land pattern | Not published | Derived land with a "derived" flag and source | LIB-05 |
| L7 | SOIC8 land not checked against an AOS drawing | No drawing in the datasheet | "unverified-accepted" status carried into every reuse | LIB-05 |
| L8 | Inductor rule impossible (DCR, size) | No compliant part with a datasheet | Deviation logged, user approved | RQ-05 |
| L9 | C-numbers from memory | Not verified | Count only when the JLCPCB/LCSC page confirms MPN + package | RQ-03 |

### Schematic

| # | Symptom | Cause | Fix | Rule |
|---|---|---|---|---|
| S1 | First sheet unreadable (overlaps, loops, scattered ports) | Automatic layout engine | Coordinate plan on 100 mil grid, place by coordinates | SCH-R |
| S2 | `design_execute_plan` blocked | Q1 stacked pins not netted in the plan | Plan lists every pin | SCH-P |
| S3 | Wired nets got auto names | No net labels | One label per key net | SCH-F |
| S4 | Block box lines through GND symbols and text | Boxes drawn before text was checked | `sch_overlap.py` box-line check | SCH-B |
| S5 | Notes frame lost line breaks / text outside frame | Frame newline not kept; frame too small | One label per line; frame-fit check | SCH-I |
| S6 | C12 value read as TP8's | Value closer to another part | Nearest-part and 200 mil-from-TP check | SCH-D |
| S7 | Duplicate test points | Over-reading "GND pair" | One test point per net | SCH-O |
| S8 | Claimed "connected" from the plan | Plan coordinates, not the file | Read real pin ends from the saved file | SCH-S |
| S9 | Dots where only 2 items meet | Stale cache + unmerged straight joins | Merge collinear joins; dots only at 3+ items | SCH-Q |
| S10 | Reported "fine" before checking after a library update | No mandatory check | `conn_check.py` before every report | SCH-P |

### Process and communication

| # | Symptom | Cause | Fix | Rule |
|---|---|---|---|---|
| P1 | Many review rounds for one sheet | No checks before showing the user | Evidence pack per gate; all checkers PASS first | WF-02 |
| P2 | Claims about the screen without evidence | Inference | Never state screen content without a tool result, file or capture | COM-01 |
| P3 | Asked about an earlier message that did not exist (6 TPs) | Mismatch between user memory and session | Say so, keep the current state, ask | COM-01 |
| P4 | Gates ticked by the agent risk | - | Only the user ticks gates | WF-01 |

## PCB (seed, from the buck layout start)

| # | Symptom | Cause | Fix | Rule |
|---|---|---|---|---|
| B1 | check_placement flagged 21 "violations" | Touching courtyard outlines and silk, not copper | Read flags by type; courtyards may touch, not overlap | PCB-12 |
| B2 | Placement script crashed | See T5 | `set_component_position` one part at a time | PCB-12 |
| B3 | Stackup showed 0.07 mm, no core | New PcbDoc default stackup | Set 1.6 mm FR-4 in Layer Stack Manager (manual) | PCB-01 |
