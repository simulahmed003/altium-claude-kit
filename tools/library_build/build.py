"""build.py - batch library build: one new SchLib + PcbLib from a plan (LIB-30, LIB-34..38, P13). Windows only.

Usage (cmd.exe, from the kit folder):
  python tools\\library_build\\build.py <plan.json> [--out <folder>]
  python tools\\library_build\\build.py --example          print an example plan
Needs: pip install olefile pywin32. Altium is not needed; never run it on a library that is open in Altium.

What it does, per part in the plan (old component name in the source SchLib -> new part):
  - copies the component from the source SchLib; renames it to its MPN (Manufacturer Part Number 1), or keeps the
    old name when it has no MPN (Board Features: the footprint name)
  - keeps exactly the parameter set of its category (rules/library_parameters.json, LIB-34); removes the others
    and logs their values; sets Component Type, Category, Symbol (LIB-37)
    and the hidden Description (LIB-31): updated when present, added when missing
  - optional: replaces its graphics by a shared symbol (plan "symbols"; pins mapped by designator, by role G/S/D,
    or anode/cathode for diodes), recoloured with the plan's line colour
  - links one footprint (the plan's), sets Footprint Standard, applies plan "overrides" (only where empty) and "force"
  - copies each footprint from its source PcbLib under its new IPC-7351B name (LIB-35), with fpfix: silk 0.15 mm,
    courtyard = pads/body + margin rounded out to 0.05 mm (IPC-7351B nominal)
Writes <out>\\<out name>.SchLib, .PcbLib, _build_log.csv (part, item, old, new, note) next to them.
Then: kit pin_match <SchLib> <PcbLib>, kit lib_params --check <SchLib>, kit lib_std_check <SchLib>,
kit ws_lib_check <SchLib>; 3D models: kit kicad_models <PcbLib>, then Swap3D.pas inside Altium (TOOL-19).
The plan holds client data: keep it in the client's folder, never in the kit (WF-09).
"""
import sys, os, json, csv, struct, copy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "scripts"))
from buildsch import components, pin_set, pin_des, pin_name  # noqa: E402

EXAMPLE = {
    "output": "D:/Work/Client/MyLib_Batch1",
    "source_schlib": "D:/Work/Client/MyLib.SchLib",
    "source_pcblib": "D:/Work/Client/MyLib.PcbLib",
    "line_color": "128",
    "courtyard_margin_mm": {"default": 0.25, "small_chip": 0.15, "Connectors": 0.5},
    "footprints": {"RESC1608X55N": ["D:/Work/Client/MyLib.PcbLib", "R0603"],
                   "CAPC1608X90N": ["D:/EDA/library/footprints/chip.PcbLib", "CAPC1608_0603"]},
    "symbols": {"RES": {"lib": "D:/EDA/library/symbols/passives/resistor.SchLib", "pins": {"1": "1", "2": "2"},
                        "name": "Resistor"},
                "NMOS": {"lib": "D:/Lib/MOSFET_N.SchLib", "pins": "GSD", "name": "MOSFET N-Channel"},
                "DIODE": {"lib": "D:/Lib/Diode.SchLib", "pins": None, "name": "Diode"}},
    "parts": {"R7_OLD": {"type": "Resistors", "sub": "Chip", "fp": "RESC1608X55N", "sym": "RES"},
              "D1_OLD": {"type": "Diodes", "sub": "Rectifier & Schottky", "fp": "SODFL3516X120N", "sym": "DIODE",
                         "ak": ["1", "2"]},
              "U5_OLD": {"type": "Integrated Circuits", "sub": "Interface", "fp": "QFN50P400X400X100-25N"}},
    "own_symbol_names": {"U5_OLD": "Interface IC QFN-24"},
    "category_alias": {"Inductors/Power Inductors": "Inductors/Power"},
    "overrides": {"R7_OLD": {"MSL": "1"}},
    "force": {}
}


def load_plan(path):
    with open(path, encoding="utf-8-sig") as f:
        plan = json.load(f)
    plan.setdefault("template_schlib", plan["source_schlib"])
    plan.setdefault("template_pcblib", plan["source_pcblib"])
    return plan


def allowed_params(d, typ, sub, alias):
    """Every parameter a component of Type/Subtype may keep (lib_params set + import-only + keep list)."""
    import lib_params
    key = alias.get(f"{typ}/{sub}", f"{typ}/{sub}")
    hits = [e for e in d["electrical"] if f'{e["type"]}/{e["subtype"]}' == key]
    if not hits:
        raise SystemExit(f"category {typ}/{sub} is not in rules/library_parameters.json (kit lib_params --list)")
    return set(lib_params.param_set(d, hits[0])) | {"Category", "Component Type", "Symbol", "Comment"} | \
        set(d.get("keep_if_present_never_add", []))


log = []          # (part, item, old, new, note)


def L(part, item, old, new, note=''):
    log.append([part, item, old, new, note])


def mm_to_mil(s):
    try:
        return '%.4fmil' % (float(s.replace('mm', '')) / 0.0254)
    except Exception:
        return None


def owner_remap(recs, keep):
    """keep: list of indices into recs to keep (in order). Re-map OWNERINDEX."""
    pos = {old: new for new, old in enumerate(keep)}
    out = []
    for old in keep:
        r = recs[old]
        if r.typ == 0 and r.get('OWNERINDEX') is not None:
            oi = int(r.get('OWNERINDEX'))
            r.set('OWNERINDEX', str(pos[oi]))
        out.append(r)
    return out


def bbox(recs):
    xs, ys = [], []
    for r in recs:
        if r.typ == 1:
            x, y = struct.unpack_from('<hh', r.raw, 12 + 1 + r.raw[12] + 3 + 2)
            xs.append(x); ys.append(y)
        else:
            for k, v in r.kv:
                K = k.upper()
                if K.startswith('X') and K[1:].isdigit() or K == 'LOCATION.X' or K == 'CORNER.X':
                    xs.append(int(v))
                if K.startswith('Y') and K[1:].isdigit() or K == 'LOCATION.Y' or K == 'CORNER.Y':
                    ys.append(int(v))
    return (min(xs or [0]), min(ys or [0]), max(xs or [0]), max(ys or [0]))


def shared_graphics(plan, key, ak, ourpins, ourpinnames=None):
    sy = plan["symbols"][key]
    path, pmap = sy["lib"], sy.get("pins")
    LINE = plan.get("line_color", "128")
    if pmap == 'GSD':
        role = {}
        for des, nm in ourpinnames.items():
            role[nm.upper()[0]] = des
        pmap = {'1': role['G'], '2': role['S'], '3': role['D']}
    c = components(path)
    (rs, extra), = c.values()
    g = []
    for r in rs[1:]:
        if r.typ == 0 and r.rec in ('34', '41', '44', '45', '46', '47', '48'):
            continue
        r = copy.deepcopy(r)
        if r.typ == 1:
            d = pin_des(r.raw)
            if ak:
                new = ak[0] if d == '1' else ak[1]
                r.raw = pin_set(r.raw, name='A' if d == '1' else 'K', des=new)
            else:
                r.raw = pin_set(r.raw, des=pmap[d])
        else:
            if r.get('COLOR') is not None:
                r.set('COLOR', LINE)
            if r.get('ISSOLID') == 'T':
                r.set('AREACOLOR', LINE)
            r.drop('UNIQUEID')
        g.append(r)
    got = sorted(pin_des(r.raw) for r in g if r.typ == 1)
    if got != sorted(ourpins):
        raise ValueError('pin set mismatch %s %s %s' % (key, got, ourpins))
    return g, {p: b for p, b in extra.items()}, path


def build_component(plan, ours, d, old, p):
    rs, extra = ours[old]
    rs = [copy.deepcopy(r) for r in rs]
    head = rs[0]
    prm = {r.get('NAME'): r for r in rs if r.typ == 0 and r.rec == '41' and r.get('OWNERINDEX') is None}
    OVR, FORCE = plan.get("overrides", {}), plan.get("force", {})
    for k, v in OVR.get(old, {}).items():
        if prm.get(k) is not None and not (prm[k].get('TEXT') or ''):
            prm[k].set('TEXT', v); L(old, 'parameter value', k + ': (empty)', v, 'from the datasheet')
    for k, v in FORCE.get(old, {}).items():
        if prm.get(k) is not None:
            L(old, 'parameter value', k + ': ' + (prm[k].get('TEXT') or ''), v, 'corrected to the datasheet')
            prm[k].set('TEXT', v)
    mpn = (prm.get('Manufacturer Part Number 1').get('TEXT') if prm.get('Manufacturer Part Number 1') else '') or ''
    new = mpn or (p['fp'] if p['type'] == 'Board Features' else old)
    if new != old:
        L(new, 'component name', old, new, 'renamed to MPN' if mpn else 'no MPN; named after the footprint')
    head.set('LIBREFERENCE', new)
    fs = 'IPC-7351B Nominal' if p['fp'].endswith('N') and p['fp'][:3].isupper() and '_' not in p['fp'] else ('IPC-7351B Least' if p['fp'].endswith('L') and '_' not in p['fp'] else 'Manufacturer')
    if 'TestPoint' in p['fp']: fs = 'Manufacturer'
    r = prm.get('Footprint Standard')
    if r is not None and (r.get('TEXT') or '') != fs:
        L(new, 'parameter value', 'Footprint Standard: ' + (r.get('TEXT') or '(empty)'), fs, 'follows the new footprint')
        r.set('TEXT', fs)
    if head.get('DESIGNITEMID') is not None:
        head.set('DESIGNITEMID', new)
    # --- which old records to keep
    keep = []
    pcb45 = [i for i, r in enumerate(rs) if r.typ == 0 and r.rec == '45' and r.get('MODELTYPE') == 'PCBLIB']
    cur = [i for i in pcb45 if rs[i].get('ISCURRENT') == 'T'] or pcb45[:1]
    drop45 = set(pcb45) - set(cur[:1])
    dropped = set(drop45)
    changed = True
    while changed:
        changed = False
        for i, r in enumerate(rs):
            if i not in dropped and r.typ == 0 and r.get('OWNERINDEX') is not None and int(r.get('OWNERINDEX')) in dropped:
                dropped.add(i); changed = True
    for i in drop45:
        L(new, 'footprint link removed', rs[i].get('MODELNAME'), '', 'only one footprint per part')
    allowed = allowed_params(d, p['type'], p['sub'], plan.get('category_alias', {}))
    for i, r in enumerate(rs):
        if i in dropped:
            continue
        if r.typ == 0 and r.rec == '41' and r.get('OWNERINDEX') is None and r.get('NAME') not in allowed:
            L(new, 'parameter removed', r.get('NAME'), '', 'not in the frozen list (value: %s)' % (r.get('TEXT') or ''))
            continue
        keep.append(i)
    # footprint link
    i45 = cur[0]
    oldfp = rs[i45].get('MODELNAME')
    for k in ('MODELNAME', 'MODELDATAFILEENTITY0'):
        if rs[i45].get(k) is not None:
            rs[i45].set(k, p['fp'])
    if oldfp != p['fp']:
        L(new, 'footprint', oldfp, p['fp'], '')
    # --- symbol
    pin_streams = {k: v for k, v in extra.items()}
    if p.get('sym'):
        ourpins = [pin_des(r.raw) for r in rs if r.typ == 1]
        ourpinnames = {pin_des(r.raw): pin_name(r.raw) for r in rs if r.typ == 1}
        g, pin_streams, src = shared_graphics(plan, p['sym'], p.get('ak'), sorted(set(ourpins)), ourpinnames)
        rest = [i for i in keep if not (rs[i].typ == 1 or (rs[i].typ == 0 and rs[i].get('OWNERPARTID') not in (None, '-1') and rs[i].rec not in ('34', '41', '44', '45', '46', '47', '48')))]
        rest = [i for i in rest if i != 0]
        head.set('PARTCOUNT', '2'); head.set('DISPLAYMODECOUNT', '1'); head.set('CURRENTPARTID', '1')
        x0, y0, x1, y1 = bbox(g)
        L(new, 'symbol', 'own symbol', 'shared ' + os.path.basename(src), 'pins mapped to the datasheet pin numbers' + (' (1 = cathode)' if p.get('ak') else ''))
        recs_rest = owner_remap(rs, [0] + rest)[1:]
        # visible text placement
        vis_y = y0 - 8
        for r in sorted(recs_rest, key=lambda r: 0 if (r.typ == 0 and r.get('NAME') == 'Comment') else 1):
            if r.typ == 0 and r.rec == '34':
                r.set('LOCATION.X', str(x0)); r.set('LOCATION.Y', str(y1 + 2))
            elif r.typ == 0 and r.rec == '41' and r.get('OWNERINDEX') is None and r.get('ISHIDDEN') != 'T':
                r.set('LOCATION.X', str(x0)); r.set('LOCATION.Y', str(vis_y)); vis_y -= 8
        # owner indices of the rest point to positions within [0]+rest; shift by len(g)
        for r in recs_rest:
            if r.typ == 0 and r.get('OWNERINDEX') is not None and r.rec in ('45', '46', '47', '48'):
                oi = int(r.get('OWNERINDEX'))
                r.set('OWNERINDEX', str(oi + len(g)))
        recs = [head] + g + recs_rest
    else:
        recs = owner_remap(rs, keep)
    # --- Component Type, Category, Symbol and the hidden Description parameter: update or add before RECORD 44
    i44 = next(i for i, r in enumerate(recs) if r.typ == 0 and r.rec == '44')
    tops = [r for r in recs if r.typ == 0 and r.rec == '41' and r.get('OWNERINDEX') is None]
    tmpl = next((r for r in tops if r.get('NAME') == 'Supplier 1'), tops[0] if tops else None)
    if tmpl is None:
        raise ValueError(f'{old}: no parameter record to copy')
    adds = []
    comment = prm.get('Comment').get('TEXT') if prm.get('Comment') else new
    symname = plan['symbols'][p['sym']].get('name', p['sym']) if p.get('sym') else plan.get('own_symbol_names', {}).get(old, comment)
    desc_field = head.get('COMPONENTDESCRIPTION', '') or ''
    have = {r.get('NAME'): r for r in recs if r.typ == 0 and r.rec == '41' and r.get('OWNERINDEX') is None}
    want = [('Component Type', p['sub'] or p['type'], False), ('Category', '%s/%s' % (p['type'], p['sub']), False),
            ('Symbol', symname, False), ('Description', desc_field, True)]
    for nm, val, hidden in want:
        if nm in have:                       # already there (an earlier build or the source): update, never duplicate
            r = have[nm]
            cur = r.get('TEXT') or ''
            if nm == 'Description' and cur and not val:
                continue
            if cur != val:
                r.set('TEXT', val); r.drop('%UTF8%TEXT')
                L(new, 'parameter value', nm + ': ' + (cur or '(empty)'), val, '')
            if hidden and r.get('ISHIDDEN') != 'T':
                r.set('ISHIDDEN', 'T'); L(new, 'parameter hidden', nm, '', 'LIB-31')
            continue
        r = copy.deepcopy(tmpl); r.set('NAME', nm); r.set('TEXT', val); r.drop('%UTF8%TEXT'); r.drop('UNIQUEID')
        if hidden:
            r.set('ISHIDDEN', 'T')
        else:
            r.drop('ISHIDDEN')
        adds.append(r)
        L(new, 'parameter added', nm, val, 'hidden, = component description (LIB-31)' if nm == 'Description' else '')
    recs = recs[:i44] + adds + recs[i44:]
    for r in recs:
        if r.typ == 0 and r.get('OWNERINDEX') is not None and int(r.get('OWNERINDEX')) >= i44:
            r.set('OWNERINDEX', str(int(r.get('OWNERINDEX')) + len(adds)))
    desc = head.get('COMPONENTDESCRIPTION', '')
    sk = new.replace('/', '_').replace('\\', '_').replace(':', '_').replace('!', '_')[:31]
    h = prm.get('Height').get('TEXT') if prm.get('Height') else ''
    return new, sk, recs, pin_streams, desc, h


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("plan", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--example", action="store_true")
    a = ap.parse_args(argv)
    if a.example:
        print(json.dumps(EXAMPLE, indent=1))
        return 0
    if not a.plan:
        ap.print_help()
        return 1
    plan = load_plan(a.plan)
    OUT = a.out or plan["output"]
    import lib_params
    from buildsch import write_lib
    from buildpcb import build as build_pcb
    import fpfix
    d = lib_params.load()
    ours = components(plan["source_schlib"])
    P, FP = plan["parts"], {k: tuple(v) for k, v in plan["footprints"].items()}
    missing = sorted(o for o in P if o not in ours) + sorted({p["fp"] for p in P.values()} - set(FP))
    if missing:
        raise SystemExit("not in the source SchLib / plan footprints: " + ", ".join(missing))
    cm = plan.get("courtyard_margin_mm", {})
    name = os.path.basename(os.path.normpath(OUT))
    os.makedirs(OUT, exist_ok=True)
    comps, fps, heights, users = [], {}, {}, {}
    for old in sorted(P):
        p = P[old]
        c = build_component(plan, ours, d, old, p)
        comps.append(c[:5])
        fps[p['fp']] = FP[p['fp']]
        users.setdefault(p['fp'], []).append((old, p))
        mil = mm_to_mil(c[5]) if c[5] else None
        if mil and float(mil[:-3]) > float(heights.get(p['fp'], '0mil')[:-3]):
            heights[p['fp']] = mil
    comps.sort(key=lambda c: c[0])
    write_lib(os.path.join(OUT, name + '.SchLib'), comps, plan["template_schlib"])

    def margin(fpn):
        us = users[fpn]
        for o, p in us:
            if p['type'] in cm:
                return cm[p['type']]
        if any(next((r.get('TEXT') for r in ours[o][0] if r.typ == 0 and r.get('NAME') == 'Package'), '')
               in ('0402', '0201', '01005') for o, p in us):
            return cm.get("small_chip", 0.15)
        return cm.get("default", 0.25)

    def ext(p):
        X, Y = (p['sy'], p['sx']) if round(p['rot']) % 180 == 90 else (p['sx'], p['sy'])
        return p['x'] - X / 2, p['x'] + X / 2, p['y'] - Y / 2, p['y'] + Y / 2, X, Y
    fixer = lambda n, data: fpfix.fix(n, data, margin(n), ext)
    flog = build_pcb(os.path.join(OUT, name + '.PcbLib'), [(n,) + fps[n] for n in sorted(fps)], plan["template_pcblib"],
                     heights, fixer)
    for n, src, pat, st in flog:
        L('(footprint) ' + n, 'footprint source', '%s :: %s' % (os.path.basename(src), pat), n, '')
        for note in fpfix.NOTES.get(n, []):
            L('(footprint) ' + n, 'footprint fix', '', note, '')
    with open(os.path.join(OUT, '_build_log.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.writer(f)
        wr.writerow(['Part / footprint', 'Item', 'Old', 'New', 'Note'])
        wr.writerows(log)
    print(f"build: {len(comps)} components, {len(fps)} footprints, {len(log)} log rows in {OUT}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
