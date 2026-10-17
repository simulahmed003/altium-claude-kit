#!/usr/bin/env python3
"""comp: the only interface between Claude and the component database.

Commands return short output: YAML for `get`, one JSON line {status, summary, issues} for the rest.
Run `comp.py <command> --help` for details.
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parents[2]
DB = KIT / "components"
INDEX = DB / "index.json"
SCHEMA = DB / "_schema" / "part.schema.json"
QTY_KEYS = {"value", "min", "typ", "max"}


def out(status, summary, issues=None, **extra):
    print(json.dumps({"status": status, "summary": summary, "issues": issues or [], **extra}))
    return 0 if status == "ok" else 1


def part_dirs():
    for p in sorted(DB.rglob("part.yaml")):
        if not any(s.startswith("_") for s in p.relative_to(DB).parts):
            yield p.parent


def find_part(mpn):
    for d in part_dirs():
        if d.name.lower() == mpn.lower():
            return d
    return None


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- validate ----------

def check_quantities(node, where, issues):
    """Every quantity dict needs a unit and a datasheet ref."""
    if isinstance(node, dict):
        if QTY_KEYS & node.keys():
            if "unit" not in node:
                issues.append(f"{where}: missing unit")
            if "ref" not in node:
                issues.append(f"{where}: missing ref")
            return
        for k, v in node.items():
            check_quantities(v, f"{where}.{k}", issues)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            check_quantities(v, f"{where}[{i}]", issues)


def validate_dir(d):
    import jsonschema

    issues = []
    try:
        rec = load(d / "part.yaml")
    except yaml.YAMLError as e:
        return [f"part.yaml: YAML error: {e}"]
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    for err in jsonschema.Draft202012Validator(schema).iter_errors(rec):
        issues.append(f"schema: {'/'.join(map(str, err.path)) or '(root)'}: {err.message}")
    if rec.get("id") != d.name:
        issues.append(f"id '{rec.get('id')}' != folder name '{d.name}'")
    rel = d.parent.relative_to(DB).as_posix()
    if rec.get("category") != rel:
        issues.append(f"category '{rec.get('category')}' != folder path '{rel}'")
    for sec in ("selection", "abs_max", "recommended", "application", "thermal"):
        check_quantities(rec.get(sec), sec, issues)
    for i, pin in enumerate(rec.get("pins") or []):
        if isinstance(pin, dict) and "ref" not in pin:
            issues.append(f"pins[{i}]: missing ref")
    if not (d / "source.yaml").exists():
        issues.append("source.yaml missing")
    if list(d.rglob("*.pdf")):
        issues.append("PDF found: datasheets must not be committed")
    return [f"{d.name}: {m}" for m in issues]


def cmd_validate(a):
    dirs = list(part_dirs()) if a.all else [find_part(m) for m in a.mpn]
    if None in dirs:
        return out("error", "part not found", [m for m, d in zip(a.mpn, dirs) if d is None])
    issues = [i for d in dirs for i in validate_dir(d)]
    return out("ok" if not issues else "fail", f"{len(dirs)} part(s) checked, {len(issues)} issue(s)", issues[:50])


# ---------- index / search / get ----------

def flat_selection(sel):
    """Flatten selection params to 'key=min..max unit' strings for search."""
    terms = []
    for k, v in (sel or {}).items():
        if isinstance(v, dict) and QTY_KEYS & v.keys():
            rng = "..".join(str(v[x]) for x in ("min", "typ", "value", "max") if x in v)
            terms.append(f"{k}={rng}{v.get('unit', '')}")
        elif not isinstance(v, (dict, list)):
            terms.append(f"{k}={v}")
    return terms


def cmd_index(a):
    parts = []
    for d in part_dirs():
        r = load(d / "part.yaml")
        parts.append({
            "id": r.get("id"), "mfr": r.get("mfr"), "category": r.get("category"),
            "package": r.get("package"), "status": r.get("status"),
            "description": r.get("description", ""), "params": flat_selection(r.get("selection")),
            "path": d.relative_to(DB).as_posix(),
        })
    INDEX.write_text(json.dumps({"generated": datetime.date.today().isoformat(), "parts": parts}, indent=1) + "\n",
                     encoding="utf-8")
    return out("ok", f"indexed {len(parts)} part(s)")


def cmd_search(a):
    parts = json.loads(INDEX.read_text(encoding="utf-8")).get("parts", [])
    tokens = [t.lower() for t in re.split(r"\s+", " ".join(a.query)) if t]
    hits = []
    for p in parts:
        text = " ".join(str(p.get(k, "")) for k in ("id", "mfr", "category", "package", "description")).lower()
        text += " " + " ".join(p.get("params", [])).lower()
        score = sum(t in text for t in tokens)
        if score:
            hits.append((score, p))
    hits.sort(key=lambda h: -h[0])
    for _, p in hits[: a.limit]:
        print(f"{p['id']:<20} {p['package']:<10} {p['status']:<20} {p['category']:<18} {p['description']}")
    if not hits:
        print("no match (run `comp index` if parts were added)")
    return 0


def digest_section(d, name):
    f = d / "digest.md"
    if not f.exists():
        return ""
    m = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", f.read_text(encoding="utf-8"), re.M | re.S)
    return m.group(1).strip() if m else ""


def cmd_get(a):
    d = find_part(a.mpn)
    if not d:
        return out("error", f"{a.mpn} not in database; use `comp ingest`")
    rec = load(d / "part.yaml")
    head = {k: rec.get(k) for k in ("id", "mfr", "package", "status")}
    if not a.section:
        head["sections"] = [k for k in rec if k not in head and k not in ("category", "datasheet", "description")]
        print(yaml.safe_dump(head, sort_keys=False, allow_unicode=True).strip())
        return 0
    body = {**head, a.section: rec.get(a.section)}
    print(yaml.safe_dump(body, sort_keys=False, allow_unicode=True).strip())
    note = digest_section(d, a.section)
    if note:
        print(f"# digest notes\n{note}")
    return 0


# ---------- project commands ----------

def cmd_new_project(a):
    dst = Path(a.path).resolve()
    if dst.exists() and any(dst.iterdir()):
        return out("error", f"{dst} exists and is not empty")
    shutil.copytree(KIT / "templates" / "project", dst, dirs_exist_ok=True)
    for f in (dst / "CLAUDE.md", dst / "project.yaml"):
        t = f.read_text(encoding="utf-8").replace("{{KIT_PATH}}", KIT.as_posix())
        if f.name == "project.yaml":
            t = t.replace("name: my-board", f"name: {dst.name}", 1)
        f.write_text(t, encoding="utf-8")
    return out("ok", f"project created at {dst}")


def cmd_pull(a):
    proj = Path(a.project).resolve()
    lock_f = proj / "components.lock.yaml"
    if not lock_f.exists():
        return out("error", f"{proj} is not a kit project (no components.lock.yaml)")
    lock = load(lock_f)
    lock.setdefault("parts", {})
    lock["parts"] = lock["parts"] or {}
    done, issues = [], []
    for mpn in a.mpn:
        d = find_part(mpn)
        if not d:
            issues.append(f"{mpn}: not in database")
            continue
        h = sha256(d / "part.yaml")
        old = lock["parts"].get(d.name)
        if old and old["sha256"] != h and not a.update:
            issues.append(f"{d.name}: DB changed since lock; re-run with --update to accept")
            continue
        dst = proj / "components" / d.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(d, dst)
        rec = load(d / "part.yaml")
        lock["parts"][d.name] = {"path": d.relative_to(DB).as_posix(), "sha256": h,
                                 "status": rec.get("status"), "pulled": datetime.date.today().isoformat()}
        if rec.get("status") != "verified":
            issues.append(f"{d.name}: status {rec.get('status')} (blocks schematic freeze)")
        done.append(d.name)
    with open(lock_f, "w", encoding="utf-8") as f:
        f.write("# Written by `comp pull`. Do not edit by hand.\n")
        yaml.safe_dump(lock, f, sort_keys=True)
    # Building lib/Project.SchLib and Project.PcbLib comes in roadmap M2.
    return out("ok" if done else "fail", f"pulled {len(done)} part(s)", issues, pulled=done)


def not_yet(milestone):
    def f(a):
        return out("not_implemented", f"`{a.cmd}` is planned in roadmap {milestone}; see docs/ROADMAP.md")
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(prog="comp", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search the index by words and params")
    s.add_argument("query", nargs="+")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("get", help="print one part, or one section of it")
    s.add_argument("mpn")
    s.add_argument("--section", help="selection | abs_max | recommended | pins | application | layout | thermal | cad")
    s.set_defaults(fn=cmd_get)

    s = sub.add_parser("validate", help="check part records")
    s.add_argument("mpn", nargs="*")
    s.add_argument("--all", action="store_true")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("index", help="rebuild components/index.json")
    s.set_defaults(fn=cmd_index)

    s = sub.add_parser("new-project", help="create a project from templates/project")
    s.add_argument("path")
    s.set_defaults(fn=cmd_new_project)

    s = sub.add_parser("pull", help="copy parts into a project and lock their versions")
    s.add_argument("mpn", nargs="+")
    s.add_argument("--project", default=".")
    s.add_argument("--update", action="store_true", help="accept newer DB versions of locked parts")
    s.set_defaults(fn=cmd_pull)

    for name, ms in (("ingest", "M1"), ("push", "M1"), ("cad", "M2")):
        s = sub.add_parser(name, help=f"(planned, {ms})")
        s.add_argument("args", nargs="*")
        s.add_argument("--pdf")
        s.set_defaults(fn=not_yet(ms))

    a = ap.parse_args(argv)
    if a.cmd == "validate" and not a.all and not a.mpn:
        ap.error("validate needs MPN(s) or --all")
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
