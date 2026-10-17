# Guideline template

Copy the block below into a new file (one topic per file, for example `power-inductor.md`).
ID: `G-<AREA>-<NN>`. The user decides the AREA codes later (for example PWR, THERM, EMC, DFM, ARCH).
A guideline with Status NOT SET carries no number and binds nothing.

```
### G-<AREA>-<NN> <title>
- Applies to: <circuit or block, for example "buck converter inductor">
- Parameter: <what is limited, with the unit>
- Value or range: NOT SET
- Why: <one line: what goes wrong without it>
- Source: <datasheet, standard, fab profile, or "user decision <date>"> (needed before Status can leave NOT SET)
- Automated by: <calclib.py function, checker script, or "none yet">
- Used by projects: <project names, or "none">
- Status: NOT SET        (NOT SET / PROPOSED / APPROVED <date>, user)
```

## Example (illustration only: no value is set, this is not a guideline)
```
### G-PWR-EX Inductor ripple current allowance
- Applies to: buck and boost converter inductor
- Parameter: peak-to-peak inductor ripple current as a ratio of output current (k = delta I / IOUT)
- Value or range: NOT SET
- Why: it sets the inductor size and the peak current; the limit should be one deliberate system choice, not a guess per project
- Source: NOT SET (user decision pending)
- Automated by: calclib.inductor_for_ripple(vin, vout, fsw, k, iout) and calclib.inductor_ripple(vin, vout, fsw, L) take k or L as an
  input; no function checks a project against an allowed range yet
- Used by projects: none
- Status: NOT SET
```
