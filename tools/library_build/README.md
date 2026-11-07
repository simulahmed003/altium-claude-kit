# Batch library builder (P13, LIB-30, LIB-34..38)

Builds one new SchLib + PcbLib from an existing library and a plan, the way the first client library batch was built
(74 parts, 2026-11-04). Windows only (it writes the OLE files with pywin32); Altium is not needed and the source
library must not be open in Altium while it runs.

```
install.cmd /full                                  once: olefile, pywin32 (tools\requirements-library.txt)
kit lib_build --example > "D:\Work\Lib\plan.json"  start a plan from the example, then edit it
kit lib_build "D:\Work\Lib\plan.json"              build into the plan's "output" folder (or --out)
```

| File | What it does |
|---|---|
| `build.py` | reads the plan, builds each component (rename to MPN, parameter set of its category from `rules/library_parameters.json`, Component Type / Category / Symbol added, shared symbol, one footprint link, overrides), writes the libraries and `_build_log.csv` |
| `buildsch.py` | SchLib records: read components, edit binary pins, write a SchLib with a template's header |
| `buildpcb.py` | copy footprints out of source PcbLibs under new names, with their 3D models, into a new PcbLib |
| `fpfix.py` | per footprint: silk 0.15 mm, courtyard = pads/body + margin rounded out to 0.05 mm (only plain rectangles are changed; the rest is logged) |
| `pcbparse.py`, `olew.py` | footprint stream parser; OLE writer (pywin32) and record helpers |

The plan (`kit lib_build --example` prints one):

| Key | Meaning |
|---|---|
| `source_schlib`, `source_pcblib` | the library being rebuilt (also the templates for the file headers, unless `template_schlib` / `template_pcblib` are given) |
| `output` | new folder; the libraries are named after it |
| `parts` | old component name -> `type`, `sub` (a subtype from `kit lib_params --list`), `fp` (new footprint name), optional `sym` (a key of `symbols`) and `ak` (diode: designators of anode and cathode) |
| `footprints` | new footprint name -> [source PcbLib, footprint name in it] |
| `symbols` | key -> `lib` (a SchLib with ONE component), `pins` (map its designators to ours, `"GSD"` to map a MOSFET by pin name, or null for a diode with `ak`), `name` (the Symbol parameter, LIB-37) |
| `own_symbol_names` | Symbol parameter for parts that keep their own drawing |
| `overrides` / `force` | parameter values to write where empty / always (each logged) |
| `category_alias` | old "Type/Subtype" -> name in the frozen list |
| `line_color`, `courtyard_margin_mm` | symbol line colour (Altium BGR integer as text); courtyard margin by default, for small chips and per Type |

The plan names client parts and paths: keep it in the client's folder, never in the kit (WF-09). After a build run
`kit pin_match`, `kit lib_params --check`, `kit lib_std_check`, `kit ws_lib_check` on the result, then 3D models with
`kit kicad_models` and `tools\altium_scripts\Swap3D.pas` inside Altium, and the review document with `kit fp_review`.
