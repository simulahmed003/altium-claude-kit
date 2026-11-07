"""SchLib records: read components (olefile), edit pins, write a new SchLib (pywin32) with a template's header."""
import struct
from olew import Writer, tree, parse_pairs, props_bytes, pstr, block

_c = {}


def ole(p):
    import olefile  # pip install olefile
    if p not in _c:
        _c[p] = olefile.OleFileIO(p)
    return _c[p]


class Rec:
    def __init__(self, typ, payload):
        self.typ = typ
        self.raw = payload
        self.kv = parse_pairs(payload) if typ == 0 else None

    def get(self, k, d=None):
        for a, b in self.kv or []:
            if a.upper() == k.upper():
                return b
        return d

    def set(self, k, v):
        for kv in self.kv:
            if kv[0].upper() == k.upper():
                kv[1] = v
                return
        self.kv.append([k, v])

    def drop(self, k):
        self.kv = [kv for kv in self.kv if kv[0].upper() != k.upper()]

    def bytes(self):
        p = props_bytes(self.kv) if self.typ == 0 else self.raw
        return struct.pack('<HBB', len(p), 0, self.typ) + p

    @property
    def rec(self):
        return self.get('RECORD') if self.typ == 0 else 'PIN'


def read_recs(data):
    i, out = 0, []
    while i + 4 <= len(data):
        n = struct.unpack_from('<H', data, i)[0]
        typ = data[i + 3]
        out.append(Rec(typ, data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


def components(path):
    o = ole(path)
    out = {}
    for e in o.listdir(streams=True, storages=False):
        if len(e) == 2 and e[1] == 'Data':
            rs = read_recs(o.openstream(e).read())
            if rs and rs[0].typ == 0 and rs[0].rec == '1':
                extra = {tuple(p): b for p, b in tree(o, [e[0]]) if p != ['Data']}
                out[rs[0].get('LIBREFERENCE')] = (rs, extra)
    return out


# ---- binary pin record helpers ----
def pin_fields(raw):
    o = 12
    dl = raw[o]; o += 1 + dl
    o += 3 + 6 + 4
    nl = raw[o]; name_at = o; o += 1 + nl
    dsl = raw[o]; des_at = o
    return name_at, des_at


def pin_set(raw, name=None, des=None):
    name_at, des_at = pin_fields(raw)
    nl = raw[name_at]
    cur_name = raw[name_at + 1:name_at + 1 + nl]
    dl = raw[des_at]
    cur_des = raw[des_at + 1:des_at + 1 + dl]
    tail = raw[des_at + 1 + dl:]
    nb = cur_name if name is None else name.encode('latin-1')
    db = cur_des if des is None else des.encode('latin-1')
    return raw[:name_at] + bytes([len(nb)]) + nb + bytes([len(db)]) + db + tail


def pin_des(raw):
    _, des_at = pin_fields(raw)
    dl = raw[des_at]
    return raw[des_at + 1:des_at + 1 + dl].decode('latin-1')


def pin_name(raw):
    name_at, _ = pin_fields(raw)
    nl = raw[name_at]
    return raw[name_at + 1:name_at + 1 + nl].decode('latin-1')


def assemble(head, graphics, rest):
    """head: component record; graphics: list of Recs (pins/graphics, owner 0);
    rest: list of Recs from the old component: designator, params, 44, 45.. (OWNERINDEX re-mapped)."""
    out = [head] + graphics
    # rest contains records whose OWNERINDEX refers to positions in old list -> remap through identity map
    idmap = {}
    for r in rest:
        idmap[id(r)] = len(out)
        out.append(r)
    return out, idmap


def write_lib(path, comps, template):
    """comps: list of (libref, storage, recs, extra_streams{parts: bytes}, description); template: any SchLib whose
    file header and Storage stream are copied (the source library)."""
    t = ole(template)
    fh = parse_pairs(t.openstream('FileHeader').read()[4:])
    head = []
    for k, v in fh:
        if k.upper() == 'COMPCOUNT':
            break
        head.append([k, v])
    head.append(['CompCount', str(len(comps))])
    for i, c in enumerate(comps):
        head += [['LibRef%d' % i, c[0]], ['CompDescr%d' % i, c[4]], ['PartCount%d' % i, c[2][0].get('PARTCOUNT', '2')]]
    w = Writer(path)
    w.put('FileHeader', block(props_bytes(head)))
    w.put('Storage', t.openstream('Storage').read())
    keys = [(c[0], c[1]) for c in comps if c[0] != c[1]]
    if keys:
        kv = [['KeyCount', str(len(keys))]]
        for i, (lr, sk) in enumerate(keys):
            kv += [['LibRef%d' % i, lr], ['SectionKey%d' % i, sk]]
        w.put('SectionKeys', block(props_bytes(kv)))
    for lr, sk, recs, extra, desc in comps:
        w.put([sk, 'Data'], b''.join(r.bytes() for r in recs))
        for p, b in extra.items():
            w.put([sk] + list(p), b)
    w.close()
