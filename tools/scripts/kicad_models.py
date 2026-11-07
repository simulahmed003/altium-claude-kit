"""kicad_models.py - pick KiCad STEP models for the standard footprints of a PcbLib and write models.csv for Swap3D.pas.

Usage:
  python kicad_models.py <lib.PcbLib> [--kicad "C:\\Program Files\\KiCad\\9.0\\share\\kicad"] [--map extra.json]
                         [--out <folder>] [--dry-run]
Default --out: <PcbLib folder>\\3D_KiCad. Default --kicad: the newest C:\\Program Files\\KiCad\\<version>\\share\\kicad.
--map: JSON {"<footprint name>": "<KiCad lib>/<KiCad footprint>"} added to the built-in IPC-7351B map.

Per mapped footprint: reads the KiCad footprint (.kicad_mod) for its pad positions, finds the rotation (0/90/180/270)
and offset that put the KiCad pads on ours (largest pad-centre error must be under 0.35 mm, every pad matched),
copies the STEP file into --out and writes one line "footprint,step file,rotation,offset x mm,offset y mm" to
models.csv. Footprints with no map entry, a pad mismatch or a model offset inside the KiCad footprint are listed
and left alone. Then, inside Altium: open the PcbLib, run tools\\altium_scripts\\Swap3D.pas > SwapKiCad3D, check in
3D, save (TOOL-19: Altium embeds the model, so the checksum is right). Rule LIB-13: KiCad models for standard
packages, the maker's model for custom parts. KiCad's 3D models are CC-BY-SA with a design exception: fine in a
board; keep their licence note when you redistribute the STEP files themselves.
"""
import argparse, glob, json, math, os, re, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import altium_io  # noqa: E402

MM = 0.00000254
MAX_ERR_MM = 0.35
# IPC-7351B footprint name -> KiCad library/footprint (the model has the same base name)
MAP = {
    "CAPC1005X55N": "Capacitor_SMD/C_0402_1005Metric", "CAPC1608X90N": "Capacitor_SMD/C_0603_1608Metric",
    "CAPC2012X145N": "Capacitor_SMD/C_0805_2012Metric", "CAPC3216X180N": "Capacitor_SMD/C_1206_3216Metric",
    "RESC1005X40N": "Resistor_SMD/R_0402_1005Metric", "RESC1608X55N": "Resistor_SMD/R_0603_1608Metric",
    "RESC2012X70N": "Resistor_SMD/R_0805_2012Metric", "RESC3216X70N": "Resistor_SMD/R_1206_3216Metric",
    "INDC3216X110N": "Inductor_SMD/L_1206_3216Metric",
    "CAPPM7343X310N": "Capacitor_Tantalum_SMD/CP_EIA-7343-31_Kemet-D",
    "CAPAE1030X1270N": "Capacitor_SMD/CP_Elec_10x12.6", "CAPAE660X850N": "Capacitor_SMD/CP_Elec_6.3x7.7",
    "SOT95P240X110-3N": "Package_TO_SOT_SMD/SOT-23-3", "SOT95P280X145-5N": "Package_TO_SOT_SMD/SOT-23-5",
    "SOT95P280X145-6N": "Package_TO_SOT_SMD/SOT-23-6",
    "SOT65P210X110-3N": "Package_TO_SOT_SMD/SOT-323_SC-70", "SOT65P210X110-5N": "Package_TO_SOT_SMD/SOT-353_SC-70-5",
    "SOTFL35P100X50-3N": "Package_TO_SOT_SMD/Texas_DRT-3",
    "SODFL2513X110N": "Diode_SMD/D_SOD-323F", "SOD3716X135N": "Diode_SMD/D_SOD-123", "SODFL3516X120N": "Diode_SMD/D_SOD-123F",
    "DIOM7959X262N": "Diode_SMD/D_SMC", "DIOM5226X240N": "Diode_SMD/D_SMB", "DIOM5025X231N": "Diode_SMD/D_SMA",
    "SOIC127P600X175-8N": "Package_SO/SOIC-8_3.9x4.9mm_P1.27mm", "SOP50P490X110-10N": "Package_SO/MSOP-10_3x3mm_P0.5mm",
    "SOP65P640X120-28N": "Package_SO/TSSOP-28_4.4x9.7mm_P0.65mm",
    "QFN50P400X400X100-25N": "Package_DFN_QFN/QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
    "QFN65P600X600X100-29L": "Package_DFN_QFN/QFN-28-1EP_6x6mm_P0.65mm_EP4.25x4.25mm",
    "QFP50P900X900X160-48N": "Package_QFP/LQFP-48_7x7mm_P0.5mm",
    "TO228P970X238-3N": "Package_TO_SOT_SMD/TO-252-2",
}


def kicad_root():
    vs = sorted(glob.glob(r"C:\Program Files\KiCad\*\share\kicad"),
                key=lambda p: [int(x) if x.isdigit() else 0 for x in re.split(r"[.\\/]", p)])
    return vs[-1] if vs else None


def kicad_pads(mod_text):
    """(pad name, x, y) with y up, as Altium."""
    out = []
    for m in re.finditer(r'\(pad\s+"([^"]*)"\s+\w+\s+\w+[^()]*\(at\s+([-\d.]+)\s+([-\d.]+)', mod_text):
        if m.group(1):
            out.append((m.group(1), float(m.group(2)), -float(m.group(3))))
    return out


def model_has_offset(mod_text):
    m = re.search(r'\(model[^\n]*\n\s*\(offset\s*\(xyz\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)\)\s*\(scale[^\n]*\)\s*'
                  r'\(rotate\s*\(xyz\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', mod_text)
    return bool(m and any(abs(float(v)) > 1e-6 for v in m.groups()))


def centroids(pads):
    acc = {}
    for n, x, y in pads:
        acc.setdefault(n, []).append((x, y))
    return {n: (sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v)) for n, v in acc.items()}


def rot(x, y, a):
    c, s = round(math.cos(math.radians(a))), round(math.sin(math.radians(a)))
    return x * c - y * s, x * s + y * c


def best_rotation(ours, kic):
    """(largest error mm, rotation, dx, dy, pads matched, our pad count) of the best of 0/90/180/270."""
    oc, kc = centroids(ours), centroids(kic)
    common = [n for n in oc if n in kc]
    if not common:
        return (float("inf"), 0, 0.0, 0.0, 0, len(oc))
    best = None
    for a in (0, 90, 180, 270):
        dx = sum(oc[n][0] - rot(*kc[n], a)[0] for n in common) / len(common)
        dy = sum(oc[n][1] - rot(*kc[n], a)[1] for n in common) / len(common)
        err = max(math.hypot(oc[n][0] - rot(*kc[n], a)[0] - dx, oc[n][1] - rot(*kc[n], a)[1] - dy) for n in common)
        if best is None or err < best[0]:
            best = (err, a, dx, dy, len(common), len(oc))
    return best


def our_pads(fp):
    out = []
    for typ, blocks in fp["prims"]:
        if typ == 2 and len(blocks) >= 5 and len(blocks[4]) >= 21:
            n = altium_io.pascal(blocks[0], 0)[0]
            m = blocks[4]
            if n:
                out.append((n, struct.unpack_from("<i", m, 13)[0] * MM, struct.unpack_from("<i", m, 17)[0] * MM))
    return out


def plan(fps, kicad, mapping):
    """rows (footprint, status, detail, csv line or None)."""
    rows = []
    for name in sorted(fps):
        rel = mapping.get(name)
        if not rel:
            rows.append((name, "SKIP", "no KiCad model mapped", None))
            continue
        lib, base = rel.split("/", 1)
        mod_p = os.path.join(kicad, "footprints", f"{lib}.pretty", f"{base}.kicad_mod")
        step_p = os.path.join(kicad, "3dmodels", f"{lib}.3dshapes", f"{base}.step")
        if not (os.path.isfile(mod_p) and os.path.isfile(step_p)):
            rows.append((name, "MISSING", f"{rel} not in {kicad}", None))
            continue
        mod = open(mod_p, encoding="utf-8").read()
        if model_has_offset(mod):
            rows.append((name, "SKIP", f"{base}: the KiCad footprint offsets/rotates its model; place it by hand", None))
            continue
        err, a, dx, dy, nc, no = best_rotation(our_pads(fps[name]), kicad_pads(mod))
        if err > MAX_ERR_MM or nc < no:
            rows.append((name, "MISMATCH", f"{base}: pads differ (largest error {err:.2f} mm, {nc}/{no} pads)", None))
            continue
        dx, dy = (0.0 if abs(v) < 0.005 else round(v, 3) for v in (dx, dy))
        rows.append((name, "OK", f"{base}.step rotation {a}, offset {dx}/{dy} mm, pads within {err:.2f} mm",
                     (f"{name},{base}.step,{a},{dx},{dy}", step_p)))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("pcblib")
    ap.add_argument("--kicad", default=None)
    ap.add_argument("--map")
    ap.add_argument("--out")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    kicad = a.kicad or kicad_root()
    if not kicad or not os.path.isdir(kicad):
        print("KiCad share folder not found: pass --kicad \"C:\\Program Files\\KiCad\\9.0\\share\\kicad\"")
        return 1
    mapping = dict(MAP)
    if a.map:
        with open(a.map, encoding="utf-8") as f:
            mapping.update(json.load(f))
    rows = plan(altium_io.pcblib_footprints(a.pcblib), kicad, mapping)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.pcblib)), "3D_KiCad")
    for name, st, why, _ in rows:
        print(f"{st:9} {name:28} {why}")
    ok = [r for r in rows if r[3]]
    if not a.dry_run and ok:
        os.makedirs(out, exist_ok=True)
        for _, _, _, (line, step) in ok:
            shutil.copyfile(step, os.path.join(out, os.path.basename(step)))
        with open(os.path.join(out, "models.csv"), "w", encoding="utf-8", newline="\r\n") as f:
            f.write("\n".join(line for _, _, _, (line, _) in ok) + "\n")
        print(f"wrote {os.path.join(out, 'models.csv')} and {len(ok)} STEP file(s); next: Swap3D.pas inside Altium (TOOL-19)")
    print(f"kicad_models: {len(rows)} footprints, {len(ok)} OK, {sum(r[1] in ('MISMATCH', 'MISSING') for r in rows)} to check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
