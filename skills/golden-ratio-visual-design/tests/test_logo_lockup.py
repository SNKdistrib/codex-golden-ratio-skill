"""Three-part lockup regression tests and a real export gate; no OCR claims."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_verify_layout as fixtures

v = fixtures.v


class LockupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="logo-lockup-test-")
        assert Path(cls.temp.name).resolve().parent == Path(tempfile.gettempdir()).resolve()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.image = Path(cls.temp.name) / "fixture.png"
        cls.image.write_bytes(fixtures.fixture_png(1000, 700))

    def setUp(self):
        gap_x, gap_y = 5*v.PHI**3, 5*v.PHI**2
        mark_h, word_h = 100, 100/v.PHI
        tag_h = word_h/v.PHI**2
        row_w = 100 + gap_x + 400
        left = (1000-row_w)/2
        top = (700-mark_h-gap_y-tag_h)/2
        self.contract = {"version":1,"profile":"logo-lockup","scope_note":"Only this three-part logo",
            "canvas":{"width":1000,"height":700},"spacing_base":5,"tolerance_px":1,
            "rules":[{"id":"brand","type":"lockup","mark":"mark","wordmark":"word","tagline":"tag",
                      "horizontal_gap_exponent":3,"vertical_gap_exponent":2,"safe_margin":20,
                      "row_alignment":"center_y","tagline_alignment":"center_x","upper_width":"free",
                      "center_on_canvas":True,"mark_to_wordmark_exponent":1,"wordmark_to_tagline_exponent":2}]}
        self.measured = {"version":1,"kind":"observed","canvas":{"width":1000,"height":700},
            "evidence":{"method":"manual","image_sha256":hashlib.sha256(self.image.read_bytes()).hexdigest()},
            "boxes":{"mark":{"x":left,"y":top,"width":100,"height":mark_h,"bounds_kind":"visible_ink"},
                     "word":{"x":left+100+gap_x,"y":top+(mark_h-word_h)/2,"width":400,"height":word_h,"bounds_kind":"visible_ink"},
                     "tag":{"x":275,"y":top+mark_h+gap_y,"width":450,"height":tag_h,"bounds_kind":"visible_ink"}}}

    def report(self):
        return v.verify(self.contract,self.measured,self.image)

    def test_all_roles_and_named_relationships_pass(self):
        report=self.report()
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['validation_profile'],'logo-lockup')
        self.assertEqual(report['global_composition_conformity'],'NOT_ESTABLISHED')

    def test_mark_wordmark_vertical_offset_fails(self):
        self.measured['boxes']['word']['y']+=4
        self.assertEqual(self.report()['status'],'FAIL')

    def test_tagline_horizontal_offset_fails(self):
        self.measured['boxes']['tag']['x']+=4
        self.assertEqual(self.report()['status'],'FAIL')

    def test_whole_group_offset_fails(self):
        for box in self.measured['boxes'].values():box['x']+=5
        self.assertEqual(self.report()['status'],'FAIL')

    def test_missing_role_is_unverified(self):
        del self.measured['boxes']['tag']
        self.assertEqual(self.report()['status'],'UNVERIFIED')

    def test_line_box_is_not_ink(self):
        self.measured['boxes']['word']['bounds_kind']='line_box'
        self.assertEqual(self.report()['status'],'UNVERIFIED')

    def test_extra_observed_element_cannot_be_ignored(self):
        self.measured['boxes']['extra']=dict(self.measured['boxes']['word'])
        self.assertEqual(self.report()['status'],'UNVERIFIED')

    def test_zero_gap_fails(self):
        self.measured['boxes']['word']['x']=self.measured['boxes']['mark']['x']+100
        self.assertEqual(self.report()['status'],'FAIL')

    def test_safe_area_violation_fails(self):
        self.contract['rules'][0]['safe_margin']=300
        self.assertEqual(self.report()['status'],'FAIL')

    def test_partial_rule_cannot_use_lockup_profile(self):
        self.contract['rules']=[{"id":"only_x","type":"align","a":"word","b":"tag","edge":"x"}]
        with self.assertRaises(ValueError):self.report()

    def test_duplicate_roles_are_rejected(self):
        self.contract['rules'][0]['tagline']='word'
        with self.assertRaises(ValueError):self.report()

    def bottom_left(self):
        rule=self.contract['rules'][0]
        rule.update(row_alignment='bottom',tagline_alignment='left',upper_width='at_most_tagline')
        mark,word,tag=(self.measured['boxes'][name] for name in ('mark','word','tag'))
        word['y']=mark['y']+mark['height']-word['height']
        tag['x']=mark['x']
        tag['width']=word['x']+word['width']-mark['x']+1

    def test_explicit_bottom_left_with_width_limit_passes(self):
        self.bottom_left()
        self.assertEqual(self.report()['status'],'PASS')

    def test_center_alignment_cannot_substitute_for_bottom(self):
        self.bottom_left()
        mark,word=(self.measured['boxes'][name] for name in ('mark','word'))
        word['y']=mark['y']+(mark['height']-word['height'])/2
        report=self.report()
        self.assertEqual(next(c['status'] for c in report['checks'] if c['id']=='brand:row'),'FAIL')

    def test_centered_tagline_cannot_substitute_for_left_edge(self):
        self.bottom_left()
        self.measured['boxes']['tag']['x']+=3
        report=self.report()
        self.assertEqual(next(c['status'] for c in report['checks'] if c['id']=='brand:tagline'),'FAIL')

    def test_tiny_width_overshoot_is_rejected(self):
        self.bottom_left()
        mark,word,tag=(self.measured['boxes'][name] for name in ('mark','word','tag'))
        tag['width']=word['x']+word['width']-mark['x']-0.25
        report=self.report()
        self.assertEqual(next(c['status'] for c in report['checks'] if c['id']=='brand:width_limit'),'FAIL')

    def test_missing_alignment_is_not_silently_centered(self):
        del self.contract['rules'][0]['row_alignment']
        self.assertEqual(self.report()['status'],'UNVERIFIED')

    def export(self, existing=False):
        folder=Path(self.temp.name)/self._testMethodName
        folder.mkdir(exist_ok=True)
        spec, measured, out=folder/'contract.json',folder/'observed.json',folder/'delivered.png'
        spec.write_text(json.dumps(self.contract),encoding='utf-8')
        measured.write_text(json.dumps(self.measured),encoding='utf-8')
        if existing:out.write_bytes(b'KEEP EXISTING FILE')
        script=fixtures.MODULE.parent/'export_verified.py'
        result=subprocess.run([sys.executable,str(script),'--spec',str(spec),'--measurements',str(measured),
                               '--image',str(self.image),'--out',str(out)],capture_output=True,text=True)
        return result.returncode,out

    def test_export_success_copies_exact_verified_image(self):
        code,out=self.export()
        self.assertEqual(code,0)
        self.assertEqual(out.read_bytes(),self.image.read_bytes())

    def test_export_failure_creates_no_delivery_file(self):
        self.measured['boxes']['tag']['x']+=10
        code,out=self.export()
        self.assertEqual(code,1)
        self.assertFalse(out.exists())

    def test_unverified_export_creates_no_delivery_file(self):
        del self.measured['boxes']['tag']
        code,out=self.export()
        self.assertEqual(code,2)
        self.assertFalse(out.exists())

    def test_export_never_overwrites_existing_file(self):
        code,out=self.export(existing=True)
        self.assertEqual(code,2)
        self.assertEqual(out.read_bytes(),b'KEEP EXISTING FILE')


if __name__=='__main__':unittest.main()
