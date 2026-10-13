"""sch_overlap.py - text overlap check on a saved .SchDoc (read-only).
   python sch_overlap.py <file.SchDoc>
Text size is estimated (Times New Roman 10: ~65 mil per character, 110 mil tall; bold 12: ~80 / 140), so the
result is a screen for problems, not a proof: confirm with a screenshot. Reports:
  - text overlapping text            - text crossing a wire
  - text over a pin line             - text inside a symbol body (designator/value)
  - rotated designators / values (all text must be horizontal)
  - text, symbol body or power-port glyph crossing a block-box line; a wire running along a box line
  - a pin number under a wire or a junction dot (rule n)
  - text that does not fit inside its text frame (100 mil margin)
  - a value / designator closer to another part than to its own, or within 200 mil of a test point
"""
import sys
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0])
from schdoc_text import records, mil

CW, CH = {1: 65, 2: 65, 9: 80}, {1: 110, 2: 110, 9: 140}


def tbox(x, y, text, font, just=0):
    w, h = len(text) * CW.get(font, 65), CH.get(font, 110)
    jx, jy = just % 3, just // 3          # 0 left/bottom, 1 centre, 2 right/top
    x0, y0 = x - w * jx / 2, y - h * jy / 2
    return (x0, y0, x0 + w, y0 + h)


def hit(a, b, pad=0):
    return a[0] < b[2] + pad and b[0] < a[2] + pad and a[1] < b[3] + pad and b[1] < a[3] + pad


def seg_box(x1, y1, x2, y2, t=5):
    return (min(x1, x2) - t, min(y1, y2) - t, max(x1, x2) + t, max(y1, y2) + t)


def main(path, override=None):
    """override: {designator: (x, y)} - test designator positions (rotation 0, font 1) before moving them."""
    override = override or {}
    recs = records(path)[1:]
    comps = {i: r for i, r in enumerate(recs) if r.get("RECORD") == "1"}
    des = {int(r["OWNERINDEX"]): r.get("TEXT") for r in recs if r.get("RECORD") == "34"}
    texts, wires, pins, bodies, problems = [], [], [], [], []
    boxes, frames, polylines, pinnums, ports = [], [], [], [], []
    comp_pts = {}
    params = {}
    for i, r in enumerate(recs):
        rec, own = r.get("RECORD"), int(r.get("OWNERINDEX", -1))
        who = des.get(own, "sheet")
        if rec in ("34", "41") and r.get("ISHIDDEN") != "T" and own in comps:
            if rec == "41":
                params[i] = r
            t = r.get("TEXT", "")
            if rec == "41" and t.startswith("="):            # =Value -> show the referenced parameter
                ref = t[1:].upper()
                t = next((p.get("TEXT", "") for p in recs if p.get("RECORD") == "41" and
                          int(p.get("OWNERINDEX", -1)) == own and p.get("NAME", "").upper() == ref), t)
            if rec == "41" and not r.get("NAME"):
                continue
            o = int(r.get("ORIENTATION", 0))
            kind = "designator" if rec == "34" else "value"
            if rec == "34" and t in override:
                x, y = override[t]
                texts.append((f"{kind} {who} '{t}'", tbox(x, y, t, 1), own))
                continue
            if o:
                problems.append(f"rotated {kind} {who} '{t}' (orientation {o * 90})")
            texts.append((f"{kind} {who} '{t}'", tbox(mil(r, "X"), mil(r, "Y"), t, int(r.get("FONTID", 1)),
                                                     int(r.get("JUSTIFICATION", 0))), own))
        elif rec == "4" and own not in comps:                   # free label (headings, group values)
            t = r.get("TEXT", "")
            if t.startswith("="):                               # special string -> sheet parameter value
                t = next((p.get("TEXT", "") for p in recs if p.get("RECORD") == "41" and
                          p.get("NAME", "").upper() == t[1:].upper() and int(p.get("OWNERINDEX", -1)) not in comps), t)
            texts.append((f"label '{t}'", tbox(mil(r, "X"), mil(r, "Y"), t, int(r.get("FONTID", 1)),
                                                int(r.get("JUSTIFICATION", 0))), -1))
        elif rec == "25":                                        # net label: text above the wire
            t = r.get("TEXT", "")
            x, y = mil(r, "X"), mil(r, "Y")
            texts.append((f"net label '{t}'", (x, y + 10, x + len(t) * 65, y + 120), -2))
        elif rec == "17":                                        # power port
            t = r.get("TEXT", "")
            x, y, o = mil(r, "X"), mil(r, "Y"), int(r.get("ORIENTATION", 0))
            w = len(t) * 65
            ports.append((t, (x - 100, y - 200, x + 100, y) if o == 3 else (x - 100, y, x + 100, y + 150)))
            if o == 3:   # ground glyph pointing down, text under it
                texts.append((f"port '{t}'", (x - w / 2, y - 330, x + w / 2, y - 210), -3))
            else:        # rail bar pointing up, text above it
                texts.append((f"port '{t}'", (x - w / 2, y + 160, x + w / 2, y + 270), -3))
        elif rec == "27":                                        # wire
            n = int(r.get("LOCATIONCOUNT", 0))
            pts = [(int(r.get(f"X{k}", 0)) * 10, int(r.get(f"Y{k}", 0)) * 10) for k in range(1, n + 1)]
            wires += [seg_box(*pts[k], *pts[k + 1]) for k in range(len(pts) - 1)]
            polylines.append(pts)
        elif rec == "2" and own in comps:                        # pin line
            x, y, ln = mil(r, "X"), mil(r, "Y"), int(r.get("PINLENGTH", 0)) * 10
            rot = int(r.get("PINCONGLOMERATE", 0)) & 3
            dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][rot]
            pins.append((who, seg_box(x, y, x + dx * ln, y + dy * ln, 3)))
            comp_pts.setdefault(who, []).extend([(x, y), (x + dx * ln, y + dy * ln)])
            pc = int(r.get("PINCONGLOMERATE", 0))
            if pc & 0x10 and not pc & 0x04:          # designator shown, pin not hidden
                n = r.get("DESIGNATOR", "")
                w = len(n) * 50
                if dy == 0:                           # number above the line, 30 mil out from the body end
                    x0 = x + 30 if dx > 0 else x - 30 - w
                    pinnums.append((who, n, (x0, y + 10, x0 + w, y + 100)))
                else:
                    y0 = y + 30 if dy > 0 else y - 30 - w
                    pinnums.append((who, n, (x + 10, y0, x + 100, y0 + w)))
        elif rec == "14" and own not in comps:                   # block box
            boxes.append((mil(r, "X"), mil(r, "Y"), int(r.get("CORNER.X", 0)) * 10, int(r.get("CORNER.Y", 0)) * 10))
        elif rec == "28":                                        # text frame
            frames.append((mil(r, "X"), mil(r, "Y"), int(r.get("CORNER.X", 0)) * 10, int(r.get("CORNER.Y", 0)) * 10,
                           r.get("TEXT", "").replace("~1", "\n")))
        elif rec == "14" and own in comps:                       # symbol body rectangle
            bodies.append((who, (mil(r, "X"), mil(r, "Y"),
                                 int(r.get("CORNER.X", 0)) * 10, int(r.get("CORNER.Y", 0)) * 10)))
    bodies = [(w, (min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3]))) for w, b in bodies]
    for i, (na, a, oa) in enumerate(texts):
        for nb, b, ob in texts[i + 1:]:
            if hit(a, b):
                problems.append(f"overlap: {na} / {nb}")
        for w in wires:
            if hit(a, w) and not na.startswith("net label"):
                problems.append(f"on a wire: {na}")
                break
        for who, p in pins:
            if hit(a, p):
                problems.append(f"over a pin of {who}: {na}")
                break
        for who, b in bodies:
            if hit(a, b) and (na.startswith("designator") or na.startswith("value")):
                problems.append(f"inside the body of {who}: {na}")
                break
    # --- block boxes: nothing may cross a box line (wires may enter / leave across it)
    edges = []
    for x1, y1, x2, y2 in boxes:
        x1, x2, y1, y2 = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        edges += [seg_box(x1, y1, x2, y1, 2), seg_box(x1, y2, x2, y2, 2),
                  seg_box(x1, y1, x1, y2, 2), seg_box(x2, y1, x2, y2, 2)]
    for e in edges:
        for na, a, _ in texts:
            if hit(a, e):
                problems.append(f"box line through {na}")
        for who, b in bodies:
            if hit(b, e):
                problems.append(f"box line through the body of {who}")
        for t, g in ports:
            if hit(g, e):
                problems.append(f"box line through power port {t} at {g[:2]}")
        horiz = e[3] - e[1] < 10
        mid = (e[1] + e[3]) / 2 if horiz else (e[0] + e[2]) / 2
        for pts in polylines:
            for k in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[k], pts[k + 1]
                if horiz:
                    along = ay == by and abs(ay - mid) < 60 and min(ax, bx) < e[2] and max(ax, bx) > e[0]
                else:
                    along = ax == bx and abs(ax - mid) < 60 and min(ay, by) < e[3] and max(ay, by) > e[1]
                if along:
                    problems.append(f"wire runs along a box line near {pts[k]}-{pts[k + 1]}")
    # --- junction dots: a wire end on another wire's interior, or 3+ wire ends at one point
    ends = {}
    for pts in polylines:
        for p in (pts[0], pts[-1]):
            ends[p] = ends.get(p, 0) + 1
    dots = {p for p, c in ends.items() if c >= 3}
    for p in ends:
        for pts in polylines:
            for k in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[k], pts[k + 1]
                if (ax == bx == p[0] and min(ay, by) < p[1] < max(ay, by)) or \
                        (ay == by == p[1] and min(ax, bx) < p[0] < max(ax, bx)):
                    dots.add(p)
    for who, n, b in pinnums:
        if any(hit(b, w) for w in wires) or any(hit(b, (x - 25, y - 25, x + 25, y + 25)) for x, y in dots):
            problems.append(f"pin number {who}.{n} under a wire or junction dot")
    # --- text frames: wrapped text must fit with a 100 mil margin
    for x1, y1, x2, y2, t in frames:
        w, h = abs(x2 - x1) - 200, abs(y2 - y1) - 200
        per = max(int(w // 65), 1)
        lines = 0
        for para in t.split("\n"):
            cur, lines = 0, lines + 1
            for word in para.split():
                if len(word) > per:
                    problems.append(f"text frame at {(x1, y1)}: word '{word}' wider than the frame")
                if cur and cur + 1 + len(word) > per:
                    lines, cur = lines + 1, len(word)
                else:
                    cur += (1 if cur else 0) + len(word)
        if lines * 120 > h:
            problems.append(f"text frame at {(x1, y1)}: {lines} lines need {lines * 120 + 200} mil, frame is {abs(y2 - y1)}")
        fb = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        if any(hit(fb, wb) for wb in wires):
            problems.append(f"text frame at {(x1, y1)} touches a wire")
        for who, b in bodies:
            if hit(fb, b, 50):
                problems.append(f"text frame at {(x1, y1)} touches the body of {who}")
    # --- value / designator must be closest to its own part, and 200 mil from any test point
    # each part = its pin lines + body rectangles (nearest real geometry, not the bounding box)
    cbox = {}
    for who, pb in pins:
        cbox.setdefault(who, []).append(pb)
    for who, bb in bodies:
        cbox.setdefault(who, []).append(bb)

    def dist(a, b):
        dx = max(b[0] - a[2], a[0] - b[2], 0)
        dy = max(b[1] - a[3], a[1] - b[3], 0)
        return (dx * dx + dy * dy) ** 0.5
    for na, a, own in texts:
        if not (na.startswith("value") or na.startswith("designator")):
            continue
        me = na.split()[1]
        if me not in cbox:
            continue
        d_me = min(dist(a, g) for g in cbox[me])
        for other, gs in cbox.items():
            if other == me:
                continue
            d = min(dist(a, g) for g in gs)
            if d + 50 < d_me:
                problems.append(f"{na} is closer to {other} ({d:.0f}) than to {me} ({d_me:.0f})")
            if other.startswith("TP") and not me.startswith("TP") and d < 200:
                problems.append(f"{na} is {d:.0f} mil from test point {other}")
    for p in sorted(set(problems)):
        print(p)
    print(f"\n{len(texts)} text items, {len(set(problems))} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    ov = {}
    if len(sys.argv) > 2:                      # optional: python sch_overlap.py sheet.SchDoc --targets
        from sch_text import T
        ov = {k: v[0] for k, v in T.items()}
    sys.exit(main(sys.argv[1], ov))
