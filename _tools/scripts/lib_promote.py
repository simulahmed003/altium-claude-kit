"""lib_promote.py - promote a project's library parts into the global catalog / library (rule LIB-06).

Usage:
  python lib_promote.py <project dir> [--parts ID ...] [--info info.json] [--dry-run]
  python lib_promote.py <project dir> --verify
  python lib_promote.py - --plan                   (rebuild promote_plan.json only)
Refuses unless the project's G1 is ticked in gates.md (footprints signed off). For every symbol in the
project's libs\\*.SchLib (or --parts) and the footprint it links:
  - content hash equal to the catalog's current rev  -> nothing to do
  - new or changed                                    -> rev + 1, catalog entry written, CHANGELOG line
Part data comes from the symbol parameters (Value, Manufacturer, MPN, LCSC, JLCPCB Type, Datasheet); the
datasheet PDF (docs\\datasheets\\) is copied to _global\\datasheets\\ with its sha256.
--info: JSON {"components": {id: {...fields: caveats, lcsc_verified, preferred, datasheet_url}}, "footprints": {name:
{status, status_source, caveats, courtyard_mm}}} - required for footprint status (LIB-05) on first promotion.
Writes libs\\lib_manifest.json in the project (origin "promoted") and _global\\catalog\\promote_plan.json:
the altium-lib copy_component_cross_library calls (preserve_external_paths=true) that put the parts into
_global\\libs\\<category>.SchLib/.PcbLib. Python never writes the libraries.
The plan is always derived from the whole catalog versus the global library files (not from this run), so a
re-run with nothing changed keeps every copy still pending. --plan rebuilds it alone; catalog_check FAILs
when a pending item is missing from the plan.
--verify: every catalog item found in a global library must match its catalog hash; the rest are pending.
Exit 0 on success, 1 on refusal or any problem.
"""
import argparse, json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import altium_io, libcat as lc


def promote(project, parts=None, info=None, dry=False, root=None):
    info = info or {}
    out, errs, plan, log, copies = [], [], [], [], []
    if not lc.gate_ticked(project, "G1"):
        return [], ["G1 is not ticked in gates.md: promotion refused (LIB-06)"], []
    cat = lc.load_catalog(root)
    man = lc.load_manifest(project)
    syms, fps = lc.read_local(project)
    pname = os.path.basename(os.path.abspath(project))
    want = parts or sorted(syms)
    for sid in want:
        if sid not in syms:
            errs.append(f"{sid}: not in the project libraries")
            continue
        s, slib = syms[sid]
        h = altium_io.symbol_hash(s)
        cat_ = lc.category_of(lc.prefix_of(s))
        fpn = s["footprints"][0] if s["footprints"] else None
        ci = info.get("components", {}).get(sid, {})
        old = lc.find(cat, "c", sid)
        if old and old["symbol_hash"] == h:
            out.append(f"{sid}: unchanged (rev {old['rev']})")
            rev = old["rev"]
        else:
            rev = (old["rev"] + 1) if old else 1
            ds = lc.param(s, "Datasheet")
            dsp = os.path.join(project, "docs", "datasheets", ds) if ds and ds != "-" else None
            dsrec = None
            if dsp and os.path.isfile(dsp):
                dsrec = dict(path=f"datasheets/{ds}", sha256=lc.sha256(dsp), url=ci.get("datasheet_url", ""))
                copies.append((dsp, lc.gpath("datasheets", ds, root=root)))
            elif ds and ds != "-":
                errs.append(f"{sid}: datasheet {ds} not found in docs\\datasheets")
            entry = dict(id=sid, category=cat_, symbol=sid, global_lib=f"libs/{cat_}.SchLib", rev=rev, symbol_hash=h,
                         footprint=fpn, value=lc.param(s, "Value"), description="", mfr=lc.param(s, "Manufacturer"),
                         mpn=lc.param(s, "MPN"), lcsc=lc.param(s, "LCSC"), lcsc_verified=False,
                         jlc_tier=lc.param(s, "JLCPCB Type"), datasheet=dsrec, preferred=False, caveats=[],
                         source_project=pname,
                         promoted=dict(date=lc.today(), gate="G1", rules_version=lc.rules_version()),
                         history=(old or {}).get("history", []) + [dict(rev=rev, date=lc.today(), hash=h, project=pname)])
            for r in s["records"]:
                if r.get("RECORD") == "1":
                    entry["description"] = r.get("COMPONENTDESCRIPTION", "")
            entry.update({k: v for k, v in ci.items() if k in lc.COMP_FIELDS})
            if old:
                cat["components"].remove(old)
            cat["components"].append(entry)
            out.append(f"{sid}: {'rev ' + str(rev) if old else 'new'} -> {entry['global_lib']}")
            log.append(f"component {sid} rev {rev} hash {h} from {pname}")
            plan.append(dict(tool="altium-lib copy_component_cross_library", source=slib.replace("\\", "/"),
                             target=lc.gpath(entry["global_lib"], root=root).replace("\\", "/"), component=sid,
                             preserve_external_paths=True))
        man["components"][sid] = dict(rev=rev, symbol_hash=h, origin="promoted", footprint=fpn)
        if fpn:
            if fpn not in fps:
                errs.append(f"{sid}: footprint {fpn} not in the project PcbLib")
                continue
            f, plib = fps[fpn]
            fh = altium_io.footprint_hash(f)
            fi = info.get("footprints", {}).get(fpn, {})
            fo = lc.find(cat, "f", fpn)
            if fo and fo["footprint_hash"] == fh:
                frev = fo["rev"]
            elif fo is None or fo["footprint_hash"] != fh:
                frev = (fo["rev"] + 1) if fo else 1
                fe = dict(name=fpn, category=cat_, global_lib=f"libs/{cat_}.PcbLib", rev=frev, footprint_hash=fh,
                          status=fi.get("status"), status_source=fi.get("status_source", ""), caveats=[], courtyard_mm=None,
                          step=None, source_project=pname,
                          history=(fo or {}).get("history", []) + [dict(rev=frev, date=lc.today(), hash=fh, project=pname)])
                fe.update({k: v for k, v in fi.items() if k in lc.FP_FIELDS})
                if fe["status"] not in lc.FP_STATUS:
                    errs.append(f"footprint {fpn}: status '{fe['status']}' must be one of {lc.FP_STATUS} (--info)")
                if fo:
                    cat["footprints"].remove(fo)
                cat["footprints"].append(fe)
                out.append(f"  footprint {fpn}: {'rev ' + str(frev) if fo else 'new'} -> {fe['global_lib']}")
                log.append(f"footprint {fpn} rev {frev} hash {fh} from {pname}")
                plan.append(dict(tool="altium-lib copy_component_cross_library (PcbLib)", source=plib.replace("\\", "/"),
                                 target=lc.gpath(fe["global_lib"], root=root).replace("\\", "/"), component=fpn,
                                 preserve_external_paths=True))
            man["footprints"][fpn] = dict(rev=frev, footprint_hash=fh, origin="promoted")
    if errs and not dry:
        return out, errs, plan               # nothing written on error
    if not dry:
        lc.save_catalog(cat, root)
        for line in log:
            lc.changelog(line, root)
        for src, dst in copies:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        lc.save_manifest(project, man)
        plan, perr = write_plan(root, os.path.dirname(os.path.abspath(project)))
        errs += perr
    return out, errs, plan


def build_plan(root=None, projects_root=None):
    """Copies still to run, derived from the catalog versus the global library files (idempotent).
    An item is pending when its global library file is missing or does not hold it yet. The source is the
    library in projects\\<source_project>\\libs that holds the item with the catalog hash."""
    projects_root = projects_root or os.path.join(lc.ROOT, "projects")
    cat = lc.load_catalog(root)
    gsyms, gfps = lc.read_global(cat, root)
    plan, errs, local = [], [], {}
    for kind, items, key, have, hk, hf in (
            ("c", cat["components"], "id", gsyms, "symbol_hash", altium_io.symbol_hash),
            ("f", cat["footprints"], "name", gfps, "footprint_hash", altium_io.footprint_hash)):
        for it in items:
            if it[key] in have:
                continue                        # present (hash checked by verify)
            sp = it["source_project"]
            if sp not in local:
                pdir = os.path.join(projects_root, sp)
                local[sp] = lc.read_local(pdir) if os.path.isdir(pdir) else ({}, {})
            src = local[sp][0 if kind == "c" else 1].get(it[key])
            if src is None or hf(src[0]) != it[hk]:
                errs.append(f"{it[key]}: no library in {sp}\\libs holds it with the catalog hash (rev {it['rev']})")
                continue
            plan.append(dict(tool="altium-lib copy_component_cross_library" + ("" if kind == "c" else " (PcbLib)"),
                             source=src[1].replace("\\", "/"),
                             target=lc.gpath(it["global_lib"], root=root).replace("\\", "/"), component=it[key],
                             preserve_external_paths=True))
    plan.sort(key=lambda p: (p["target"], p["component"]))
    return plan, errs


def write_plan(root=None, projects_root=None):
    plan, errs = build_plan(root, projects_root)
    with open(lc.gpath("catalog", "promote_plan.json", root=root), "w", encoding="utf-8") as f:
        json.dump(dict(built=lc.today(), note="derived from the catalog versus _global\\libs by lib_promote.py --plan",
                       copies=plan), f, indent=1)
    return plan, errs


def plan_gaps(root=None):
    """Pending items (verify) that promote_plan.json does not list."""
    _, pending = verify(root)
    p = lc.gpath("catalog", "promote_plan.json", root=root)
    listed = set()
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            listed = {c["component"] for c in json.load(f).get("copies", [])}
    return [i for i in pending if i not in listed]


def verify(root=None):
    cat = lc.load_catalog(root)
    syms, fps = lc.read_global(cat, root)
    errs, pending = [], []
    for c in cat["components"]:
        if c["id"] not in syms:
            pending.append(c["id"])
        elif altium_io.symbol_hash(syms[c["id"]][0]) != c["symbol_hash"]:
            errs.append(f"{c['id']}: hash in {c['global_lib']} differs from catalog rev {c['rev']}")
    for f in cat["footprints"]:
        if f["name"] not in fps:
            pending.append(f["name"])
        elif altium_io.footprint_hash(fps[f["name"]][0]) != f["footprint_hash"]:
            errs.append(f"{f['name']}: hash in {f['global_lib']} differs from catalog rev {f['rev']}")
    return errs, pending


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("project")
    ap.add_argument("--parts", nargs="*")
    ap.add_argument("--info")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--plan", action="store_true", help="only rebuild promote_plan.json (project may be '-')")
    ap.add_argument("--projects-root", help="where source projects live (default D:\\EDA\\projects)")
    ap.add_argument("--global-root", help="default D:\\EDA\\_global (tests use a temp folder)")
    a = ap.parse_args(argv)
    if a.plan:
        plan, errs = write_plan(a.global_root, a.projects_root)
        for p in plan:
            print(f"copy {p['component']} -> {os.path.basename(p['target'])}")
        for e in errs:
            print("FAIL", e)
        print(f"{len(plan)} altium-lib copies planned in promote_plan.json")
        print("RESULT", "FAIL" if errs else "PASS")
        return 1 if errs else 0
    if a.verify:
        errs, pending = verify(a.global_root)
        for e in errs:
            print("FAIL", e)
        print(f"{len(pending)} items waiting for the altium-lib copy (global library file not written yet)" if pending else "all global items present")
        print("RESULT", "FAIL" if errs else "PASS")
        return 1 if errs else 0
    info = json.load(open(a.info, encoding="utf-8")) if a.info else {}
    out, errs, plan = promote(a.project, a.parts, info, a.dry_run, a.global_root)
    for line in out:
        print(line)
    for e in errs:
        print("FAIL", e)
    print(f"{len(plan)} altium-lib copies planned" + (" (dry run, nothing written)" if a.dry_run else ""))
    print("RESULT", "FAIL" if errs else "PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
