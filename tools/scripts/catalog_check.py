"""catalog_check.py - check the global catalog and (optionally) a project's manifest (rules RQ-01, RQ-03, LIB-05, LIB-06).

Usage:
  python catalog_check.py [--global-root DIR] [--project DIR] [--strict] [--write-md]
Catalog (library\\catalog\\components.json):
  - every field present; IDs unique; category = file category; footprint of each component in the catalog
  - datasheet: sha256 of the file in library\\datasheets equal to the recorded one (RQ-01), else FAIL;
    a PDF not on disk is a NOT FETCHED note (PDFs are not in git: datasheets_fetch.py); a missing source url is
    a note (a FAIL with --strict)
  - lcsc_verified is true or false; false is listed as NOT VERIFIED (RQ-03, a FAIL with --strict)
  - footprint status one of datasheet-verified / derived / unverified-accepted, with its source (LIB-05)
  - global library files that exist: content hash = catalog rev; files not written yet are PENDING
    (a FAIL with --strict); a pending item missing from catalog\\promote_plan.json is always a FAIL
--project: every manifest entry exists in the catalog with a rev <= the catalog rev (LIB-06).
--write-md regenerates components.md. Exit 0 when clean, 1 otherwise.
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import altium_io, libcat as lc
import lib_promote


def check(root=None, project=None, strict=False):
    cat = lc.load_catalog(root)
    errs, notes = [], []
    if not cat["components"] and not cat["footprints"]:
        errs.append("catalog is empty or missing")
    ids = [c.get("id") for c in cat["components"]]
    for d in {i for i in ids if ids.count(i) > 1}:
        errs.append(f"duplicate component id {d}")
    fpn = {f["name"] for f in cat["footprints"]}
    fetched_missing = []
    for c in cat["components"]:
        i = c.get("id", "?")
        miss = [k for k in lc.COMP_FIELDS if k not in c]
        if miss:
            errs.append(f"{i}: missing fields {miss}")
            continue
        if c["global_lib"] != lc.symbol_lib(c["category"], c["family"]):
            errs.append(f"{i}: global_lib {c['global_lib']} must be {lc.symbol_lib(c['category'], c['family'])}")
        if c["footprint"] and c["footprint"] not in fpn:
            errs.append(f"{i}: footprint {c['footprint']} not in the catalog")
        ds = c["datasheet"]
        if ds:
            p = lc.gpath(ds["path"], root=root)
            if not os.path.isfile(p):
                fetched_missing.append(i)
            elif lc.sha256(p) != ds["sha256"]:
                errs.append(f"{i}: datasheet {ds['path']} sha256 changed")
            if not ds.get("url"):
                (errs if strict else notes).append(f"{i}: datasheet without a source url")
        elif c.get("mpn") not in ("", "-", None):
            errs.append(f"{i}: MPN {c['mpn']} without a datasheet")
        if not isinstance(c["lcsc_verified"], bool):
            errs.append(f"{i}: lcsc_verified must be true/false")
        elif not c["lcsc_verified"] and c.get("lcsc") not in ("", "-"):
            (errs if strict else notes).append(f"{i}: LCSC {c['lcsc']} NOT VERIFIED")
    for f in cat["footprints"]:
        n = f.get("name", "?")
        miss = [k for k in lc.FP_FIELDS if k not in f]
        if miss:
            errs.append(f"{n}: missing fields {miss}")
            continue
        if f["status"] not in lc.FP_STATUS:
            errs.append(f"{n}: status '{f['status']}' not in {lc.FP_STATUS}")
        if not f["status_source"]:
            errs.append(f"{n}: status without a source")
        if f["global_lib"] != lc.footprint_lib(f["package_type"]):
            errs.append(f"{n}: global_lib {f['global_lib']} must be {lc.footprint_lib(f['package_type'])}")
    if fetched_missing:
        notes.append(f"NOT FETCHED: {len(fetched_missing)} datasheet PDFs are not on disk (vendor PDFs are not in git; "
                     f"run datasheets_fetch.py): {', '.join(fetched_missing[:4])}{' ...' if len(fetched_missing) > 4 else ''}")
    verr, pending = lib_promote.verify(root)
    errs += verr
    if pending:
        (errs if strict else notes).append(f"PENDING: {len(pending)} items not yet in the global library files "
                                           f"(run the altium-lib copies in promote_plan.json)")
    gaps = lib_promote.plan_gaps(root)
    if gaps:
        errs.append(f"{len(gaps)} pending items are not in promote_plan.json (rebuild: lib_promote.py - --plan): "
                    f"{', '.join(gaps[:5])}{' ...' if len(gaps) > 5 else ''}")
    if project:
        man = lc.load_manifest(project)
        if not os.path.isfile(lc.manifest_path(project)):
            errs.append("project has no libs\\lib_manifest.json")
        for kind, items, ck in (("component", man["components"], "c"), ("footprint", man["footprints"], "f")):
            for i, e in items.items():
                g = lc.find(cat, ck, i)
                if g is None:
                    errs.append(f"manifest {kind} {i}: not in the catalog")
                elif e["rev"] > g["rev"]:
                    errs.append(f"manifest {kind} {i}: rev {e['rev']} newer than catalog rev {g['rev']}")
    return errs, notes, cat


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--global-root")
    ap.add_argument("--project")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--write-md", action="store_true")
    a = ap.parse_args(argv)
    errs, notes, cat = check(a.global_root, a.project, a.strict)
    if a.write_md and cat["components"]:
        lc.save_catalog(cat, a.global_root)
    for n in notes:
        print("NOTE", n)
    for e in errs:
        print("FAIL", e)
    print(f"{len(cat['components'])} components, {len(cat['footprints'])} footprints, {len(errs)} problems, {len(notes)} notes")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
