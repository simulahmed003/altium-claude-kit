"""Footprint rule fixes on raw Data streams: silk width 0.15 mm, courtyard = pads/body + margin."""
import struct
from pcbparse import blk, i32, MM, parse_fp
SILK, CRT, ASSY = 33, 71, 69
NOTES = {}
U = lambda mm: int(round(mm / MM))


def walk(d):
    """yield (type, start, end, payload_start) for every primitive record (blocks only)."""
    nb, o = blk(d, 0)
    out = []
    while o < len(d):
        t = d[o]; s = o; o += 1
        if t == 2:
            for _ in range(6): _, o = blk(d, o)
        elif t == 5:
            _, o = blk(d, o); _, o = blk(d, o)
        else:
            b, o2 = blk(d, o)
            out.append((t, s + 1 + 4, o2))
            o = o2
    return out


def fix(name, d, margin, ext_fn):
    d = bytearray(d)
    notes = []
    recs = walk(bytes(d))
    # silk widths
    ch = 0
    for t, p, e in recs:
        if d[p] != SILK: continue
        if t == 4:
            w = i32(d, p + 29)
            if abs(w * MM - 0.15) > 0.001:
                struct.pack_into('<i', d, p + 29, U(0.15)); ch += 1
        if t == 1:
            r = i32(d, p + 21); w = i32(d, p + 41)
            if w < 2 * r * 0.9 and abs(w * MM - 0.15) > 0.001:   # leave filled pin-1 dots
                struct.pack_into('<i', d, p + 41, U(0.15)); ch += 1
    if ch: notes.append('silk lines set to 0.15 mm (%d)' % ch)
    # courtyard
    _, pads, _, _, tracks, arcs = parse_fp(bytes(d))
    E = [ext_fn(p) for p in pads]
    if not E:
        NOTES[name] = notes; return bytes(d)
    xs0 = [e[0] for e in E] + [e[1] for e in E]; ys0 = [e[2] for e in E] + [e[3] for e in E]
    for t in tracks:
        if t['layer'] == ASSY: xs0 += [t['x1'], t['x2']]; ys0 += [t['y1'], t['y2']]
    for a in arcs:
        if a['layer'] == ASSY and a['r'] >= 0.3: xs0 += [a['x'] - a['r'], a['x'] + a['r']]; ys0 += [a['y'] - a['r'], a['y'] + a['r']]
    import math
    for t, p, e in recs:
        if t == 12:
            b = d[p:e]; Lp = struct.unpack_from('<I', b, 18)[0]; o2 = 22 + Lp
            n = struct.unpack_from('<I', b, o2)[0]
            for i in range(n):
                vx, vy = struct.unpack_from('<dd', b, o2 + 4 + 16 * i)
                xs0.append(vx * MM); ys0.append(vy * MM)
    r2 = lambda v, up: (math.ceil(v * 20 - 1e-6) if up else math.floor(v * 20 + 1e-6)) / 20
    tgt = (r2(min(xs0) - margin, 0), r2(max(xs0) + margin, 1), r2(min(ys0) - margin, 0), r2(max(ys0) + margin, 1))
    ct = [(p) for t, p, e in recs if t == 4 and d[p] == CRT]
    ca = [(p) for t, p, e in recs if t == 1 and d[p] == CRT]
    if not ct:
        notes.append('no courtyard (not drawn; needs adding in Altium)')
        NOTES[name] = notes; return bytes(d)
    pts = [(i32(d, p + 13), i32(d, p + 17), i32(d, p + 21), i32(d, p + 25)) for p in ct]
    X = [v for q in pts for v in (q[0], q[2])]; Y = [v for q in pts for v in (q[1], q[3])]
    xmin, xmax, ymin, ymax = min(X), max(X), min(Y), max(Y)
    edge = [q for q in pts if (q[0] == q[2] and q[0] in (xmin, xmax)) or (q[1] == q[3] and q[1] in (ymin, ymax))]
    rect = len(edge) == 4 and not ca and all(v in (xmin, xmax) for q in edge for v in (q[0], q[2])) and all(v in (ymin, ymax) for q in edge for v in (q[1], q[3]))
    old = (xmin * MM, xmax * MM, ymin * MM, ymax * MM)
    if max(abs(a - b) for a, b in zip(old, tgt)) <= 0.01:
        NOTES[name] = notes; return bytes(d)
    if not rect:
        notes.append('courtyard is not a plain rectangle; not changed (outer %.2f..%.2f x %.2f..%.2f, rule box %.2f..%.2f x %.2f..%.2f)' % (old + tgt))
        NOTES[name] = notes; return bytes(d)
    mp = {xmin: U(tgt[0]), xmax: U(tgt[1])}; mq = {ymin: U(tgt[2]), ymax: U(tgt[3])}
    for p in ct:
        x1, y1, x2, y2 = i32(d, p + 13), i32(d, p + 17), i32(d, p + 21), i32(d, p + 25)
        if (x1 == x2 and x1 in (xmin, xmax)) or (y1 == y2 and y1 in (ymin, ymax)):
            struct.pack_into('<iiii', d, p + 13, mp.get(x1, x1), mq.get(y1, y1), mp.get(x2, x2), mq.get(y2, y2))
    notes.append('courtyard set to IPC-7351B: pads/body + %.2f mm, rounded out to 0.05 mm (was %.2f..%.2f x %.2f..%.2f, now %.2f..%.2f x %.2f..%.2f)' % ((margin,) + old + tgt))
    NOTES[name] = notes
    return bytes(d)
