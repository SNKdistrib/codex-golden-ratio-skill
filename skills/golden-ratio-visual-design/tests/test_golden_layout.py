"""Calculator invariants; these do not validate the aesthetics of a design."""
import importlib.util
import math
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "golden_layout.py"
spec = importlib.util.spec_from_file_location("golden_layout", MODULE)
layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


class CalculatorTests(unittest.TestCase):
    def test_horizontal_split_subtracts_margins_and_gap(self):
        result = layout.calculate(1016, 629, 34, 21, "x")
        a, b = result["main"], result["secondary"]
        self.assertAlmostEqual(a["width"] + b["width"] + 21, 1016 - 68)
        self.assertAlmostEqual(a["width"] / b["width"], layout.PHI)
        self.assertAlmostEqual(a["x"], 34)
        self.assertAlmostEqual(b["x"] + b["width"], 1016 - 34)

    def test_vertical_split_subtracts_margins_and_gap(self):
        result = layout.calculate(800, 1000, 21, 13, "y")
        a, b = result["main"], result["secondary"]
        self.assertAlmostEqual(a["height"] + b["height"] + 13, 1000 - 42)
        self.assertAlmostEqual(a["height"] / b["height"], layout.PHI)
        self.assertAlmostEqual(b["y"] + b["height"], 1000 - 21)

    def test_focus_positions_are_inside_usable_canvas(self):
        result = layout.calculate(1000, 700, 34)
        for axis, total in (("x", 1000), ("y", 700)):
            first, second = result["golden_focus_positions"][axis]
            self.assertGreater(first, 34)
            self.assertLess(second, total - 34)
            self.assertAlmostEqual((second - 34) / (first - 34), layout.PHI)

    def test_invalid_dimensions_are_rejected(self):
        cases = [(0, 700, 0, 0), (100, -1, 0, 0), (100, 100, -1, 0),
                 (100, 100, 0, -1), (100, 100, 50, 0), (100, 100, 0, 100),
                 (math.inf, 100, 0, 0), (100, math.nan, 0, 0)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                layout.calculate(*args)

    def test_invalid_axis_is_rejected(self):
        with self.assertRaises(ValueError):
            layout.calculate(100, 100, axis="z")


if __name__ == "__main__":
    unittest.main()
