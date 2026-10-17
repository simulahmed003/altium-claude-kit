"""calcs_run.py - run a project's calculations from ai/calc_inputs.json with calclib (rule RQ-02).

Usage:
  python calcs_run.py <calc_inputs.json> [--md]
calc_inputs.json:
  {"checks": [{"name": "FB divider 20.0k / 4.99k", "fn": "divider_worst",
               "args": {"vref3": [0.985, 1.0, 1.015], "rt": 20000, "rb": 4990, "r_tol": 0.001},
               "ref": 5.0,                         (optional: also print min/max as % of ref)
               "limits": {"lo_pct": [-2, 2], "hi_pct": [-2, 2]},   (optional: [min, max] per result key)
               "source": "lmr33630.pdf Eq. 3"}]}
A plain-number result is reported under the key "value". --md prints a table for calcs.md.
Exit 0 when every limit holds, 1 otherwise.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calclib


def run(inputs):
    rows, fails = [], 0
    for c in inputs["checks"]:
        fn = getattr(calclib, c["fn"])
        args = {k: tuple(v) if isinstance(v, list) else v for k, v in c["args"].items()}
        r = fn(**args)
        r = dict(r) if isinstance(r, dict) else dict(value=r)
        if "ref" in c:
            for k in ("lo", "hi", "nom", "value"):
                if k in r and isinstance(r[k], (int, float)):
                    r[k + "_pct"] = calclib.pct(r[k], c["ref"])
        bad = [f"{k} {r.get(k)} outside {lim}" for k, lim in c.get("limits", {}).items()
               if not (lim[0] <= r.get(k, float("nan")) <= lim[1])]
        fails += bool(bad)
        rows.append(dict(name=c["name"], result=r, ok=not bad, why=bad, source=c.get("source", "")))
    return rows, fails


def fmt(v):
    return f"{v:.4g}" if isinstance(v, float) else str(v)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("inputs")
    ap.add_argument("--md", action="store_true")
    a = ap.parse_args(argv)
    rows, fails = run(json.load(open(a.inputs, encoding="utf-8")))
    if a.md:
        print("| Check | Result | Status | Source |\n|---|---|---|---|")
    for r in rows:
        res = ", ".join(f"{k} {fmt(v)}" for k, v in r["result"].items())
        if a.md:
            print(f"| {r['name']} | {res} | {'PASS' if r['ok'] else 'FAIL'} | {r['source']} |")
        else:
            print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['name']}: {res}" + (f"  <- {'; '.join(r['why'])}" if r["why"] else ""))
    print(f"{len(rows)} checks, {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
