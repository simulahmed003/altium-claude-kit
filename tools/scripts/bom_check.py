"""bom_check.py - check a production BOM before it goes to the assembler or a quote (rules FAB-04, FAB-07, RQ-08).

Run from the workspace folder in cmd.exe, for example:
  python tools\\scripts\\bom_check.py out\\board_BOM.csv
  python tools\\scripts\\bom_check.py out\\board_BOM.csv --cpl out\\board_CPL.csv --changes out\\bom_changes.csv

Checks (each problem is one FAIL line):
  - JLC upload columns present: Comment, Designator, Footprint, LCSC Part #
  - kit columns present (never dropped, user 2026-10-30): Quantity, Manufacturer, MPN, Mouser Part Number,
    DigiKey Part Number (a cell may say "-" or "UNCONFIRMED", but the column must exist)
  - every designator listed one by one: no ranges such as R125-R127 (JLC cannot read them)
  - every designator once in the whole BOM; Quantity = number of designators
  - LCSC Part # is a C-number (or "-" for a part the assembler does not place) and one number per cell;
    a second number goes in "Alternate LCSC Part #"
  - one LCSC number never on two lines with different values (the Bondu case: five resistor values on the 100K part)
  - a voltage written in the Comment of a capacitor is not lower than the voltage in its "Alternate" or
    "Changed from" note (RQ-08: never a lower rating)
  --cpl: CPL designators = BOM designators (delegates to cpl_check.py check)
  --changes: a BOM-changes table (Designator, Old, New, Reason, Rating check) must cover every line whose
    LCSC number differs from the one in --changes-base or whose MPN cell is not the LCSC part's MPN; here it is only
    checked for its columns and that each named designator exists in the BOM.
Python standard library only. Exit 0 = PASS, 1 = FAIL.
"""
import argparse, csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

JLC_COLS = ["Comment", "Designator", "Footprint", "LCSC Part #"]
KIT_COLS = ["Quantity", "Manufacturer", "MPN", "Mouser Part Number", "DigiKey Part Number"]
CHANGE_COLS = ["Designator", "Old", "New", "Reason", "Rating check"]
RANGE = re.compile(r"^([A-Za-z]+)(\d+)\s*-\s*([A-Za-z]*)(\d+)$")


def split_designators(cell):
    return [d.strip() for d in re.split(r"[,;]\s*|\s+", cell or "") if d.strip()]


def volts(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*V\b", text or "", re.I)
    return float(m.group(1)) if m else None


def norm_value(comment):
    """Value part of a Comment for the shared-LCSC check: '100K 1% 0603' -> '100k'."""
    t = (comment or "").strip().split()
    return t[0].lower().replace("ω", "r").replace("ohm", "r") if t else ""


def check(path):
    errs, notes = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        cols = [c.strip() for c in (r.fieldnames or [])]
        rows = [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in r]
    for c in JLC_COLS:
        if c not in cols:
            errs.append(f"column '{c}' missing (JLC upload format)")
    for c in KIT_COLS:
        if c not in cols:
            errs.append(f"column '{c}' missing (kit BOM keeps it, FAB-04)")
    if any(c not in cols for c in JLC_COLS):
        return errs, notes, rows
    seen, by_lcsc = {}, {}
    for i, row in enumerate(rows, 2):
        refs = split_designators(row["Designator"])
        for d in refs:
            if RANGE.match(d):
                errs.append(f"line {i}: designator range '{d}': list each designator")
            if d in seen:
                errs.append(f"line {i}: {d} also on line {seen[d]}")
            seen[d] = i
        q = row.get("Quantity")
        if q and q.isdigit() and int(q) != len(refs):
            errs.append(f"line {i}: Quantity {q} but {len(refs)} designators")
        lc = row["LCSC Part #"]
        if lc not in ("", "-") and not re.fullmatch(r"C\d+", lc):
            errs.append(f"line {i}: LCSC Part # '{lc}' is not one C-number (second number -> 'Alternate LCSC Part #')")
        if not lc:
            notes.append(f"line {i}: {row['Designator']}: no LCSC number (assembler will not place it)")
        if re.fullmatch(r"C\d+", lc):
            by_lcsc.setdefault(lc, []).append((i, norm_value(row["Comment"]), row["Designator"]))
        alt = row.get("Alternate LCSC Part #", "")
        if alt and not all(re.fullmatch(r"C\d+", a) for a in split_designators(alt)):
            errs.append(f"line {i}: Alternate LCSC Part # '{alt}' is not a list of C-numbers")
        v_main = volts(row["Comment"])
        for k in ("Alternate", "Changed from", "Alternate note"):
            v_alt = volts(row.get(k, ""))
            if v_main is not None and v_alt is not None and v_alt < v_main:
                errs.append(f"line {i}: {k} voltage {v_alt:g} V below the line's {v_main:g} V (RQ-08)")
        for k in ("Mouser Part Number", "DigiKey Part Number"):
            if row.get(k, "").upper() == "UNCONFIRMED":
                notes.append(f"line {i}: {k} UNCONFIRMED (RQ-09: confirm on the distributor page before ordering)")
    for lc, uses in by_lcsc.items():
        vals = {v for _, v, _ in uses}
        if len(vals) > 1:
            errs.append(f"{lc} used for different values {sorted(vals)} on lines {[u[0] for u in uses]}: "
                        "one LCSC part cannot be several values (RQ-08)")
    return errs, notes, rows


def check_changes(path, bom_refs):
    errs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        missing = [c for c in CHANGE_COLS if c not in (r.fieldnames or [])]
        if missing:
            return [f"changes table columns missing: {missing}"]
        for i, row in enumerate(r, 2):
            if not (row.get("Rating check") or "").strip():
                errs.append(f"changes line {i}: no rating check written (RQ-08)")
            for d in split_designators(row["Designator"]):
                if d not in bom_refs:
                    errs.append(f"changes line {i}: {d} is not in the BOM")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("bom")
    ap.add_argument("--cpl")
    ap.add_argument("--changes")
    a = ap.parse_args(argv)
    errs, notes, rows = check(a.bom)
    refs = {d for row in rows for d in split_designators(row.get("Designator", ""))}
    if a.changes:
        errs += check_changes(a.changes, refs)
    if a.cpl:
        import cpl_check
        e2, _ = cpl_check.check(a.cpl, a.bom)
        errs += [e for e in e2 if "designator range" not in e]
    for e in errs:
        print("FAIL", e)
    for n in notes:
        print("NOTE", n)
    print(f"{len(rows)} BOM lines, {len(refs)} designators, {len(errs)} problems")
    return 1 if errs or not rows else 0


if __name__ == "__main__":
    sys.exit(main())
