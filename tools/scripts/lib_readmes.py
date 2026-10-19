"""lib_readmes.py - one README per symbol family and per footprint / 3D model package type (LIB-15, LIB-16).

Usage:
  python lib_readmes.py [--check]
Creates library/symbols/<category>/<family>.README.md for every family in parts/taxonomy.json and
library/footprints/<type>.README.md + library/models/step/<type>/README.md for every type in libcat.PACKAGE_TYPES.
A README that exists is never rewritten: only the block between the CONTENTS markers is refreshed from the catalog,
so text a person adds (maintainer, notes, decisions) stays. --check writes nothing and exits 1 when a README is
missing or its contents block is stale.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libcat as lc

BEGIN, END = "<!-- CONTENTS (lib_readmes.py refreshes this block; edit outside it) -->", "<!-- /CONTENTS -->"

ABOUT = {
    "resistor": "Fixed resistors: chip, thin film, current sense, through hole.",
    "capacitor_mlcc": "Multilayer ceramic capacitors.",
    "capacitor_electrolytic": "Aluminium electrolytic capacitors (polarised).",
    "capacitor_polymer": "Polymer and tantalum-polymer capacitors (polarised).",
    "inductor_power": "Power inductors for converters and filters.",
    "ferrite_bead": "Ferrite beads and chip EMI filters.",
    "mosfet": "N- and P-channel MOSFETs, single and dual.",
    "diode_rectifier": "Standard and fast recovery rectifier diodes.",
    "diode_schottky": "Schottky diodes.",
    "diode_zener": "Zener and voltage-reference diodes.",
    "diode_tvs": "TVS and ESD protection diodes and arrays.",
    "led": "Indicator LEDs.",
    "bjt": "Bipolar transistors, single and dual.",
    "power_buck": "Step-down converters and controllers.",
    "power_boost": "Step-up converters and controllers.",
    "power_ldo": "Linear regulators and LDOs.",
    "power_switch": "Load switches, eFuses, ideal diodes, hot-swap.",
    "mcu": "Microcontrollers.",
    "interface": "Transceivers and bridges (UART, RS-485, CAN, USB, I2C, Ethernet PHY).",
    "analog": "Op-amps, comparators, references, ADC and DAC.",
    "sensor": "Temperature, current, motion and environmental sensors.",
    "logic": "Logic gates, buffers, level shifters, multiplexers.",
    "memory": "EEPROM, flash, FRAM.",
    "clock": "Clock generators, buffers, RTCs.",
    "terminal_block": "Screw and spring terminal blocks.",
    "header": "Pin headers and sockets.",
    "usb": "USB connectors.",
    "board_to_board": "Board-to-board and mezzanine connectors.",
    "test_point": "Test pads and test points.",
    "crystal": "Quartz crystals.",
    "oscillator": "Crystal and MEMS oscillators.",
    "fuse": "Fuses and PTC resettable fuses.",
    "switch": "Push buttons, slide and DIP switches.",
    "relay": "Relays.",
}

PKG_ABOUT = {
    "chip": "Two-terminal chip parts (R, C, L, LED, ferrite) by IPC-7351 size: RESC1608_0603, CAPC3216_1206 ...",
    "soic": "Gull-wing small outline packages: SOIC, HSOIC, SOP, MSOP, TSSOP.",
    "sot": "SOT-23, TSOT, SC-70 and similar.",
    "qfn_dfn": "No-lead packages: QFN, DFN, SON, WSON, VSON.",
    "to": "TO-220, TO-252 (DPAK), TO-263 (D2PAK) and similar.",
    "terminal_block": "Screw and spring terminal blocks.",
    "test_point": "Test pads.",
    "inductor_smd": "Part-specific SMD power inductor bodies.",
    "header": "Pin headers and sockets.",
    "usb": "USB connectors.",
    "crystal_osc": "Crystal and oscillator packages.",
}


def pkg_types():
    seen = []
    for _, t in lc.PACKAGE_TYPES:
        if t not in seen:
            seen.append(t)
    return seen


def family_contents(cat, category, family):
    rows = [c for c in cat["components"] if c.get("category") == category and c.get("family") == family]
    if not rows:
        return "No symbols yet. The file `%s.SchLib` is created when the first part of this family is promoted." % family
    out = ["| Symbol | MPN | Footprint | Rev |", "|---|---|---|---|"]
    out += [f"| {c['id']} | {c.get('mpn', '-')} | {c.get('footprint', '-')} | {c.get('rev')} |"
            for c in sorted(rows, key=lambda c: c["id"])]
    return "\n".join(out)


def package_contents(cat, ptype, models):
    rows = [f for f in cat["footprints"] if f.get("package_type") == ptype]
    if not rows:
        return "No footprints yet. The file `%s.PcbLib` is created when the first footprint of this type is promoted." % ptype
    have = {m.get("footprint") for m in models}
    out = ["| Footprint | Status | Rev | 3D model |", "|---|---|---|---|"]
    out += [f"| {f['name']} | {f.get('status')} | {f.get('rev')} | {'yes' if f['name'] in have else 'missing'} |"
            for f in sorted(rows, key=lambda f: f["name"])]
    return "\n".join(out)


def family_text(category, family, required, contents):
    return f"""# {category} / {family}

{ABOUT.get(family, "")}

Symbols of this family live in `{family}.SchLib` in this folder (rules LIB-10, LIB-11, LIB-15).

Maintainer: (unassigned)

## Contents

{BEGIN}
{contents}
{END}

## What goes in

- One symbol per pin list and kind, shared by every part with exactly that pin list (LIB-10). Values, MPNs and
  ratings are parameters, never a new symbol.
- Symbol name: `<KIND>` for two-pin passives (RES, CAP, IND), `<KIND>_<n>P_<pin names>` for discretes
  (PMOS_8P_SSSGDDDD), `<base part>_<package code>` for ICs (LMR33630_DDA).
- Local project component name: `<prefix>_<value>_<key rating>_<package>_<MPN>`, one per MPN (LIB-14).

## Drawing standard (LIB-02, LIB-03, LIB-11)

- Pin ends on the 100 mil grid; line width 1 (small); one line colour; font size 10.
- Visible text: Designator and Comment (=Value) only; MPN, Manufacturer, LCSC, Datasheet and ratings hidden.
- One visible pin per pad, same number (LIB-01). Passive pins 100 mil (capacitor 80 mil), IC pins 200 mil.
- ICs: pins grouped as in the datasheet, power top, ground bottom, inputs left, outputs right, symmetric where
  the pinout allows, pin names exactly as in the datasheet.

## Facts the component database must hold for this family

{", ".join(f"`{k}`" for k in required) or "(none listed yet in taxonomy.json)"}

## Adding or changing a symbol

By a person: close the library in Altium only when you are done, keep the drawing standard, then tell Claude in the
project. Claude runs `catalog_check.py` and `lib_status.py`, reports what changed and asks before adapting catalog
entries or project copies (LIB-16).

By Claude: build from the part record (`gen_sym.py`), dry-run into `libs/_dryrun/`, `pin_match.py --style`, user
check at G1, then `lib_promote.py` (LIB-09, LIB-11, P2).

## Notes and decisions

(add here)
"""


def package_text(ptype, contents):
    return f"""# footprints / {ptype}

{PKG_ABOUT.get(ptype, "")}

Footprints of this type live in `{ptype}.PcbLib` in this folder; each footprint exists once and every family links
to it (LIB-10, LIB-15). Their 3D models are in `library/models/step/{ptype}/`.

Maintainer: (unassigned)

## Contents

{BEGIN}
{contents}
{END}

## Naming

| Footprint | Pattern | Example |
|---|---|---|
| IPC-7351 chip parts | `<type><metric size>_<imperial size>` | `RESC1608_0603`, `CAPC3216_1206` |
| IC or other package | `<package>_<drawing code>`, or `<part>_<package>_<code>` when the land is part-specific | `SOIC8_MS012`, `LMR33630_HSOIC8_DDA` |
| Connector | `<type>_<series>-<pins>-<pitch>` | `TB_MKDS1.5-2-5.08` |

## Building a footprint (LIB-05, LIB-12)

- Land from the datasheet's recommended land (page and quote in the part record), else IPC-7351 from the package
  facts, marked "derived". Status: datasheet-verified / derived / unverified-accepted.
- Missing land or package facts: fetch the datasheet, add them to the part record first, then build.

## Changing a footprint by hand

Edit it, then tell Claude in the project. Claude runs `catalog_check.py` and `lib_status.py`, reports what changed
and asks before adapting the catalog, the hashes or project copies (LIB-16).

## Notes and decisions

(add here)
"""


def model_text(ptype, contents):
    return f"""# 3D models / {ptype}

STEP models for the footprints in `library/footprints/{ptype}.PcbLib`. One model per body, shared by every part on
that footprint: a 10 uF and a 22 uF 0603 capacitor use the same `CAPC1608_0603.step` (LIB-13).

Maintainer: (unassigned)

## Contents

{BEGIN}
{contents}
{END}

## Naming

`<footprint name>.step`, for example `RESC1608_0603.step`. Placement offset and rotation go in
`library/models/index.json` (cad_register.py), not in the file name.

## Getting a model (LIB-13)

1. Library first: a model for this footprint already here? Use it.
2. JLC/EasyEDA by the part's LCSC number (STEP).
3. The maker's website.
4. A similar part's model with the same body, only as a marked substitute the user accepts at G1.

Check the model's box against the part record's body length, width and height (inside the datasheet min/max),
then `cad_register.py <file> --footprint <name> --source <url or note>`, which records sha256 and source.

## Adding a model by hand

Put the .step file here with the name above and tell Claude in the project. Claude checks the box, registers it
and links it to the footprint after asking (LIB-16).

## Notes and decisions

(add here)
"""


def refresh(path, text, contents, check):
    if not os.path.isfile(path):
        if not check:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        return f"{'MISSING' if check else 'created'} {path}"
    with open(path, encoding="utf-8") as f:
        old = f.read()
    if BEGIN not in old or END not in old:
        return None
    new = old[:old.index(BEGIN) + len(BEGIN)] + "\n" + contents + "\n" + old[old.index(END):]
    if new == old:
        return None
    if not check:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
    return f"{'STALE' if check else 'refreshed'} {path}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--global-root")
    a = ap.parse_args(argv)
    root = a.global_root
    cat = lc.load_catalog(root=root) if hasattr(lc, "load_catalog") else json.load(
        open(lc.gpath("catalog", "components.json", root=root), encoding="utf-8"))
    with open(lc.gpath("parts", "taxonomy.json", root=root), encoding="utf-8") as f:
        tax = json.load(f)
    idx = lc.gpath("models", "index.json", root=root)
    models = json.load(open(idx, encoding="utf-8")).get("models", []) if os.path.isfile(idx) else []
    msgs = []
    for category, fams in tax["categories"].items():
        for family, spec in fams.items():
            body = family_contents(cat, category, family)
            p = lc.gpath("symbols", category, f"{family}.README.md", root=root)
            msgs.append(refresh(p, family_text(category, family, spec.get("required", []), body), body, a.check))
    for t in pkg_types():
        body = package_contents(cat, t, models)
        msgs.append(refresh(lc.gpath("footprints", f"{t}.README.md", root=root), package_text(t, body), body, a.check))
        msgs.append(refresh(lc.gpath("models", "step", t, "README.md", root=root), model_text(t, body), body, a.check))
    msgs = [m for m in msgs if m]
    for m in msgs:
        print(m)
    print(f"lib_readmes: {len(msgs)} {'problems' if a.check else 'changes'}")
    return 1 if a.check and msgs else 0


if __name__ == "__main__":
    sys.exit(main())
