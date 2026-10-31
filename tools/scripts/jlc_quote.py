"""jlc_quote.py - JLCPCB assembly quote arithmetic: full cost when lines are short on stock (rule FAB-08, RQ-02).

Run from the workspace folder in cmd.exe, for example:
  python tools\\scripts\\jlc_quote.py shortfall ai\\quote_1000.json
  python tools\\scripts\\jlc_quote.py shortfall ai\\quote_1000.json --csv out\\quote_1000_shortfall.csv
  python tools\\scripts\\jlc_quote.py summary ai\\quote_*.json --csv out\\quote_summary.csv

When JLC cannot place some BOM lines at a quantity (stock shortfall), it quotes the board without them. This adds
them back with JLC's own rates, so the total reads as if nothing were short. Input JSON (one board, one quantity):
{
 "board": "EXT01", "quantity": 1000, "quoted_total_usd": 1015.43,
 "quoted": {"pcb": 120.0, "setup": 25.75, "stencil": 8.27, "parts": 300.1, "feeder": 10.85, "smt": 14.2, "other": 2.9},
 "rates_file": "rules/fab-profiles/jlcpcb_assembly.json",      (optional; "rates": {...} overrides single values)
 "short": [ {"designator": "J102", "lcsc": "C6291464", "line_cost_usd": 220.80, "extended": true,
             "mount": "tht", "joints_per_board": 3} ]
}
line_cost_usd = the parts cost JLC shows for that line at this quantity (the line's unit price x needed quantity);
if only a unit price is known give "unit_usd" and "qty_per_board" instead.
Rates (observed in quotes, re-read them from a fresh quote of the same day before relying on them):
  feeder_per_extended_type_usd, smt_per_joint_usd, tht_per_joint_usd, tht_per_board_usd.
Output: added cost per short line (parts + feeder + joints) and the full total. Excludes shipping and tax.
Python standard library only. Exit 0 = PASS, 1 = FAIL (missing data).
"""
import argparse, csv, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_RATES = os.path.join(ROOT, "rules", "fab-profiles", "jlcpcb_assembly.json")


def load_rates(q):
    path = q.get("rates_file") or DEFAULT_RATES
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    rates = json.load(open(path, encoding="utf-8")).get("rates", {}) if os.path.isfile(path) else {}
    rates = {k: (v["value"] if isinstance(v, dict) else v) for k, v in rates.items()}
    rates.update(q.get("rates", {}))
    return rates


def shortfall(q):
    rates, n = load_rates(q), int(q["quantity"])
    need = ("feeder_per_extended_type_usd", "smt_per_joint_usd", "tht_per_joint_usd", "tht_per_board_usd")
    missing = [k for k in need if k not in rates]
    if missing:
        raise ValueError(f"rates missing: {missing}")
    lines = []
    for s in q.get("short", []):
        if "line_cost_usd" in s:
            parts = float(s["line_cost_usd"])
        else:
            parts = float(s["unit_usd"]) * float(s["qty_per_board"]) * n
        feeder = rates["feeder_per_extended_type_usd"] if s.get("extended", True) else 0.0
        joints = int(s.get("joints_per_board", 2)) * n
        if s.get("mount", "smt") == "tht":
            labour = joints * rates["tht_per_joint_usd"] + n * rates["tht_per_board_usd"]
        else:
            labour = joints * rates["smt_per_joint_usd"]
        lines.append({"designator": s.get("designator", ""), "lcsc": s.get("lcsc", ""), "parts_usd": round(parts, 2),
                      "feeder_usd": round(feeder, 2), "joints": joints, "labour_usd": round(labour, 2),
                      "added_usd": round(parts + feeder + labour, 2)})
    added = round(sum(l["added_usd"] for l in lines), 2)
    total = round(float(q["quoted_total_usd"]) + added, 2)
    return {"board": q.get("board", ""), "quantity": n, "quoted_total_usd": float(q["quoted_total_usd"]),
            "added_usd": added, "full_total_usd": total, "per_board_usd": round(total / n, 4), "lines": lines,
            "rates": rates}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shortfall"); s.add_argument("quote"); s.add_argument("--csv")
    m = sub.add_parser("summary"); m.add_argument("quotes", nargs="+"); m.add_argument("--csv")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "shortfall":
            r = shortfall(json.load(open(a.quote, encoding="utf-8")))
            for l in r["lines"]:
                print(f"{l['designator']:<14} {l['lcsc']:<10} parts ${l['parts_usd']:.2f} feeder ${l['feeder_usd']:.2f} "
                      f"{l['joints']} joints ${l['labour_usd']:.2f} -> +${l['added_usd']:.2f}")
            print(f"{r['board']} x{r['quantity']}: JLC quote ${r['quoted_total_usd']:.2f} + short lines ${r['added_usd']:.2f}"
                  f" = full ${r['full_total_usd']:.2f} (${r['per_board_usd']:.4f}/board, shipping excluded)")
            if a.csv:
                with open(a.csv, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(r["lines"][0]) if r["lines"] else ["designator"])
                    w.writeheader(); w.writerows(r["lines"])
            return 0
        files = [p for pat in a.quotes for p in (glob.glob(pat) or [pat])]
        rows = [shortfall(json.load(open(p, encoding="utf-8"))) for p in files]
        rows.sort(key=lambda r: (r["board"], r["quantity"]))
        print(f"{'Board':<14}{'Qty':>7}{'JLC quote':>14}{'Short lines':>14}{'Full total':>14}{'Per board':>12}")
        for r in rows:
            print(f"{r['board']:<14}{r['quantity']:>7}{r['quoted_total_usd']:>14.2f}{r['added_usd']:>14.2f}"
                  f"{r['full_total_usd']:>14.2f}{r['per_board_usd']:>12.4f}")
        if a.csv:
            with open(a.csv, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Board", "Quantity", "JLC quote USD", "Short lines USD", "Full total USD", "Per board USD"])
                for r in rows:
                    w.writerow([r["board"], r["quantity"], r["quoted_total_usd"], r["added_usd"], r["full_total_usd"],
                                r["per_board_usd"]])
        return 0
    except (KeyError, ValueError) as e:
        print("FAIL", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
