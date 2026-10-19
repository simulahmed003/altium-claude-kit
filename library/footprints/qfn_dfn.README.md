# footprints / qfn_dfn

No-lead packages: QFN, DFN, SON, WSON, VSON.

Footprints of this type live in `qfn_dfn.PcbLib` in this folder; each footprint exists once and every family links
to it (LIB-10, LIB-15). Their 3D models are in `library/models/step/qfn_dfn/`.

Maintainer: (unassigned)

## Contents

<!-- CONTENTS (lib_readmes.py refreshes this block; edit outside it) -->
No footprints yet. The file `qfn_dfn.PcbLib` is created when the first footprint of this type is promoted.
<!-- /CONTENTS -->

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
