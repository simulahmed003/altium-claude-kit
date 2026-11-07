"""ws_lib_check.py - is a symbol library ready for the Altium 365 Library Importer (rule LIB-38)? Read-only.

Usage:
  python ws_lib_check.py <lib.SchLib>
Per component:
  - Component Type present and free of characters the Workspace refuses in a type tag (/ \\ : * ? " < > |)
  - Category present and exactly "<Type>/<Subtype>", with the subtype equal to Component Type
  - Symbol parameter present (LIB-37)
  - description at most 256 characters (the importer refuses longer ones without naming the part)
Exit 0 when every component passes, 1 otherwise.
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_io import schlib_symbols

BAD = re.compile(r'[/\\:*?"<>|]')


def check(name, sym):
    why = []
    p = {q["name"]: q["text"] for q in sym["params"]}
    ctype, cat = p.get("Component Type", ""), p.get("Category", "")
    if not ctype:
        why.append("no Component Type")
    elif BAD.search(ctype):
        why.append(f"Component Type '{ctype}' holds a character the Workspace refuses ({BAD.search(ctype).group()})")
    if not cat:
        why.append("no Category")
    else:
        parts = cat.split("/")
        if len(parts) != 2 or not all(parts):
            why.append(f"Category '{cat}' is not exactly Type/Subtype (a '/' inside a name breaks it)")
        elif ctype and parts[1] != ctype and parts[0] != ctype:
            why.append(f"Category '{cat}' does not end with Component Type '{ctype}'")
    if not p.get("Symbol"):
        why.append("no Symbol parameter")
    desc = ""
    for r in sym.get("records", []):
        if isinstance(r, dict) and r.get("RECORD") == "1":
            desc = r.get("COMPONENTDESCRIPTION", "")
    if len(desc) > 256:
        why.append(f"description {len(desc)} characters (> 256)")
    return why


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("schlib")
    a = ap.parse_args(argv)
    syms = schlib_symbols(a.schlib)
    fails = 0
    for n in sorted(syms):
        why = check(n, syms[n])
        if why:
            fails += 1
            print(f"FAIL  {n}: " + "; ".join(why))
    print(f"\n{len(syms)} components, {len(syms) - fails} PASS, {fails} FAIL")
    return 1 if fails or not syms else 0


if __name__ == "__main__":
    sys.exit(main())
