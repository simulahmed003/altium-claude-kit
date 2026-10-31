"""lib_audit.py - audit the kit global library against the library rules, list what to rebuild, record check status
(rules LIB-14, LIB-17, LIB-19).

Run from the workspace folder in cmd.exe, for example:
  python tools\\scripts\\lib_audit.py                       table of every catalog component, verdict OK / REBUILD
  python tools\\scripts\\lib_audit.py --md library\\catalog\\AUDIT.md   same, written as a Markdown file
  python tools\\scripts\\lib_audit.py --only R_10k_1%_0603_0603WAF1002T5E
  python tools\\scripts\\lib_audit.py mark <catalog id> --status checked --by Claude --note "datasheet p1, p3"
  python tools\\scripts\\lib_audit.py mark <catalog id> --status confirmed --by Simul
  python tools\\scripts\\lib_audit.py source <catalog id> --from dblib --ref "Celestial.DbLib: RES_0603_10K"
Checks per component (each failed check is one reason to rebuild):
  name      library reference (symbol name) is exactly the MPN (LIB-14)
  record    a part record exists for the MPN (RQ-01) and its review status is verified
  numbers   the record has LCSC, Mouser and DigiKey numbers (RQ-09)
  params    the symbol has Comment, Description, Manufacturer, MPN, LCSC, Mouser, DigiKey, Datasheet;
            Datasheet is a URL, not a file name (LIB-14)
  footprint the footprint status is datasheet-verified (LIB-05; derived / unverified-accepted are listed)
  model     the footprint has a 3D model (LIB-13)
  check     the component's check status (LIB-19): unchecked -> checked (agent's datasheet check, LIB-18)
            -> confirmed (a person confirmed it); only "confirmed" passes
  source    where the items came from (LIB-17): dblib (with the DbLib item), kit, or built; unknown fails
Components without an MPN (test pads, DNP placeholders) are only checked for footprint and check status.
mark / source write into library\\catalog\\components.json (and components.md); everything else is read-only.
Only a person may mark "confirmed" (like a gate): the agent marks "checked" at most.
Python standard library only. Exit 0 = every audited component OK, 1 = something to rebuild.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import libcat as lc

PARAMS = ("Comment", "Description", "Manufacturer", "MPN", "LCSC", "Mouser", "DigiKey", "Datasheet")
STATUSES = ("unchecked", "checked", "confirmed")
SOURCES = ("dblib", "kit", "built")


def parts_by_mpn():
    p = lc.gpath("parts", "index.json")
    if not os.path.isfile(p):
        return {}
    idx = json.load(open(p, encoding="utf-8"))
    return {e["mpn"]: e for e in idx.get("parts", [])}


def symbol_params(c):
    path = lc.gpath(c["global_lib"]) if c.get("global_lib") else None
    if not path or not os.path.isfile(path):
        return None
    try:
        import altium_io
        sym = altium_io.schlib_symbols(path).get(c["symbol"])
    except Exception:
        return None
    if not sym:
        return None
    return {p["name"]: p.get("text", "") for p in sym["params"]}


def audit(cat, parts, only=None):
    fps = {f["name"]: f for f in cat.get("footprints", [])}
    rows = []
    for c in cat["components"]:
        if only and c["id"] not in only:
            continue
        mpn = c.get("mpn") if c.get("mpn") not in (None, "", "-") else None
        why = []
        if mpn:
            if c.get("symbol") != mpn:
                why.append(f"name '{c.get('symbol')}' is not the MPN")
            rec = parts.get(mpn)
            if not rec:
                why.append("no part record")
            else:
                if rec.get("status") != "verified":
                    why.append(f"record {rec.get('status')}, not verified")
                skus = {s.split(":")[0].lower() for s in rec.get("skus", [])}
                miss = [n for n in ("lcsc", "mouser", "digikey") if n not in skus]
                if miss:
                    names = {"lcsc": "LCSC", "mouser": "Mouser", "digikey": "DigiKey"}
                    why.append("record lacks " + "/".join(names[m] for m in miss))
            prm = symbol_params(c)
            if prm is None:
                why.append("symbol not readable in the global SchLib")
            else:
                miss = [p for p in PARAMS if not prm.get(p)]
                if miss:
                    why.append("params missing: " + ", ".join(miss))
                ds = prm.get("Datasheet", "")
                if ds and not ds.lower().startswith("http"):
                    why.append("Datasheet param is a file name, not a URL")
        fp = fps.get(c.get("footprint"), {})
        if fp.get("status") != "datasheet-verified":
            why.append(f"footprint {c.get('footprint')} {fp.get('status', 'not in catalog')}")
        if not fp.get("step"):
            why.append("no 3D model")
        chk = (c.get("check") or {}).get("status", "unchecked")
        if chk != "confirmed":
            why.append(f"check: {chk}")
        if mpn and (c.get("source") or {}).get("from") not in SOURCES:
            why.append("source unknown")
        rows.append({"id": c["id"], "mpn": mpn or "-", "check": chk, "verdict": "OK" if not why else "REBUILD",
                     "why": why})
    return rows


def to_md(rows):
    out = ["# Kit library audit", "", f"Generated by `tools/scripts/lib_audit.py` on {lc.today()}; do not edit by hand.", "",
           f"{sum(r['verdict'] == 'OK' for r in rows)} OK, {sum(r['verdict'] != 'OK' for r in rows)} to rebuild "
           f"(rules LIB-14, LIB-17, LIB-19).", "",
           "| Component | MPN | Check | Verdict | Reasons |", "|---|---|---|---|---|"]
    out += [f"| {r['id']} | {r['mpn']} | {r['check']} | {r['verdict']} | {'; '.join(r['why']) or '-'} |" for r in rows]
    return "\n".join(out) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("mark", "source"):
        ap = argparse.ArgumentParser(prog=f"lib_audit.py {argv[0]}")
        ap.add_argument("id")
        if argv[0] == "mark":
            ap.add_argument("--status", choices=STATUSES, required=True)
            ap.add_argument("--by", required=True)
            ap.add_argument("--note", default="")
        else:
            ap.add_argument("--from", dest="src", choices=SOURCES, required=True)
            ap.add_argument("--ref", default="", help="the DbLib or library item it was copied from")
        a = ap.parse_args(argv[1:])
        cat = lc.load_catalog()
        c = next((x for x in cat["components"] if x["id"] == a.id), None)
        if not c:
            print(f"FAIL no catalog component {a.id}"); return 1
        if argv[0] == "mark":
            if a.status == "confirmed" and a.by.lower() in ("claude", "agent", "ai"):
                print("FAIL only a person marks a component confirmed (LIB-19)"); return 1
            c["check"] = {"status": a.status, "by": a.by, "date": lc.today(), "note": a.note}
        else:
            c["source"] = {"from": a.src, "ref": a.ref, "date": lc.today()}
        lc.save_catalog(cat)
        print(f"{a.id}: {argv[0]} recorded"); return 0
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--md", help="write the table to this Markdown file")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    rows = audit(lc.load_catalog(), parts_by_mpn(), set(a.only) if a.only else None)
    for r in rows:
        print(f"{r['verdict']:<8}{r['id']:<44}{r['check']:<10}{'; '.join(r['why'])}")
    print(f"{len(rows)} components, {sum(r['verdict'] == 'OK' for r in rows)} OK, "
          f"{sum(r['verdict'] != 'OK' for r in rows)} to rebuild")
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(to_md(rows))
        print(f"written {a.md}")
    return 0 if rows and all(r["verdict"] == "OK" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
