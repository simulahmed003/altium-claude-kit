"""lib_params.py - the library parameter set of a category, and a check of a SchLib against it (LIB-23, LIB-31, LIB-34).

Reads rules/library_parameters.json (the frozen parameter tables). Read-only on libraries.

Usage:
  python lib_params.py "Capacitors/Ceramic (MLCC)"   parameter set of one subtype (Type/Subtype, or the subtype alone)
  python lib_params.py Capacitors                    every subtype of one Type
  python lib_params.py --list                        the 89 subtypes, one per line
  python lib_params.py --check <lib.SchLib>          per component: missing, extra and duplicate parameters against
                                                     the set of its Category (LIB-34); exit 1 when any component fails
  python lib_params.py --write-doc                   regenerate docs/LIBRARY_PARAMETERS.md from the JSON
Options: --json (machine-readable output for the first three forms)

Why: the full tables are about 20 kB. An agent that needs the set of one category runs this and reads a few lines
instead of loading the whole table into its context.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
JSON_PATH = os.path.join(ROOT, "rules", "library_parameters.json")
DOC_PATH = os.path.join(ROOT, "docs", "LIBRARY_PARAMETERS.md")
LINKS = ["Mouser Price/Stock", "DigiKey Price/Stock", "LCSC Price/Stock"]
IMPORT_ONLY = {"Category"}          # written at import time, may be absent in the SchLib
FIELD_ONLY = {"Comment"}             # stored in the component field, not as a parameter record
ALWAYS_OK = {"Designator", "Component Type", "Symbol", "altium.hash"}


def load(path=JSON_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def subtypes(d):
    return [(e["type"], e["subtype"]) for e in d["electrical"]]


def find(d, key):
    """Return the electrical entries matching 'Type/Subtype', 'Subtype' or 'Type' (case-insensitive)."""
    k = key.strip().lower()
    hits = [e for e in d["electrical"] if f'{e["type"]}/{e["subtype"]}'.lower() == k]
    hits = hits or [e for e in d["electrical"] if e["subtype"].lower() == k]
    return hits or [e for e in d["electrical"] if e["type"].lower() == k]


def common_names(d):
    return [c["name"] for c in d["common"]]


def param_set(d, entry):
    """Every parameter name a component of this subtype carries (LIB-34): common + links + required + optional."""
    names = [n for n in common_names(d) if n not in IMPORT_ONLY]
    names += [n for n in LINKS if n not in names]
    names += [n for n in entry["required"] + entry["optional"] if n not in names]
    return names


def hint(d, n):
    hs = [x for x in d.get("electrical_hints", {}).get(n, []) if not x.startswith(n)]
    return f"  ({'; '.join(hs)})" if hs else ""


def describe(d, entry, common=True):
    h = lambda n: hint(d, n)
    out = [f'{entry["type"]}/{entry["subtype"]}']
    if common:
        out += [f'  common ({len(d["common"])}): ' + ", ".join(common_names(d)), "  links: " + ", ".join(LINKS)]
    out += ["  required electrical:"] + [f"    {n}{h(n)}" for n in entry["required"]]
    out += ["  optional electrical (present, empty when unknown):"] + [f"    {n}{h(n)}" for n in entry["optional"] or ["-"]]
    return "\n".join(out)


def check_component(d, params, keep=None):
    """params: list of (name, text). Returns (category, problems)."""
    keep = set(keep if keep is not None else d.get("keep_if_present_never_add", []))
    names = [n for n, _ in params]
    val = dict(params)
    cat = val.get("Category", "")
    probs = []
    dups = sorted({n for n in names if names.count(n) > 1})
    if dups:
        probs.append("duplicate: " + ", ".join(dups))
    hits = [e for e in d["electrical"] if f'{e["type"]}/{e["subtype"]}' == cat]
    if not hits:
        probs.append(f"Category '{cat}' is not in the tree" if cat else "no Category parameter")
        return cat, probs
    want = param_set(d, hits[0])
    missing = [n for n in want if n not in val and n not in FIELD_ONLY]
    extra = [n for n in dict.fromkeys(names) if n not in want and n not in keep and n not in ALWAYS_OK
             and n not in IMPORT_ONLY]
    if missing:
        probs.append("missing: " + ", ".join(missing))
    if extra:
        probs.append("not in the set (remove and log, LIB-34): " + ", ".join(extra))
    return cat, probs


def check_lib(d, path):
    sys.path.insert(0, HERE)
    from altium_io import schlib_symbols
    syms = schlib_symbols(path)
    bad = 0
    for name in sorted(syms):
        cat, probs = check_component(d, [(p["name"], p["text"]) for p in syms[name]["params"]])
        if probs:
            bad += 1
            print(f"FAIL  {name} [{cat or '-'}]: " + "; ".join(probs))
        else:
            print(f"PASS  {name} [{cat}]")
    print(f"lib_params --check: {len(syms)} components, {bad} FAIL")
    return 1 if bad else 0


def write_doc(d, path=DOC_PATH):
    h = lambda n: hint(d, n).replace("  (", " (")
    L = ["# Library parameter tables", "",
         "Generated by `tools/scripts/lib_params.py --write-doc` from `rules/library_parameters.json`; do not edit by hand.",
         "Rules: LIB-23 (tables), LIB-31 (frozen), LIB-32 (value sources), LIB-34 (one set per category).",
         "For one category run `kit lib_params \"<Type>/<Subtype>\"` instead of reading this file.", "",
         "## Common parameters (every component; Category is import only)", "",
         "| Group | Parameter | Need | Format | Example |", "|---|---|---|---|---|"]
    L += [f'| {c["group"]} | {c["name"]} | {c["need"]} | {c["format"]} | {c["example"]} |' for c in d["common"]]
    L += ["", "Link parameters (LIB-31): " + ", ".join(LINKS) + ".", "",
          f'## Electrical parameters by subtype ({len(d["electrical"])} subtypes)', "",
          "| Type | Subtype | Required | Optional |", "|---|---|---|---|"]
    for e in d["electrical"]:
        req = ", ".join(n + h(n) for n in e["required"]) or "Common parameters only"
        opt = ", ".join(n + h(n) for n in e["optional"]) or "-"
        L.append(f'| {e["type"]} | {e["subtype"]} | {req} | {opt} |')
    text = "\n".join(L) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("category", nargs="?", help='"Type/Subtype", a subtype or a Type')
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", metavar="SCHLIB")
    ap.add_argument("--write-doc", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--params", default=JSON_PATH, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    d = load(a.params)
    if a.write_doc:
        write_doc(d)
        print(f"written {os.path.relpath(DOC_PATH, ROOT)}")
        return 0
    if a.check:
        return check_lib(d, a.check)
    if a.list:
        rows = [f"{t}/{s}" for t, s in subtypes(d)]
        print(json.dumps(rows, indent=1) if a.json else "\n".join(rows))
        return 0
    if not a.category:
        ap.print_help()
        return 1
    hits = find(d, a.category)
    if not hits:
        print(f"No subtype or Type named '{a.category}'. Run with --list.")
        return 1
    if a.json:
        print(json.dumps({f'{e["type"]}/{e["subtype"]}': param_set(d, e) for e in hits}, indent=1, ensure_ascii=False))
    else:
        print("\n\n".join(describe(d, e, i == 0) for i, e in enumerate(hits)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
