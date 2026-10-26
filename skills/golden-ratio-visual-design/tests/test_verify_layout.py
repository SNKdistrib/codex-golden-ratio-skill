"""Synthetic unit tests; these are not proof of a real design's visual quality."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.dont_write_bytecode = True
MODULE = Path(__file__).resolve().parents[1] / "scripts" / "verify_layout.py"
spec = importlib.util.spec_from_file_location("verify_layout", MODULE)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def fixture_png(width, height):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + b"\0" * width * 3) * height)) + chunk(b"IEND", b""))


class VerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="golden-verifier-test-")
        # Confirm that automatic recursive cleanup stays in the intended temp parent.
        assert Path(cls.temp.name).resolve().parent == Path(tempfile.gettempdir()).resolve()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.image = Path(cls.temp.name) / "fixture.png"
        cls.image.write_bytes(fixture_png(1000, 700))

    def setUp(self):
        self.contract = {"version": 1, "canvas": {"width": 1000, "height": 700},
            "spacing_base": 8, "tolerance_px": 1,
            "rules": [
                {"id": "title_alignment", "type": "align", "a": "title", "b": "subtitle", "edge": "x"},
                {"id": "height_ratio", "type": "ratio", "a": {"box": "play", "value": "height"},
                 "b": {"box": "profile", "value": "height"}},
                {"id": "label_gap", "type": "gap", "axis": "y", "from": "label", "to": "profile", "exponent": 1},
                {"id": "control_gap", "type": "gap", "axis": "y", "from": "profile", "to": "play", "exponent": 2},
                {"id": "group_position", "type": "void_ratio", "axis": "y", "before": "subtitle", "after": "footer",
                 "group": ["label", "profile", "play"], "dominant": "after"}]}
        self.observed = {"version": 1, "kind": "observed", "canvas": {"width": 1000, "height": 700},
            "evidence": {"method": "manual", "image_sha256": hashlib.sha256(self.image.read_bytes()).hexdigest()},
            "boxes": {
                "title": {"x": 40, "y": 40, "width": 300, "height": 40},
                "subtitle": {"x": 40, "y": 93, "width": 200, "height": 20},
                "label": {"x": 40, "y": 250, "width": 100, "height": 13},
                "profile": {"x": 40, "y": 276, "width": 354, "height": 34},
                "play": {"x": 40, "y": 331, "width": 354, "height": 55},
                "footer": {"x": 40, "y": 386 + 137 * v.PHI, "width": 354, "height": 20}}}

    def run_verify(self):
        return v.verify(self.contract, self.observed, self.image)

    def test_valid_geometry(self):
        self.assertEqual(self.run_verify()["status"], "PASS")

    def test_local_pass_does_not_claim_global_conformity(self):
        report = self.run_verify()
        self.assertEqual(report["status_label"], "PASS_DECLARED_RULES_ONLY")
        self.assertEqual(report["global_composition_conformity"], "NOT_ESTABLISHED")

    def test_inner_void_ratio(self):
        self.contract["rules"][-1] = {"id": "group_position", "type": "inner_void_ratio",
            "container": "panel", "group": ["label", "profile", "play"], "axis": "y", "dominant": "after"}
        self.observed["boxes"]["panel"] = {"x": 30, "y": 113, "width": 380,
            "height": 273 + 137 * v.PHI}
        self.assertEqual(self.run_verify()["status"], "PASS")

    def test_inner_void_overflow_fails(self):
        self.contract["rules"][-1] = {"id": "group_position", "type": "inner_void_ratio",
            "container": "panel", "group": ["label", "profile", "play"], "axis": "y", "dominant": "after"}
        self.observed["boxes"]["panel"] = {"x": 30, "y": 300, "width": 380, "height": 100}
        self.assertEqual(self.run_verify()["status"], "FAIL")

    def test_inner_void_horizontal_overflow_fails(self):
        self.contract["rules"][-1] = {"id": "group_position", "type": "inner_void_ratio",
            "container": "panel", "group": ["label", "profile", "play"], "axis": "y", "dominant": "after"}
        self.observed["boxes"]["panel"] = {"x": 30, "y": 113, "width": 380,
            "height": 273 + 137 * v.PHI}
        self.observed["boxes"]["profile"]["x"] = 500
        result = self.run_verify()
        self.assertEqual(next(c["status"] for c in result["checks"] if c["id"] == "group_position"), "FAIL")

    def test_subtitle_alignment(self):
        self.observed["boxes"]["subtitle"]["x"] += 12
        self.assertEqual(self.run_verify()["status"], "FAIL")

    def test_label_gap(self):
        self.observed["boxes"]["label"]["y"] += 10
        self.assertEqual(self.run_verify()["status"], "FAIL")

    def test_profile_height(self):
        self.observed["boxes"]["profile"]["height"] = 45
        self.assertEqual(self.run_verify()["status"], "FAIL")

    def test_group_shift(self):
        for name in ["label", "profile", "play"]:
            self.observed["boxes"][name]["y"] += 30
        result = self.run_verify()
        self.assertEqual(next(c["status"] for c in result["checks"] if c["id"] == "group_position"), "FAIL")

    def test_missing_box(self):
        del self.observed["boxes"]["title"]
        self.assertEqual(self.run_verify()["status"], "UNVERIFIED")

    def test_hash_mismatch(self):
        self.observed["evidence"]["image_sha256"] = "0" * 64
        self.assertEqual(self.run_verify()["status"], "UNVERIFIED")

    def test_planned_not_observed(self):
        self.observed["kind"] = "planned"
        self.assertEqual(self.run_verify()["status"], "UNVERIFIED")

    def test_empty_rules(self):
        self.contract["rules"] = []
        self.assertEqual(self.run_verify()["status"], "UNVERIFIED")

    def test_wrong_image_dimensions(self):
        self.observed["pixel_ratio"] = 2
        self.assertEqual(self.run_verify()["status"], "UNVERIFIED")

    def test_aspect_distortion(self):
        self.contract["canvas"]["width"] = 1200
        self.assertEqual(self.run_verify()["status"], "FAIL")

    def test_invalid_width(self):
        self.observed["boxes"]["play"]["width"] = 0
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_outside_canvas(self):
        self.observed["boxes"]["title"]["x"] = -1
        self.assertEqual(self.run_verify()["status"], "FAIL")

    def test_no_tolerance_bypass(self):
        self.contract["tolerance_px"] = 999
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_no_zero_exponent_golden_claim(self):
        self.contract["rules"][1]["exponent"] = 0
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_nonfinite_input(self):
        self.observed["boxes"]["play"]["x"] = float("nan")
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_json_duplicate_key(self):
        p = Path(self.temp.name) / "duplicate.json"
        p.write_text('{"version":1,"version":2}', encoding="utf-8")
        with self.assertRaises(ValueError):
            v.load_json(p)

    def test_uniform_scaling(self):
        for box in self.observed["boxes"].values():
            for key in box:
                box[key] /= 2
        self.observed["canvas"] = {"width": 500, "height": 350}
        self.observed["pixel_ratio"] = 2
        self.assertEqual(self.run_verify()["status"], "PASS")

    def test_cli_does_not_overwrite_evidence(self):
        p = Path(self.temp.name) / "input.json"
        p.write_text(json.dumps(self.contract), encoding="utf-8")
        before = p.read_bytes()
        result = subprocess.run([sys.executable, str(MODULE), "--spec", str(p), "--measurements", str(p),
                                 "--image", str(self.image), "--out", str(p)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(p.read_bytes(), before)

    def test_coordinate_is_not_a_length_ratio(self):
        self.contract["rules"][1]["a"]["value"] = "x"
        with self.assertRaises(ValueError):
            self.run_verify()

    def test_zero_gap_even_with_rounding_tolerance(self):
        self.contract["spacing_base"] = 0.1
        self.observed["boxes"]["profile"]["y"] = 263
        result = self.run_verify()
        self.assertEqual(next(c["status"] for c in result["checks"] if c["id"] == "label_gap"), "FAIL")

    def test_jpeg_frame_dimensions(self):
        path = Path(self.temp.name) / "header-fixture.jpg"
        path.write_bytes(b"\xff\xd8\xff\xc0" + struct.pack(">HBHHB", 8, 8, 629, 1016, 0) + b"\xff\xd9")
        self.assertEqual(v.image_size(path), (1016, 629))

    def test_truncated_jpeg(self):
        path = Path(self.temp.name) / "truncated.jpg"
        path.write_bytes(b"\xff\xd8\xff\xc0\x00\xff")
        with self.assertRaises(ValueError):
            v.image_size(path)


if __name__ == "__main__":
    unittest.main()
