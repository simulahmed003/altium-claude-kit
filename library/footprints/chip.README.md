# footprints / chip

Two-terminal chip parts (R, C, L, LED, ferrite), named by IPC-7351B: RESC1005X40N (0402), CAPC1608X90N (0603) ...

Footprints of this type live in `chip.PcbLib` in this folder; each footprint exists once and every family links
to it (LIB-10, LIB-15). Their 3D models are in `library/models/step/chip/`.

Maintainer: (unassigned)

## Contents

<!-- CONTENTS (lib_readmes.py refreshes this block; edit outside it) -->
| Footprint | Status | Rev | 3D model |
|---|---|---|---|
| CAPC1608_0603 | derived | 1 | missing |
| CAPC3216_1206 | derived | 1 | missing |
| RESC1608_0603 | derived | 1 | yes |
<!-- /CONTENTS -->

## Naming

| Footprint | Pattern | Example |
|---|---|---|
| IPC-7351B families (LIB-17) | IPC-7351B name, density N by default | `RESC1005X40N` (0402), `CAPC1608X90N` (0603), `SOIC127P600X175-8N`, `QFN50P400X400X100-25N` |
| Parts without an IPC family | `<Manufacturer>_<Series or MPN>` | `JST_B2B-XH-A`, `Molex_526101471` |

Older items named `RESC1608_0603` keep that name until they are migrated with `lib_promote.py`.

How to read an IPC-7351B name: `RESC1005X40N` = chip resistor, body 1.0 x 0.5 mm (imperial 0402), height 0.40 mm,
Nominal density. Metric 1005 = 0402, 1608 = 0603, 2012 = 0805, 3216 = 1206.

## Building a footprint (LIB-05, LIB-12)

- One generic IPC-7351B land per package, sized for the largest body that uses it; R and C of one size on the
  same land rule. Courtyard: pads and body + 0.25 mm (0.15 mm below 0603, 0.5 mm connectors), rounded outward to
  0.05 mm; silkscreen 0.15 mm (LIB-18).
- Land from the datasheet's recommended land (page and quote in the part record), else IPC-7351B from the package
  facts, marked "derived". Status: datasheet-verified / derived / unverified-accepted.
- Missing land or package facts: fetch the datasheet, add them to the part record first, then build.

## Changing a footprint by hand

Edit it, then tell Claude in the project. Claude runs `catalog_check.py` and `lib_status.py`, reports what changed
and asks before adapting the catalog, the hashes or project copies (LIB-16).

## Notes and decisions

(add here)
