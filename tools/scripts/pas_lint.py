"""pas_lint.py - check a DelphiScript (.pas) before it runs inside Altium, for what stops Altium's script engine (TOOL-21).

Usage:
  python pas_lint.py <script.pas> [<script.pas> ...]      one line per finding, exit 1 when any FAIL
  python pas_lint.py <folder>                              every .pas in it (not recursive)
  python pas_lint.py <script.pas> --allow-modal            a script the user runs by hand may show a message box
Checks (wedge study 2026-11-07 and LESSONS T5-T8, L10-L13):
  FAIL  UTF-8 byte-order mark at the start: Altium reads it as "Unknown identifier: ï" and stops in the debugger
  FAIL  unfilled template token (%NAME%): "Expression expected but % found"; the server that fills it is not running
  FAIL  modal calls in an agent script (ShowMessage, ShowInfo, ShowWarning, ShowError, MessageDlg, InputBox,
        InputQuery, ConfirmNoYes, .ShowModal): nobody answers them and every later script waits (TOOL-05, TOOL-07)
  FAIL  identifiers that crash or do not exist in AD24-26 (TOOL-06, TOOL-18): StrictDelimiter, DelimitedText,
        Model.Rotation_X, LayerObject_V7, PrintPreview, -REditScript:Stop
  WARN  a script that changes documents (AddPCBObject, AddSchObject, RegisterSchObjectInContainer, RemovePCBObject,
        .Modified, SaveDocument) without try/except or try/finally: an error stops it halfway through an edit
  WARN  PcbLib footprint loop that adds or moves primitives without SetState_CurrentComponent (TOOL-19: only the
        current footprint has board-origin coordinates; the others landed 1270 mm away)
  WARN  .Free on an object that is used again later in the file ("Undeclared identifier: Free", a freed object)
  WARN  non-ASCII characters outside comments and strings
Comments ({ }, (* *), //) and string literals are ignored for the identifier checks.
"""
import argparse, os, re, sys

MODAL = r"\b(ShowMessage|ShowInfo|ShowWarning|ShowError|MessageDlg|InputBox|InputQuery|ConfirmNoYes|ConfirmOkCancel)\s*\(|\.ShowModal\b"
BAD = {r"\bStrictDelimiter\b": "TStringList.StrictDelimiter crashes the engine (TOOL-06)",
       r"\bDelimitedText\b": "DelimitedText crashes the engine (TOOL-06)",
       r"\bRotation_X\b": "Model.Rotation_X does not exist (TOOL-18)",
       r"\bLayerObject_V7\b": "LayerObject_V7 does not exist in AD24-26 (TOOL-18)",
       r"\bPrintPreview\b": "print preview opens a modal (TOOL-07)"}
EDITS = r"\b(AddPCBObject|AddSchObject|RegisterSchObjectInContainer|RemovePCBObject|SaveDocument|SaveToFile)\b|\.Modified\s*:="
TOKEN = r"%[A-Z][A-Z0-9_]{2,}%"


def strip_code(src):
    """source with comments and string literals blanked (same length, line breaks kept)."""
    out, i, n = [], 0, len(src)
    blank = lambda s: re.sub(r"[^\n]", " ", s)
    while i < n:
        c = src[i]
        if c == "{":
            j = src.find("}", i)
            j = n if j < 0 else j + 1
        elif src.startswith("(*", i):
            j = src.find("*)", i)
            j = n if j < 0 else j + 2
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
        elif c == "'":
            j = i + 1
            while j < n and not (src[j] == "'" and not src.startswith("''", j)):
                j += 2 if src.startswith("''", j) else 1
            j = min(n, j + 1)
        else:
            out.append(c)
            i += 1
            continue
        out.append(blank(src[i:j]))
        i = j
    return "".join(out)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def lint_text(raw, allow_modal=False):
    """raw: bytes of the file -> [(level, line, message)]."""
    found = []
    if raw.startswith(b"\xef\xbb\xbf"):
        found.append(("FAIL", 1, "UTF-8 byte-order mark: save without BOM (Altium: 'Unknown identifier: ï')"))
        raw = raw[3:]
    try:
        src = raw.decode("utf-8")
    except UnicodeDecodeError:
        src = raw.decode("cp1252", errors="replace")
    code = strip_code(src)
    for m in re.finditer(TOKEN, src):
        found.append(("FAIL", line_of(src, m.start()), f"unfilled template token {m.group(0)}"))
    if not allow_modal:
        for m in re.finditer(MODAL, code, re.I):
            found.append(("FAIL", line_of(code, m.start()), f"modal call {m.group(0).strip('( ')}: nobody answers it, "
                                                          "every later script waits (write to a log file instead)"))
    for pat, why in BAD.items():
        for m in re.finditer(pat, code):
            found.append(("FAIL", line_of(code, m.start()), why))
    for m in re.finditer(r"REditScript\s*:\s*Stop", src, re.I):
        found.append(("FAIL", line_of(src, m.start()), "-REditScript:Stop can start a second Altium (TOOL-18)"))
    edits = re.search(EDITS, code, re.I)
    if edits and not re.search(r"\btry\b", code, re.I):
        found.append(("WARN", line_of(code, edits.start()), "changes documents without try/except or try/finally: "
                                                           "an error stops it halfway through the edit"))
    if re.search(r"\bLibraryIterator_Create\b|\bGetComponent\s*\(|\bGetComponentByName\b", code) \
            and re.search(r"\b(AddPCBObject|MoveByXY|\.X\s*:=|\.Y\s*:=|\.Model\b)", code) \
            and not re.search(r"\bSetState_CurrentComponent\b", code):
        found.append(("WARN", 1, "PcbLib loop edits primitives without SetState_CurrentComponent: only the current "
                                 "footprint is at the board origin (TOOL-19)"))
    for m in re.finditer(r"\b(\w+)\.Free\b", code):
        var = m.group(1)
        if re.search(rf"\b{re.escape(var)}\s*\.(?!Free\b)\w", code[m.end():]) and \
                not re.search(rf"\b{re.escape(var)}\s*:=", code[m.end():]):
            found.append(("WARN", line_of(code, m.start()), f"{var}.Free, then {var} is used again (a freed object: "
                                                         "'Undeclared identifier: Free')"))
    for m in re.finditer(r"[^\x00-\x7f]", code):
        found.append(("WARN", line_of(code, m.start()), f"non-ASCII character {m.group(0)!r} in code"))
        break
    return sorted(found, key=lambda f: (f[1], f[0]))


def files_of(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(".pas"))
        else:
            out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--allow-modal", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    fails = warns = 0
    files = files_of(a.paths)
    for f in files:
        try:
            raw = open(f, "rb").read()
        except OSError as e:
            print(f"FAIL  {f}: {e}")
            fails += 1
            continue
        res = lint_text(raw, a.allow_modal)
        for lvl, ln, msg in res:
            print(f"{lvl:4}  {os.path.basename(f)}:{ln}  {msg}")
        fails += sum(r[0] == "FAIL" for r in res)
        warns += sum(r[0] == "WARN" for r in res)
        if not res:
            print(f"PASS  {os.path.basename(f)}")
    print(f"pas_lint: {len(files)} file(s), {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
