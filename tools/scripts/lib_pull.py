"""lib_pull.py - take parts from the global library into a project's local libraries (rule LIB-06).

Usage:
  python lib_pull.py <project dir> <component ID ...> [--global-root DIR]      plan the copies
  python lib_pull.py <project dir> --verify [--global-root DIR]               check and record them
Plan: writes ai\\lib_pull_plan.json with the altium-lib copy_component_cross_library calls (global category
library -> projects\\<p>\\libs\\<p>.SchLib / .PcbLib, preserve_external_paths=true) and marks the parts
"planned" in libs\\lib_manifest.json. The agent runs the copies (library closed in Altium), then --verify:
every planned / pulled part's local content hash must equal the catalog rev it came from; verified parts
become "pulled". Exit 0 when everything is planned / verified, 1 otherwise.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import altium_io, libcat as lc


def plan(project, ids, root=None):
    cat, man = lc.load_catalog(root), lc.load_manifest(project)
    pname = os.path.basename(os.path.abspath(project))
    lsch = os.path.join(project, "libs", f"{pname}.SchLib").replace("\\", "/")
    lpcb = os.path.join(project, "libs", f"{pname}.PcbLib").replace("\\", "/")
    copies, errs = [], []
    for i in ids:
        c = lc.find(cat, "c", i)
        if c is None:
            errs.append(f"{i}: not in the catalog")
            continue
        src = lc.gpath(c["global_lib"], root=root)
        if not os.path.isfile(src):
            errs.append(f"{i}: global library {c['global_lib']} not written yet (see promote_plan.json)")
        copies.append(dict(tool="altium-lib copy_component_cross_library", source=src.replace("\\", "/"), target=lsch,
                           component=i, preserve_external_paths=True))
        man["components"][i] = dict(rev=c["rev"], symbol_hash=c["symbol_hash"], origin="planned", footprint=c["footprint"])
        f = lc.find(cat, "f", c["footprint"]) if c.get("footprint") else None
        if f and c["footprint"] not in man["footprints"]:
            copies.append(dict(tool="altium-lib copy_component_cross_library (PcbLib)",
                               source=lc.gpath(f["global_lib"], root=root).replace("\\", "/"), target=lpcb,
                               component=f["name"], preserve_external_paths=True))
            man["footprints"][f["name"]] = dict(rev=f["rev"], footprint_hash=f["footprint_hash"], origin="planned")
        if c.get("caveats"):
            print(f"NOTE {i}: caveats: {'; '.join(c['caveats'])}")
    os.makedirs(os.path.join(project, "ai"), exist_ok=True)
    with open(os.path.join(project, "ai", "lib_pull_plan.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(date=lc.today(), copies=copies,
                       after="update each copied symbol's footprint link to the local PcbLib if needed, then lib_pull.py --verify"),
                  fh, indent=1)
    lc.save_manifest(project, man)
    return copies, errs


def verify(project):
    man = lc.load_manifest(project)
    syms, fps = lc.read_local(project)
    errs, n = [], 0
    for kind, items, local, hfn, hk in (("component", man["components"], syms, altium_io.symbol_hash, "symbol_hash"),
                                        ("footprint", man["footprints"], fps, altium_io.footprint_hash, "footprint_hash")):
        for i, e in items.items():
            if e["origin"] not in ("planned", "pulled"):
                continue
            if i not in local:
                errs.append(f"{kind} {i}: not in the local libraries yet")
            elif hfn(local[i][0]) != e[hk]:
                errs.append(f"{kind} {i}: local content differs from global rev {e['rev']}")
            else:
                e["origin"] = "pulled"
                n += 1
    lc.save_manifest(project, man)
    return n, errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("project")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    if a.verify:
        n, errs = verify(a.project)
        for e in errs:
            print("FAIL", e)
        print(f"{n} items verified")
    else:
        if not a.ids:
            ap.error("give component IDs or --verify")
        copies, errs = plan(a.project, a.ids, a.global_root)
        for e in errs:
            print("FAIL", e)
        print(f"{len(copies)} altium-lib copies planned in ai\\lib_pull_plan.json")
    print("RESULT", "FAIL" if errs else "PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
