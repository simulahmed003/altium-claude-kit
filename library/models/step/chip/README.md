# 3D models / chip

STEP models for the footprints in `library/footprints/chip.PcbLib`. One model per body, shared by every part on
that footprint: a 10 uF and a 22 uF 0603 capacitor use the same `CAPC1608_0603.step` (LIB-13).

Maintainer: (unassigned)

## Contents

<!-- CONTENTS (lib_readmes.py refreshes this block; edit outside it) -->
| Footprint | Status | Rev | 3D model |
|---|---|---|---|
| CAPC1608_0603 | derived | 1 | missing |
| CAPC3216_1206 | derived | 1 | missing |
| RESC1608_0603 | derived | 1 | missing |
<!-- /CONTENTS -->

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
