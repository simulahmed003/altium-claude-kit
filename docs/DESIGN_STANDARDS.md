# Design standards: what binds a design, and who owns it

An agent needs two things to design a board: **how to work** (the rules) and **what good looks like** (the design
standard). This page defines the layers of the design standard, which one wins, and what makes something general
(central repo) or specific to one user or one project. The feedback loop that fills these layers is in
[RULE_FEEDBACK_LOOP.md](RULE_FEEDBACK_LOOP.md).

## The layers

| # | Layer | Where | Holds | Owner | Shared? |
|---|---|---|---|---|---|
| 1 | Rules | `rules/` | HOW agents work: gates, evidence, tool use, file formats, checks | maintainer (WF-04) | central, everyone |
| 2 | Guidelines | `guidelines/` (core) and `rules/domains/<domain>/` (per field, planned) | WHAT a good design needs, from physics, standards (IPC, JEDEC) and datasheets, with a source for every value | maintainer, one at a time | central, everyone |
| 3 | Fab profile | `rules/fab-profiles/<fab>.json` | what one manufacturer can build (min trace, drill, annular ring) | maintainer, dated from the fab's page | central, picked per project |
| 4 | User standard | `standards/local/<name>.md` | one person's or one company's house style and policies | that user or company | local only, never pushed |
| 5 | Project | `projects/<name>/requirements.md`, `constraints.md` | the numbers of one board | the designer | the project's own repo |

`project.json` names the fab profile, the user standard and (planned) the domain packs a project uses (`fab_profile`, `standard`, `domains`).

## Which one wins
1. **Rules always apply.** A project may deviate only with a recorded user approval (RQ-05).
2. **Fab profile is a hard floor.** No layer may go looser than what the fab can build. Tighter is always allowed.
3. **More specific wins when it is stricter or when it records why.** Project > user standard > guidelines.
   A looser value than a guideline needs a one-line reason in the project's `PROJECT.md` (for example "prototype, hand-soldered").
4. **No value without a source.** A missing value stays NOT SET. The agent asks; it never fills a gap with a guess.

## What makes something user-specific (the "cause")
A design choice belongs to the **user standard**, not the central repo, when its cause is one of these:

| Cause | Example |
|---|---|
| House style | block titles on the schematic, A3 sheets, designator order, title-block fields |
| Company or customer policy | 50 % voltage derating instead of the guideline's value, only AEC-Q parts, approved-vendor list |
| Industry requirement the user works under | automotive, medical, or space rules that do not apply to everyone |
| The user's equipment and process | 1.5 mm test pads for the user's probes, hand assembly, their reflow profile |
| Preference with no measurable effect | silkscreen font, net-label style |

It belongs to the **project** when it follows from that board's requirements (input voltage, size, enclosure).

### Sorting test (ask in order; the first yes decides)
1. Only true for this board? → **project**.
2. Taste, house style or company policy, with no source beyond "we prefer"? → **user standard**.
3. Depends on what one fab can build? → **fab profile**.
4. A sourced engineering target for a class of circuits? → **guideline**.
5. Correctness, safety, manufacturability or tool behaviour that would bite any user? → **rule**.
Anything else is a lesson for `docs/LESSONS_LEARNED.md`.

It goes **central** (rule, guideline or fab profile) only when all of these hold:
1. **Source:** it follows from physics, a standard, a datasheet or a tool's behaviour, and the source is cited.
2. **Reach:** it would help any user designing that kind of circuit, not only this user.
3. **Evidence:** seen in two or more projects or by two or more users, or once if missing it could damage hardware or waste a fab run.
4. **Checkable:** a script can check it, or a checklist line can be judged yes/no.
5. **Generalised:** no project numbers, part numbers, customer names or paths, unless they are the subject (a catalog part).

Failing 1 or 2 means user standard. Failing 3 means it stays PROPOSED until the evidence exists.

### Already in the central rules but looks user-specific (to settle in the rule-by-rule review)
- Parts of `04_SCHEMATIC.md` came from one user's S1 brief: whole A3 sheet, titled blocks of about 8 parts, one GND per cluster. Candidates for a user standard.
- FAB-04 (JLCPCB BOM columns) belongs with the JLCPCB fab profile.
- RQ-06 (capacitor rating) and RQ-07 (thermal target) are design targets, so guideline candidates.

## Starting with no user standard
A new user starts with rules, guidelines and a fab profile only. Copy `standards/TEMPLATE.md` to `standards/local/<name>.md`
when the first user-specific choice comes up. The feedback loop fills it as the user corrects the agent.
