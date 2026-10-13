"""datasheets_fetch.py - download the catalog's datasheet PDFs into _global\\datasheets and check their sha256 (rule RQ-01).

Usage:
  python datasheets_fetch.py [--global-root DIR] [--only ID ...] [--dry-run]
Vendor PDFs are not stored in git. The catalog (_global\\catalog\\components.json) keeps, per component,
datasheet.path (file name), datasheet.sha256 and datasheet.url (where it came from). For every component:
  - file present, sha256 equal   -> OK, never downloaded again, never overwritten
  - file present, sha256 differs -> FAIL, the file is left as it is (move it away yourself, then re-run)
  - file missing                 -> download from datasheet.url, keep it only if the sha256 matches
A url of the form https://jlcpcb.com/partdetail/<C-number> is a part page: its datasheet link is signed and
expires after about 30 minutes, so the script reads the page and follows the current link.
If a download fails or the hash differs (the vendor changed the PDF), nothing is written; save the right PDF
by hand under the catalog file name and run catalog_check.py. Python standard library only.
Exit 0 when every datasheet is present and correct, 1 otherwise.
"""
import argparse, hashlib, html, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libcat as lc

UA = {"User-Agent": "Mozilla/5.0 (datasheets_fetch.py)"}
JLC_PAGE = re.compile(r"^https://jlcpcb\.com/partdetail/")
JLC_FILE = re.compile(r"(https://jlc-prod-smt\.oss-[a-z0-9-]+\.aliyuncs\.com/smtDataManualFile/[^\"'<> ]+?"
                      r"x-oss-signature=[0-9a-f]{64})")


def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def candidates(url):
    """Direct PDF urls for a catalog url. A JLCPCB part page repeats its signed link in several encodings,
    some cut inside the page's script chunks, so every distinct copy is returned (longest first)."""
    if not JLC_PAGE.match(url):
        return [url]
    page = get(url).decode("utf-8", "ignore")
    found = {html.unescape(m.group(1)).replace("\\u0026", "&") for m in JLC_FILE.finditer(page)}
    if not found:
        raise ValueError("no datasheet link found on the JLCPCB part page")
    return sorted(found, key=len, reverse=True)


def download(url):
    last = None
    for u in candidates(url):
        try:
            return get(u)
        except Exception as e:
            last = e
    raise last


def fetch(root=None, only=None, dry=False):
    cat = lc.load_catalog(root)
    rows, bad = [], 0
    for c in cat["components"]:
        ds = c.get("datasheet")
        if not ds or (only and c["id"] not in only):
            continue
        dst = lc.gpath(ds["path"], root=root)
        if os.path.isfile(dst):
            if lc.sha256(dst) == ds["sha256"]:
                rows.append(("OK", c["id"], "present, sha256 matches"))
            else:
                bad += 1
                rows.append(("FAIL", c["id"], f"{ds['path']} is present but its sha256 differs; left untouched"))
            continue
        url = ds.get("url", "")
        if not url:
            bad += 1
            rows.append(("FAIL", c["id"], "no datasheet.url in the catalog: save the PDF by hand"))
            continue
        if dry:
            rows.append(("PLAN", c["id"], f"download {url}"))
            continue
        try:
            data = download(url)
        except Exception as e:
            bad += 1
            rows.append(("FAIL", c["id"], f"download failed ({type(e).__name__}: {e}); save the PDF by hand from {url}"))
            continue
        got = hashlib.sha256(data).hexdigest()
        if not data.startswith(b"%PDF"):
            bad += 1
            rows.append(("FAIL", c["id"], f"{url} did not return a PDF; save it by hand"))
        elif got != ds["sha256"]:
            bad += 1
            rows.append(("FAIL", c["id"], f"downloaded file sha256 {got[:12]}... differs from the catalog "
                                          f"{ds['sha256'][:12]}... (vendor changed the PDF?); nothing written"))
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            tmp = dst + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dst)
            rows.append(("FETCHED", c["id"], f"{ds['path']} ({len(data)} bytes, sha256 matches)"))
    return rows, bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--global-root")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    rows, bad = fetch(a.global_root, a.only, a.dry_run)
    for st, i, msg in rows:
        print(f"{st:8} {i}: {msg}")
    print(f"{len(rows)} datasheets, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
