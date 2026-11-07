"""lib_std_check.py - parameter VALUES and the Description of every component in a SchLib (LIB-23, LIB-31). Read-only.

Usage:
  python lib_std_check.py <lib.SchLib> [<lib.SchLib> ...]      one line per component, exit 1 when any FAIL
  python lib_std_check.py <lib.SchLib> --json                   machine-readable
  python lib_std_check.py --value "4.7 uF"                      check one value string (to try a format)

Value format (rules/09_LIBRARY_STANDARD.md, "Value format"):
  unknown = empty (never N/A, -, TBD); ASCII only (u not µ, Ohm not Ω, no ±); SI prefix and unit without a space
  (100nF, 50V); decimal point, no trailing zeros (2.2uF, not 2,2uF or 2.20uF); ranges with "to", not "~";
  resistance below 1k with R (10R, 49.9R), from 1k with k (4.7k); one value per parameter (no "2 (dual)").
Description (docs/LIBRARY_STANDARD.md, "Naming conventions"):
  present in the component field and as the hidden Description parameter, the two equal, under 256 characters,
  starting with the Type's word: RES, CAP, IND, DIODE, MOSFET / BJT / IGBT (other Types have no pattern yet, R9).
Parameter NAMES per category are checked by lib_params.py --check; this tool checks what is written in them.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# parameters whose text is free text, a name, a link or an ID: no value-format check
FREE = {"Description", "Comment", "Manufacturer 1", "Manufacturer Part Number 1", "Supplier 1", "Supplier Part Number 1",
        "LCSC Part Number", "DigiKey Part Number", "Mouser Part Number", "Datasheet URL", "Datasheet Revision",
        "Mouser Price/Stock", "DigiKey Price/Stock", "LCSC Price/Stock", "Category", "Component Type", "Symbol",
        "Package", "Footprint Standard", "Status", "Lifecycle", "Notes", "Verified By", "Verified Date", "Mounting",
        "RoHS", "REACH", "Series", "Designator", "Footprint", "altium.hash", "Function", "Protocol", "Topology"}
UNKNOWN = {"n/a", "na", "-", "--", "tbd", "tba", "?", "none", "unknown", "nil"}
DESC_WORD = {"Resistors": ("RES",), "Capacitors": ("CAP",), "Inductors": ("IND",), "Diodes": ("DIODE",),
             "Transistors": ("MOSFET", "BJT", "IGBT")}
NONASCII_FIX = {"µ": "u", "μ": "u", "Ω": "R / Ohm", "±": "(drop it: 1%)", "–": "-", "−": "-"}


def value_problems(name, text):
    """Problems of one parameter value (empty list when it follows the format)."""
    t = text or ""
    if not t.strip() or t.startswith("="):
        return []                                  # empty = unknown (allowed); "=Value" is a reference
    p = []
    if t != t.strip():
        p.append("leading/trailing space")
    s = t.strip()
    if s.lower() in UNKNOWN:
        return [f"'{s}' for unknown: leave it empty"]
    if name in FREE:
        return p
    bad = sorted({c for c in s if ord(c) > 127 and c != "°"})
    if bad:
        p.append("non-ASCII " + " ".join(f"'{c}'" + (f" -> {NONASCII_FIX[c]}" if c in NONASCII_FIX else "") for c in bad))
    if re.search(r"\d,\d", s):
        p.append("decimal comma: use a point")
    if re.search(r"(?<![\w.])\d+(\.\d+)?\s+[pnumkKMG]?(F|H|V|A|W|Hz|R|Ohm|s|%)\b", s):
        p.append("space between number and unit (write 100nF, 50V)")
    if re.search(r"\d\.\d*?0(?=[A-Za-z%°]|\s|$)", s) and not re.search(r"\d\.0+\d", s):
        p.append("trailing zero after the decimal point (2.2uF, not 2.20uF)")
    if "~" in s:
        p.append("range with '~': use 'to' (-40°C to 85°C)")
    if re.search(r"\(.+\)", s):
        p.append("one value per parameter: no remark in brackets")
    if re.search(r"\d\s*mfd\b", s, re.I):
        p.append("'mfd': use uF")
    if name == "Resistance" or name.startswith("Resistance"):
        m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(R|Ohm|ohm|k|K|M|m)?(Ohm)?", s)
        if m:
            v, unit = float(m.group(1)), m.group(2) or ""
            if unit == "":
                p.append("resistance without unit: 10R below 1k, 4.7k from 1k")
            elif unit in ("R", "Ohm", "ohm") and v >= 1000:
                p.append(f"{s}: from 1k write k ({v / 1000:g}k)")
            elif unit == "K":
                p.append("kilo is lower-case k")
    return p


def description_problems(typ, field, param):
    p = []
    if not field:
        p.append("no Description in the component field")
    if param is None:
        p.append("no hidden Description parameter")
    elif field and param.strip() != field.strip():
        p.append("Description field and parameter differ")
    d = (field or param or "").strip()
    if len(d) >= 256:
        p.append(f"Description {len(d)} characters (under 256)")
    words = DESC_WORD.get(typ)
    if d and words and not d.split()[0] in words:
        p.append(f"Description should start with {' / '.join(words)} ({typ} pattern), has '{d.split()[0]}'")
    return p


def check_symbol(name, sym):
    params = {}
    hidden = {}
    for q in sym["params"]:
        params.setdefault(q["name"], q["text"])
        hidden[q["name"]] = q.get("hidden")
    head = next((r for r in sym.get("records", []) if r.get("RECORD") == "1"), {})
    cat = params.get("Category", "")
    typ = cat.split("/")[0] if cat else ""
    probs = [f"{n}: {x}" for n, t in params.items() for x in value_problems(n, t)]
    probs += description_problems(typ, head.get("COMPONENTDESCRIPTION", ""), params.get("Description"))
    if "Description" in params and hidden.get("Description") is False:
        probs.append("Description parameter is visible (LIB-31: hidden)")
    comment = params.get("Comment", "")
    if not comment:
        probs.append("Comment empty (the value, or the short part name for ICs)")
    elif typ == "Resistors" and not comment.startswith("="):
        probs += [f"Comment: {x}" for x in value_problems("Resistance", comment)]
    return cat, probs


def check_lib(path):
    from altium_io import schlib_symbols
    out = []
    for name, sym in sorted(schlib_symbols(path).items()):
        cat, probs = check_symbol(name, sym)
        out.append({"lib": path, "component": name, "category": cat, "problems": probs})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("schlib", nargs="*")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--value", help="check one value string")
    ap.add_argument("--name", default="Value", help="parameter name for --value (Resistance enables the R/k check)")
    a = ap.parse_args(argv)
    if a.value is not None:
        p = value_problems(a.name, a.value)
        print("PASS" if not p else "FAIL  " + "; ".join(p))
        return 1 if p else 0
    if not a.schlib:
        ap.print_help()
        return 1
    rows = [r for lib in a.schlib for r in check_lib(lib)]
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
    else:
        for r in rows:
            print(("FAIL  " if r["problems"] else "PASS  ") + f'{r["component"]} [{r["category"] or "-"}]'
                  + (": " + "; ".join(r["problems"]) if r["problems"] else ""))
    bad = sum(1 for r in rows if r["problems"])
    if not a.json:
        print(f"lib_std_check: {len(rows)} components, {bad} FAIL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
