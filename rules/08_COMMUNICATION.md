# 08 Communication

### COM-01 Evidence for every claim about the screen
- MUST NOT: state what is on the user's screen or in Altium without evidence (tool result, file, capture).
- Why: claims from plans were wrong (Q1 "gap", earlier "6 TPs" message).
- Check: checklist
- Source: LESSONS P2, P3
- Status: CHECKLIST

### COM-02 Short reports, user actions first
- MUST: keep reports short; put what the user must do first, with exact menu paths; tables for lists.
- Why: user request 2026-10-13.
- Check: checklist
- Source: user brief 2026-10-13
- Status: CHECKLIST

### COM-03 New downloads
- MUST: ask before the first download of a new file type. Exception: datasheet PDFs from the maker's website or LCSC for a part being added to the component database (RQ-01) are downloaded without asking; the source link is recorded in library\datasheets\index.json.
- Why: user request.
- Check: checklist
- Source: user brief 2026-10-13; datasheet exception: user 2026-10-17
- Status: CHECKLIST

### COM-04 Destructive edits
- MUST: announce every destructive edit and get a yes, unless the current brief already authorises it.
- Why: user controls irreversible changes.
- Check: checklist
- Source: workspace CLAUDE.md "Reads before writes"
- Status: CHECKLIST

### COM-05 Blocked by Altium
- MUST: when a popup, dialog or wedge blocks work, stop, log it, and give the exact steps; retry a call at most once.
- Why: loops on failures wasted time and risked Altium.
- Check: checklist
- Source: workspace CLAUDE.md; LESSONS T5-T8
- Status: CHECKLIST
