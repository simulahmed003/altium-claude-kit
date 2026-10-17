"""altium_io.py - read Altium files without Altium (pure Python, read-only).

Shared by every checker in tools/scripts. Units: mil unless named otherwise.
  CFB(path)                         compound-file (OLE2) reader
  sch_records(path)                 text records of a .SchDoc FileHeader (list of dicts; [0] is the header)
  sheet_model(path)                 parts, pin tips, wires, labels, ports, junctions of a .SchDoc (or .json records)
  schlib_symbols(path)              {name: {pins, params, footprints, records}}
  pcblib_footprints(path)           {name: {pads: [designator], data: bytes}}
  pcbdoc_components(path)           {designator: {x, y, rotation, layer, footprint}}
  prjpcb_documents(path)            [DocumentPath values] from a .PrjPcb
  symbol_hash(sym) / footprint_hash(fp)   normalized content hashes (identity fields dropped)
Run as a script: python altium_io.py <file> prints a short summary.
"""
import hashlib, json, struct, sys

# ---------------------------------------------------------------- compound file


class CFB:
    def __init__(self, path):
        with open(path, "rb") as fh:              # closed at once: Altium must be able to write the file
            self.d = fh.read()
        h = self.d[:512]
        if h[:8] != bytes.fromhex("D0CF11E0A1B11AE1"):
            raise ValueError(f"{path}: not a compound file")
        self.ss = 1 << struct.unpack_from("<H", h, 0x1E)[0]
        self.mss = 1 << struct.unpack_from("<H", h, 0x20)[0]
        nfat, dir1, _, cutoff, mf1, nmf, difat1, ndifat = struct.unpack_from("<IIIIIIII", h, 0x2C)
        self.cutoff = cutoff
        difat = list(struct.unpack_from("<109I", h, 0x4C))
        s = difat1
        for _ in range(ndifat):
            v = struct.unpack_from(f"<{self.ss // 4}I", self._sec(s))
            difat += v[:-1]
            s = v[-1]
        self.fat = []
        for s in difat[:nfat]:
            self.fat += struct.unpack_from(f"<{self.ss // 4}I", self._sec(s))
        dirs = self._chain(dir1)
        self.ents = []
        for i in range(0, len(dirs), 128):
            e = dirs[i:i + 128]
            nl = struct.unpack_from("<H", e, 64)[0]
            left, right, child = struct.unpack_from("<III", e, 68)
            self.ents.append(dict(name=e[:max(nl - 2, 0)].decode("utf-16-le"), type=e[66], left=left, right=right,
                                  child=child, start=struct.unpack_from("<I", e, 116)[0],
                                  size=struct.unpack_from("<Q", e, 120)[0]))
        root = self.ents[0]
        self.mini = self._chain(root["start"])[:root["size"]] if root["start"] < 0xFFFFFFFA else b""
        self.minifat = []
        if nmf:
            mf = self._chain(mf1)
            self.minifat = list(struct.unpack_from(f"<{len(mf) // 4}I", mf))

    def _sec(self, n):
        o = 512 + n * self.ss
        return self.d[o:o + self.ss]

    def _chain(self, s):
        out, seen = [], set()
        while s < 0xFFFFFFFA and s not in seen:
            seen.add(s)
            out.append(self._sec(s))
            s = self.fat[s]
        return b"".join(out)

    def read(self, e):
        if e["size"] < self.cutoff:
            out, s = [], e["start"]
            while s < 0xFFFFFFFA:
                out.append(self.mini[s * self.mss:(s + 1) * self.mss])
                s = self.minifat[s]
            return b"".join(out)[:e["size"]]
        return self._chain(e["start"])[:e["size"]]

    def children(self, idx):
        out, stack = [], [self.ents[idx]["child"]]
        while stack:
            i = stack.pop()
            if i == 0xFFFFFFFF or i >= len(self.ents):
                continue
            out.append(i)
            stack += [self.ents[i]["left"], self.ents[i]["right"]]
        return out

    def stream(self, name):
        e = next((x for x in self.ents if x["name"] == name and x["type"] == 2), None)
        return self.read(e) if e else None

    def storages(self):
        res = {}
        for i in self.children(0):
            e = self.ents[i]
            if e["type"] == 1:
                res[e["name"]] = {self.ents[j]["name"]: self.read(self.ents[j]) for j in self.children(i)
                                  if self.ents[j]["type"] == 2}
        return res


def pascal(b, o):
    n = b[o]
    return b[o + 1:o + 1 + n].decode("latin-1"), o + 1 + n


def text_fields(raw):
    t = raw.rstrip(b"\x00").decode("latin-1", "replace")
    return {kv.split("=", 1)[0].upper(): kv.split("=", 1)[1] for kv in t.split("|") if "=" in kv}


def split_sch_stream(data):
    """Schematic record stream: [len u16][0][type u8][payload]; type 0 text, 1 binary."""
    o, out = 0, []
    while o + 4 <= len(data):
        ln = struct.unpack_from("<H", data, o)[0]
        out.append((data[o + 3], data[o + 4:o + 4 + ln]))
        o += 4 + ln
    return out


# ---------------------------------------------------------------- schematic sheet

def sch_records(path):
    data = CFB(path).stream("FileHeader")
    return [text_fields(p) if k == 0 else {} for k, p in split_sch_stream(data)]


def mil(r, k):
    return int(r.get(f"LOCATION.{k}", 0)) * 10 + int(r.get(f"LOCATION_FRAC.{k}", 0)) // 10000


def _v(r, k):
    return int(r.get(k, 0)) * 10 + int(r.get(k + "_FRAC", 0)) // 10000


DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]


def sheet_model(path):
    """Everything the sheet checkers need, in mil. Accepts a .SchDoc or a .json list of records
    (fixtures: records()[1:] dumped as JSON, see dump_records)."""
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            recs = json.load(fh)
    else:
        recs = sch_records(path)[1:]
    comp_idx = {i for i, r in enumerate(recs) if r.get("RECORD") == "1"}
    des = {}
    for r in recs:
        if r.get("RECORD") == "34" and int(r.get("OWNERINDEX", -1)) in comp_idx:
            des[int(r["OWNERINDEX"])] = r.get("TEXT")
    m = dict(records=recs, comp_idx=comp_idx, des=des, comps={}, pins={}, pin_lines=[], wires=[], labels=[],
             ports=[], junctions=[], designators=[])
    for i in comp_idx:
        r = recs[i]
        m["comps"].setdefault(des.get(i, f"?{i}"), []).append(dict(
            index=i, lib_ref=r.get("LIBREFERENCE"), x=mil(r, "X"), y=mil(r, "Y"),
            o=int(r.get("ORIENTATION", 0)), mirrored=r.get("ISMIRRORED") == "T"))
    m["designators"] = [des[i] for i in sorted(des)]
    for r in recs:
        rec, own = r.get("RECORD"), int(r.get("OWNERINDEX", -1))
        if rec == "2" and own in comp_idx:
            c = int(r.get("PINCONGLOMERATE", 0))
            x, y, ln = mil(r, "X"), mil(r, "Y"), _v(r, "PINLENGTH")
            dx, dy = DIRS[c & 3]
            tip = (x + dx * ln, y + dy * ln)
            who = des.get(own, f"?{own}")
            m["pins"][(who, r.get("DESIGNATOR"))] = tip
            m["pin_lines"].append(dict(who=who, pin=r.get("DESIGNATOR"), body=(x, y), tip=tip, rot=c & 3,
                                       hidden=bool(c & 4), show_number=bool(c & 16)))
        elif rec == "27":
            n = int(r.get("LOCATIONCOUNT", 0))
            m["wires"].append([(_v(r, f"X{k}"), _v(r, f"Y{k}")) for k in range(1, n + 1)])
        elif rec == "25":
            m["labels"].append((r.get("TEXT", ""), (mil(r, "X"), mil(r, "Y"))))
        elif rec == "17":
            m["ports"].append((r.get("TEXT", ""), (mil(r, "X"), mil(r, "Y")), int(r.get("ORIENTATION", 0))))
        elif rec == "29":
            m["junctions"].append((mil(r, "X"), mil(r, "Y")))
    return m


def dump_records(sheet, out):
    """Write the records of a .SchDoc (header dropped) as JSON - fixture format for the sheet checkers."""
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(sch_records(sheet)[1:], fh, indent=0)


# ---------------------------------------------------------------- symbol library

def _binary_pin(rec):
    p = 4 + 1 + 2 + 1 + 4
    _, p = pascal(rec, p)
    p += 2
    flags = rec[p]
    p += 1
    length, x, y = struct.unpack_from("<hhh", rec, p)
    p += 6 + 4
    name, p = pascal(rec, p)
    desig, p = pascal(rec, p)
    return dict(designator=desig, name=name, x=x, y=y, rot=flags & 3, length=length,
                hidden=bool(flags & 0x04), show_name=bool(flags & 0x08), show_number=bool(flags & 0x10))


def pin_tip(p):
    """Connection point (schematic units, 10 mil) - Altium stores the body end."""
    dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][p["rot"]]
    return p["x"] + dx * p["length"], p["y"] + dy * p["length"]


def schlib_symbols(path):
    out = {}
    for st, streams in CFB(path).storages().items():
        data = streams.get("Data")
        if not data:
            continue
        name, pins, params, fps, recs = None, [], [], [], []
        for kind, rec in split_sch_stream(data):
            if kind == 1 and len(rec) > 5 and struct.unpack_from("<i", rec, 0)[0] == 2:
                pins.append(_binary_pin(rec))
            elif kind == 0:
                f = text_fields(rec)
                recs.append(f)
                r = f.get("RECORD")
                if r == "1":
                    name = f.get("LIBREFERENCE", st)
                elif r == "45" and f.get("MODELTYPE", "").upper() == "PCBLIB":
                    fps.append(f.get("MODELNAME"))
                elif r in ("41", "34"):
                    params.append(dict(name=f.get("NAME", "Designator" if r == "34" else ""), text=f.get("TEXT", ""),
                                       hidden=f.get("ISHIDDEN") == "T"))
                elif r == "2":
                    c = int(f.get("PINCONGLOMERATE", 0))
                    pins.append(dict(designator=f.get("DESIGNATOR"), name=f.get("NAME", ""),
                                     x=int(f.get("LOCATION.X", 0)), y=int(f.get("LOCATION.Y", 0)), rot=c & 3,
                                     length=int(f.get("PINLENGTH", 0)), hidden=bool(c & 4),
                                     show_name=bool(c & 8), show_number=bool(c & 16)))
        if name:
            out[name] = dict(pins=pins, params=params, footprints=fps, records=recs)
    return out


_ID_KEYS = {"UNIQUEID", "INDEXINSHEET", "OWNERINDEX", "ALLPINCOUNT", "ISNOTACCESIBLE", "CURRENTPARTID",
            "LIBRARYPATH", "SOURCELIBRARYNAME", "TARGETFILENAME", "SHEETPARTFILENAME", "MODELDATAFILEENTITY0",
            "MODELDATAFILEKIND0", "DATAFILECOUNT", "MODELDATAFILE0"}


def symbol_hash(sym):
    """Content hash: pins + every text record with identity / location-of-source keys dropped, order-free."""
    pins = sorted((p["designator"], p["name"], pin_tip(p), p["rot"], p["length"], p["hidden"]) for p in sym["pins"])
    recs = sorted(json.dumps(sorted((k, v) for k, v in r.items() if k not in _ID_KEYS)) for r in sym["records"])
    return hashlib.sha256(json.dumps([pins, recs]).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- footprint library

_BLOCKS = {2: 6, 5: 2}   # pad: 6 length-prefixed blocks, text: 2, other primitives: 1


def pcblib_footprints(path):
    out = {}
    for st, streams in CFB(path).storages().items():
        data = streams.get("Data")
        if not data:
            continue
        n = struct.unpack_from("<I", data, 0)[0]
        name, _ = pascal(data, 4)
        if "|" in name:
            continue
        o, pads, prims = 4 + n, [], []
        while o < len(data):
            typ = data[o]
            o += 1
            if typ == 0:
                break
            blocks = []
            for b in range(_BLOCKS.get(typ, 1)):
                ln = struct.unpack_from("<I", data, o)[0]
                blk = data[o + 4:o + 4 + ln]
                if typ == 2 and b == 0:
                    pads.append(pascal(blk, 0)[0])
                blocks.append(blk)
                o += 4 + ln
            prims.append((typ, blocks))
        params = text_fields(streams.get("Parameters", b"")[4:]) if streams.get("Parameters") else {}
        out[name] = dict(pads=pads, prims=prims, params=params)
    return out


def footprint_hash(fp):
    """Content hash of the primitive geometry (identity GUIDs live in other streams and are excluded).
    The last 2 bytes of a pad's 6th block are the corner radius % of the newer per-layer pad entry. Altium writes
    the legacy array value (25), altium-lib writes 50; Altium reads the legacy array and rewrites the entry on save
    (LESSONS T29), so they are dropped."""
    h = hashlib.sha256()
    norm = []
    for typ, blocks in fp["prims"]:
        if typ == 2 and len(blocks) == 6 and len(blocks[5]) >= 2:
            blocks = blocks[:5] + [blocks[5][:-2]]
        norm.append((typ, blocks))
    for typ, blocks in sorted(norm, key=lambda t: (t[0], t[1])):
        h.update(bytes([typ]))
        for b in blocks:
            h.update(struct.pack("<I", len(b)) + b)
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- PCB document and project

def pcbdoc_components(path):
    c = CFB(path)
    out = {}
    for i, e in enumerate(c.ents):
        if e["name"] == "Components6":
            for j in c.children(i):
                if c.ents[j]["name"] == "Data":
                    d, o = c.read(c.ents[j]), 0
                    while o + 4 <= len(d):
                        ln = struct.unpack_from("<I", d, o)[0]
                        f = text_fields(d[o + 4:o + 4 + ln])
                        o += 4 + ln
                        num = lambda v: float(str(v).replace("mil", "").strip() or 0)
                        out[f.get("SOURCEDESIGNATOR")] = dict(x=num(f.get("X", 0)), y=num(f.get("Y", 0)),
                                                              rotation=num(f.get("ROTATION", 0)),
                                                              layer=f.get("LAYER"), footprint=f.get("PATTERN"))
    return out


def prjpcb_documents(path):
    docs = []
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("DocumentPath="):
                docs.append(line.split("=", 1)[1])
    return docs


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Print a summary of an Altium file (read-only).")
    ap.add_argument("file")
    a = ap.parse_args(argv)
    f = a.file.lower()
    if f.endswith(".schlib"):
        for n, s in schlib_symbols(a.file).items():
            print(f"{n}: {len(s['pins'])} pins, footprints {s['footprints']}, hash {symbol_hash(s)}")
    elif f.endswith(".pcblib"):
        for n, p in pcblib_footprints(a.file).items():
            print(f"{n}: {len(p['pads'])} pads, hash {footprint_hash(p)}")
    elif f.endswith(".pcbdoc"):
        for n, p in sorted(pcbdoc_components(a.file).items()):
            print(n, p)
    elif f.endswith(".schdoc"):
        m = sheet_model(a.file)
        print(f"{len(m['records'])} records, {len(m['comps'])} parts, {len(m['pins'])} pins, {len(m['wires'])} wires")
    elif f.endswith(".prjpcb"):
        print(prjpcb_documents(a.file))
    else:
        print("unknown file type")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
