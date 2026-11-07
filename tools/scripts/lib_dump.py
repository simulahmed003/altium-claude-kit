"""lib_dump.py - read the geometry of a .PcbLib / .SchLib offline (no Altium) for review documents and checks.

Usage:
  python lib_dump.py <lib.PcbLib> [<lib.SchLib>] --out <folder>
      writes <folder>\\_pcblib_dump.txt, _schlib_dump.txt and fpsum.json (the inputs of fp_review.py)
  python lib_dump.py <lib.PcbLib> --footprint <name>      print one footprint (pads, tracks, arcs) in mm
  python lib_dump.py <lib.SchLib> --symbol <name>         print one symbol (pins, graphics) in mil

Dump format (one record per line, "|" separated; PCB in mm from the footprint origin, SCH in mil):
  FP|name                                   PAD|designator|x|y|size x|size y|shape|rotation|hole|hole type|slot|layer
  TRK|x1|y1|x2|y2|width|layer               ARC|x|y|radius|start deg|end deg|width|layer
  VIA|x|y|diameter|hole                     BOX|0|x0|y0|x1|y1|layer            (fills)
  SYM|name|description                      PIN|designator|name|electrical|orientation|x|y|length|show name|-|part
  RECT|x1|y1|x2|y2   LINE|x1|y1|x2|y2       PL|15 (polygon) or 6 (polyline)|-|x,y|x,y...
  ARC|x|y|radius|start deg|end deg          ELL|x|y|radius|second radius
fpsum.json: {component: {footprint, mpn, package}} from the SchLib (first PCB model, MPN and Package parameters).
Pad shape: 1 round, 2 rectangle, 3 octagon (as Altium stores it); hole type and slot are not read (0).
Why: reading the libraries offline never wedges Altium (TOOL-20), and the numbers are the stored ones, exact.
"""
import argparse, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import altium_io  # noqa: E402

MM = 0.00000254         # one Altium internal unit (1/10000 mil) in mm
LAYERS = {1: "Top Layer", 32: "Bottom Layer", 33: "Top Overlay", 34: "Bottom Overlay", 35: "Top Paste",
          36: "Bottom Paste", 37: "Top Solder", 38: "Bottom Solder", 74: "Multi-Layer"}
LAYERS.update({56 + n: f"Mechanical Layer {n}" for n in range(1, 17)})
PIN_DIRS = {0: (1, 0), 1: (0, 1), 2: (-1, 0), 3: (0, -1)}


def layer_name(n):
    return LAYERS.get(n, f"Layer {n}")


def _i(b, o):
    return struct.unpack_from("<i", b, o)[0] * MM


def footprint_geometry(fp):
    """altium_io footprint -> {pads, tracks, arcs, vias, boxes} in mm."""
    g = {"pads": [], "tracks": [], "arcs": [], "vias": [], "boxes": []}
    for typ, blocks in fp["prims"]:
        b = blocks[0] if blocks else b""
        if typ == 2 and len(blocks) >= 5 and len(blocks[4]) >= 60:
            m = blocks[4]
            name = altium_io.pascal(blocks[0], 0)[0]
            g["pads"].append(dict(n=name, x=round(_i(m, 13), 5), y=round(_i(m, 17), 5), sx=round(_i(m, 21), 5),
                                  sy=round(_i(m, 25), 5), shape=m[49], rot=round(struct.unpack_from("<d", m, 52)[0], 3),
                                  hole=round(_i(m, 45), 5), htype=0, hw=0.0, layer=layer_name(m[0])))
        elif typ == 4 and len(b) >= 33:
            g["tracks"].append(dict(x1=_i(b, 13), y1=_i(b, 17), x2=_i(b, 21), y2=_i(b, 25), w=_i(b, 29),
                                    layer=layer_name(b[0])))
        elif typ == 1 and len(b) >= 45:
            a0, a1 = struct.unpack_from("<dd", b, 25)
            g["arcs"].append(dict(x=_i(b, 13), y=_i(b, 17), r=_i(b, 21), a0=a0, a1=a1, w=_i(b, 41),
                                  layer=layer_name(b[0])))
        elif typ == 3 and len(b) >= 29:
            g["vias"].append(dict(x=_i(b, 13), y=_i(b, 17), d=_i(b, 21), hole=_i(b, 25)))
        elif typ == 6 and len(b) >= 29:
            x0, y0, x1, y1 = _i(b, 13), _i(b, 17), _i(b, 21), _i(b, 25)
            g["boxes"].append(dict(kind=0, x0=min(x0, x1), y0=min(y0, y1), x1=max(x0, x1), y1=max(y0, y1),
                                   layer=layer_name(b[0])))
    return g


def _mil(r, k):
    """schematic coordinate in mil: the stored value is in 10 mil, with an optional _FRAC part."""
    v = int(r.get(k, 0) or 0) + int(r.get(k + "_FRAC", 0) or 0) / 100000
    return int(round(v * 10))


def symbol_geometry(sym):
    """altium_io symbol -> {desc, pins, rects, lines, polys, arcs, ells} in mil."""
    head = next((r for r in sym["records"] if r.get("RECORD") == "1"), {})
    s = {"desc": head.get("COMPONENTDESCRIPTION", ""), "pins": [], "rects": [], "lines": [], "polys": [],
         "arcs": [], "ells": []}
    for p in sym["pins"]:
        s["pins"].append(dict(n=p["designator"], name=p["name"], el=p.get("electrical", 4), ori=p["rot"],
                              x=p["x"] * 10, y=p["y"] * 10, L=p["length"] * 10, show_name=p["show_name"],
                              part=p.get("part", 1)))
    for r in sym["records"]:
        k = r.get("RECORD")
        if k in ("14", "10"):                        # rectangle, round rectangle
            s["rects"].append([_mil(r, "LOCATION.X"), _mil(r, "LOCATION.Y"), _mil(r, "CORNER.X"), _mil(r, "CORNER.Y")])
        elif k == "13":
            s["lines"].append([_mil(r, "LOCATION.X"), _mil(r, "LOCATION.Y"), _mil(r, "CORNER.X"), _mil(r, "CORNER.Y")])
        elif k in ("6", "7"):
            n = int(r.get("LOCATIONCOUNT", 0) or 0)
            pts = [(_mil(r, f"X{i}"), _mil(r, f"Y{i}")) for i in range(1, n + 1)]
            if pts:
                s["polys"].append(dict(closed=k == "7", pts=pts))
        elif k == "12":
            s["arcs"].append(dict(x=_mil(r, "LOCATION.X"), y=_mil(r, "LOCATION.Y"), r=_mil(r, "RADIUS"),
                                  a0=float(r.get("STARTANGLE", 0) or 0), a1=float(r.get("ENDANGLE", 360) or 360)))
        elif k == "8":
            s["ells"].append(dict(x=_mil(r, "LOCATION.X"), y=_mil(r, "LOCATION.Y"), r=_mil(r, "RADIUS"),
                                  r2=_mil(r, "SECONDARYRADIUS")))
    return s


def pcb_dump_lines(path):
    out = []
    for name, fp in sorted(altium_io.pcblib_footprints(path).items()):
        g = footprint_geometry(fp)
        out.append(f"FP|{name}")
        out += [f"PAD|{p['n']}|{p['x']:.5f}|{p['y']:.5f}|{p['sx']:.5f}|{p['sy']:.5f}|{p['shape']}|{p['rot']:.3f}|"
                f"{p['hole']:.5f}|{p['htype']}|{p['hw']:.5f}|{p['layer']}" for p in g["pads"]]
        out += [f"TRK|{t['x1']:.5f}|{t['y1']:.5f}|{t['x2']:.5f}|{t['y2']:.5f}|{t['w']:.5f}|{t['layer']}" for t in g["tracks"]]
        out += [f"ARC|{a['x']:.5f}|{a['y']:.5f}|{a['r']:.5f}|{a['a0']:.3f}|{a['a1']:.3f}|{a['w']:.5f}|{a['layer']}"
                for a in g["arcs"]]
        out += [f"VIA|{v['x']:.5f}|{v['y']:.5f}|{v['d']:.5f}|{v['hole']:.5f}" for v in g["vias"]]
        out += [f"BOX|0|{b['x0']:.5f}|{b['y0']:.5f}|{b['x1']:.5f}|{b['y1']:.5f}|{b['layer']}" for b in g["boxes"]]
    return out


def sch_dump_lines(path):
    out = []
    for name, sym in sorted(altium_io.schlib_symbols(path).items()):
        s = symbol_geometry(sym)
        out.append(f"SYM|{name}|{s['desc'].replace('|', '/')}")
        out += [f"PIN|{p['n']}|{p['name']}|{p['el']}|{p['ori']}|{p['x']}|{p['y']}|{p['L']}|{int(p['show_name'])}|-|{p['part']}"
                for p in s["pins"]]
        out += ["RECT|" + "|".join(map(str, r)) for r in s["rects"]]
        out += ["LINE|" + "|".join(map(str, r)) for r in s["lines"]]
        out += [f"PL|{15 if pl['closed'] else 6}|-|" + "|".join(f"{x},{y}" for x, y in pl["pts"]) for pl in s["polys"]]
        out += [f"ARC|{a['x']}|{a['y']}|{a['r']}|{a['a0']}|{a['a1']}" for a in s["arcs"]]
        out += [f"ELL|{e['x']}|{e['y']}|{e['r']}|{e['r2']}" for e in s["ells"]]
    return out


def fpsum(path):
    out = {}
    for name, sym in sorted(altium_io.schlib_symbols(path).items()):
        prm = {p["name"]: p["text"] for p in sym["params"]}
        mpn = prm.get("Manufacturer Part Number 1") or prm.get("MPN") or ""
        out[name] = dict(footprint=(sym["footprints"] or [""])[0], mpn=mpn, package=prm.get("Package", ""))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("libs", nargs="+", help=".PcbLib and/or .SchLib")
    ap.add_argument("--out", help="folder for the dump files and fpsum.json")
    ap.add_argument("--footprint")
    ap.add_argument("--symbol")
    a = ap.parse_args(argv)
    pcb = [p for p in a.libs if p.lower().endswith(".pcblib")]
    sch = [p for p in a.libs if p.lower().endswith(".schlib")]
    if a.footprint:
        fps = {n: f for p in pcb for n, f in altium_io.pcblib_footprints(p).items()}
        if a.footprint not in fps:
            print(f"footprint {a.footprint} not found")
            return 1
        print(json.dumps(footprint_geometry(fps[a.footprint]), indent=1))
        return 0
    if a.symbol:
        syms = {n: s for p in sch for n, s in altium_io.schlib_symbols(p).items()}
        if a.symbol not in syms:
            print(f"symbol {a.symbol} not found")
            return 1
        print(json.dumps(symbol_geometry(syms[a.symbol]), indent=1))
        return 0
    if not a.out:
        ap.error("--out is required to write the dump files")
    os.makedirs(a.out, exist_ok=True)
    wrote = []
    if pcb:
        lines = [l for p in pcb for l in pcb_dump_lines(p)]
        with open(os.path.join(a.out, "_pcblib_dump.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        wrote.append(f"_pcblib_dump.txt ({sum(l.startswith('FP|') for l in lines)} footprints)")
    if sch:
        lines = [l for p in sch for l in sch_dump_lines(p)]
        with open(os.path.join(a.out, "_schlib_dump.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        summ = {}
        for p in sch:
            summ.update(fpsum(p))
        with open(os.path.join(a.out, "fpsum.json"), "w", encoding="utf-8") as f:
            json.dump(summ, f, indent=1, ensure_ascii=False)
        wrote.append(f"_schlib_dump.txt and fpsum.json ({len(summ)} components)")
    print(f"lib_dump: wrote {', '.join(wrote)} in {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
