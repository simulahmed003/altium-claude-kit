"""distributor_lookup.py - find distributor part numbers for a list of (Manufacturer, MPN) pairs.

Usage (cmd.exe):
    python distributor_lookup.py parts.csv out.csv [--digikey] [--mouser] [--nexar]

parts.csv columns: Component, Manufacturer, MPN   (one row per library component)
out.csv: one row per purchasing listing found, with exact-MPN and manufacturer match flags.
Every packaging variation is listed; nothing is picked automatically.

Credentials are read from environment variables (never put them in this file or in the library):
    DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET      DigiKey Product Information V4 (OAuth2 client credentials)
    MOUSER_API_KEY                                Mouser Search API key
    NEXAR_CLIENT_ID, NEXAR_CLIENT_SECRET          Nexar application (scope supply.domain)
Set them for one cmd session with:  set DIGIKEY_CLIENT_ID=...   (or permanently with setx).
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request

# Credentials may also come from %USERPROFILE%\.distributor_keys.json, e.g.
#   {"DIGIKEY_CLIENT_ID": "...", "DIGIKEY_CLIENT_SECRET": "...", "MOUSER_API_KEY": "..."}
# Environment variables win over the file.
_KEYS = os.path.join(os.path.expanduser('~'), '.distributor_keys.json')
if os.path.exists(_KEYS):
    for _k, _v in json.load(open(_KEYS, encoding='utf-8-sig')).items():
        os.environ.setdefault(_k, _v)

def norm(s):
    return re.sub(r'[^A-Z0-9]', '', (s or '').upper())

def http(url, data=None, headers=None, form=False):
    body = None
    h = dict(headers or {})
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode(); h['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            body = json.dumps(data).encode(); h['Content-Type'] = 'application/json'
    h.setdefault('Accept', 'application/json')
    req = urllib.request.Request(url, data=body, headers=h)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:          # rate limited: back off and retry
                time.sleep(2 ** (attempt + 1)); continue
            raise RuntimeError(f'{url} -> HTTP {e.code}: {e.read()[:300]!r}')

def mfr_match(want, got):
    """Loose manufacturer check: first significant word of the library name inside the distributor's name."""
    w = [t for t in re.findall(r'[A-Za-z]+', want or '') if t.lower() not in ('the', 'inc', 'corp', 'group', 'llc')]
    return bool(w) and w[0].lower() in (got or '').lower()

# ---------------------------------------------------------------- DigiKey V4
class DigiKey:
    TOKEN = 'https://api.digikey.com/v1/oauth2/token'
    SEARCH = 'https://api.digikey.com/products/v4/search/keyword'

    def __init__(self):
        self.cid, self.secret = os.environ['DIGIKEY_CLIENT_ID'], os.environ['DIGIKEY_CLIENT_SECRET']
        self.token, self.expires = None, 0

    def auth(self):
        if time.time() < self.expires - 30:                 # reuse the token until shortly before expiry
            return self.token
        r = http(self.TOKEN, {'client_id': self.cid, 'client_secret': self.secret, 'grant_type': 'client_credentials'}, form=True)
        self.token, self.expires = r['access_token'], time.time() + int(r.get('expires_in', 600))
        return self.token

    def lookup(self, mfr, mpn):
        h = {'Authorization': 'Bearer ' + self.auth(), 'X-DIGIKEY-Client-Id': self.cid,
             'X-DIGIKEY-Locale-Site': 'US', 'X-DIGIKEY-Locale-Language': 'en', 'X-DIGIKEY-Locale-Currency': 'USD'}
        r = http(self.SEARCH, {'Keywords': mpn, 'Limit': 20, 'Offset': 0}, h)
        prods = (r.get('ExactMatches') or []) + (r.get('Products') or [])
        seen, out = set(), []
        for p in prods:
            pmpn = p.get('ManufacturerProductNumber', '')
            pm = (p.get('Manufacturer') or {}).get('Name', '')
            for v in p.get('ProductVariations') or []:
                sku = v.get('DigiKeyProductNumber')
                if not sku or sku in seen: continue
                seen.add(sku)
                out.append(dict(Distributor='DigiKey', SKU=sku, DistMPN=pmpn, DistManufacturer=pm,
                                Packaging=(v.get('PackageType') or {}).get('Name', ''),
                                Stock=v.get('QuantityAvailableforPackageType', ''), MOQ=v.get('MinimumOrderQuantity', ''),
                                URL=p.get('ProductUrl', ''), Datasheet=p.get('DatasheetUrl', ''),
                                Status=(p.get('ProductStatus') or {}).get('Status', '')))
        return out

# ---------------------------------------------------------------- Mouser
class Mouser:
    URL = 'https://api.mouser.com/api/v1/search/partnumber?apiKey='

    def __init__(self):
        self.key = os.environ['MOUSER_API_KEY']

    def lookup(self, mfr, mpn):
        r = http(self.URL + urllib.parse.quote(self.key),
                 {'SearchByPartRequest': {'mouserPartNumber': mpn, 'partSearchOptions': 'Exact'}})
        errs = r.get('Errors') or []
        if errs:
            raise RuntimeError('Mouser: ' + '; '.join(e.get('Message', '') for e in errs))
        out = []
        for p in (r.get('SearchResults') or {}).get('Parts') or []:
            out.append(dict(Distributor='Mouser', SKU=p.get('MouserPartNumber', ''), DistMPN=p.get('ManufacturerPartNumber', ''),
                            DistManufacturer=p.get('Manufacturer', ''),
                            Packaging='; '.join(x.get('AttributeValue', '') for x in p.get('ProductAttributes', []) if x.get('AttributeName') == 'Packaging'),
                            Stock=p.get('AvailabilityInStock', '') or p.get('Availability', ''), MOQ=p.get('Min', ''),
                            URL=p.get('ProductDetailUrl', ''), Datasheet=p.get('DataSheetUrl', ''), Status=p.get('LifecycleStatus', '') or ''))
        return out

# ---------------------------------------------------------------- Nexar (Octopart)
class Nexar:
    TOKEN = 'https://identity.nexar.com/connect/token'
    API = 'https://api.nexar.com/graphql'
    Q = '''query($q:String!){ supSearchMpn(q:$q, limit:5){ results{ part{ mpn manufacturer{name}
          sellers(authorizedOnly:true){ company{name} offers{ sku packaging inventoryLevel moq clickUrl } } } } } }'''

    def __init__(self):
        self.cid, self.secret = os.environ['NEXAR_CLIENT_ID'], os.environ['NEXAR_CLIENT_SECRET']
        self.token, self.expires = None, 0

    def auth(self):
        if time.time() < self.expires - 30:
            return self.token
        r = http(self.TOKEN, {'grant_type': 'client_credentials', 'client_id': self.cid, 'client_secret': self.secret, 'scope': 'supply.domain'}, form=True)
        self.token, self.expires = r['access_token'], time.time() + int(r.get('expires_in', 3600))
        return self.token

    def lookup(self, mfr, mpn):
        r = http(self.API, {'query': self.Q, 'variables': {'q': mpn}}, {'Authorization': 'Bearer ' + self.auth()})
        if r.get('errors'):
            raise RuntimeError('Nexar: ' + '; '.join(e.get('message', '') for e in r['errors']))
        out = []
        for res in ((r.get('data') or {}).get('supSearchMpn') or {}).get('results') or []:
            part = res['part']
            for s in part.get('sellers') or []:
                for o in s.get('offers') or []:
                    out.append(dict(Distributor=s['company']['name'], SKU=o.get('sku', ''), DistMPN=part.get('mpn', ''),
                                    DistManufacturer=(part.get('manufacturer') or {}).get('name', ''), Packaging=o.get('packaging') or '',
                                    Stock=o.get('inventoryLevel', ''), MOQ=o.get('moq', ''), URL=o.get('clickUrl', ''), Datasheet='', Status=''))
        return out

# ---------------------------------------------------------------- main
def main():
    import argparse
    ap = argparse.ArgumentParser(description='Distributor part numbers and product links by exact MPN (LIB-32).')
    ap.add_argument('parts_csv'); ap.add_argument('out_csv')
    ap.add_argument('--digikey', action='store_true'); ap.add_argument('--mouser', action='store_true'); ap.add_argument('--nexar', action='store_true')
    a = ap.parse_args()
    if not (a.digikey or a.mouser or a.nexar): a.digikey = a.mouser = True
    src, dst = a.parts_csv, a.out_csv
    sources = []
    if a.digikey: sources.append(DigiKey())
    if a.mouser: sources.append(Mouser())
    if a.nexar: sources.append(Nexar())
    rows = list(csv.DictReader(open(src, encoding='utf-8-sig')))
    cols = ['Component', 'Manufacturer', 'MPN', 'Distributor', 'SKU', 'DistMPN', 'DistManufacturer', 'ExactMPN', 'ManufacturerMatch',
            'Packaging', 'Stock', 'MOQ', 'Status', 'URL', 'Datasheet', 'Error']
    with open(dst, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for row in rows:
            mpn, mfr = row['MPN'].strip(), row.get('Manufacturer', '').strip()
            if not mpn:
                continue
            for s in sources:
                try:
                    hits = s.lookup(mfr, mpn)
                except Exception as e:
                    w.writerow(dict(Component=row['Component'], Manufacturer=mfr, MPN=mpn, Distributor=type(s).__name__, Error=str(e)[:300])); continue
                if not hits:
                    w.writerow(dict(Component=row['Component'], Manufacturer=mfr, MPN=mpn, Distributor=type(s).__name__, Error='no listing'))
                for h in hits:
                    h.update(Component=row['Component'], Manufacturer=mfr, MPN=mpn,
                             ExactMPN='yes' if norm(h['DistMPN']) == norm(mpn) else 'no',
                             ManufacturerMatch='yes' if mfr_match(mfr, h['DistManufacturer']) else 'CHECK')
                    w.writerow(h)
                time.sleep(0.6)   # stay well under the per-minute limits
            print(row['Component'], mpn, 'done', flush=True)

if __name__ == '__main__':
    main()
