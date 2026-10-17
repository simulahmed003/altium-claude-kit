"""Unit tests for calclib.py. Expected values: buck-12v-5v-3a calcs.md (calcs_check.py output, 2026-10-13)
and hand-checked closed forms."""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import calclib as c


class Divider(unittest.TestCase):
    def test_nominal(self):
        self.assertAlmostEqual(c.divider_vout(1.0, 20e3, 4.99e3), 5.008, places=3)

    def test_worst_case_buck(self):
        w = c.divider_worst((0.985, 1.0, 1.015), 20e3, 4.99e3, 0.001)
        self.assertAlmostEqual(c.pct(w["lo"], 5), -1.50, places=2)
        self.assertAlmostEqual(c.pct(w["hi"], 5), 1.83, places=2)

    def test_zero_tolerance_is_vref_spread(self):
        w = c.divider_worst((0.99, 1.0, 1.01), 4e3, 1e3, 0.0)
        self.assertAlmostEqual(w["lo"], 4.95)
        self.assertAlmostEqual(w["hi"], 5.05)


class Inductor(unittest.TestCase):
    def test_ripple_buck(self):
        self.assertAlmostEqual(c.inductor_ripple(18, 5, 340e3, 10e-6), 1.062, places=3)

    def test_inverse(self):
        L = c.inductor_for_ripple(12, 5, 400e3, 0.3, 3)
        self.assertAlmostEqual(c.inductor_ripple(12, 5, 400e3, L), 0.9, places=6)

    def test_isat(self):
        r = c.inductor_check(3, 1.062, 6.2, 6.9, isc_max=5.05)
        self.assertTrue(r["isat_ok"] and r["irms_ok"])
        self.assertAlmostEqual(r["peak"], 3.531, places=3)
        self.assertFalse(c.inductor_check(3, 1.0, 4.0, 6.9, isc_max=5.05)["isat_ok"])


class Caps(unittest.TestCase):
    def test_derating(self):
        self.assertAlmostEqual(c.cap_derated(22e-6, 0.2, 0.1), 22e-6 * 0.72)


class Uvlo(unittest.TestCase):
    def test_buck_en(self):
        r = c.en_uvlo((1.2, 1.231, 1.26), 0.1, 51e3, 10e3, 0.01)
        self.assertAlmostEqual(r["von"], 7.51, places=2)
        self.assertAlmostEqual(r["von_min"], 7.20, places=2)
        self.assertAlmostEqual(r["von_max"], 7.82, places=2)
        self.assertAlmostEqual(r["voff"], 6.90, places=2)


class Thermal(unittest.TestCase):
    def test_buck_tj(self):
        p = c.loss_from_efficiency(15, 0.93)
        self.assertAlmostEqual(p, 1.129, places=3)
        self.assertAlmostEqual(c.junction_temp(50, 43, p), 98.5, places=1)
        self.assertAlmostEqual(c.rth_needed(125, 50, p), 66.4, places=1)


class Trace(unittest.TestCase):
    def test_buck_widths(self):
        self.assertAlmostEqual(c.trace_width_ipc2221(3.0), 1.37, places=2)
        self.assertAlmostEqual(c.trace_width_ipc2221(1.79), 0.67, places=2)

    def test_internal_wider(self):
        self.assertGreater(c.trace_width_ipc2221(2, external=False), c.trace_width_ipc2221(2))

    def test_2oz_halves_width(self):
        self.assertAlmostEqual(c.trace_width_ipc2221(2, oz=2) * 2, c.trace_width_ipc2221(2, oz=1))


if __name__ == "__main__":
    unittest.main()
