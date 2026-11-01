"""Actual raster/mesh mutations, sealed contracts, exports and hook decisions."""
import copy
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import golden_delivery as gate
import codex_guard as guard
from verify_scene import verify_scene,project,PHI


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='golden-strict-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{'GOLDEN_STATE_DIR':str(self.root/'state'),'CODEX_THREAD_ID':'test-session'})
        self.env.start();self.addCleanup(self.env.stop)
        self.contract={'version':1,'profile':'logo-lockup','scope_note':'Three synthetic ink regions',
          'canvas':{'width':600,'height':200},'spacing_base':5,'tolerance_px':1,
          'rules':[{'id':'lockup','type':'lockup','mark':'mark','wordmark':'wordmark','tagline':'tagline',
          'horizontal_gap_exponent':3,'vertical_gap_exponent':2,'safe_margin':21,'center_on_canvas':True,
          'row_alignment':'bottom','tagline_alignment':'left','upper_width':'at_most_tagline',
          'mark_to_wordmark_exponent':1,'tolerance_pct':2}]}
        self.plan={'version':2,'mode':'layout','scope':'Synthetic three-part logo raster test','canvas':[600,200],
          'background':'transparent','image':'candidate.png','contract':'contract.json',
          'layers':[{'id':name,'path':name+'.png','role':'geometry'} for name in ('mark','wordmark','tagline')]}
        self.write('contract.json',self.contract);self.write('plan.json',self.plan)
        self.job=self.root/'job.json'

    def write(self,name,value):
        (self.root/name).write_text(json.dumps(value),encoding='utf-8')

    def begin(self,track=False):
        return gate.begin(self.root/'plan.json',self.job,track=track)

    def render(self,offset=0):
        composed=Image.new('RGBA',(600,200))
        for name,rect in [('mark',(67,40,162,123)),('wordmark',(184,72+offset,532,123+offset)),('tagline',(67,137,533,159))]:
            layer=Image.new('RGBA',(600,200));ImageDraw.Draw(layer).rectangle(rect,fill=(20,130,240,255))
            layer.save(self.root/(name+'.png'));composed=Image.alpha_composite(composed,layer)
        composed.save(self.root/'candidate.png')

    def test_real_pixels_pass_and_export(self):
        self.begin();self.render()
        report=gate.export(self.job,self.root/'final.png')
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(gate.validate_receipt(self.root/'final.png.golden.json')['status'],'PASS')

    def test_shift_actual_pixels_fails_not_just_annotations(self):
        self.begin();self.render(offset=4)
        self.assertEqual(gate.export(self.job,self.root/'final.png')['status'],'FAIL')
        self.assertFalse((self.root/'final.png').exists())

    def test_white_background_rejected(self):
        self.begin();self.render()
        with Image.open(self.root/'candidate.png') as image:
            white=Image.new('RGBA',image.size,'white');white.alpha_composite(image)
        white.save(self.root/'candidate.png')
        with self.assertRaisesRegex(ValueError,'alpha'):gate.check(self.job)

    def test_changed_color_rejected(self):
        self.begin();self.render()
        with Image.open(self.root/'candidate.png') as image:
            image.putpixel((80,80),(255,0,0,255));image.save(self.root/'candidate.png')
        with self.assertRaisesRegex(ValueError,'colors'):gate.check(self.job)

    def test_missing_layer_blocks(self):
        self.begin();self.render();(self.root/'tagline.png').unlink()
        with self.assertRaises(OSError):gate.check(self.job)

    def test_changed_contract_cannot_make_bad_render_pass(self):
        self.begin();self.render(offset=4)
        self.contract['rules'][0]['row_alignment']='center_y';self.write('contract.json',self.contract)
        with self.assertRaisesRegex(ValueError,'sealed'):gate.check(self.job)

    def test_begin_after_render_rejected(self):
        self.render()
        with self.assertRaisesRegex(ValueError,'before rendering'):self.begin()

    def test_phi_ratio_cannot_be_omitted(self):
        del self.contract['rules'][0]['mark_to_wordmark_exponent'];self.write('contract.json',self.contract)
        with self.assertRaisesRegex(ValueError,'structural'):self.begin()

    def test_extra_layer_cannot_be_silently_ignored(self):
        self.plan['layers'].append({'id':'extra','path':'extra.png','role':'geometry'});self.write('plan.json',self.plan)
        self.begin();self.render();Image.new('RGBA',(600,200),(0,0,0,255)).save(self.root/'extra.png')
        with self.assertRaises(ValueError):gate.check(self.job)

    def test_export_cannot_overwrite(self):
        self.begin();self.render();gate.export(self.job,self.root/'final.png')
        with self.assertRaisesRegex(ValueError,'new'):gate.export(self.job,self.root/'final.png')

    def test_modified_delivery_receipt_fails(self):
        self.begin();self.render();gate.export(self.job,self.root/'final.png')
        (self.root/'final.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Delivered'):gate.validate_receipt(self.root/'final.png.golden.json')

    def test_hook_blocks_registered_unfinished_job(self):
        self.begin(track=True)
        result=guard.handle({'hook_event_name':'Stop','session_id':'test-session'})
        self.assertEqual(result['decision'],'block')

    def test_hook_does_not_loop(self):
        self.begin(track=True)
        result=guard.handle({'hook_event_name':'Stop','session_id':'test-session','stop_hook_active':True})
        self.assertFalse(result['continue'])

    def test_hook_allows_valid_delivery(self):
        self.begin(track=True);self.render();gate.export(self.job,self.root/'final.png')
        self.assertEqual(guard.handle({'hook_event_name':'Stop','session_id':'test-session'}),{})

    def test_hook_rechecks_modified_delivery(self):
        self.begin(track=True);self.render();gate.export(self.job,self.root/'final.png')
        (self.root/'final.png').write_bytes(b'changed')
        self.assertEqual(guard.handle({'hook_event_name':'Stop','session_id':'test-session'})['decision'],'block')

    def test_nonvisual_session_unaffected(self):
        self.assertEqual(guard.handle({'hook_event_name':'Stop','session_id':'other-session'}),{})

    def test_direct_image_generation_needs_prepared_job(self):
        e={'hook_event_name':'PreToolUse','session_id':'test-session','tool_name':'image_gen__imagegen'}
        self.assertEqual(guard.handle(e)['hookSpecificOutput']['permissionDecision'],'deny')
        self.begin(track=True);self.assertEqual(guard.handle(e),{})

    def test_unrelated_tools_not_blocked(self):
        self.assertEqual(guard.handle({'hook_event_name':'PreToolUse','session_id':'test-session','tool_name':'read_file'}),{})

    def test_uncertain_manual_geometry_not_certified(self):
        self.begin();self.render()
        import verify_layout as legacy
        m={'version':1,'kind':'observed','canvas':{'width':600,'height':200},'boxes':{},
           'evidence':{'method':'manual','uncertainty_px':2,'image_sha256':gate.digest(self.root/'candidate.png')}}
        r=legacy.verify(self.contract,m,self.root/'candidate.png')
        self.assertEqual(next(c for c in r['checks'] if c['id']=='measurement_vs_tolerance')['status'],'UNVERIFIED')


class SceneTests(unittest.TestCase):
    def setUp(self):
        self.camera={'viewport':[200,200],'world_to_clip':[.1,0,0,0,0,.1,0,0,0,0,.01,0,0,0,.05,1]}
        self.scene={'version':1,'coordinate_space':'world','camera':self.camera,
          'objects':{'form':{'vertices':[[0,0,0],[PHI,0,0],[0,1,2]],'faces':[[0,1,2]]}}}
        self.contract={'version':1,'inventory':['form'],'rules':[{'id':'width_height','type':'ratio','space':'world',
          'a':{'object':'form','vertices':[0,1]},'b':{'object':'form','vertices':[0,2]},'structural':True}]}
        # The third vertex is 1 unit from the origin initially; depth tests change it.
        self.scene['objects']['form']['vertices'][2]=[0,1,0]

    def test_world_ratio(self):
        self.assertEqual(verify_scene(self.contract,self.scene)['status'],'PASS')

    def test_bad_mesh_dimension_fails(self):
        self.scene['objects']['form']['vertices'][1][0]=1.2
        self.assertEqual(verify_scene(self.contract,self.scene)['status'],'FAIL')

    def test_projection_is_not_world_ratio(self):
        # A segment receding in depth has its true length corrected to one unit.
        self.scene['objects']['form']['vertices'][2]=[0,math.sqrt(.75),.5]
        self.assertEqual(verify_scene(self.contract,self.scene)['status'],'PASS')
        self.contract['rules'][0]['space']='projected'
        self.assertEqual(verify_scene(self.contract,self.scene)['status'],'FAIL')

    def test_orthogonal_rotation_preserves_world_ratio(self):
        self.scene['objects']['form']['vertices']=[[z,x,y] for x,y,z in self.scene['objects']['form']['vertices']]
        self.assertEqual(verify_scene(self.contract,self.scene)['status'],'PASS')

    def test_uninventoried_object_rejected(self):
        self.scene['objects']['ignored']=copy.deepcopy(self.scene['objects']['form'])
        with self.assertRaisesRegex(ValueError,'inventory'):verify_scene(self.contract,self.scene)

    def test_no_structural_relation_rejected(self):
        self.contract['rules'][0]['structural']=False
        with self.assertRaisesRegex(ValueError,'structural'):verify_scene(self.contract,self.scene)

    def test_nonfinite_vertex_rejected(self):
        self.scene['objects']['form']['vertices'][0][0]=float('nan')
        with self.assertRaises(ValueError):verify_scene(self.contract,self.scene)

    def test_behind_camera_rejected(self):
        with self.assertRaisesRegex(ValueError,'behind'):project([0,0,-30],self.camera)

    def test_real_scene_raster_pipeline(self):
        with tempfile.TemporaryDirectory(prefix='golden-scene-') as temp:
            root=Path(temp)
            plan={'version':2,'mode':'scene','scope':'Triangle source geometry and actual projected pixels',
              'canvas':[200,200],'background':'transparent','contract':'contract.json','scene':'scene.json','camera':self.camera,
              'image':'candidate.png','layers':[{'id':'form','role':'geometry','path':'form.png'}]}
            (root/'plan.json').write_text(json.dumps(plan));(root/'contract.json').write_text(json.dumps(self.contract))
            gate.begin(root/'plan.json',root/'job.json')
            (root/'scene.json').write_text(json.dumps(self.scene))
            image=Image.new('RGBA',(200,200));pts=[project(p,self.camera) for p in self.scene['objects']['form']['vertices']]
            ImageDraw.Draw(image).polygon([tuple(p) for p in pts],fill=(20,130,240,255))
            image.save(root/'form.png');image.save(root/'candidate.png')
            self.assertEqual(gate.export(root/'job.json',root/'final.png')['status'],'PASS')
            # A real added patch in BOTH candidate and layer preserves composition,
            # but must fail the independent geometry-to-raster silhouette check.
            ImageDraw.Draw(image).rectangle((150,150,160,160),fill=(20,130,240,255))
            image.save(root/'form.png');image.save(root/'candidate.png')
            with self.assertRaisesRegex(ValueError,'silhouette'):gate.check(root/'job.json')


if __name__=='__main__':unittest.main()
