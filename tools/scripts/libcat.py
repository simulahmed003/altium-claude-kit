"""libcat.py - shared code for the global library and catalog (rules LIB-05, LIB-06). Imported by
lib_promote, lib_pull, lib_update, lib_status, catalog_check, cad_register, cad_check.

Layout (D:\\EDA\\library):
  catalog\\components.json    single source of truth (components + footprints); components.md is generated
  catalog\\CHANGELOG.md       one line per promotion / revision
  symbols\\<category>\\<family>.SchLib, footprints\\<package type>.PcbLib   global libraries (altium-lib writes them, never Python)
  datasheets\\                PDFs referenced by the catalog (sha256 recorded)
  models\\step\\, models\\index.json   3D models (cad_register.py / cad_check.py)
Project side: projects\\<p>\\libs\\lib_manifest.json records which global rev and content hash each local part has.
Python never writes .SchLib / .PcbLib: copies are planned here and done with altium-lib
copy_component_cross_library (preserve_external_paths=true), then verified by content hash.
python libcat.py --help prints this text.
"""
import datetime, glob, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import altium_io

GLOBAL = os.environ.get("EDA_GLOBAL", os.path.join(ROOT, "library"))
CATEGORIES = {"R": "passives", "C": "passives", "L": "passives", "FB": "passives", "U": "ics", "Q": "discretes",
              "D": "discretes", "J": "connectors", "TP": "connectors", "SW": "electromech", "Y": "passives"}
# Family when the part has no component-database record: only prefixes with one obvious family. Others need
# a database record (library\parts, by MPN) or "family" in --info.
DEFAULT_FAMILY = {"R": "passives/resistor", "C": "passives/capacitor_mlcc", "L": "passives/inductor_power",
                  "FB": "passives/ferrite_bead", "TP": "connectors/test_point", "LED": "discretes/led"}
# Global footprint libraries are sorted by package type (user decision 2026-10-19): first match wins.
PACKAGE_TYPES = ((r"^(RES|CAP|IND|LED|DIO|FUS|BEAD|FER)C\d", "chip"), (r"H?SOIC|^SO\d|SOP\d|MSOP|TSSOP", "soic"),
                 (r"^SOT|TSOT|^SC70|^SC-70", "sot"), (r"QFN|DFN|^SON|WSON|VSON", "qfn_dfn"), (r"^TO[-_]?\d|DPAK|D2PAK", "to"),
                 (r"^TB_", "terminal_block"), (r"^TP_", "test_point"), (r"^IND_", "inductor_smd"),
                 (r"^HDR|^PINHDR|^PH_", "header"), (r"^USB", "usb"), (r"^XTAL|^OSC", "crystal_osc"))
FP_STATUS = ("datasheet-verified", "derived", "unverified-accepted")
COMP_FIELDS = ("id", "category", "family", "symbol", "global_lib", "rev", "symbol_hash", "footprint", "value", "description",
               "mfr", "mpn", "lcsc", "lcsc_verified", "jlc_tier", "datasheet", "preferred", "caveats",
               "source_project", "promoted", "history")
FP_FIELDS = ("name", "category", "package_type", "global_lib", "rev", "footprint_hash", "status", "status_source", "caveats",
             "courtyard_mm", "step", "source_project", "history")


def today():
    return datetime.date.today().isoformat()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def gpath(*p, root=None):
    return os.path.join(root or GLOBAL, *p)


def load_catalog(root=None):
    p = gpath("catalog", "components.json", root=root)
    if not os.path.isfile(p):
        return {"schema": 1, "components": [], "footprints": []}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_catalog(cat, root=None):
    os.makedirs(gpath("catalog", root=root), exist_ok=True)
    cat["components"].sort(key=lambda c: (c["category"], c["id"]))
    cat["footprints"].sort(key=lambda c: (c["category"], c["name"]))
    with open(gpath("catalog", "components.json", root=root), "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=1)
    with open(gpath("catalog", "components.md", root=root), "w", encoding="utf-8") as f:
        f.write(catalog_md(cat))


def changelog(line, root=None):
    p = gpath("catalog", "CHANGELOG.md", root=root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    new = not os.path.isfile(p)
    with open(p, "a", encoding="utf-8") as f:
        if new:
            f.write("# Global library changelog\n\nNewest last. One line per change: date, item, rev, hash, note.\n\n")
        f.write(f"- {today()} {line}\n")


def catalog_md(cat):
    L = ["# Global component catalog", "",
         "Generated from components.json by the lib scripts; do not edit by hand. Preferred = use first.", "",
         "## Components", "",
         "| ID | Cat | Value | MPN | LCSC | Verified | Tier | Footprint | Rev | Preferred | Caveats |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cat["components"]:
        L.append(f"| {c['id']} | {c['category']} | {c.get('value', '')} | {c.get('mpn', '')} | {c.get('lcsc', '')} | "
                 f"{'yes' if c.get('lcsc_verified') else 'NO'} | {c.get('jlc_tier', '')} | {c.get('footprint', '')} | "
                 f"{c['rev']} | {'yes' if c.get('preferred') else ''} | {'; '.join(c.get('caveats', []))} |")
    L += ["", "## Footprints", "", "| Name | Cat | Status | Source of status | Rev | Courtyard mm | 3D | Caveats |",
          "|---|---|---|---|---|---|---|---|"]
    for f in cat["footprints"]:
        L.append(f"| {f['name']} | {f['category']} | {f['status']} | {f.get('status_source', '')} | {f['rev']} | "
                 f"{f.get('courtyard_mm') or 'TODO'} | {f.get('step') or '-'} | {'; '.join(f.get('caveats', []))} |")
    gen = cat.get("generic", [])
    if gen:
        L += ["", "## Generic symbols (specs, value set per instance)", "", "| ID | Footprint | Spec |", "|---|---|---|"]
        L += [f"| {g['id']} | {g['footprint']} | {g['spec']} |" for g in gen]
    return "\n".join(L) + "\n"


def category_of(prefix):
    return CATEGORIES.get(prefix, "misc")


def symbol_lib(category, family):
    """Global symbol library of a family: symbols/<category>/<family>.SchLib (one folder per category)."""
    return f"symbols/{category}/{family}.SchLib"


def footprint_lib(package_type):
    """Global footprint library of a package type: footprints/<package type>.PcbLib (each footprint exists once)."""
    return f"footprints/{package_type}.PcbLib"


def local_libs_for(project, category, family):
    """Local libraries of a family: libs/<category>/<family>.SchLib and .PcbLib (footprints per family)."""
    d = os.path.join(project, "libs", category)
    return os.path.join(d, f"{family}.SchLib"), os.path.join(d, f"{family}.PcbLib")


def package_type_of(footprint):
    for rx, t in PACKAGE_TYPES:
        if re.search(rx, footprint or "", re.I):
            return t
    return None


def family_of(mpn, prefix, root=None):
    """(category, family) from the component database (library/parts, by MPN), else the prefix default, else None."""
    if mpn and mpn not in ("-",):
        for f in glob.glob(gpath("parts", "*", "*", "*.json", root=root)):
            try:
                with open(f, encoding="utf-8") as fh:
                    r = json.load(fh)
            except (OSError, ValueError):
                continue
            if r.get("mpn", "").lower() == mpn.lower() and "/" in r.get("category", ""):
                return tuple(r["category"].split("/"))
    d = DEFAULT_FAMILY.get(prefix)
    return tuple(d.split("/")) if d else None


def find(cat, kind, key):
    lst = cat["components"] if kind == "c" else cat["footprints"]
    k = "id" if kind == "c" else "name"
    return next((x for x in lst if x[k] == key), None)


def local_libs(project):
    """(SchLib list, PcbLib list) in projects/<p>/libs and its category folders (no _dryrun, no .bak)."""
    d = os.path.join(project, "libs")
    pick = lambda ext: sorted(f for f in glob.glob(os.path.join(d, "**", f"*.{ext}"), recursive=True)
                              if "_dryrun" not in os.path.relpath(f, d).split(os.sep))
    return pick("SchLib"), pick("PcbLib")


def read_local(project):
    """{symbol: (sym, lib)}, {footprint: (fp, lib)} from the project's libraries."""
    sl, pl = local_libs(project)
    syms, fps = {}, {}
    for lib in sl:
        for n, s in altium_io.schlib_symbols(lib).items():
            syms[n] = (s, lib)
    for lib in pl:
        for n, f in altium_io.pcblib_footprints(lib).items():
            fps[n] = (f, lib)
    return syms, fps


def read_global(cat, root=None):
    """Same, from the global family / package-type libraries that exist on disk."""
    syms, fps = {}, {}
    for lib in sorted({c["global_lib"] for c in cat["components"]}):
        p = gpath(lib, root=root)
        if os.path.isfile(p):
            for n, s in altium_io.schlib_symbols(p).items():
                syms[n] = (s, p)
    for lib in sorted({f["global_lib"] for f in cat["footprints"]}):
        p = gpath(lib, root=root)
        if os.path.isfile(p):
            for n, f in altium_io.pcblib_footprints(p).items():
                fps[n] = (f, p)
    return syms, fps


def param(sym, name):
    return next((p["text"] for p in sym["params"] if p["name"].upper() == name.upper()), "")


def prefix_of(sym):
    d = next((r.get("TEXT", "") for r in sym["records"] if r.get("RECORD") == "34"), "")
    m = re.match(r"[A-Za-z]+", d.rstrip("?"))
    return m.group(0).upper() if m else "X"


def manifest_path(project):
    return os.path.join(project, "libs", "lib_manifest.json")


def load_manifest(project):
    p = manifest_path(project)
    if not os.path.isfile(p):
        return {"schema": 1, "global_root": GLOBAL.replace("\\", "/"), "components": {}, "footprints": {}}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(project, m):
    m["updated"] = today()
    with open(manifest_path(project), "w", encoding="utf-8") as f:
        json.dump(m, f, indent=1)


def gate_ticked(project, gate):
    p = os.path.join(project, "gates.md")
    if not os.path.isfile(p):
        return False
    with open(p, encoding="utf-8") as f:
        return any(re.match(rf"\s*- \[[xX]\] \*\*{gate}\b", line) for line in f)


def rules_version():
    with open(os.path.join(ROOT, "rules", "VERSION")) as f:
        return f.read().strip()


if __name__ == "__main__":
    import argparse
    argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                            epilog=__doc__).parse_args()
