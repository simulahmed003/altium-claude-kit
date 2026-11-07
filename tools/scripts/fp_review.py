"""fp_review.py - footprint review document (LIB-33): one editable A4 .docx (+ PDF) per footprint, or one for all.

Each section: datasheet crops (pinout, outline, land pattern) with page captions, the symbol and footprint drawn
from the library data, dimension arrows, and a check table (footprint value | datasheet value, Pass / Fail / Check,
tolerance 0.01 mm, a datasheet range passes inside its min to max). Two reviewer lines at the end.

Review folder (--dir, default: the current folder):
  review.json        {"library": "MyLib", "pcblib": "..\\MyLib.PcbLib", "schlib": "..\\MyLib.SchLib",
                      "datasheets": "..\\MyLib_Datasheets"}            (paths relative to the review folder)
  specs\\<footprint>.json   per footprint: datasheet PDF, crop boxes and pages, DS values, dimension arrows
                           (pick crop boxes with --page; see an existing spec for the keys: chip2, auto, checks, dims)
  <datasheets>\\_datasheet_index.csv   optional: Component name, MPN, Manufacturer, Datasheet file, URL
Library data: read offline from the PcbLib / SchLib (lib_dump.py); without them in review.json the folder must hold
_pcblib_dump.txt, _schlib_dump.txt and fpsum.json (kit lib_dump <PcbLib> <SchLib> --out <folder>).

Usage:
  python fp_review.py <footprint> [<footprint> ...]   build those reviews (<dir>\\<footprint>\\<footprint>_review.docx)
  python fp_review.py --all                            one document with every footprint that has a spec
  python fp_review.py --page <pdf> <page>              save a gridded page image to pick crop boxes
  python fp_review.py --sheet <pdf> [pages...]         contact sheet of a PDF's pages
Options: --dir <review folder>, --library <name> (title, default from review.json)
Needs: pip install matplotlib pymupdf python-docx (PDF export uses Word through pywin32 when present; the .docx is
complete without it). Datasheet PDFs stay local (never committed); the crops are pictures inside the .docx.
"""
import json
import math
import os
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle, Arc
    from matplotlib.transforms import Affine2D
    import pymupdf
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor
    MISSING = None
except ImportError as _e:          # --help and the tests work without them
    MISSING = _e.name

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = Path.cwd()
DS_DIR = HERE / "datasheets"
FPSUM = HERE / "fpsum.json"
LIBNAME = "library"
CFG = {}


def configure(folder, library=None):
    """Set the review folder and read its review.json."""
    global HERE, DS_DIR, FPSUM, LIBNAME, OUT_ALL, DSIDX, CFG
    HERE = Path(folder).resolve()
    cfgp = HERE / "review.json"
    CFG = json.loads(cfgp.read_text(encoding="utf-8-sig")) if cfgp.exists() else {}
    rel = lambda k, d: (HERE / CFG[k]).resolve() if CFG.get(k) else d
    DS_DIR = rel("datasheets", HERE / "datasheets")
    FPSUM = rel("fpsum", HERE / "fpsum.json")
    LIBNAME = library or CFG.get("library") or (Path(CFG["pcblib"]).stem if CFG.get("pcblib") else "library")
    OUT_ALL = HERE
    DSIDX = _ds_index()


def _ds_index():
    import csv
    p = DS_DIR / "_datasheet_index.csv"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8-sig") as fh:
        return {r["Component name"]: r for r in csv.DictReader(fh)}


def hyperlink(paragraph, url, text):
    """Clickable link in a python-docx paragraph (relative paths open the local file)."""
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                          is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    for tag, val in (("w:color", "0563C1"), ("w:u", "single")):
        e = OxmlElement(tag)
        e.set(qn("w:val"), val)
        rpr.append(e)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    r.append(t)
    h.append(r)
    paragraph._p.append(h)
OUT_ALL = HERE
DSIDX = {}
COL = {"Pass": "#7CFC7C", "Fail": "#FF8A8A", "Check": "#FFC870"}
TOL = {"pad": 0.01, "span": 0.01, "pitch": 0.01, "row": 0.01}
ELEC = {0: "Input", 1: "IO", 2: "Output", 3: "OpenCollector", 4: "Passive", 5: "HiZ", 6: "OpenEmitter", 7: "Power"}


# ---- library data ---------------------------------------------------------------------------
def _lines(kind):
    """dump lines: read from the library in review.json (offline, lib_dump.py) or from the dump file."""
    import lib_dump
    lib = CFG.get(kind)
    if lib:
        return (lib_dump.pcb_dump_lines if kind == "pcblib" else lib_dump.sch_dump_lines)(str((HERE / lib).resolve()))
    lines = []
    for name in (["_pcblib_dump.txt"] if kind == "pcblib" else ["_schlib_dump.txt", "_schlib_dump2.txt"]):
        if (HERE / name).exists():
            lines += (HERE / name).read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        sys.exit(f"no {kind} in review.json and no dump file in {HERE} (kit lib_dump <lib> --out <folder>)")
    return lines


def load_fpsum():
    import lib_dump
    if CFG.get("schlib") and not FPSUM.exists():
        return lib_dump.fpsum(str((HERE / CFG["schlib"]).resolve()))
    return json.loads(FPSUM.read_text(encoding="utf-8"))


def load_pcb():
    fps, cur = {}, None
    for line in _lines("pcblib"):
        f = line.split("|")
        if f[0] == "FP":
            cur = fps.setdefault(f[1], {"pads": [], "tracks": [], "arcs": [], "vias": [], "boxes": []})
        elif f[0] == "PAD":
            x, y, sx, sy, shape, rot, hole, htype, hw = map(float, f[2:11])
            cur["pads"].append(dict(n=f[1], x=x, y=y, sx=sx, sy=sy, shape=int(shape), rot=rot, hole=hole,
                                    htype=int(htype), hw=hw, layer=f[11]))
        elif f[0] == "TRK":
            cur["tracks"].append(dict(x1=float(f[1]), y1=float(f[2]), x2=float(f[3]), y2=float(f[4]),
                                      w=float(f[5]), layer=f[6]))
        elif f[0] == "ARC":
            cur["arcs"].append(dict(x=float(f[1]), y=float(f[2]), r=float(f[3]), a0=float(f[4]), a1=float(f[5]),
                                    w=float(f[6]), layer=f[7]))
        elif f[0] == "VIA":
            cur["vias"].append(dict(x=float(f[1]), y=float(f[2]), d=float(f[3]), hole=float(f[4])))
        elif f[0] == "BOX":
            cur["boxes"].append(dict(kind=int(f[1]), x0=float(f[2]), y0=float(f[3]), x1=float(f[4]), y1=float(f[5]),
                                     layer=f[6]))
    for fp in fps.values():
        # some footprints are stored around the absolute library origin instead of the 1270 mm board origin
        if fp["pads"] and abs(fp["pads"][0]["x"]) > 500:
            for p in fp["pads"] + fp["vias"] + fp["arcs"]:
                p["x"] += 1270
                p["y"] += 1270
            for t in fp["tracks"]:
                for k in ("x1", "x2", "y1", "y2"):
                    t[k] += 1270
            for b in fp["boxes"]:
                for k in ("x0", "x1", "y0", "y1"):
                    b[k] += 1270
        layers = {t["layer"] for t in fp["tracks"]} | {a["layer"] for a in fp["arcs"]}
        fp["assy"] = "Mechanical Layer 13" if "Mechanical Layer 13" in layers else "Mechanical Layer 5"
    return fps


def load_sch():
    syms, cur = {}, None
    for _ in (1,):
        for line in _lines("schlib"):
            f = line.split("|")
            if f[0] == "SYM":
                cur = syms.setdefault(f[1], {"desc": "", "pins": [], "rects": [], "lines": [], "polys": [],
                                             "arcs": [], "ells": []})
                if len(f) > 2:
                    cur["desc"] = f[2]
            elif f[0] == "PIN":
                cur["pins"].append(dict(n=f[1], name=f[2], el=int(f[3]), ori=int(f[4]), x=int(f[5]), y=int(f[6]),
                                        L=int(f[7]), show_name=f[8] not in ("0", "False"), part=int(f[10])))
            elif f[0] == "RECT":
                cur["rects"].append(list(map(int, f[1:5])))
            elif f[0] == "LINE":
                cur["lines"].append(list(map(int, f[1:5])))
            elif f[0] == "PL":
                pts = [tuple(map(int, p.split(","))) for p in f[3:]]
                cur["polys"].append(dict(closed=f[1] == "15", pts=pts))
            elif f[0] == "ARC":
                cur["arcs"].append(dict(x=int(f[1]), y=int(f[2]), r=int(f[3]), a0=float(f[4]), a1=float(f[5])))
            elif f[0] == "ELL":
                cur["ells"].append(dict(x=int(f[1]), y=int(f[2]), r=int(f[3]), r2=int(f[4])))
    return syms


class Pad:
    """Pad with its size after rotation (X x Y on the board) and its edges."""

    def __init__(self, p):
        self.__dict__.update(p)
        r = round(p["rot"]) % 180
        self.X, self.Y = (p["sy"], p["sx"]) if r == 90 else (p["sx"], p["sy"])
        self.l, self.r, self.b, self.t = self.x - self.X / 2, self.x + self.X / 2, self.y - self.Y / 2, self.y + self.Y / 2


# ---- footprint drawing ----------------------------------------------------------------------
LAYER_STYLE = {"Top Overlay": ("#ffff00", 5), "Mechanical Layer 13": ("#ff00ff", 4),
               "Mechanical Layer 15": ("#00c000", 3), "Mechanical 13": ("#ff00ff", 4), "Mechanical 15": ("#00c000", 3)}


def draw_footprint(fp, spec, results, out):
    pads = [Pad(p) for p in fp["pads"]]
    xs = [p.l for p in pads] + [p.r for p in pads] + [t[k] for t in fp["tracks"] for k in ("x1", "x2")]
    ys = [p.b for p in pads] + [p.t for p in pads] + [t[k] for t in fp["tracks"] for k in ("y1", "y2")]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = max(x1 - x0, y1 - y0)
    u = span / 10  # layout unit: label rows and arrow offsets scale with the part
    lm, rm, tm, bm = (spec.get("margin", {}).get(k, d) for k, d in (("l", 5), ("r", 5), ("t", 4), ("b", 3)))
    xlim = (x0 - lm * u, x1 + rm * u)
    ylim = (y0 - bm * u, y1 + tm * u)
    w_in = 12
    h_in = w_in * (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=150)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.patch.set_facecolor("#5f5f5f")
    ax.set_facecolor("#5f5f5f")
    pt_per_mm = w_in * 72 / (xlim[1] - xlim[0])
    for p in pads:
        if p.shape == 1 and abs(p.sx - p.sy) < 1e-6:
            patch = Circle((p.x, p.y), p.sx / 2)
        elif p.shape == 1:
            patch = FancyBboxPatch((p.x - p.X / 2, p.y - p.Y / 2), p.X, p.Y,
                                   boxstyle=f"round,pad=0,rounding_size={min(p.X, p.Y) / 2}")
        else:
            patch = Rectangle((p.x - p.X / 2, p.y - p.Y / 2), p.X, p.Y)
        if round(p.rot) % 90:
            patch = Rectangle((p.x - p.sx / 2, p.y - p.sy / 2), p.sx, p.sy)
            patch.set_transform(Affine2D().rotate_deg_around(p.x, p.y, p.rot) + ax.transData)
        patch.set_color("#ff2a2a" if "Bottom" not in p.layer else "#3060ff")
        patch.set_zorder(2)
        ax.add_patch(patch)
        if p.hole > 0:
            if p.htype == 2 and p.hw > 0:  # slot
                ax.add_patch(FancyBboxPatch((p.x - p.hw / 2, p.y - p.hole / 2), p.hw, p.hole, zorder=3,
                                            boxstyle=f"round,pad=0,rounding_size={min(p.hw, p.hole) / 2}",
                                            color="#202020"))
            else:
                ax.add_patch(Circle((p.x, p.y), p.hole / 2, color="#202020", zorder=3))
        fs = max(8, min(20, min(p.X, p.Y) * pt_per_mm * 0.55))
        ax.text(p.x, p.y, p.n, color="white", ha="center", va="center", fontsize=fs, zorder=6)
    for v in fp["vias"]:
        ax.add_patch(Circle((v["x"], v["y"]), v["d"] / 2, color="#c8a000", zorder=2))
        ax.add_patch(Circle((v["x"], v["y"]), v["hole"] / 2, color="#202020", zorder=3))
    style = dict(LAYER_STYLE)
    style[fp["assy"]] = ("#ff00ff", 4)
    for t in fp["tracks"]:
        c, z = style.get(t["layer"], ("#b0b0b0", 1))
        ax.plot([t["x1"], t["x2"]], [t["y1"], t["y2"]], color=c, lw=max(1.2, t["w"] * pt_per_mm),
                solid_capstyle="round", zorder=z, alpha=0.9)
    for a in fp["arcs"]:
        c, z = style.get(a["layer"], ("#b0b0b0", 1))
        ax.add_patch(Arc((a["x"], a["y"]), 2 * a["r"], 2 * a["r"], theta1=a["a0"], theta2=a["a1"], color=c,
                         lw=max(1.2, a["w"] * pt_per_mm), zorder=z))
    for b in fp["boxes"]:
        c, z = LAYER_STYLE.get(b["layer"], ("#ff2a2a", 2) if "Top Layer" in b["layer"] else ("#b0b0b0", 1))
        ax.add_patch(Rectangle((b["x0"], b["y0"]), b["x1"] - b["x0"], b["y1"] - b["y0"], fill=False, ec=c,
                               lw=1.2, ls="--", zorder=z))
    ax.plot(0, 0, marker="x", color="white", ms=14, mew=3, zorder=7)

    fs = spec.get("font", 15)

    def label(x, y, text, res, ha="center"):
        ax.text(x, y, text, ha=ha, va="center", fontsize=fs, zorder=8,
                bbox=dict(boxstyle="square,pad=0.25", fc=COL[res], ec="none"))

    for d in spec.get("dims", []):
        res = results.get(d["check"], "Check")
        (ax_, ay), (bx, by), at = d["a"], d["b"], d["at"] * u if d.get("u", True) else d["at"]
        ext = dict(color="#cfefff", lw=0.8, ls=":", zorder=4)
        arr = dict(arrowstyle="<->", color="#9ff", lw=1.6)
        if d["dir"] == "h":
            y = d.get("base", y1 if at > 0 else y0) + at
            ax.plot([ax_, ax_], [ay, y], **ext)
            ax.plot([bx, bx], [by, y], **ext)
            ax.annotate("", (ax_, y), (bx, y), arrowprops=arr, zorder=5)
            lx = d.get("lx", (ax_ + bx) / 2)
            label(lx, y + 0.45 * u * (1 if at > 0 else 1), d["text"], res)
        else:
            x = d.get("base", x1 if at > 0 else x0) + at
            ax.plot([ax_, x], [ay, ay], **ext)
            ax.plot([bx, x], [by, by], **ext)
            ax.annotate("", (x, ay), (x, by), arrowprops=arr, zorder=5)
            ly = d.get("ly", (ay + by) / 2)
            side = 1 if at > 0 else -1
            lx = d.get("lx", x + d["lx_u"] * u if "lx_u" in d else x + side * 0.25 * u)
            if abs(lx - x) > 0.3 * u:
                ax.plot([lx, x], [ly, (ay + by) / 2], **ext)
            label(lx, ly, d["text"], res, ha="left" if side > 0 else "right")
    ax.text(xlim[0] + 0.2 * u, ylim[1] - 0.45 * u, f"{spec['footprint']}   (top view, mm; label = footprint | datasheet)",
            color="white", fontsize=15, va="center")
    ax.text(xlim[0] + 0.2 * u, ylim[0] + 0.35 * u, "pads red · silk yellow · assembly magenta · courtyard green · "
            "× origin · label: green Pass, red Fail, orange Check", color="white", fontsize=11, va="center")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


# ---- symbol drawing -------------------------------------------------------------------------
DIRS = {0: (1, 0), 1: (0, 1), 2: (-1, 0), 3: (0, -1)}


def draw_symbol(name, s, out, part=1):
    pins = [p for p in s["pins"] if p["part"] in (0, part)]
    pts = [(p["x"], p["y"]) for p in pins] + [(p["x"] + DIRS[p["ori"]][0] * p["L"], p["y"] + DIRS[p["ori"]][1] * p["L"])
                                             for p in pins]
    for r in s["rects"] + s["lines"]:
        pts += [(r[0], r[1]), (r[2], r[3])]
    for pl in s["polys"]:
        pts += pl["pts"]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs) - 120, max(xs) + 120, min(ys) - 80, max(ys) + 200
    w_in = min(8, max(4, (x1 - x0) / 220))
    fig, ax = plt.subplots(figsize=(w_in, w_in * (y1 - y0) / (x1 - x0)), dpi=150)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.patch.set_facecolor("#fff8e7")
    fs = 13 if len(pins) < 20 else 10
    for r in s["rects"]:
        ax.add_patch(Rectangle((min(r[0], r[2]), min(r[1], r[3])), abs(r[2] - r[0]), abs(r[3] - r[1]),
                               fc="#ffffb0", ec="#800000", lw=2, zorder=1))
    for l in s["lines"]:
        ax.plot([l[0], l[2]], [l[1], l[3]], color="#00008b", lw=2, zorder=2)
    for pl in s["polys"]:
        xy = pl["pts"] + ([pl["pts"][0]] if pl["closed"] else [])
        ax.plot([p[0] for p in xy], [p[1] for p in xy], color="#00008b", lw=2, zorder=2)
        if pl["closed"]:
            ax.add_patch(Polygon(pl["pts"], closed=True, fc="#00008b", zorder=2))
    for a in s["arcs"]:
        ax.add_patch(Arc((a["x"], a["y"]), 2 * a["r"], 2 * a["r"], theta1=a["a0"], theta2=a["a1"], color="#00008b",
                         lw=2, zorder=2))
    for e in s["ells"]:
        ax.add_patch(Ellipse((e["x"], e["y"]), 2 * e["r"], 2 * e["r2"], fill=False, ec="#00008b", lw=2, zorder=2))
    for p in pins:
        dx, dy = DIRS[p["ori"]]
        ex, ey = p["x"] + dx * p["L"], p["y"] + dy * p["L"]
        ax.plot([p["x"], ex], [p["y"], ey], color="black", lw=2.2, zorder=3)
        mx, my = (p["x"] + ex) / 2, (p["y"] + ey) / 2
        if dy == 0:
            ax.text(mx, my + 15, p["n"], ha="center", va="bottom", fontsize=fs, zorder=4)
        else:
            ax.text(mx + 15, my, p["n"], ha="left", va="center", fontsize=fs, rotation=90, zorder=4)
        if p["show_name"] and s["rects"]:
            ha = {0: "right", 2: "left"}.get(p["ori"], "center")
            ax.text(p["x"] - dx * 18, p["y"] - dy * 18, p["name"], ha=ha, va="center", fontsize=fs,
                    rotation=90 if dy else 0, zorder=4)
        kind = ELEC.get(p["el"])
        if kind in ("Input", "Output", "IO"):
            sz = 22
            if kind == "IO":
                c = (p["x"] + dx * 40, p["y"] + dy * 40)
                poly = [(c[0] + dx * 30, c[1] + dy * 30), (c[0] - dy * sz, c[1] + dx * sz),
                        (c[0] - dx * 30, c[1] - dy * 30), (c[0] + dy * sz, c[1] - dx * sz)]
            else:
                tip, base = (0, 60) if kind == "Input" else (60, 0)
                t = (p["x"] + dx * tip, p["y"] + dy * tip)
                b = (p["x"] + dx * base, p["y"] + dy * base)
                poly = [t, (b[0] - dy * sz, b[1] + dx * sz), (b[0] + dy * sz, b[1] - dx * sz)]
            ax.add_patch(Polygon(poly, closed=True, fc="white", ec="black", lw=1.4, zorder=5))
    ax.text((x0 + x1) / 2, y1 - 70, name, ha="center", fontsize=12)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(out, facecolor=fig.get_facecolor(), pad_inches=0.05)
    plt.close(fig)


# ---- datasheet crops ------------------------------------------------------------------------
def crop(pdf, page, box, out, dpi=200):
    doc = pymupdf.open(DS_DIR / pdf)
    pg = doc[page - 1]
    r = pg.rect
    clip = pymupdf.Rect(r.x0 + box[0] * r.width, r.y0 + box[1] * r.height, r.x0 + box[2] * r.width,
                        r.y0 + box[3] * r.height)
    pg.get_pixmap(dpi=dpi, clip=clip).save(out)


def grid_page(pdf, page, out):
    """Page image with a 5 % grid so crop boxes can be read off as fractions."""
    doc = pymupdf.open(DS_DIR / pdf)
    pg = doc[page - 1]
    pix = pg.get_pixmap(dpi=100)
    pix.save(out)
    from PIL import Image, ImageDraw
    im = Image.open(out).convert("RGB")
    d = ImageDraw.Draw(im)
    for i in range(1, 20):
        c = (255, 0, 0) if i % 2 == 0 else (255, 170, 170)
        d.line([(im.width * i / 20, 0), (im.width * i / 20, im.height)], fill=c, width=1)
        d.line([(0, im.height * i / 20), (im.width, im.height * i / 20)], fill=c, width=1)
        if i % 2 == 0:
            d.text((im.width * i / 20 + 2, 2), f"{i * 5}", fill=(255, 0, 0))
            d.text((2, im.height * i / 20 + 2), f"{i * 5}", fill=(255, 0, 0))
    im.save(out)


# ---- checks ---------------------------------------------------------------------------------
def evaluate(spec, fp):
    P = {p["n"]: Pad(p) for p in fp["pads"]}
    def bbox(layer):
        """(width, height) of the tracks and arcs on a layer, e.g. 'Mechanical Layer 13'."""
        xs = [t[k] for t in fp["tracks"] if t["layer"] == layer for k in ("x1", "x2")]
        ys = [t[k] for t in fp["tracks"] if t["layer"] == layer for k in ("y1", "y2")]
        for a in fp["arcs"]:
            if a["layer"] == layer:
                xs += [a["x"] - a["r"], a["x"] + a["r"]]
                ys += [a["y"] - a["r"], a["y"] + a["r"]]
        return (max(xs) - min(xs), max(ys) - min(ys)) if xs else (float("nan"), float("nan"))

    env = {"P": P, "pads": list(P.values()), "abs": abs, "min": min, "max": max, "round": round, "math": math,
           "bbox": bbox, "chr": chr, "ASSY": fp["assy"], "CRT": "Mechanical Layer 15"}
    rows, results = [], {}
    for c in spec["checks"]:
        if "fp" in c:
            val = eval(c["fp"], env)
            ds = c["ds"]
            if isinstance(val, float) and math.isnan(val):  # layer missing in this footprint
                rows.append((c["label"], c.get("ds_text", f"{c.get('sym', '')} {ds_text(ds)}"),
                             "no outline on this layer", "–", "–", "Check"))
                results[c["label"]] = "Check"
                continue
            if isinstance(ds, dict) and "min" in ds:  # minimum only
                res = "Pass" if val >= ds["min"] - 1e-9 else "Fail"
                row = (c["label"], f"{c['sym']} ≥{ds['min']:.3f} (min.)", f"{val:.3f}", "above min" if res == "Pass"
                       else "below min", "min.", res)
            elif isinstance(ds, dict):  # maximum only
                res = "Pass" if val <= ds["max"] + 1e-9 else "Fail"
                row = (c["label"], f"{c['sym']} ≤{ds['max']:.3f} (max.)", f"{val:.3f}", "below max" if res == "Pass"
                       else "above max", "max.", res)
            elif isinstance(ds, list):  # min to max range
                res = "Pass" if ds[0] - 1e-9 <= val <= ds[1] + 1e-9 else "Fail"
                row = (c["label"], f"{c['sym']} {ds[0]:.2f}–{ds[1]:.2f}", f"{val:.3f}", "in range" if res == "Pass"
                       else "outside", "range", res)
            elif ds is None:
                res = c.get("result", "Check")
                row = (c["label"], c.get("ds_text", "not given"), f"{val:.3f}", "–", "–", res)
            else:
                tol = TOL[c["tol"]] if isinstance(c["tol"], str) else c["tol"]
                diff = round(val - ds, 3) + 0.0
                res = "Pass" if abs(diff) <= tol + 1e-9 else "Fail"
                row = (c["label"], f"{c['sym']} {ds:.3f}", f"{val:.3f}", f"{diff:+.3f}", f"±{tol:.2f}", res)
        else:
            res = c["result"]
            row = (c["label"], c["ds_text"], c["fp_text"], c.get("diff", "–"), c.get("tol_text", "–"), res)
        if "fp2" in c:
            row = row[:2] + (row[2] + f" × {eval(c['fp2'], env):.3f}",) + row[3:]
        if "note" in c:
            row = row[:2] + (row[2] + " (" + c["note"] + ")",) + row[3:]
        rows.append(row)
        results[c["label"]] = res
    return rows, results


# ---- document -------------------------------------------------------------------------------
def shade(cell, hex_fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill.lstrip("#"))
    tcpr.append(shd)


def picture(container, path, width_mm, cap, new_page=False):
    p = container.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = new_page
    p.add_run().add_picture(str(path), width=Mm(width_mm))
    c = container.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = c.add_run(cap)
    r.italic = True
    r.font.size = Pt(9)


def ds_text(ds):
    if ds is None:
        return "–"
    if isinstance(ds, dict):
        return f"≥{ds['min']:.2f}" if "min" in ds else f"≤{ds['max']:.2f}"
    return f"{ds[0]:.2f}–{ds[1]:.2f}" if isinstance(ds, list) else f"{ds:.3f}"


def chip2(spec, fp):
    """Checks and dimension arrows for a two-terminal part from DS values only.

    spec["chip2"] = {"L": [sym, ds], "W": [sym, ds], "G": [sym, ds], "Z": [sym, ds], "C": [sym, ds],
                     "bodyL": [sym, [min, max]], "bodyW": [sym, [min, max]]}; any key may be left out.
    L = pad length along the part axis, W = pad width across it, G = gap, Z = outer span, C = centre to centre.
    A DS value may be a number or a [min, max] range.
    """
    c = spec["chip2"]
    P = {p["n"]: Pad(p) for p in fp["pads"]}
    k1, k2 = spec.get("chip2_pads", ["1", "2"])
    a, b = sorted((P[k1], P[k2]), key=lambda p: (p.x, p.y))
    along_x = abs(b.x - a.x) >= abs(b.y - a.y)
    if not along_x:
        a, b = sorted((P[k1], P[k2]), key=lambda p: p.y)
    n1, n2 = f"P['{a.n}']", f"P['{b.n}']"
    if along_x:
        expr = {"L": f"{n1}.X", "W": f"{n1}.Y", "G": f"{n2}.l - {n1}.r", "Z": f"{n2}.r - {n1}.l",
                "C": f"{n2}.x - {n1}.x", "bodyL": "bbox(ASSY)[0]", "bodyW": "bbox(ASSY)[1]"}
    else:
        expr = {"L": f"{n1}.Y", "W": f"{n1}.X", "G": f"{n2}.b - {n1}.t", "Z": f"{n2}.t - {n1}.b",
                "C": f"{n2}.y - {n1}.y", "bodyL": "bbox(ASSY)[1]", "bodyW": "bbox(ASSY)[0]"}
    names = {"L": "Pad length", "W": "Pad width", "G": "Gap", "Z": "Outer span", "C": "Pad centre to centre",
             "bodyL": "Body length (assembly)", "bodyW": "Body width (assembly)"}
    tols = {"L": "pad", "W": "pad", "G": "span", "Z": "span", "C": "row"}
    checks = [{"label": "Pin count", "ds_text": spec.get("pins_ds", "2"), "fp_text": "2 pads, 2 symbol pins",
               "result": "Pass"}]
    checks += spec.get("checks_pre", [])
    env = {"P": P}
    dims = []
    for k in ("L", "W", "G", "Z", "C", "bodyL", "bodyW"):
        if k not in c:
            continue
        sym, ds = c[k]
        ck = {"label": names[k], "sym": sym, "ds": ds, "fp": expr[k]}
        if ds is None:
            ck["ds_text"] = spec.get("no_land_text", "not in the datasheet")
        if k in tols:
            ck["tol"] = tols[k]
        checks.append(ck)
        if k.startswith("body"):
            continue
        val = eval(expr[k], env)
        text = f"{sym} {names[k].lower()} {val:.3f} | DS {ds_text(ds)}"
        ends = {"L": (a.l, a.r) if along_x else (a.b, a.t), "G": (a.r, b.l) if along_x else (a.t, b.b),
                "Z": (a.l, b.r) if along_x else (a.b, b.t), "C": (a.x, b.x) if along_x else (a.y, b.y),
                "W": (b.b, b.t) if along_x else (b.l, b.r)}[k]
        at = {"L": -1.3, "G": -2.6, "Z": -3.9, "C": 1.3, "W": 1.2}[k]
        if along_x:
            if k == "W":
                dims.append({"check": names[k], "dir": "v", "a": [b.r, ends[0]], "b": [b.r, ends[1]], "at": at,
                             "text": text})
            else:
                yref = a.b if at < 0 else a.t
                dims.append({"check": names[k], "dir": "h", "a": [ends[0], yref], "b": [ends[1], yref], "at": at,
                             "text": text})
        elif k == "W":
            dims.append({"check": names[k], "dir": "h", "a": [ends[0], b.t], "b": [ends[1], b.t], "at": at,
                         "text": text})
        else:
            xref = a.l if at < 0 else a.r
            dims.append({"check": names[k], "dir": "v", "a": [xref, ends[0]], "b": [xref, ends[1]], "at": at,
                         "text": text})
    checks.append({"label": "Courtyard", "ds": None, "ds_text": "rule open", "fp": "bbox(CRT)[0]",
                   "fp2": "bbox(CRT)[1]"})
    checks.append({"label": "Paste / mask", "ds_text": "rule open", "fp_text": "from board rules", "result": "Check"})
    checks += spec.get("checks_post", [])
    spec["checks"] = checks
    spec["dims"] = dims + spec.get("dims", [])
    spec.setdefault("margin", {"l": 3, "r": 10, "t": 4.5, "b": 6.5} if along_x else {"l": 10, "r": 10, "t": 3, "b": 3})


def autorows(spec, fp, sym_pins):
    """Checks and arrows for parts with pads in rows (SOT, SOIC, TSSOP, QFN, modules) from DS values only.

    spec["auto"] = {"rows": "lr" | "tb" | "quad", "skip": [pad names left out of the rows (EP, tabs, mounting)],
                    "L": [sym, ds] pad length, "W": [sym, ds] pad width, "P": [sym, ds] pitch,
                    "C": [sym, ds] row C-C (left-right), "C2": [sym, ds] row C-C (top-bottom, quad),
                    "Z": [sym, ds] outer span, "G": [sym, ds] inner gap,
                    "EP": {"pad": name, "X": [sym, ds], "Y": [sym, ds]},
                    "bodyX": [sym, [min, max]], "bodyY": [sym, [min, max]]}
    A DS value may be a number, a [min, max] range or {"min": v}; null means not given (Check).
    """
    a = spec["auto"]
    P = {p["n"]: Pad(p) for p in fp["pads"]}
    skip = set(a.get("skip", []))
    sig = [p for n, p in P.items() if n not in skip]
    mode = a.get("rows", "lr")
    if mode == "tb":
        lo = sorted([p for p in sig if p.y < 0], key=lambda p: p.x)
        hi = sorted([p for p in sig if p.y > 0], key=lambda p: p.x)
    else:
        if mode == "quad":  # side pads: the pads that sit beyond the corner diagonal
            side = [p for p in sig if abs(p.x) >= abs(p.y)]
        else:
            side = sig
        lo = sorted([p for p in side if p.x < 0], key=lambda p: -p.y)
        hi = sorted([p for p in side if p.x > 0], key=lambda p: -p.y)
    if mode == "quad":
        top = [p for p in sig if abs(p.y) > abs(p.x) and p.y > 0]
        bot = [p for p in sig if abs(p.y) > abs(p.x) and p.y < 0]
    r0 = f"P['{lo[0].n}']"
    r1 = f"P['{lo[1].n}']" if len(lo) > 1 else None
    h0 = f"P['{hi[0].n}']" if hi else None
    vert = mode == "tb"  # rows run along x
    ax_len, ax_wid = ("Y", "X") if vert else ("X", "Y")
    expr = {"L": f"{r0}.{ax_len}", "W": f"{r0}.{ax_wid}"}
    if r1:
        expr["P"] = f"abs({r1}.x - {r0}.x)" if vert else f"abs({r0}.y - {r1}.y)"
        expr["P_all"] = (f"abs(P['{lo[-1].n}'].x - {r0}.x)" if vert else f"abs({r0}.y - P['{lo[-1].n}'].y)")
    if h0:
        expr["C"] = f"{h0}.y - {r0}.y" if vert else f"{h0}.x - {r0}.x"
        expr["Z"] = f"{h0}.t - {r0}.b" if vert else f"{h0}.r - {r0}.l"
        expr["G"] = f"{h0}.b - {r0}.t" if vert else f"{h0}.l - {r0}.r"
    if mode == "quad" and top and bot:
        expr["C2"] = f"P['{top[0].n}'].y - P['{bot[0].n}'].y"
    names = {"L": "Pad length", "W": "Pad width", "P": "Pitch", "C": "Row spacing (C-C)", "C2": "Row spacing top-bottom (C-C)",
             "Z": "Outer land span", "G": "Inner gap"}
    tols = {"L": "pad", "W": "pad", "P": "pitch", "C": "row", "C2": "row", "Z": "span", "G": "span"}
    # pins of the symbol against the pads
    pads = set(P)
    pins = {p["n"] for p in sym_pins}
    miss = sorted(pins - pads)
    extra = sorted(pads - pins)
    first = P.get("1")
    where = ""
    if first:
        where = ("top" if first.y > 0.01 else "bottom" if first.y < -0.01 else "middle") + "-" + \
                ("left" if first.x < -0.01 else "right" if first.x > 0.01 else "centre")
    checks = [{"label": "Pin count", "ds_text": a.get("pins_ds", str(len(pads))),
               "fp_text": f"{len(pads)} pads, {len(pins)} symbol pins",
               "result": "Pass" if not miss and not extra else "Check"},
              {"label": "Pin numbers symbol = pads", "ds_text": "every symbol pin has a pad",
               "fp_text": "all match" if not miss and not extra else
               f"pins without pad: {', '.join(miss) or '–'}; pads without pin: {', '.join(extra) or '–'}",
               "result": "Pass" if not miss and not extra else "Check"},
              {"label": "Orientation", "ds_text": a.get("pin1_ds", "pin 1 position per datasheet"),
               "fp_text": f"pad 1 at {where}", "result": a.get("pin1_result", "Pass")}]
    checks += spec.get("checks_pre", [])
    dims = []
    lab = {}
    for k in ("L", "W", "P", "C", "C2", "Z", "G"):
        if k not in a or k not in expr:
            continue
        sym, ds = a[k]
        ck = {"label": names[k], "sym": sym, "ds": ds, "fp": expr[k], "tol": tols[k]}
        if ds is None:
            ck["ds_text"] = "not in the datasheet"
        checks.append(ck)
        if k == "P" and "P_all" in expr and len(lo) > 2:
            n = len(lo) - 1
            tot = ds * n if isinstance(ds, (int, float)) else None
            checks.append({"label": f"Total pitch ({n} × P)", "sym": f"{n}×{sym}", "ds": tot, "fp": expr["P_all"],
                           "tol": "pitch", **({"ds_text": "–"} if tot is None else {})})
        lab[k] = (f"{sym} " if sym not in ("", "–") else "") + f"{names[k].split(' (')[0].lower()} " + "{v:.3f} | DS " + ds_text(ds)
    if "EP" in a:
        e = a["EP"]
        for ax, k in (("X", "X"), ("Y", "Y")):
            if ax in e:
                sym, ds = e[ax]
                checks.append({"label": f"Exposed pad {ax}", "sym": sym, "ds": ds, "fp": f"P['{e['pad']}'].{k}",
                               "tol": "pad", **({"ds_text": "not in the datasheet"} if ds is None else {})})
    for k, axn in (("bodyX", 0), ("bodyY", 1)):
        if k in a:
            sym, ds = a[k]
            checks.append({"label": f"Body {'X' if axn == 0 else 'Y'} (assembly)", "sym": sym, "ds": ds,
                           "fp": f"bbox(ASSY)[{axn}]"})
    checks.append({"label": "Courtyard", "ds": None, "ds_text": "rule open", "fp": "bbox(CRT)[0]",
                   "fp2": "bbox(CRT)[1]"})
    checks.append({"label": "Paste / mask", "ds_text": "rule open", "fp_text": "from board rules", "result": "Check"})
    checks += spec.get("checks_post", [])
    env = {"P": P, "abs": abs}

    def v(k):
        return eval(expr[k], env)

    # arrows: pad length and outer span below the parts, row C-C above, pitch and width at the left
    p0 = lo[-1]  # bottom (or right-most) pad of the first row
    if not vert:
        if "L" in lab:
            dims.append({"check": names["L"], "dir": "h", "a": [p0.l, p0.b], "b": [p0.r, p0.b], "at": -1.2,
                         "text": lab["L"].format(v=v("L"))})
        if "Z" in lab:
            dims.append({"check": names["Z"], "dir": "h", "a": [p0.l, p0.b], "b": [hi[-1].r, p0.b], "at": -2.4,
                         "text": lab["Z"].format(v=v("Z"))})
        if "C" in lab:
            dims.append({"check": names["C"], "dir": "h", "a": [lo[0].x, lo[0].t], "b": [hi[0].x, lo[0].t],
                         "at": 1.2, "text": lab["C"].format(v=v("C"))})
        if "G" in lab:
            dims.append({"check": names["G"], "dir": "h", "a": [lo[0].r, lo[0].t], "b": [hi[0].l, lo[0].t],
                         "at": 2.4, "text": lab["G"].format(v=v("G"))})
        if "P" in lab:
            dims.append({"check": names["P"], "dir": "v", "a": [lo[0].l, lo[0].y], "b": [lo[1].l, lo[1].y],
                         "at": -0.4, "lx_u": -1.4, "text": lab["P"].format(v=v("P"))})
        if "W" in lab:
            dims.append({"check": names["W"], "dir": "v", "a": [p0.l, p0.t], "b": [p0.l, p0.b], "at": -0.4,
                         "lx_u": -1.4, "text": lab["W"].format(v=v("W"))})
    else:
        if "L" in lab:
            dims.append({"check": names["L"], "dir": "v", "a": [lo[0].l, lo[0].b], "b": [lo[0].l, lo[0].t],
                         "at": -1.2, "text": lab["L"].format(v=v("L"))})
        if "Z" in lab:
            dims.append({"check": names["Z"], "dir": "v", "a": [lo[0].l, lo[0].b], "b": [lo[0].l, hi[0].t],
                         "at": -2.6, "text": lab["Z"].format(v=v("Z"))})
        if "C" in lab:
            dims.append({"check": names["C"], "dir": "v", "a": [hi[-1].r, lo[-1].y], "b": [hi[-1].r, hi[-1].y],
                         "at": 1.2, "text": lab["C"].format(v=v("C"))})
        if "P" in lab:
            dims.append({"check": names["P"], "dir": "h", "a": [lo[0].x, lo[0].b], "b": [lo[1].x, lo[1].b],
                         "at": -1.2, "text": lab["P"].format(v=v("P"))})
        if "W" in lab:
            dims.append({"check": names["W"], "dir": "h", "a": [lo[-1].l, lo[-1].b], "b": [lo[-1].r, lo[-1].b],
                         "at": -2.4, "text": lab["W"].format(v=v("W"))})
    spec["checks"] = checks
    spec["dims"] = dims + spec.get("dims", [])
    spec.setdefault("margin", {"l": 6.5, "r": 2.5, "t": 3, "b": 3.6} if not vert else {"l": 7, "r": 7, "t": 2.5, "b": 3.5})


def pad_dims(spec, fp, rows):
    """Arrows from spec["pdims"] = [[check label, kind, pad a, pad b], ...]; text from the evaluated check row.

    kind: cx / cy centre to centre, ex / ey outer edge to outer edge, px / py size of pad a, hx hole of pad a.
    """
    P = {p["n"]: Pad(p) for p in fp["pads"]}
    byl = {r[0]: r for r in rows}
    out = []
    allp = list(P.values())
    gl, gr = min(p.l for p in allp), max(p.r for p in allp)
    gb, gt = min(p.b for p in allp), max(p.t for p in allp)
    nh = nv = 0
    for lab, kind, a, b in spec.get("pdims", []):
        A, B = P[a], P[b or a]
        r = byl.get(lab)
        text = f"{lab.lower()} {r[2]} | DS {r[1].strip() or '-'}" if r else lab
        if kind in ("cx", "ex", "px", "hx"):
            x1, x2 = {"cx": (A.x, B.x), "ex": (min(A.l, B.l), max(A.r, B.r)), "px": (A.l, A.r),
                      "hx": (A.x - A.hole / 2, A.x + A.hole / 2)}[kind]
            top = nh % 2 == 0
            off = 0.9 + 1.0 * (nh // 2)
            nh += 1
            yref = gt if top else gb
            out.append({"check": lab, "dir": "h", "a": [x1, yref], "b": [x2, yref], "at": off if top else -off,
                        "base": yref, "u": True, "text": text})
        else:
            y1, y2 = {"cy": (A.y, B.y), "ey": (min(A.b, B.b), max(A.t, B.t)), "py": (A.b, A.t)}[kind]
            right = nv % 2 == 0
            off = 0.9 + 1.0 * (nv // 2)
            nv += 1
            xref = gr if right else gl
            out.append({"check": lab, "dir": "v", "a": [xref, y1], "b": [xref, y2], "at": off if right else -off,
                        "base": xref, "u": True, "text": text})
    return out


def generic_dims(fp):
    """Overall land spans, pad 1 size and the pitch to the nearest pad, for parts without datasheet values."""
    pads = [Pad(p) for p in fp["pads"]]
    if not pads:
        return []
    l, r = min(p.l for p in pads), max(p.r for p in pads)
    b, t = min(p.b for p in pads), max(p.t for p in pads)
    d = [{"check": "x", "dir": "h", "a": [l, b], "b": [r, b], "at": -1.5, "base": b, "text": f"land span X {r - l:.3f} | DS –"},
         {"check": "x", "dir": "v", "a": [r, b], "b": [r, t], "at": 1.5, "base": r, "text": f"land span Y {t - b:.3f} | DS –"}]
    p1 = next((p for p in pads if p.n == "1"), pads[0])
    d.append({"check": "x", "dir": "h", "a": [p1.l, t], "b": [p1.r, t], "at": 0.8, "base": t,
              "text": f"pad {p1.n} {p1.X:.3f} × {p1.Y:.3f} | DS –"})
    if len(pads) > 1:
        q = min((p for p in pads if p is not p1), key=lambda p: (p.x - p1.x) ** 2 + (p.y - p1.y) ** 2)
        d.append({"check": "x", "dir": "h", "a": [p1.x, b], "b": [q.x, b], "at": -3.0, "base": b,
                  "text": f"pad {p1.n}-{q.n} C-C {((q.x - p1.x) ** 2 + (q.y - p1.y) ** 2) ** 0.5:.3f} | DS –"})
    return d


def build(name, pcb, sch, fpsum, doc=None, first=True):
    spec = json.loads((HERE / "specs" / f"{name}.json").read_text(encoding="utf-8-sig"))
    spec["footprint"] = name
    fp = pcb[name]
    comps = [k for k, v in fpsum.items() if v["footprint"] == name]
    if "chip2" in spec:
        chip2(spec, fp)
    if "auto" in spec:
        autorows(spec, fp, sch[comps[0]]["pins"] if comps and comps[0] in sch else [])
    out = HERE / name
    out.mkdir(exist_ok=True)
    rows, results = evaluate(spec, fp)
    spec["dims"] = spec.get("dims", []) + pad_dims(spec, fp, rows)
    if not spec["dims"]:
        spec["dims"] = generic_dims(fp)
        spec.setdefault("margin", {"l": 3, "r": 4, "t": 2.5, "b": 4})
    results.setdefault("x", "Check")
    draw_footprint(fp, spec, results, out / "dims.png")
    ds = spec["datasheet"]
    for key, c in spec["crops"].items():
        crop(c.get("pdf", ds["pdf"]), c["page"], c["box"], out / f"ds_{key}.png")
    for i, c in enumerate(spec.get("extra_crops", [])):
        crop(c.get("pdf", ds["pdf"]), c["page"], c["box"], out / f"ds_extra{i}.png")

    single = doc is None
    if single:
        doc = new_doc()
    mpns = ", ".join(sorted({fpsum[k]["mpn"] for k in comps}))
    h = doc.add_heading(f"{name}  ·  {mpns} ({spec['package']})", level=1)
    h.paragraph_format.page_break_before = not first
    p = doc.add_paragraph()
    p.add_run("Used by: ").bold = True
    p.add_run(", ".join(f"{k} ({fpsum[k]['mpn']})" if fpsum[k]["mpn"] != k else k for k in comps) + ".  ")
    p.add_run("Datasheet: ").bold = True
    p.add_run(ds["title"] + ".  ")
    for k in comps:  # local file and online link per component (hybrid setup)
        row = DSIDX.get(k, {})
        q = doc.add_paragraph(style="List Bullet")
        q.add_run(f"{k}" + (f" ({fpsum[k]['mpn']})" if fpsum[k]["mpn"] and fpsum[k]["mpn"] != k else "") + ": ")
        if row.get("Datasheet file"):
            q.add_run("local ")
            hyperlink(q, f"../{DS_DIR.name}/{row['Datasheet file']}", row["Datasheet file"])
        else:
            q.add_run("local: not found").bold = True
        q.add_run("  ·  online ")
        if row.get("URL"):
            hyperlink(q, row["URL"], row["URL"])
        else:
            q.add_run("not found").bold = True
    for e in spec.get("extra_docs", []):
        q = doc.add_paragraph(style="List Bullet")
        q.add_run(e["label"] + ": local ")
        hyperlink(q, f"../{DS_DIR.name}/{e['local']}", e["local"])
        q.add_run("  ·  online ")
        hyperlink(q, e["url"], e["url"])
    p = doc.add_paragraph()
    p.add_run("Tolerances: ").bold = True
    p.add_run("±0.01 mm on every dimension (LIB-33); a datasheet range passes inside its min to max; "
              "courtyard and paste/mask rules open.")
    worst = "FAIL" if "Fail" in results.values() else "CHECK" if "Check" in results.values() else "PASS"
    p = doc.add_paragraph()
    r = p.add_run(f"Result: {worst}")
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = {"FAIL": RGBColor(0xC0, 0, 0), "CHECK": RGBColor(0xC0, 0x70, 0),
                        "PASS": RGBColor(0, 0x80, 0)}[worst]
    bad = [k.lower() for k, v in results.items() if v == "Fail"]
    if bad:
        p.add_run("  (" + ", ".join(bad) + ")")

    doc.add_heading("1. Pins", level=2)
    syms = []
    for k in comps:
        if k in sch:
            draw_symbol(f"{k} ({fpsum[k]['mpn']})" if fpsum[k]["mpn"] and fpsum[k]["mpn"] != k else k, sch[k], out / f"symbol_{len(syms)}.png")
            syms.append((k, out / f"symbol_{len(syms)}.png"))
    if "pinout" in spec["crops"]:
        t = doc.add_table(rows=1, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        picture(t.cell(0, 0), out / "ds_pinout.png", spec["crops"]["pinout"].get("w", 70),
                spec["crops"]["pinout"]["cap"])
        k, img = syms[0]
        picture(t.cell(0, 1), img, 85, f"Symbol {k} ({fpsum[k]['mpn']}) drawn from {LIBNAME}.SchLib data")
        rest = syms[1:]
    else:
        rest = syms
    for k, img in rest:
        picture(doc, img, 70, f"Symbol {k} ({fpsum[k]['mpn']}) drawn from {LIBNAME}.SchLib data")
    if "ordering" in spec["crops"]:
        c = spec["crops"]["ordering"]
        picture(doc, out / "ds_ordering.png", c.get("w", 120), c["cap"])
    doc.add_paragraph(spec["pin_note"])

    doc.add_heading("2. Footprint", level=2)
    if "outline" in spec["crops"]:
        c = spec["crops"]["outline"]
        picture(doc, out / "ds_outline.png", c.get("w", 150), c["cap"])
    for i, c in enumerate(spec.get("extra_crops", [])):
        picture(doc, out / f"ds_extra{i}.png", c.get("w", 150), c["cap"], new_page=c.get("new_page", False))
    if "outline" not in spec["crops"] and "land" not in spec["crops"] and not spec.get("extra_crops"):
        missing(doc, "Package drawing: " + spec.get("missing_outline", "not in the datasheet available in the folder"))
    if "land" in spec["crops"]:
        c = spec["crops"]["land"]
        picture(doc, out / "ds_land.png", c.get("w", 170), c["cap"], new_page=True)
    else:
        missing(doc, "Land pattern: " + spec.get("missing_land", "not given in the datasheet available in the folder; "
                "the footprint values are shown for the reviewer"), new_page=True)
    picture(doc, out / "dims.png", spec.get("dims_w", 182), f"{name} drawn from {LIBNAME}.PcbLib data "
            "(exact pad, silk, assembly and courtyard coordinates).")

    doc.add_heading("3. Check", level=2).paragraph_format.page_break_before = True
    t = doc.add_table(rows=1, cols=6)
    t.style = "Table Grid"
    t.autofit = False
    for c, h in zip(t.rows[0].cells, ("Check", "Datasheet", "Footprint", "Diff", "Tol", "Result")):
        c.text = ""
        c.paragraphs[0].add_run(h).bold = True
        shade(c, "#D9D9D9")
    for row in rows:
        cells = t.add_row().cells
        for c, v in zip(cells, row):
            c.text = v
        shade(cells[5], COL[row[5]])
        cells[5].paragraphs[0].runs[0].bold = True
    for col, w in zip(t.columns, (36, 44, 44, 20, 16, 22)):
        col.width = Mm(w)
        for c in col.cells:
            c.width = Mm(w)
    if spec.get("note"):
        doc.add_paragraph(spec["note"])
    doc.add_paragraph()
    for n in (1, 2):
        doc.add_paragraph(f"Reviewer {n}: ____________________   Date: ____________   OK / Not OK   "
                          "Comment: ______________________________")
    if single:
        doc.save(out / f"{name}_review.docx")
    return worst, rows


def new_doc():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Mm(14))
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10)
    return doc


def missing(doc, text, new_page=False):
    """A shaded one-cell box that says which datasheet picture is missing."""
    if new_page:
        doc.add_paragraph().paragraph_format.page_break_before = True
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    c = t.cell(0, 0)
    c.text = ""
    r = c.paragraphs[0].add_run(text)
    r.bold = True
    shade(c, "#FFE7B3")


def to_pdf(paths):
    import win32com.client  # noqa: PLC0415
    w = win32com.client.Dispatch("Word.Application")
    w.Visible = False
    try:
        for p in paths:
            d = w.Documents.Open(str(p), False, True)
            d.ExportAsFixedFormat(str(p.with_suffix(".pdf")), 17)
            d.Close(0)
    finally:
        w.Quit()


def contact_sheet(pdf, out, pages=None, cols=5):
    """Thumbnails of a datasheet's pages, numbered, to find the land and outline pages at a glance."""
    from PIL import Image, ImageDraw
    doc = pymupdf.open(DS_DIR / pdf)
    pages = pages or list(range(1, doc.page_count + 1))
    thumbs = []
    for n in pages:
        pix = doc[n - 1].get_pixmap(dpi=36)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        ImageDraw.Draw(im).text((4, 4), f"p{n}", fill=(255, 0, 0))
        thumbs.append(im)
    w, h = max(t.width for t in thumbs), max(t.height for t in thumbs)
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (w * cols, h * rows), "white")
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % cols) * w, (i // cols) * h))
    sheet.save(out)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    folder, library = ".", None
    for opt in ("--dir", "--library"):
        if opt in args:
            i = args.index(opt)
            if opt == "--dir":
                folder = args[i + 1]
            else:
                library = args[i + 1]
            del args[i:i + 2]
    if MISSING:
        print(f"fp_review needs {MISSING}: pip install matplotlib pymupdf python-docx")
        return 2
    configure(folder, library)
    if args and args[0] == "--sheet":
        out = HERE / "_pages" / f"{Path(args[1]).stem}_sheet.png"
        out.parent.mkdir(exist_ok=True)
        contact_sheet(args[1], out, [int(x) for x in args[2:]] or None)
        print(out)
        return 0
    if args and args[0] == "--page":
        out = HERE / "_pages" / f"{Path(args[1]).stem}_p{args[2]}.png"
        out.parent.mkdir(exist_ok=True)
        grid_page(args[1], int(args[2]), out)
        print(out)
        return 0
    pcb, sch = load_pcb(), load_sch()
    fpsum = load_fpsum()
    every = args == ["--all"]
    names = sorted(p.stem for p in (HERE / "specs").glob("*.json")) if every else args
    index = []
    doc = summary = None
    if every:
        doc = new_doc()
        doc.add_heading(f"{LIBNAME} footprint review", level=0)
        p = doc.add_paragraph()
        p.add_run("One section per footprint, in the order of the table below (LIB-33). ").bold = True
        p.add_run("Each section has the datasheet pin, outline and land-pattern pictures with page captions, the symbol "
                  f"and footprint drawn from {LIBNAME}.SchLib / .PcbLib, and a check table. Tolerance ±0.01 mm on "
                  "every dimension; a datasheet range passes inside its min to max; courtyard and paste/mask rules are "
                  "open (Check). Drawing labels read footprint value | datasheet value, coloured green Pass, red Fail, "
                  "orange Check. Datasheet links: local files in ../" + DS_DIR.name + " (this folder sits next to it) "
                  "and the maker's online link.")
        doc.add_heading("Datasheets to source", level=2)
        need = [(k, r.get("MPN") or fpsum.get(k, {}).get("mpn", ""), r.get("Manufacturer", ""), "datasheet not found")
                for k, r in DSIDX.items() if not r.get("Datasheet file")]
        for n in names:
            s = json.loads((HERE / "specs" / f"{n}.json").read_text(encoding="utf-8-sig"))
            for k, mpn, mfr, what in s.get("to_source", []):
                need.append((k, mpn, mfr, what))
        t = doc.add_table(rows=1, cols=4)
        t.style = "Table Grid"
        for c, h in zip(t.rows[0].cells, ("Component", "Manufacturer part number", "Manufacturer", "Missing")):
            c.text = ""
            c.paragraphs[0].add_run(h).bold = True
            shade(c, "#D9D9D9")
        for row in need:
            for c, v in zip(t.add_row().cells, row):
                c.text = v or "unknown"
        doc.add_heading("Footprints", level=2)
        summary = doc.add_table(rows=1, cols=5)
        summary.style = "Table Grid"
        for c, h in zip(summary.rows[0].cells, ("#", "Footprint", "Components (MPN)", "Result", "Decision (Edit / Keep)")):
            c.text = ""
            c.paragraphs[0].add_run(h).bold = True
            shade(c, "#D9D9D9")
    for i, n in enumerate(names):
        worst, rows = build(n, pcb, sch, fpsum, doc, first=False) if every else build(n, pcb, sch, fpsum)
        index.append((n, worst, rows))
        print(n, worst)
        for r in rows:
            print("   ", " | ".join(r))
    if every:
        for i, (n, worst, rows) in enumerate(index, 1):
            comps = "; ".join(f"{k} ({v['mpn']})" if v["mpn"] != k else k
                              for k, v in fpsum.items() if v["footprint"] == n)
            cells = summary.add_row().cells
            for c, v in zip(cells, (str(i), n, comps, worst, "")):
                c.text = v
            shade(cells[3], COL[worst.title()])
        for col, w in zip(summary.columns, (10, 52, 70, 18, 32)):
            for c in col.cells:
                c.width = Mm(w)
        OUT_ALL.mkdir(exist_ok=True)
        path = OUT_ALL / f"{LIBNAME}_footprint_review.docx"
        doc.save(path)
        import csv
        with open(OUT_ALL / "index.csv", "w", newline="", encoding="utf-8-sig") as fh:
            wr = csv.writer(fh)
            wr.writerow(["Footprint", "Components (MPN)", "Result", "Fails", "Checks", "Failed items",
                         "Decision (Edit / Keep)", "Reviewed by", "Date"])
            for n, worst, rows in index:
                comps = "; ".join(f"{k} ({v['mpn']})" for k, v in fpsum.items() if v["footprint"] == n)
                wr.writerow([n, comps, worst, sum(r[5] == "Fail" for r in rows), sum(r[5] == "Check" for r in rows),
                             "; ".join(r[0] for r in rows if r[5] == "Fail"), "", "", ""])
        paths = [path]
    else:
        paths = [HERE / n / f"{n}_review.docx" for n in names]
    try:
        to_pdf(paths)
    except Exception as e:  # Word missing: the .docx files are still complete
        print("PDF export skipped:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
