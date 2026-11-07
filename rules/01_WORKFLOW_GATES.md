# 01 Workflow and gates

Format of every rule: ID, MUST / MUST NOT, Why, Check, Source, Status.
Status: ENFORCED (a script fails if broken) / CHECKLIST (a human or the agent ticks it) / PROPOSED (not binding
until the user approves) / SEED (starting value, refined in its phase).

### WF-01 Gate order and sign-off
- MUST: pass gates in order G1 footprints, S1 schematic readability, G2 layout, G3 DRC and audit, G4 Gerbers. Only the user ticks a gate.
- MUST NOT: produce or send fab output before all five are ticked.
- Why: gates catch errors that are expensive after fab; the agent ticking its own gate hides mistakes.
- Check: gate_check.py (reads gates.md, reports ticked / not ticked)
- Source: workspace CLAUDE.md "Human gates"; user 2026-10-13 (S1 added before G2)
- Status: ENFORCED

### WF-02 Evidence pack before presenting a gate
- MUST: present a gate only with ai\review\<gate>_evidence.md: every offline checker PASS plus the agent's own capture review.
- Why: the buck schematic needed many review rounds because problems were shown before they were checked.
- Check: gate_check.py <gate> <project>
- Source: LESSONS P1 (buck S1, 2026-10-13)
- Status: ENFORCED

### WF-03 Rules version per project
- MUST: record the rules VERSION in project.json at start and in every evidence pack. Rules never change an old project silently.
- Why: rules grow; an old design must be judged by the rules it was built with.
- Check: gate_check.py (writes the version into the evidence)
- Source: user brief 2026-10-13 (governance)
- Status: ENFORCED

### WF-04 Rule changes
- MUST: only the user approves rule changes. Propose a rule when a check fails twice or the user corrects the same kind of thing twice. Bump VERSION and CHANGELOG.
- Why: rules are a contract with the user.
- Check: checklist (CHANGELOG entry with user approval date)
- Source: user brief 2026-10-13
- Status: CHECKLIST

### WF-05 Resumable work
- MUST: keep a progress file (logs\WORKSPACE_PROGRESS.md, the project PROJECT.md, or the batch `_decision_log.md`) current after every finished step (what is done, where the files are, what is next), so a new session or a usage-limit stop resumes by reading that file alone; commit per finished part when the brief allows commits.
- Why: usage limits interrupted long unattended runs.
- Check: checklist
- Source: LESSONS T28; usage limits stopped the footprint check (2026-11-02) and the portfolio capture (2026-11-05) mid-run
- Status: CHECKLIST

### WF-06 Commits
- MUST: ask before every git commit unless the current brief says when to commit.
- Why: the user controls history.
- Check: checklist
- Source: workspace CLAUDE.md / START_PROMPT ("ask before git commits")
- Status: CHECKLIST

### WF-07 Pending items at phase start
- MUST: read PROJECT.md "pending" lines and do them first (for buck: Update PCB for TP1-TP5, restore U1/Q1).
- Why: open items from earlier phases were nearly forgotten (U1/Q1 off-board).
- Check: checklist
- Source: LESSONS T19
- Status: CHECKLIST

### WF-08 Design feedback log and harvest
- MUST: append one line to `ai/feedback.jsonl` whenever the user corrects the work, rejects an option or picks a better one; at the end of every design stage (gate ticked or result accepted), run the altium-rule-harvest skill and let the user sort every item before anything is written to a standard or proposed upstream.
- Why: user feedback is the evidence for better rules; without a log it is lost, and without the user's sort one person's taste leaks into the central rules.
- Check: checklist (feedback.jsonl lines, ai/review/harvest_<stage>.md with every row sorted)
- Source: user brief 2026-10-17 (design feedback should improve the central rules); docs/RULE_FEEDBACK_LOOP.md
- Status: PROPOSED

### WF-09 Projects live where the user keeps them
- MUST: work on a design in its own folder (an employer's or customer's folder, any drive); put the kit's project files beside it with `new_project.py <name> --attach <folder>` (they go to `<folder>\_eda\` only) and run the checkers on that folder. Production packages, quotes and backups are written next to the design, in the user's folder.
- MUST NOT: move or copy a work project into the kit's projects\ folder, or a temporary upload copy there; a temporary copy (e.g. for a browser upload) goes to the workspace tmp\ folder and is deleted when the task ends, and the user is told where it was.
- Why: the user organises work per employer; a copy under projects\ splits the design into two versions (Extention_01, 2026-10-30).
- Check: new_project.py --attach (never writes outside <folder>\_eda); gate_check.py reads design_dir from project.json
- Source: user 2026-10-30 ("work on the project where it was ... organize different employer work"; "later update the rule so project can be anywhere")
- Status: ENFORCED

### WF-10 Start the session where the tools load
- MUST: start Claude Code in the workspace folder (it holds .mcp.json, the guard hook and the permissions); reach a project in the user's own folder (WF-09) by adding it to that session: `kit start "<folder>"` (= `claude --add-dir "<folder>"` from the workspace).
- MUST NOT: start a session inside a project or client folder for Altium work: the three Altium servers and the guard hook do not load there, and moving the folder later does not load them into a running session.
- Why: a whole library job ran in a client folder without the Altium servers; 3D models were embedded offline (red boxes) and the user had to copy the folder into the workspace and restart (2026-11-04).
- Check: doctor.py (prints the start command); kit.cmd start
- Source: thread 2026-11-04 ("you have mcp to run script"; "i shift the working directory so i think now you can do all automatically"); kit review 2026-11-07 (docs/KIT_REVIEW_2026-11.md)
- Status: ENFORCED

### WF-11 Preflight before each work session
- MUST: run `kit doctor` (doctor.py) at the start of a session and before writing any rule, tool or library: no FAIL; when the workspace is behind origin/main, pull before writing (or tell the user); a second Altium instance is a stop.
- Why: a session on an un-pulled workspace wrote rules on a two-week-old base and reused taken IDs (LIB-17..20, P9, version 1.6.0); extra Altium instances caused licence conflicts (2026-11-03).
- Check: doctor.py; rules_lint.py (CHANGELOG order, --next-id)
- Source: PR #32 (stale base); thread 2026-11-03 (X2.EXE spawned extra instances); kit review 2026-11-07 (docs/KIT_REVIEW_2026-11.md)
- Status: ENFORCED

### WF-12 One brief and one permission round per batch
- MUST: for a batch (a library, a cleanup, a production package), send one brief before starting that lists every permission the whole batch needs (deletes, renames, overwrites, new parts made from scratch, Altium launches, downloads), get one yes, then work to the end and send one final report: what was done (counts from the tools), what the user must check or do by hand, and the decision log.
- MUST: when the batch sets a visual standard (symbol style and colours, 3D look, a review-document layout), put one rendered sample per kind in the brief and start the batch only after the user accepts them; when something new needs a permission mid-batch, park it in the decision log, finish everything else, and ask once at the end; stop early only for a KILL SWITCH, a second Altium instance or a step that cannot be undone and was not in the brief.
- Why: the user works from a phone and studies; per-step questions stalled batches for hours, and the user asked to "take necessary permission at once" (2026-11-04). Symbol colours, the resistor drawing and the polarised capacitor were redone four times across the whole library, while the review document, agreed on one sample (SOT65P210X110-5N) first, scaled to 68 footprints in one pass.
- Check: checklist (one brief, one final report, decision log with open items)
- Source: thread 2026-11-04 ("take necessary permission at once"; "ask all permissions at once, finish, then report"); thread 2026-11-07 ("all decisions you make and apply ... do not disturb me")
- Status: CHECKLIST

### WF-13 Do the asked scope at the asked pace
- MUST: deliver what was asked and nothing extra (no review spreadsheet, extra document or adjacent task unless asked); when the user says "fast" or "do your best", go on with the most likely reading, state the assumptions in one line each, and let the user correct afterwards instead of asking first.
- MUST NOT: drop a standing quality rule for speed: the datasheet check (LIB-18), calculations in code (RQ-02) and gates stay.
- Why: a parameter update first produced a review spreadsheet the user did not want, and footprint checks started before the requested integrated library; meanwhile the S8550 datasheet check was skipped "for speed" (2026-10-30, 2026-11-02).
- Check: checklist (the report names the assumptions made)
- Source: thread 2026-10-30 ("do your best ... make it fast"); thread 2026-11-02 ("i do not need the review spreadsheet"; "stop doing this first create an integrated library"); kit review 2026-11-07 (docs/KIT_REVIEW_2026-11.md)
- Status: CHECKLIST

### WF-14 Scripts written for a job become kit tools
- MUST: when a job needs a script that the next job will need again (a library builder, a review-document generator, an Altium .pas helper, a lookup), put it in `tools/scripts/` (Python) or `tools/altium_scripts/` (DelphiScript) with a `--help` docstring, a line in docs/TOOLS_GUIDE.md and a test where it can run without Altium, in the same session; a one-off script is deleted when the job ends.
- Why: the review-document generator, Swap3D.pas and the batch library builder lived only in a client folder, so each new session rebuilt them from scratch at a high token cost.
- Check: checklist (TOOLS_GUIDE row per new script); selftest.py (every script answers --help)
- Source: threads 2026-11-03/04 (make_review_sot353.py, Swap3D.pas, plan.py in client folders); thread 2026-10-31 (every tool usable from cmd with a guide); kit review 2026-11-07 (docs/KIT_REVIEW_2026-11.md)
- Status: CHECKLIST
