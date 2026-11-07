"""Minimal structured-storage (OLE) writer and reader helpers. Writing needs pywin32 (Windows); reading needs olefile."""
import struct

M_CREATE = 0x1000 | 0x2 | 0x10  # STGM_CREATE | STGM_READWRITE | STGM_SHARE_EXCLUSIVE


class Writer:
    def __init__(self, path):
        import pythoncom  # pywin32: pip install pywin32 (Windows only)
        self.root = pythoncom.StgCreateDocfile(path, M_CREATE, 0)
        self.stg = {(): self.root}

    def _dir(self, parts):
        parts = tuple(parts)
        if parts not in self.stg:
            parent = self._dir(parts[:-1])
            self.stg[parts] = parent.CreateStorage(parts[-1], M_CREATE, 0, 0)
        return self.stg[parts]

    def put(self, path, data):
        parts = path.split('/') if isinstance(path, str) else list(path)
        st = self._dir(parts[:-1]).CreateStream(parts[-1], M_CREATE, 0, 0)
        st.Write(bytes(data))
        del st

    def close(self):
        for k in sorted(self.stg, key=len, reverse=True):
            self.stg[k].Commit(0)
        self.stg.clear()
        self.root = None


def tree(ole, prefix):
    """All streams below storage prefix (list), as (relative parts, bytes)."""
    out = []
    for e in ole.listdir(streams=True, storages=False):
        if e[:len(prefix)] == list(prefix):
            out.append((e[len(prefix):], ole.openstream(e).read()))
    return out


def pstr(s):
    b = s.encode('latin-1')
    return bytes([len(b)]) + b


def block(b):
    return struct.pack('<I', len(b)) + b


def props_bytes(pairs):
    s = '|' + '|'.join('%s=%s' % (k, v) for k, v in pairs)
    return s.encode('latin-1') + b'\x00'


def parse_pairs(b):
    s = b.rstrip(b'\x00').decode('latin-1')
    out = []
    for p in s.split('|'):
        if '=' in p:
            k, v = p.split('=', 1)
            out.append([k, v])
    return out
