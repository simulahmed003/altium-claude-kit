"""calclib.py - engineering calculations used by every project (rule RQ-02). Standard library only.

Import it:  from calclib import divider_worst, ...      Run it:  python calclib.py --help
Units: V, A, Ohm, H, F, Hz, C, W, mm. Triples are (min, typ, max). Each function cites its formula.
  divider_vout(vref, rt, rb)                         VOUT = VREF (1 + RT/RB)
  divider_worst(vref3, rt, rb, r_tol)                nominal and worst case with resistor tolerance
  inductor_ripple(vin, vout, fsw, L)                 dI = VOUT (1 - VOUT/VIN) / (fsw L)
  inductor_for_ripple(vin, vout, fsw, k, iout)       L = (VIN - VOUT) VOUT / (fsw k IOUT VIN)
  inductor_check(iout, ripple, isat, irms_rating, isc_max=None)   peak, rms, Isat / Irms margins
  cap_derated(c, tol, dc_bias_loss)                  C_eff = C (1 - tol) (1 - bias loss)
  en_uvlo(ven3, hys, rt, rb, r_tol)                  VON = VEN (1 + RT/RB), VOFF = VON (1 - HYS/VEN_typ)
  loss_from_efficiency(pout, eta)                    P = POUT (1 - eta) / eta
  junction_temp(ta, rth_ja, p)                       TJ = TA + RthJA P
  rth_needed(tj_max, ta, p)                          RthJA <= (TJmax - TA) / P
  trace_width_ipc2221(amps, oz=1, dT=10, external=True)   IPC-2221 width in mm
"""
import math, sys


def divider_vout(vref, rt, rb):
    return vref * (1 + rt / rb)


def divider_worst(vref3, rt, rb, r_tol):
    vmin, vtyp, vmax = vref3
    nom = divider_vout(vtyp, rt, rb)
    lo = vmin * (1 + rt * (1 - r_tol) / (rb * (1 + r_tol)))
    hi = vmax * (1 + rt * (1 + r_tol) / (rb * (1 - r_tol)))
    return dict(nom=nom, lo=lo, hi=hi)


def pct(v, ref):
    return (v / ref - 1) * 100


def inductor_ripple(vin, vout, fsw, L):
    return vout * (1 - vout / vin) / (fsw * L)


def inductor_for_ripple(vin, vout, fsw, k, iout):
    return (vin - vout) * vout / (fsw * k * iout * vin)


def inductor_check(iout, ripple, isat, irms_rating, isc_max=None):
    peak = iout + ripple / 2
    rms = math.sqrt(iout ** 2 + ripple ** 2 / 12)
    need = max(peak, isc_max or 0)
    return dict(peak=peak, rms=rms, isat_need=need, isat_ok=isat >= need, irms_ok=irms_rating >= rms)


def cap_derated(c, tol, dc_bias_loss):
    return c * (1 - tol) * (1 - dc_bias_loss)


def en_uvlo(ven3, hys, rt, rb, r_tol):
    vmin, vtyp, vmax = ven3
    von = vtyp * (1 + rt / rb)
    lo = vmin * (1 + rt * (1 - r_tol) / (rb * (1 + r_tol)))
    hi = vmax * (1 + rt * (1 + r_tol) / (rb * (1 - r_tol)))
    return dict(von=von, von_min=lo, von_max=hi, voff=von * (1 - hys / vtyp))


def loss_from_efficiency(pout, eta):
    return pout * (1 - eta) / eta


def junction_temp(ta, rth_ja, p):
    return ta + rth_ja * p


def rth_needed(tj_max, ta, p):
    return (tj_max - ta) / p


def trace_width_ipc2221(amps, oz=1.0, dT=10.0, external=True):
    k = 0.048 if external else 0.024
    area = (amps / (k * dT ** 0.44)) ** (1 / 0.725)          # mil^2
    return area / (1.378 * oz) * 0.0254                        # mil -> mm


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--demo", action="store_true", help="print one example of each function")
    a = ap.parse_args(argv)
    if a.demo:
        w = divider_worst((0.985, 1.0, 1.015), 20e3, 4.99e3, 0.001)
        print(f"divider 20.0k/4.99k: {w['nom']:.4f} V, {pct(w['lo'], 5):+.2f} % / {pct(w['hi'], 5):+.2f} %")
        print(f"trace 3 A 1 oz 10 C: {trace_width_ipc2221(3):.2f} mm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
