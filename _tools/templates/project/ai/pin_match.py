"""pin_match.py - every schematic symbol must have exactly the same pins as the footprint it links to.

Reads the real library files (no Altium, no extra packages):
  python pin_match.py <lib.SchLib> <lib.PcbLib>
Checks per symbol:
  1. set of pin numbers == set of pad numbers of the linked footprint (one pin per pad, no extras)
  2. no pin is hidden
  3. no two pins share a connection point (no stacked pins)
Prints PASS / FAIL per symbol and exits 1 if anything fails.
"""
import struct, sys
from collections import Counter


# ---------- minimal Compound File Binary (OLE2) reader ----------
class CFB:
    def __init__(self, path):
        self.d = open(path, "rb").read()
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
            name = e[:max(nl - 2, 0)].decode("utf-16-le")
            typ = e[66]
            left, right, child = struct.unpack_from("<III", e, 68)
            start = struct.unpack_from("<I", e, 116)[0]
            size = struct.unpack_from("<Q", e, 120)[0]
            self.ents.append(dict(name=name, type=typ, left=left, right=right, child=child, start=start, size=size))
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

    def _read(self, e):
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

    def storages(self):
        """{storage name: {stream name: bytes}} for the top-level storages."""
        res = {}
        for i in self.children(0):
            e = self.ents[i]
            if e["type"] == 1:
                res[e["name"]] = {self.ents[j]["name"]: self._read(self.ents[j]) for j in self.children(i)
                                  if self.ents[j]["type"] == 2}
        return res


def pascal(b, o):
    n = b[o]
    return b[o + 1:o + 1 + n].decode("latin-1"), o + 1 + n


# ---------- SchLib ----------
def schlib_symbols(path):
    """{symbol name: dict(pins=[(designator, x, y, orientation, length, hidden)], footprints=[names])}"""
    out = {}
    for st, streams in CFB(path).storages().items():
        data = streams.get("Data")
        if not data:
            continue
        o, name, pins, fps = 0, None, [], []
        while o + 4 <= len(data):
            ln = struct.unpack_from("<H", data, o)[0]
            kind = data[o + 3]
            rec = data[o + 4:o + 4 + ln]
            o += 4 + ln
            if kind == 1 and len(rec) > 5 and struct.unpack_from("<i", rec, 0)[0] == 2:  # binary pin
                p = 4 + 1 + 2 + 1 + 4
                _, p = pascal(rec, p)                      # description
                p += 2                                     # formal type, electrical type
                flags = rec[p]; p += 1
                length, x, y = struct.unpack_from("<hhh", rec, p); p += 6 + 4
                pname, p = pascal(rec, p)
                desig, p = pascal(rec, p)
                pins.append((desig, x, y, flags & 0x03, length, bool(flags & 0x04)))
            elif kind == 0:
                t = rec.rstrip(b"\x00").decode("latin-1", "replace")
                f = {kv.split("=", 1)[0].upper(): kv.split("=", 1)[1] for kv in t.split("|") if "=" in kv}
                if f.get("RECORD") == "1":
                    name = f.get("LIBREFERENCE", st)
                elif f.get("RECORD") == "45" and f.get("MODELTYPE", "").upper() == "PCBLIB":
                    fps.append(f.get("MODELNAME"))
                elif f.get("RECORD") == "2":               # text-form pin (older writers)
                    pins.append((f.get("DESIGNATOR"), int(f.get("LOCATION.X", 0)), int(f.get("LOCATION.Y", 0)),
                                 int(f.get("PINCONGLOMERATE", 0)) & 3, int(f.get("PINLENGTH", 0)),
                                 bool(int(f.get("PINCONGLOMERATE", 0)) & 4)))
        if name:
            out[name] = dict(pins=pins, footprints=fps)
    return out


def pin_tip(x, y, rot, length):
    """Altium stores the body end; the connection point is length away along the pin's rotation."""
    dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][rot]
    return x + dx * length, y + dy * length


# ---------- PcbLib ----------
BLOCKS = {2: 6, 5: 2}   # pad has 6 length-prefixed blocks, text 2, every other primitive 1


def pcblib_pads(path):
    """{footprint name: [pad designators]}"""
    out = {}
    for st, streams in CFB(path).storages().items():
        data = streams.get("Data")
        if not data:
            continue
        n = struct.unpack_from("<I", data, 0)[0]
        name, _ = pascal(data, 4)
        if "|" in name:            # library header storages, not footprints
            continue
        o = 4 + n
        pads = []
        while o < len(data):
            typ = data[o]; o += 1
            if typ == 0:
                break
            for b in range(BLOCKS.get(typ, 1)):
                ln = struct.unpack_from("<I", data, o)[0]
                blk = data[o + 4:o + 4 + ln]
                if typ == 2 and b == 0:
                    pads.append(pascal(blk, 0)[0])
                o += 4 + ln
        out[name] = pads
    return out


def main(sch, pcb):
    syms, fps = schlib_symbols(sch), pcblib_pads(pcb)
    fails = 0
    print(f"{'symbol':24} {'footprint':22} result  detail")
    for s in sorted(syms):
        pins, links = syms[s]["pins"], syms[s]["footprints"]
        why = []
        if len(links) != 1:
            why.append(f"{len(links)} footprint links")
        fp = links[0] if links else "-"
        pads = fps.get(fp)
        if pads is None:
            why.append(f"footprint {fp} not in {pcb}")
        else:
            pn, pd = Counter(p[0] for p in pins), Counter(pads)
            if pn != pd:
                why.append(f"pins {sorted(pn.elements())} vs pads {sorted(pd.elements())}")
        hidden = [p[0] for p in pins if p[5]]
        if hidden:
            why.append(f"hidden pins {hidden}")
        pos = Counter(pin_tip(p[1], p[2], p[3], p[4]) for p in pins)
        stacked = [p[0] for p in pins if pos[pin_tip(p[1], p[2], p[3], p[4])] > 1]
        if stacked:
            why.append(f"stacked pins {stacked}")
        fails += bool(why)
        print(f"{s:24} {fp:22} {'FAIL' if why else 'PASS'}    {'; '.join(why) or f'{len(pins)} pins = {len(pads)} pads'}")
    print(f"\n{len(syms)} symbols, {len(syms) - fails} PASS, {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
