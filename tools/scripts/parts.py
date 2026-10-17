"""parts.py - component database: one record per orderable part, facts tied to datasheet pages (roadmap M1).

Layout (library\\, see library\\parts\\README.md):
  parts\\taxonomy.json                     categories, families, required facts, units
  parts\\<category>\\<family>\\<MPN>__<mfr>.json   one record per manufacturer part number
  parts\\index.json                        generated search index (do not edit)
  datasheets\\<file>.pdf                    PDFs, not in git; datasheets\\index.json (in git) keeps sha256, url, pages
  datasheets\\_text\\<sha16>.txt            page text cache (pdftotext -layout, pages split by form feed; not in git)
  market\\<supplier>_<sku>.json            price and stock snapshots with the fetch date (not in git; changes daily)

Commands:
  find <text> [--category c]           search the index (mpn, mfr, supplier sku, description, category)
  new --mpn M --mfr F --category c/f [--lcsc C123] [--package P] [--description D]   offline skeleton
  new --lcsc C123 [--category c/f]     online: mpn, mfr, package, description, supplier params and datasheet url from LCSC
  fetch <mpn> [--url U | --file PDF]   download (or register a local) datasheet: sha256, datasheets\\index.json, link
  text <mpn> [--pages 3-5] [--grep RE] [--mode layout|raw|table]   page text for the extractor; --grep lists
                                       matching pages; raw keeps a table row on one line (quote the row label with it)
  locate <mpn>                         pages that hold each section (abs max, recommended, pins, package, layout ...)
  market <mpn>                         refresh LCSC price and stock into market\\ (RQ-04: check at BOM time)
  get <mpn> [--section S]              print a record or one section (market snapshot shown with its date)
  check [<mpn> ...] [--strict]         schema, taxonomy, units, every quote found on its cited page, abs max vs recommended
  index                                rebuild parts\\index.json
  status                               counts by category and review status
Facts are written by the extractor (an AI agent or a person) from the page text; this script never invents a value.
Every fact cites {page, quote}: the quote must appear on that page of that PDF (in any text mode), which check
verifies. For a table value quote the row with its label (raw mode), so the value is tied to the right row.
When the PDF text layer lacks the value (glyphs without text), the extractor reads the page image and sets
"visual": true; check then lists the fact for a person to confirm instead of matching the quote.
Supplier parameters (supplier_params) are for search only and never a source (rule RQ-01).
A key may carry a condition tag after '@' (rds_on@vgs_4v5) when the datasheet gives the same quantity under
several conditions; units and required-fact checks use the part before '@'.
min / typ / max are stored as the datasheet columns print them; all-negative values (P-channel) are ordered by magnitude.
Python standard library only; text extraction calls pdftotext (poppler, shipped with Git for Windows).
Exit 0 = PASS, 1 = FAIL / not found.
"""
import argparse, datetime, glob, hashlib, json, os, re, shutil, subprocess, sys, unicodedata, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCHEMA = "part/1"
REVIEW = ("draft", "extracted", "checked", "verified")   # verified = a person checked pins, abs max, package
NUM_FIELDS = ("min", "typ", "max", "value")
UA = {"User-Agent": "Mozilla/5.0 (parts.py)"}
LCSC_API = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={}"
LOCATE = {
    "abs_max": r"absolute\s+maximum",
    "recommended": r"recommended\s+operating",
    "electrical": r"electrical\s+characteristics|specifications",
    "thermal": r"thermal\s+(information|resistance|characteristics)",
    "pins": r"pin\s+(configuration|description|functions|assignment)|pinout",
    "package": r"package\s+(outline|dimensions|information)|mechanical\s+data|dimensions",
    "land_pattern": r"land\s+pattern|recommended\s+(pad|footprint|land|solder)|footprint",
    "application": r"typical\s+application|application\s+information|design\s+procedure",
    "layout": r"layout\s+(guidelines|example|recommendations)|pcb\s+layout",
    "ordering": r"ordering\s+information|part\s+number(ing)?\s+(system|code)|marking",
    "handling": r"reflow|soldering\s+profile|moisture\s+sensitivity|storage",
}


def lib_root():
    return os.environ.get("EDA_GLOBAL", os.path.join(ROOT, "library"))


def p(*a):
    return os.path.join(lib_root(), *a)


def today():
    return datetime.date.today().isoformat()


def load_json(path, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def slug(s):
    return re.sub(r"[^A-Za-z0-9.+_-]", "_", s.strip()).strip("_") or "_"


def taxonomy():
    return load_json(p("parts", "taxonomy.json"))


def family_of(tax, cat):
    parts = cat.split("/")
    if len(parts) != 2:
        return None
    return tax["categories"].get(parts[0], {}).get(parts[1])


def manufacturers():
    return (load_json(p("parts", "manufacturers.json")) or {"manufacturers": {}})["manufacturers"]


def canon_mfr(name):
    """(canonical name, file slug) for a manufacturer name or alias; unknown names keep their own spelling."""
    n = name.strip().lower()
    for canon, d in manufacturers().items():
        if n == canon.lower() or n in (x.lower() for x in d.get("aliases", [])):
            return canon, d["slug"]
    return name.strip(), slug(name).lower()


def record_path(rec):
    return p("parts", *rec["category"].split("/"), f"{slug(rec['mpn'])}__{canon_mfr(rec['mfr'])[1]}.json")


def all_records():
    out = []
    for f in sorted(glob.glob(p("parts", "*", "*", "*.json"))):
        out.append((f, load_json(f)))
    return out


def find_record(key):
    """By MPN (case-insensitive), supplier sku, or file name."""
    k = key.lower()
    hits = []
    for f, r in all_records():
        skus = [s.get("sku", "").lower() for s in r.get("suppliers", [])]
        if r.get("mpn", "").lower() == k or k in skus or os.path.basename(f).lower().startswith(slug(key).lower() + "__"):
            hits.append((f, r))
    return hits


def one(key):
    hits = find_record(key)
    if len(hits) != 1:
        print(f"FAIL {'no part' if not hits else 'several parts'} for '{key}'"
              + ("" if not hits else ": " + ", ".join(os.path.basename(f) for f, _ in hits)))
        return None, None
    return hits[0]


# ---------------- datasheets and page text ----------------
def ds_index():
    return load_json(p("datasheets", "index.json"), {"schema": 1, "datasheets": {}})


def pdftotext_exe():
    exe = shutil.which("pdftotext")
    if exe:
        return exe
    for c in (r"C:\Program Files\Git\mingw64\bin\pdftotext.exe", r"C:\Program Files (x86)\Git\mingw64\bin\pdftotext.exe"):
        if os.path.isfile(c):
            return c
    return None


# Symbol-font characters that PDFs put in the private use area (U+F0xx = Symbol code xx) -> real characters
SYMBOL_PUA = {0xF0B1: "±", 0xF0B0: "°", 0xF057: "Ω", 0xF06D: "μ", 0xF0A3: "≤", 0xF0B3: "≥",
              0xF0D7: "×", 0xF02D: "-", 0xF0BB: "≈", 0xF0B9: "≠", 0xF044: "Δ", 0xF071: "θ",
              0xF074: "τ", 0xF0A5: "∞", 0xF0D6: "√", 0xF0BE: "-", 0xF020: " "}
MODES = ("layout", "raw", "table")   # pdftotext modes; raw keeps a table row on one line, layout keeps columns


def pages_of(sha, mode="layout"):
    """Page texts of a datasheet in one pdftotext mode (list, page 1 = index 0), cached. None if no PDF or no tool."""
    cache = p("datasheets", "_text", f"{sha[:16]}.{mode}.txt")
    if not os.path.isfile(cache):
        entry = ds_index()["datasheets"].get(sha)
        pdf = p("datasheets", entry["file"]) if entry else None
        exe = pdftotext_exe()
        if not pdf or not os.path.isfile(pdf) or not exe:
            return None
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        r = subprocess.run([exe, f"-{mode}", "-enc", "UTF-8", pdf, cache], capture_output=True)
        if r.returncode != 0 or not os.path.isfile(cache):
            return None
    with open(cache, encoding="utf-8", errors="replace") as f:
        text = f.read().translate(SYMBOL_PUA)
    pages = text.split("")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def page_variants(sha):
    """[(mode, pages)] for every mode that produced text; all modes have the same page count."""
    out = [(m, pages_of(sha, m)) for m in MODES]
    return [(m, pg) for m, pg in out if pg is not None]


def norm(s):
    """Normalize for quote matching: unicode compatibility form, one minus sign, no whitespace, lower case."""
    s = unicodedata.normalize("NFKC", s)
    for a, b in (("\u2212", "-"), ("\u2013", "-"), ("\u2014", "-"), ("\u00b5", "\u03bc"), ("\u2126", "\u03a9")):
        s = s.replace(a, b)
    s = "".join(c for c in s if c.isspace() or unicodedata.category(c)[0] != "C")   # control, format and unmapped private-use glyphs carry no meaning for matching
    return re.sub(r"\s+", "", s).lower()


def quote_on_page(quote, page_text):
    return bool(quote.strip()) and norm(quote) in norm(page_text)


def add_datasheet(pdf_path, url="", source="manual", mfr="", covers=(), title="", revision=""):
    """Copy a PDF into library\\datasheets (once) and record it in datasheets\\index.json. Returns its sha256."""
    sha = sha256(pdf_path)
    idx = ds_index()
    entry = idx["datasheets"].get(sha)
    if not entry:
        name = os.path.basename(pdf_path)
        dest = p("datasheets", name)
        if os.path.isfile(dest) and sha256(dest) != sha:
            name = f"{os.path.splitext(name)[0]}_{sha[:8]}.pdf"
            dest = p("datasheets", name)
        if os.path.abspath(pdf_path) != os.path.abspath(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(pdf_path, dest)
        entry = {"file": name, "url": url, "source": source, "mfr": mfr, "title": title, "revision": revision,
                 "added": today(), "pages": None, "covers": []}
        idx["datasheets"][sha] = entry
    for m in covers:
        if m not in entry["covers"]:
            entry["covers"].append(m)
    if url and not entry.get("url"):
        entry["url"] = url
    save_json(p("datasheets", "index.json"), idx)
    pages = pages_of(sha)
    if pages is not None and entry.get("pages") != len(pages):
        entry["pages"] = len(pages)
        save_json(p("datasheets", "index.json"), idx)
    return sha


def http_get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def lcsc_detail(sku):
    data = json.loads(http_get(LCSC_API.format(sku)).decode("utf-8"))
    r = data.get("result")
    if not r or r.get("productCode", "").upper() != sku.upper():
        raise ValueError(f"LCSC has no product {sku}")
    return r


# ---------------- checks ----------------
def check_record(f, r, tax, strict=False):
    """Returns (problems, notes). Problems fail the check."""
    bad, notes = [], []
    for k in ("schema", "mpn", "mfr", "category", "description", "datasheets", "suppliers", "facts", "pins", "notes", "review"):
        if k not in r:
            bad.append(f"missing field {k}")
    if bad:
        return bad, notes
    if r["schema"] != SCHEMA:
        bad.append(f"schema {r['schema']} != {SCHEMA}")
    if canon_mfr(r["mfr"])[0] != r["mfr"]:
        bad.append(f"mfr {r['mfr']!r} should be the canonical name {canon_mfr(r['mfr'])[0]!r}")
    elif r["mfr"] not in manufacturers():
        notes.append(f"mfr {r['mfr']!r} not in manufacturers.json (add it with a slug)")
    fam = family_of(tax, r["category"])
    if fam is None:
        bad.append(f"category {r['category']} not in taxonomy.json")
    if os.path.abspath(f) != os.path.abspath(record_path(r)):
        bad.append(f"file should be {os.path.relpath(record_path(r), lib_root())}")
    status = r["review"].get("status")
    if status not in REVIEW:
        bad.append(f"review.status {status} not in {REVIEW}")
    known = ds_index()["datasheets"]
    shas = [d.get("sha256", "") for d in r["datasheets"]]
    for s in shas:
        if s not in known:
            bad.append(f"datasheet {s[:12]} not in datasheets/index.json")
    page_cache = {s: page_variants(s) for s in shas if s in known}

    def check_ref(where, ref):
        if not isinstance(ref, dict) or not isinstance(ref.get("page"), int) or not ref.get("quote"):
            bad.append(f"{where}: ref needs page (int) and quote")
            return
        s = ref.get("ds") or (shas[0] if shas else "")
        s = next((x for x in shas if x.startswith(s)), None) if s else None
        if not s:
            bad.append(f"{where}: ref.ds does not match a datasheet of this part")
            return
        variants = page_cache.get(s)
        if not variants:
            notes.append(f"{where}: quote not checked (PDF or pdftotext missing)")
            return
        n = len(variants[0][1])
        if not 1 <= ref["page"] <= n:
            bad.append(f"{where}: page {ref['page']} outside 1..{n}")
        elif ref.get("visual"):
            notes.append(f"{where}: visual reference (read from the page image; the text layer lacks it) - confirm on p{ref['page']}")
        else:
            mode = ref.get("mode")
            if mode and mode not in MODES:
                bad.append(f"{where}: ref.mode {mode!r} not in {MODES}")
                return
            use = [pg for m, pg in variants if not mode or m == mode]
            if not any(ref["page"] <= len(pg) and quote_on_page(ref["quote"], pg[ref["page"] - 1]) for pg in use):
                bad.append(f"{where}: quote {ref['quote']!r} not found on page {ref['page']}"
                           + (f" ({mode} text)" if mode else ""))

    for sec, facts in r["facts"].items():
        if sec not in tax["sections"]:
            bad.append(f"facts section {sec} unknown (taxonomy sections)")
            continue
        for key, fact in facts.items():
            where = f"{sec}.{key}"
            unit = tax["keys"].get(key.split("@")[0])     # key@tag = same quantity under another condition
            if unit is None:
                bad.append(f"{where}: key not in taxonomy keys")
            elif fact.get("unit") != unit:
                bad.append(f"{where}: unit {fact.get('unit')!r}, taxonomy says {unit!r}")
            vals = [fact[k] for k in NUM_FIELDS if k in fact]
            if not vals:
                bad.append(f"{where}: needs one of {NUM_FIELDS}")
            if unit not in ("-",) and any(not isinstance(v, (int, float)) for v in vals):
                bad.append(f"{where}: numeric unit {unit} needs numbers")
            nums = [fact[k] for k in ("min", "typ", "max") if isinstance(fact.get(k), (int, float))]
            if all(v <= 0 for v in nums):   # datasheets print negative quantities ordered by magnitude (P-channel)
                nums = [abs(v) for v in nums]
            if nums != sorted(nums):
                bad.append(f"{where}: min <= typ <= max violated")
            check_ref(where, fact.get("ref"))
    am, rc = r["facts"].get("abs_max", {}), r["facts"].get("recommended", {})
    for key in set(am) & set(rc):         # same key and tag in both sections
        a, b = am[key].get("max"), rc[key].get("max")
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(b) > abs(a):
            bad.append(f"recommended.{key} max {b} exceeds abs_max {a}")
    seen = set()
    for i, pin in enumerate(r["pins"]):
        n = str(pin.get("number", ""))
        if not n or not pin.get("name"):
            bad.append(f"pins[{i}]: needs number and name")
        if n in seen:
            bad.append(f"pins: number {n} twice")
        seen.add(n)
        check_ref(f"pins[{n}]", pin.get("ref"))
    for sec, items in r["notes"].items():
        if sec not in tax["note_sections"]:
            bad.append(f"notes section {sec} unknown")
            continue
        for i, it in enumerate(items):
            if not it.get("text"):
                bad.append(f"notes.{sec}[{i}]: empty text")
            check_ref(f"notes.{sec}[{i}]", it.get("ref"))
    for s in r["suppliers"]:
        if s.get("name") == "LCSC" and not re.fullmatch(r"C\d+", s.get("sku", "")):
            bad.append(f"LCSC sku {s.get('sku')!r} is not C<digits>")
    if fam and status in ("extracted", "checked", "verified"):
        have = {f"{sec}.{k.split('@')[0]}" for sec, fs in r["facts"].items() for k in fs}
        miss = [q for q in fam["required"] if q not in have and q not in r["review"].get("not_in_datasheet", [])]
        if miss:
            (bad if strict or status != "extracted" else notes).append("required facts missing: " + ", ".join(miss))
    return bad, notes


# ---------------- commands ----------------
def cmd_new(a):
    tax = taxonomy()
    params, ds_url, sup = {}, "", []
    mpn, mfr, package, desc = a.mpn, a.mfr, a.package or "", a.description or ""
    if a.lcsc and not a.offline:
        r = lcsc_detail(a.lcsc)
        mpn = mpn or r.get("productModel", "")
        mfr = mfr or r.get("brandNameEn", "")
        package = package or r.get("encapStandard", "")
        desc = desc or r.get("productIntroEn") or r.get("productNameEn", "")
        params = {x.get("paramNameEn"): x.get("paramValueEn") for x in r.get("paramVOList") or [] if x.get("paramNameEn")}
        ds_url = r.get("pdfUrl", "")
        if not a.category:
            cat = r.get("catalogName", "")
            hits = [f"{c}/{f}" for c, fams in tax["categories"].items() for f, d in fams.items() if cat in d.get("lcsc", [])]
            if len(hits) != 1:
                print(f"FAIL LCSC category '{cat}' maps to {hits or 'no family'}: give --category <category>/<family>")
                return 1
            a.category = hits[0]
    if a.lcsc:
        sup.append({"name": "LCSC", "sku": a.lcsc, "url": f"https://www.lcsc.com/product-detail/{a.lcsc}.html",
                    "verified": today() if params else None})
    mfr = canon_mfr(mfr)[0] if mfr else mfr
    if not (mpn and mfr and a.category):
        print("FAIL need --mpn, --mfr and --category (or --lcsc online)")
        return 1
    if family_of(tax, a.category) is None:
        print(f"FAIL category {a.category} not in taxonomy.json (category/family)")
        return 1
    rec = {"schema": SCHEMA, "mpn": mpn, "mfr": mfr, "category": a.category, "description": desc, "package": package,
           "lifecycle": {"status": "unknown"}, "datasheets": [], "datasheet_url": ds_url, "suppliers": sup,
           "supplier_params": params, "facts": {}, "pins": [], "notes": {}, "catalog_ids": [],
           "review": {"status": "draft", "created": today(), "open": []}}
    path = record_path(rec)
    if os.path.isfile(path):
        print(f"FAIL exists: {os.path.relpath(path, lib_root())}")
        return 1
    save_json(path, rec)
    print(f"created {os.path.relpath(path, lib_root())}" + (f"; datasheet url from LCSC: {ds_url}" if ds_url else ""))
    return 0


def cmd_fetch(a):
    f, r = one(a.key)
    if not r:
        return 1
    src = a.file
    url = a.url or r.get("datasheet_url", "")
    if not src:
        if not url:
            print("FAIL no --url, --file or datasheet_url in the record")
            return 1
        data = http_get(url)
        if not data.startswith(b"%PDF"):
            print(f"FAIL {url} did not return a PDF")
            return 1
        sku = next((s["sku"] for s in r["suppliers"] if s.get("name") == "LCSC"), "")
        src = p("datasheets", f"{slug(r['mpn'])}{'_' + sku if sku else ''}.pdf")
        if os.path.isfile(src):
            src = src[:-4] + f"_{hashlib.sha256(data).hexdigest()[:8]}.pdf"
        os.makedirs(os.path.dirname(src), exist_ok=True)
        with open(src, "wb") as out:
            out.write(data)
    sha = add_datasheet(src, url=url, source=a.source or ("lcsc" if "lcsc.com" in url else "manual" if not url else "web"),
                        mfr=r["mfr"], covers=[r["mpn"]], title=a.title or "", revision=a.revision or "")
    if not any(d.get("sha256") == sha for d in r["datasheets"]):
        e = ds_index()["datasheets"][sha]
        r["datasheets"].append({"sha256": sha, "file": e["file"], "url": e.get("url", ""), "title": e.get("title", ""),
                                "revision": e.get("revision", "")})
        save_json(f, r)
    pages = pages_of(sha)
    print(f"datasheet {sha[:12]} {ds_index()['datasheets'][sha]['file']}: "
          + (f"{len(pages)} pages of text" if pages is not None else "no text (pdftotext missing?)"))
    return 0


def parse_pages(spec, n):
    out = set()
    for part in (spec or f"1-{n}").split(","):
        lo, _, hi = part.partition("-")
        out.update(range(int(lo), int(hi or lo) + 1))
    return [x for x in sorted(out) if 1 <= x <= n]


def part_pages(r, ds, mode="layout"):
    shas = [d["sha256"] for d in r["datasheets"]]
    sha = next((s for s in shas if s.startswith(ds or "")), None)
    if not sha:
        print("FAIL part has no datasheet (run fetch)")
        return None, None
    pages = pages_of(sha, mode)
    if pages is None:
        print("FAIL no page text: PDF missing or pdftotext not found")
    return sha, pages


def cmd_text(a):
    f, r = one(a.key)
    if not r:
        return 1
    sha, pages = part_pages(r, a.ds, a.mode)
    if pages is None:
        return 1
    if a.grep:
        rx = re.compile(a.grep, re.I)
        for i, t in enumerate(pages, 1):
            lines = [ln.strip() for ln in t.splitlines() if rx.search(ln)]
            if lines:
                print(f"--- page {i}: " + " | ".join(lines[:6])[:400])
        return 0
    for i in parse_pages(a.pages, len(pages)):
        print(f"===== {r['mpn']} datasheet {sha[:12]} page {i}/{len(pages)} ({a.mode}) =====")
        print(pages[i - 1].rstrip())
    return 0


def cmd_locate(a):
    f, r = one(a.key)
    if not r:
        return 1
    sha, pages = part_pages(r, a.ds)
    if pages is None:
        return 1
    print(f"{r['mpn']}: {len(pages)} pages, datasheet {sha[:12]}")
    for name, rx in LOCATE.items():
        hits = [i for i, t in enumerate(pages, 1) if re.search(rx, t, re.I)]
        print(f"  {name:12s} {', '.join(map(str, hits[:15])) or '-'}")
    return 0


def cmd_market(a):
    f, r = one(a.key)
    if not r:
        return 1
    sku = next((s["sku"] for s in r["suppliers"] if s.get("name") == "LCSC"), None)
    if not sku:
        print("FAIL no LCSC sku in suppliers")
        return 1
    d = lcsc_detail(sku)
    snap = {"supplier": "LCSC", "sku": sku, "fetched": datetime.datetime.now().isoformat(timespec="seconds"),
            "stock": d.get("stockNumber"), "currency": d.get("currencyType") or "USD",
            "price_breaks": [[x.get("ladder"), float(x.get("productPrice"))] for x in d.get("productPriceList") or []],
            "min_order": d.get("minBuyNumber"), "reel": d.get("minPacketNumber"), "packaging": d.get("productArrange"),
            "jlc_part_class": None}
    save_json(p("market", f"LCSC_{sku}.json"), snap)
    print(json.dumps(snap, indent=1))
    return 0


def cmd_get(a):
    f, r = one(a.key)
    if not r:
        return 1
    if a.section:
        sec = r["facts"].get(a.section) if a.section in r["facts"] else r.get(a.section, r["notes"].get(a.section))
        print(json.dumps(sec, indent=1, ensure_ascii=False))
        return 0 if sec is not None else 1
    out = dict(r)
    snaps = [load_json(p("market", f"{s.get('name')}_{s.get('sku')}.json")) for s in r["suppliers"]]
    out["market"] = [s for s in snaps if s] or "no snapshot (run: parts.py market <mpn>)"
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


def cmd_check(a):
    tax = taxonomy()
    recs = all_records() if not a.keys else [x for k in a.keys for x in find_record(k)]
    if a.keys and not recs:
        print("FAIL no matching parts")
        return 1
    fails = total_unchecked = 0
    for f, r in recs:
        bad, notes = check_record(f, r, tax, a.strict)
        unchecked = sum("quote not checked" in n for n in notes)
        if unchecked and a.strict:
            bad.append(f"{unchecked} quotes cannot be checked: PDF and page text missing (--strict)")
        total_unchecked += unchecked
        name = f"{r.get('mpn')} ({r.get('review', {}).get('status')})"
        print(f"{'FAIL' if bad else 'PASS'}  {name}" + (f": {len(bad)} problems" if bad else ""))
        for b in bad:
            print(f"      - {b}")
        for n in notes[:3] if not a.verbose else notes:
            print(f"      note: {n}")
        fails += bool(bad)
    print(f"\nparts check: {len(recs)} parts, {fails} FAIL"
          + (f", {total_unchecked} quotes NOT CHECKED (PDF and page text missing)" if total_unchecked else ""))
    return 1 if fails else 0


def build_index():
    rows = []
    for f, r in all_records():
        summ = {k: {x: v[x] for x in NUM_FIELDS + ("unit",) if x in v} for k, v in r.get("facts", {}).get("summary", {}).items()}
        rows.append({"mpn": r.get("mpn"), "mfr": r.get("mfr"), "category": r.get("category"), "package": r.get("package", ""),
                     "description": r.get("description", ""), "skus": [f"{s.get('name')}:{s.get('sku')}" for s in r.get("suppliers", [])],
                     "status": r.get("review", {}).get("status"), "catalog_ids": r.get("catalog_ids", []),
                     "file": os.path.relpath(f, p("parts")).replace("\\", "/"), "summary": summ})
    return {"schema": 1, "generated_by": "parts.py index", "count": len(rows), "parts": rows}


def cmd_index(a):
    idx = build_index()
    save_json(p("parts", "index.json"), idx)
    print(f"index: {idx['count']} parts")
    return 0


def cmd_find(a):
    idx = load_json(p("parts", "index.json")) or build_index()
    q = a.text.lower()
    hits = [x for x in idx["parts"] if (not a.category or x["category"].startswith(a.category)) and
            any(q in str(v).lower() for v in (x["mpn"], x["mfr"], x["description"], x["category"], " ".join(x["skus"]), x["package"]))]
    for x in hits:
        print(f"{x['mpn']:28s} {x['mfr'][:20]:20s} {x['category']:28s} {x['status']:9s} {' '.join(x['skus'])}  {x['description'][:60]}")
    print(f"{len(hits)} found")
    return 0 if hits else 1


def cmd_status(a):
    from collections import Counter
    c = Counter((r.get("category"), r.get("review", {}).get("status")) for _, r in all_records())
    for (cat, st), n in sorted(c.items()):
        print(f"{cat:30s} {st:10s} {n}")
    print(f"total {sum(c.values())}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("new"); s.add_argument("--mpn", default=""); s.add_argument("--mfr", default="")
    s.add_argument("--category", default=""); s.add_argument("--lcsc", default=""); s.add_argument("--package")
    s.add_argument("--description"); s.add_argument("--offline", action="store_true"); s.set_defaults(fn=cmd_new)
    s = sp.add_parser("fetch"); s.add_argument("key"); s.add_argument("--url"); s.add_argument("--file")
    s.add_argument("--source"); s.add_argument("--title"); s.add_argument("--revision"); s.set_defaults(fn=cmd_fetch)
    s = sp.add_parser("text"); s.add_argument("key"); s.add_argument("--pages"); s.add_argument("--grep")
    s.add_argument("--mode", choices=MODES, default="layout")
    s.add_argument("--ds", default=""); s.set_defaults(fn=cmd_text)
    s = sp.add_parser("locate"); s.add_argument("key"); s.add_argument("--ds", default=""); s.set_defaults(fn=cmd_locate)
    s = sp.add_parser("market"); s.add_argument("key"); s.set_defaults(fn=cmd_market)
    s = sp.add_parser("get"); s.add_argument("key"); s.add_argument("--section"); s.set_defaults(fn=cmd_get)
    s = sp.add_parser("check"); s.add_argument("keys", nargs="*"); s.add_argument("--strict", action="store_true")
    s.add_argument("--verbose", action="store_true"); s.set_defaults(fn=cmd_check)
    s = sp.add_parser("index"); s.set_defaults(fn=cmd_index)
    s = sp.add_parser("find"); s.add_argument("text"); s.add_argument("--category", default=""); s.set_defaults(fn=cmd_find)
    s = sp.add_parser("status"); s.set_defaults(fn=cmd_status)
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except (OSError, ValueError) as e:
        print(f"FAIL {e}")
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
