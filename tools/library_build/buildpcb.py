"""Write a new PcbLib from footprints copied out of source PcbLibs (pywin32), with a template's library streams."""
import struct, re
from olew import Writer, tree, pstr, block, props_bytes, parse_pairs
from pcbparse import props

_cache = {}


def ole(path):
    import olefile  # pip install olefile
    if path not in _cache:
        _cache[path] = olefile.OleFileIO(path)
    return _cache[path]


def find_storage(o, pattern):
    for e in o.listdir(streams=True, storages=False):
        if len(e) == 2 and e[1] == 'Parameters':
            pr = props(o.openstream(e).read()[4:])
            if pr.get('PATTERN') == pattern:
                return e[0]
    raise KeyError(pattern)


def models_of(o):
    """model id -> (props bytes, stream bytes)"""
    d = o.openstream('Library/Models/Data').read()
    out, i, n = {}, 0, 0
    while i + 4 <= len(d):
        L = struct.unpack_from('<I', d, i)[0]
        b = d[i + 4:i + 4 + L]
        i += 4 + L
        mid = props(b'|' + b).get('ID')
        sname = 'Library/Models/%d' % n
        out[mid] = (b, o.openstream(sname).read() if o.exists(sname) else None)
        n += 1
    return out


def build(path, fps, template, heights=None, fix=None):
    """fps: list of (new name, source file, source pattern). template: any PcbLib (its library streams are copied).
    heights: new name -> mil string. fix(name, data) -> data edits each footprint (fpfix)."""
    heights = heights or {}
    t = ole(template)
    w = Writer(path)
    w.put('FileHeader', t.openstream('FileHeader').read())
    for parts, data in tree(t, ['FileVersionInfo']):
        w.put(['FileVersionInfo'] + parts, data)
    libdata = t.openstream('Library/Data').read()
    hl = struct.unpack_from('<I', libdata, 0)[0]
    header = libdata[:4 + hl]
    names, toc, models, log = [], [], [], []
    seen_models = set()
    for new, src, pat in fps:
        o = ole(src)
        st = find_storage(o, pat)
        items = tree(o, [st])
        data = dict((tuple(p), b) for p, b in items)
        d = data[('Data',)]
        L = struct.unpack_from('<I', d, 0)[0]
        d = block(pstr(new)) + d[4 + L:]
        if fix:
            d = fix(new, d)
        prm = parse_pairs(data[('Parameters',)][4:])
        pr = dict(prm)
        for kv in prm:
            if kv[0] == 'PATTERN':
                kv[1] = new
            if kv[0] == 'HEIGHT' and new in heights:
                kv[1] = heights[new]
        pb = props_bytes(prm)
        if len(new) > 31:
            raise ValueError('name too long ' + new)
        for p, b in items:
            if tuple(p) == ('Data',):
                b = d
            elif tuple(p) == ('Parameters',):
                b = block(pb)
            w.put([new] + p, b)
        names.append(new)
        # pad count from TOC of source
        srcmod = models_of(o)
        for mid in re.findall(rb'MODELID=(\{[0-9A-Fa-f-]+\})', d):
            mid = mid.decode()
            if mid in srcmod and mid not in seen_models:
                seen_models.add(mid)
                models.append(srcmod[mid])
        hmil = dict(prm).get('HEIGHT', '0mil').replace('mil', '')
        toc.append('Name=%s|Pad Count=%d|Height=%s|Description=%s' % (new, d.count(b'\x02') and pads_count(d), hmil, pr.get('DESCRIPTION', '')))
        log.append((new, src, pat, st))
    w.put('Library/Header', struct.pack('<I', 1))
    body = struct.pack('<I', len(names)) + b''.join(block(pstr(n)) for n in names)
    w.put('Library/Data', header + body)
    tocb = ('\r\n'.join(toc) + '\r\n').encode('latin-1') + b'\x00'
    w.put('Library/ComponentParamsTOC/Header', struct.pack('<I', 1))
    w.put('Library/ComponentParamsTOC/Data', block(tocb))
    w.put('Library/EmbeddedFonts', t.openstream('Library/EmbeddedFonts').read())
    for sub in ('LayerKindMapping', 'ModelsNoEmbed', 'PadViaLibrary', 'Textures'):
        for parts, data in tree(t, ['Library', sub]):
            if sub == 'PadViaLibrary' and parts == ['Data']:
                pass
            w.put(['Library', sub] + parts, data)
    w.put('Library/Models/Header', struct.pack('<I', len(models)))
    w.put('Library/Models/Data', b''.join(block(m[0]) for m in models))
    for i, m in enumerate(models):
        if m[1] is not None:
            w.put('Library/Models/%d' % i, m[1])
    w.close()
    return log


def pads_count(d):
    from pcbparse import parse_fp
    return len(parse_fp(d)[1])
