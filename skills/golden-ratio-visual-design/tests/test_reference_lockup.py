"""Regression checks for the accepted reference; supplied observations, not OCR."""
from pathlib import Path
import unittest
import test_verify_layout as fixtures


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]/'assets/examples/snk-lockup'
        self.contract=fixtures.v.load_json(self.root/'contract.json')
        self.measured=fixtures.v.load_json(self.root/'observed.json')

    def test_accepted_png_and_recorded_geometry_pass(self):
        report=fixtures.v.verify(self.contract,self.measured,self.root/'logo-transparent.png')
        self.assertEqual(report['status'],'PASS')
        stored=fixtures.v.load_json(self.root/'report.json')
        self.assertEqual(report['image_sha256'],stored['image_sha256'])
        width=next(c for c in report['checks'] if c['id']=='brand:width_limit')
        self.assertLessEqual(width['upper_right'],width['tagline_right'])

    def test_recentering_the_name_breaks_the_bottom_alignment(self):
        mark,word=(self.measured['boxes'][key] for key in ('mark','wordmark'))
        word['y']=mark['y']+(mark['height']-word['height'])/2
        report=fixtures.v.verify(self.contract,self.measured,self.root/'logo-transparent.png')
        self.assertEqual(next(c['status'] for c in report['checks'] if c['id']=='brand:row'),'FAIL')

    def test_moving_the_tagline_breaks_the_shared_left_edge(self):
        self.measured['boxes']['tagline']['x']+=4
        report=fixtures.v.verify(self.contract,self.measured,self.root/'logo-transparent.png')
        self.assertEqual(next(c['status'] for c in report['checks'] if c['id']=='brand:tagline'),'FAIL')


if __name__=='__main__':unittest.main()
