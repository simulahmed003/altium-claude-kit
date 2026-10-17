"""schdoc_text.py - read-only dump of designator / visible parameter text positions from a saved .SchDoc.
   python schdoc_text.py <file.SchDoc>   (positions in mil)"""
import struct, sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import pin_match as m


def records(path):
    c = m.CFB(path)
    e = next(x for x in c.ents if x["name"] == "FileHeader")
    data, o, out = c._read(e), 0, []
    while o + 4 <= len(data):
        ln = struct.unpack_from("<H", data, o)[0]; kind = data[o + 3]; r = data[o + 4:o + 4 + ln]; o += 4 + ln
        t = r.rstrip(b"\0").decode("latin-1", "replace") if kind == 0 else ""
        out.append({kv.split("=", 1)[0].upper(): kv.split("=", 1)[1] for kv in t.split("|") if "=" in kv})
    return out


def mil(r, k):
    return int(r.get(f"LOCATION.{k}", 0)) * 10 + int(r.get(f"LOCATION_FRAC.{k}", 0)) // 10000


if __name__ == "__main__":
    recs = records(sys.argv[1])
    body = recs[1:]                      # OWNERINDEX counts records after the header
    for i, r in enumerate(body):
        if r.get("RECORD") == "34":
            comp = body[int(r["OWNERINDEX"])]
            print(f'{r.get("TEXT"):5} part=({mil(comp,"X")},{mil(comp,"Y")}) o{comp.get("ORIENTATION","0")}'
                  f'{" mir" if comp.get("ISMIRRORED")=="T" else ""}  desig=({mil(r,"X")},{mil(r,"Y")}) o{r.get("ORIENTATION","0")}'
                  f' just{r.get("JUSTIFICATION","0")} font{r.get("FONTID")}{" HIDDEN" if r.get("ISHIDDEN")=="T" else ""}')
