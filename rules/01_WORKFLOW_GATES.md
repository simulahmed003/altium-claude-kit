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
- MUST: keep a progress file (logs\WORKSPACE_PROGRESS.md or the project PROJECT.md) current and commit per finished part when the brief allows commits.
- Why: usage limits interrupted long unattended runs.
- Check: checklist
- Source: LESSONS T28
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
