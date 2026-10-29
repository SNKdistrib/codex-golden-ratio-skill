"""Regression checks for visible glyph bounds; no OCR or aesthetic claims."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_verify_layout as fixtures

v = fixtures.v


class GlyphCenterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="glyph-centering-test-")
        assert Path(cls.temp.name).resolve().parent == Path(tempfile.gettempdir()).resolve()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.image = Path(cls.temp.name) / "fixture.png"
        cls.image.write_bytes(fixtures.fixture_png(1000, 700))

    def setUp(self):
        self.contract = {"version": 1, "canvas": {"width": 1000, "height": 700},
            "spacing_base": 8, "tolerance_px": 0.5,
            "profile": "glyph-centering", "scope_note": "Only the glyph inside this badge",
            "rules": [{"id": "glyph_center", "type": "glyph_center", "glyph": "euro", "container": "badge"}]}
        self.measured = {"version": 1, "kind": "observed", "canvas": {"width": 1000, "height": 700},
            "evidence": {"method": "manual", "image_sha256": hashlib.sha256(self.image.read_bytes()).hexdigest()},
            "boxes": {"badge": {"x": 100, "y": 100, "width": 100, "height": 100},
                      "euro": {"x": 130, "y": 120, "width": 40, "height": 60, "bounds_kind": "visible_ink"}}}

    def check(self):
        return v.verify(self.contract, self.measured, self.image)

    def test_centered_ink_passes_only_declared_scope(self):
        report = self.check()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["validation_profile"], "glyph-centering")
        self.assertEqual(report["global_composition_conformity"], "NOT_ESTABLISHED")

    def test_either_axis_offset_fails(self):
        for axis in ("x", "y"):
            with self.subTest(axis=axis):
                original = copy.deepcopy(self.measured)
                self.measured["boxes"]["euro"][axis] += 2
                self.assertEqual(self.check()["status"], "FAIL")
                self.measured = original

    def test_line_box_is_not_ink(self):
        self.measured["boxes"]["euro"]["bounds_kind"] = "line_box"
        self.assertEqual(self.check()["status"], "UNVERIFIED")

    def test_missing_glyph_is_unverified(self):
        del self.measured["boxes"]["euro"]
        self.assertEqual(self.check()["status"], "UNVERIFIED")

    def test_centered_but_oversize_glyph_fails(self):
        self.measured["boxes"]["euro"].update(x=90, width=120)
        self.assertEqual(self.check()["status"], "FAIL")

    def test_missing_scope_and_empty_checks_are_rejected(self):
        for field in ("scope_note", "rules"):
            with self.subTest(field=field):
                original = copy.deepcopy(self.contract)
                self.contract[field] = "" if field == "scope_note" else []
                with self.assertRaises(ValueError):
                    self.check()
                self.contract = original

    def test_default_composition_still_needs_four_categories(self):
        self.contract.pop("profile")
        self.assertEqual(self.check()["status"], "UNVERIFIED")

    def test_stale_evidence_cannot_pass(self):
        self.measured["evidence"]["image_sha256"] = "0" * 64
        self.assertEqual(self.check()["status"], "UNVERIFIED")

    def run_cli(self):
        contract = Path(self.temp.name) / "contract.json"
        observed = Path(self.temp.name) / "observed.json"
        contract.write_text(json.dumps(self.contract), encoding="utf-8")
        observed.write_text(json.dumps(self.measured), encoding="utf-8")
        result = subprocess.run([sys.executable, str(fixtures.MODULE), "--spec", str(contract),
                                 "--measurements", str(observed), "--image", str(self.image)],
                                capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def test_cli_pass_returns_zero(self):
        code, report = self.run_cli()
        self.assertEqual((code, report["status"]), (0, "PASS"))

    def test_cli_offset_blocks_delivery(self):
        self.measured["boxes"]["euro"]["y"] += 2
        code, report = self.run_cli()
        self.assertEqual((code, report["status"]), (1, "FAIL"))

    def test_cli_missing_ink_blocks_delivery(self):
        self.measured["boxes"]["euro"].pop("bounds_kind")
        code, report = self.run_cli()
        self.assertEqual((code, report["status"]), (2, "UNVERIFIED"))


if __name__ == "__main__":
    unittest.main()
