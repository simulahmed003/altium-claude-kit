"""lib_status.py - drift report: project local libraries vs manifest vs global catalog (rule LIB-06).

Usage:
  python lib_status.py <project dir> [--global-root DIR]
Per part in libs\\lib_manifest.json (normalized content hashes, see altium_io.symbol_hash / footprint_hash):
  OK               local = manifest = catalog current rev
  UPDATE           catalog has a newer rev than the manifest (lib_update.py)
  LOCAL CHANGED    local content differs from the rev in the manifest (drift: promote after G1 or revert)
  MISSING          in the manifest, not in the local libraries
  NOT IN CATALOG   manifest part unknown to the catalog
  PLANNED          pull planned, copy not verified yet
Parts in the local libraries but not in the manifest are listed as LOCAL ONLY (allowed before G1).
Exit 0 when nothing is LOCAL CHANGED / MISSING / NOT IN CATALOG, 1 otherwise (also without a manifest).
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import altium_io, libcat as lc

BAD = ("LOCAL CHANGED", "MISSING", "NOT IN CATALOG")


def status(project, root=None):
    rows = []
    if not os.path.isfile(lc.manifest_path(project)):
        return [("-", "-", "MISSING", "no libs\\lib_manifest.json")]
    man, cat = lc.load_manifest(project), lc.load_catalog(root)
    syms, fps = lc.read_local(project)
    for kind, items, local, hfn, hk, ck in (
            ("component", man["components"], syms, altium_io.symbol_hash, "symbol_hash", "c"),
            ("footprint", man["footprints"], fps, altium_io.footprint_hash, "footprint_hash", "f")):
        for i, e in sorted(items.items()):
            g = lc.find(cat, ck, i)
            if e.get("origin") == "planned":
                rows.append((kind, i, "PLANNED", f"rev {e['rev']}"))
            elif i not in local:
                rows.append((kind, i, "MISSING", "not in the local libraries"))
            elif hfn(local[i][0]) != e[hk]:
                rows.append((kind, i, "LOCAL CHANGED", f"differs from rev {e['rev']} in the manifest"))
            elif g is None:
                rows.append((kind, i, "NOT IN CATALOG", ""))
            elif g["rev"] > e["rev"]:
                rows.append((kind, i, "UPDATE", f"rev {e['rev']} -> {g['rev']}"))
            else:
                rows.append((kind, i, "OK", f"rev {e['rev']} ({e.get('origin')})"))
        for i in sorted(set(local) - set(items)):
            rows.append((kind, i, "LOCAL ONLY", "not promoted / not from the global library"))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("project")
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    rows = status(a.project, a.global_root)
    for kind, i, st, why in rows:
        print(f"{st:15} {kind:9} {i:24} {why}")
    bad = sum(1 for r in rows if r[2] in BAD)
    counts = {}
    for r in rows:
        counts[r[2]] = counts.get(r[2], 0) + 1
    print(f"\n{counts}")
    print("RESULT", "FAIL" if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
