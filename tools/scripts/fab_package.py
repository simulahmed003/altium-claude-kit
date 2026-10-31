"""fab_package.py - check (or start) a production package folder for the manufacturer (rule FAB-05).

Run from the workspace folder in cmd.exe, for example:
  python tools\\scripts\\fab_package.py check "D:\\Work\\Acme\\Board1\\Manufacturing_BOARD1_Rev1.0"
  python tools\\scripts\\fab_package.py readme "D:\\Work\\Acme\\Board1\\Manufacturing_BOARD1_Rev1.0" --board BOARD1 --rev 1.0
      --layers 2 --size 15.4x13.2 --thickness 1.6 --finish "LeadFree HASL" --side Top --tht J102

What goes to the manufacturer (the folder top level):
  <board>_Rev<x>_Gerber.zip   copper, mask, paste, silk, outline and drill (PTH + NPTH) files
  <board>_BOM.csv             (or .xlsx) checked with bom_check.py
  <board>_CPL.csv             (or .xlsx) checked with cpl_check.py
  <board>_Assembly*.pdf       optional assembly drawing
  README.txt                  board spec and assembly notes
Never in it: the schematic (any .SchDoc, .kicad_sch, schematic PDF), design sources (.PcbDoc, .kicad_pcb,
.PrjPcb, .kicad_pro, libraries), backups (.bak) and reference files (old CPLs, correction lists): keep those in a
`reference\\` sub-folder, which this check ignores and which is never uploaded.
check:  lists every problem; also opens the Gerber zip and looks for copper, mask, silk, outline and drill files.
readme: writes README.txt from the options (refuses to overwrite one; delete it first to rebuild).
Python standard library only. Exit 0 = PASS, 1 = FAIL.
"""
import argparse, os, re, sys, zipfile

FORBIDDEN = re.compile(r"\.(schdoc|kicad_sch|sch|pcbdoc|kicad_pcb|prjpcb|kicad_pro|schlib|pcblib|kicad_sym|kicad_mod|"
                       r"dblib|bak|outjob)$|schematic", re.I)
GERBER_NEED = {
    "copper": re.compile(r"\.(gtl|gbl|g\d+|gl\d+)$|[-_.]cu\.|copper|_top\.g|_bottom\.g", re.I),
    "solder mask": re.compile(r"\.(gts|gbs)$|mask", re.I),
    "silkscreen": re.compile(r"\.(gto|gbo)$|silk", re.I),
    "outline": re.compile(r"\.(gko|gm\d*)$|edge[_.]?cuts|outline|profile", re.I),
    "drill": re.compile(r"\.(drl|txt|xln|exc)$|drill", re.I),
}


def check(folder):
    errs, notes = [], []
    if not os.path.isdir(folder):
        return [f"{folder} is not a folder"], notes
    top = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    for f in top:
        if FORBIDDEN.search(f):
            errs.append(f"{f}: must not go to the manufacturer (schematic, design source or backup); move it to reference\\")
        if re.search(r"before|correction|[_-]old\b|_ref\b", f, re.I):
            errs.append(f"{f}: reference file in the upload folder; move it to reference\\")
    zips = [f for f in top if f.lower().endswith(".zip") and "gerber" in f.lower()]
    boms = [f for f in top if re.search(r"bom", f, re.I) and f.lower().endswith((".csv", ".xlsx", ".xls"))]
    cpls = [f for f in top if re.search(r"cpl|pick|pos", f, re.I) and f.lower().endswith((".csv", ".xlsx", ".xls"))]
    for what, lst in (("Gerber zip (name contains 'Gerber')", zips), ("BOM file", boms), ("CPL file", cpls)):
        if len(lst) != 1:
            errs.append(f"{what}: expected 1, found {len(lst)} {lst}")
    if "README.txt" not in top:
        errs.append("README.txt missing (board spec and assembly notes; `fab_package.py readme` writes one)")
    if not any(f.lower().endswith(".pdf") and "assembl" in f.lower() for f in top):
        notes.append("no assembly drawing PDF (optional)")
    for z in zips:
        try:
            with zipfile.ZipFile(os.path.join(folder, z)) as zf:
                names = zf.namelist()
        except zipfile.BadZipFile:
            errs.append(f"{z}: not a readable zip"); continue
        for n in names:
            if FORBIDDEN.search(n):
                errs.append(f"{z}: contains {n} (design source or schematic)")
        for kind, rx in GERBER_NEED.items():
            if not any(rx.search(os.path.basename(n)) for n in names):
                errs.append(f"{z}: no {kind} file found")
        notes.append(f"{z}: {len(names)} files")
    return errs, notes


README = """{board} Rev {rev} - production files
==========================================
Files
  {board}_Rev{rev}_Gerber.zip   Gerber + drill
  {board}_BOM.csv               bill of materials (LCSC Part # used for assembly; MPN, Mouser, DigiKey for reference)
  {board}_CPL.csv               pick and place (mm, rotation in degrees, JLC convention, checked per FAB-06)
  {board}_Assembly.pdf          assembly drawing (if present)

Board
  Layers          {layers}
  Size            {size} mm
  Thickness       {thickness} mm
  Copper          {copper}
  Surface finish  {finish}
  Vias            {vias}
  Assembly side   {side}
  Through-hole    {tht}

Notes
{notes}
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("folder")
    r = sub.add_parser("readme"); r.add_argument("folder")
    for k, d in (("board", None), ("rev", None), ("layers", None), ("size", None), ("thickness", "1.6"),
                 ("copper", "1 oz outer"), ("finish", "HASL lead-free"), ("vias", "tented"), ("side", "Top"),
                 ("tht", "none"), ("notes", "-")):
        r.add_argument("--" + k, required=d is None, default=d)
    a = ap.parse_args(argv)
    if a.cmd == "readme":
        p = os.path.join(a.folder, "README.txt")
        if os.path.exists(p):
            print(f"FAIL {p} exists; delete it first to rebuild"); return 1
        os.makedirs(a.folder, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(README.format(**{k: v for k, v in vars(a).items() if k not in ("cmd", "folder")}))
        print(f"wrote {p}"); return 0
    errs, notes = check(a.folder)
    for e in errs:
        print("FAIL", e)
    for n in notes:
        print("NOTE", n)
    print(f"{len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
