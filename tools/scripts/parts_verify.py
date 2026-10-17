"""parts_verify.py - walk a person through the checks of the component database (rule RQ-01), one part at a time.

Usage (from the workspace folder):   python tools\\scripts\\parts_verify.py [<mpn> ...]
For each part not yet verified it opens the datasheet PDF, shows the pins, abs max, package and every value read from a
page image ("visual"), and asks to confirm each group. A yes is recorded with `parts.py verify` (name and date).
n = not now (nothing recorded), q = stop; run it again later to continue. At the end it runs `parts.py check --gate`.
Exit code of the gate check: 0 = every part checked by a person.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts as P

ITEMS = P.PERSON_CHECKS


def vals(v):
    return " ".join(f"{x}={v[x]}" for x in ("min", "typ", "max", "value") if x in v)


def show(r, item):
    if item == "pins":
        for pin in r["pins"]:
            print(f"    pin {pin['number']:>3} {pin['name']:<6} {pin.get('description', '')[:70]}  (p{pin['ref']['page']})")
        if not r["pins"]:
            print("    (no pins recorded: two-terminal part)")
        return
    if item in ("abs_max", "package"):
        facts = r["facts"].get(item, {})
        for k, v in facts.items():
            print(f"    {k:<24} {vals(v)} {v['unit']}  {v.get('cond', '')[:50]}  (p{v['ref']['page']})")
        if not facts:
            print(f"    (no {item} facts recorded)")
        return
    n = 0
    for sec, facts in r["facts"].items():
        for k, v in facts.items():
            if v["ref"].get("visual"):
                n += 1
                print(f"    {sec}.{k:<20} {vals(v)} {v['unit']}  (p{v['ref']['page']}: {v['ref']['quote'][:50]})")
    for pin in r["pins"]:
        if pin["ref"].get("visual"):
            n += 1
            print(f"    pin {pin['number']} {pin['name']} (p{pin['ref']['page']}, from the drawing)")
    for sec, notes in r["notes"].items():
        for x in notes:
            if x["ref"].get("visual"):
                n += 1
                print(f"    note {sec}: {x['text'][:80]} (p{x['ref']['page']})")
    if not n:
        print("    (no visual values)")


def gate():
    print("\n--- gate check: every person check done?")
    return subprocess.run([sys.executable, os.path.join(HERE, "parts.py"), "check", "--gate"]).returncode


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help="MPNs to check (default: every part not yet verified)")
    keys = ap.parse_args(sys.argv[1:] if argv is None else argv).keys
    name = input("Your name for the record: ").strip()
    if not name:
        print("a name is needed")
        return 1
    recs = P.all_records() if not keys else [x for k in keys for x in P.find_record(k)]
    for f, r in recs:
        todo = [i for i in ITEMS if i not in r["review"].get("person_checks", {})]
        if not todo:
            continue
        print(f"\n=== {r['mpn']}  ({r['mfr']}, {r['category']})")
        for d in r["datasheets"]:
            pdf = P.p("datasheets", d["file"])
            print(f"  datasheet: {pdf}" + ("" if os.path.isfile(pdf) else "  (NOT ON DISK: parts.py datasheet ...)"))
            if os.path.isfile(pdf) and hasattr(os, "startfile"):
                os.startfile(pdf)
        for q in r["review"].get("open", []):
            print(f"  open question: {q}")
        ok = []
        for item in todo:
            print(f"\n  -- {item}:")
            show(r, item)
            a = input(f"  {item} matches the PDF? [y / n = not now / q = quit] ").strip().lower()
            if a == "q":
                if ok:
                    P.main(["verify", r["mpn"], "--by", name, "--items", *ok])
                return gate()
            if a == "y":
                ok.append(item)
            else:
                print("  not recorded: tell Claude what is wrong (or fix the record), then run this again")
        if ok:
            P.main(["verify", r["mpn"], "--by", name, "--items", *ok])
    return gate()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
