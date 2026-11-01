#!/usr/bin/env python3
"""Seal a visual contract before rendering, measure raster layers, verify and export.

Pillow is required for raster evidence. Missing dependency/evidence blocks export.
This is an explicit pipeline, not a universal interceptor or an adversarial trust root.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

from verify_layout import load_json, verify
from verify_scene import verify_scene, project


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)


def resolve(root, name):
    p = Path(name)
    return p.resolve() if p.is_absolute() else (root/p).resolve()


def begin(plan_path, job_path, track=False):
    plan_path, job_path = Path(plan_path).resolve(), Path(job_path).resolve()
    plan = load_json(plan_path)
    if plan.get('version') != 2 or plan.get('mode') not in ('layout', 'scene'):
        raise ValueError('Plan version 2; mode layout or scene required')
    if not isinstance(plan.get('scope'), str) or not plan['scope'].strip():
        raise ValueError('Describe the intended visual and measured scope')
    if plan.get('background') not in ('transparent', 'opaque'):
        raise ValueError('Explicit transparent or opaque background required')
    layers = plan['layers']
    ids = [item['id'] for item in layers]
    if not layers or len(ids) != len(set(ids)):
        raise ValueError('Unique, nonempty layer inventory required')
    for item in layers:
        if item.get('role') not in ('geometry', 'decoration'):
            raise ValueError('Every layer must be geometry or decoration')
        if item['role'] == 'decoration' and not item.get('reason', '').strip():
            raise ValueError('Explain nongeometric/decorative layers')
    future = [plan['image'], *(item['path'] for item in layers)]
    if plan['mode'] == 'scene':
        future.append(plan['scene'])
        if not plan.get('camera'):
            raise ValueError('Seal the camera before rendering')
    outputs = [resolve(plan_path.parent, p) for p in future]
    if len(set(outputs)) != len(outputs) or any(p.exists() for p in outputs):
        raise ValueError('Begin before rendering: all candidate/evidence paths must be new and distinct')
    contract_path = resolve(plan_path.parent, plan['contract'])
    contract = load_json(contract_path)
    if plan['mode'] == 'layout':
        golden = [r for r in contract['rules'] if r['type']=='ratio' and r.get('exponent',1)==1
                  or r['type']=='lockup' and (r.get('mark_to_wordmark_exponent')==1 or r.get('wordmark_to_tagline_exponent')==1)]
        if not golden:
            raise ValueError('Strict delivery needs an explicit structural phi ratio; a centering-only repair is a scoped legacy check')
    else:
        if not any(r.get('type')=='ratio' and r.get('structural') is True and r.get('exponent',1)==1 for r in contract['rules']):
            raise ValueError('A structural phi ratio is mandatory')
    if job_path in set(outputs) | {plan_path, contract_path}:
        raise ValueError('Job must not overwrite an input/output')
    bindings = {str(plan_path):digest(plan_path), str(contract_path):digest(contract_path)}
    for item in plan.get('protected_inputs', []):
        p = resolve(plan_path.parent, item)
        bindings[str(p)] = digest(p)
    job = dict(version=2, id=str(uuid.uuid4()), plan=str(plan_path), bindings=bindings,
               session_id=os.getenv('CODEX_THREAD_ID'), status='PREPARED')
    save_new(job_path, job)
    if track and job['session_id']:
        from codex_guard import register_job
        register_job(job['session_id'], job_path)
    return job


def check(job_path):
    # Do not trust a cached PASS: read and measure the files again on every export.
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
    job = load_json(job_path)
    if job.get('version') != 2 or job.get('status') != 'PREPARED':
        raise ValueError('A prepared version-2 job is required')
    for name, expected in job['bindings'].items():
        if digest(name) != expected:
            raise ValueError('A sealed plan, contract or protected input changed: '+name)
    plan_path = Path(job['plan']); root = plan_path.parent
    plan = load_json(plan_path)
    contract = load_json(resolve(root, plan['contract']))
    candidate = resolve(root, plan['image'])
    with Image.open(candidate) as source:
        if source.format != 'PNG':
            raise ValueError('Strict raster delivery requires PNG')
        image = source.convert('RGBA')
    if list(image.size) != plan['canvas']:
        raise ValueError('Candidate canvas changed')
    combined = Image.new('RGBA', image.size)
    boxes, masks, bindings = {}, {}, dict(job['bindings'])
    bindings[str(candidate)] = digest(candidate)
    for item in plan['layers']:
        path = resolve(root, item['path'])
        with Image.open(path) as source:
            if source.format != 'PNG' or source.size != image.size:
                raise ValueError('Evidence layers must be full-canvas PNGs')
            layer = source.convert('RGBA')
        bindings[str(path)] = digest(path)
        combined = Image.alpha_composite(combined, layer)
        if item['role']=='geometry':
            mask = layer.getchannel('A').point(lambda a:255 if a>=128 else 0)
            bbox = mask.getbbox()
            if not bbox:
                raise ValueError('Empty geometry layer: '+item['id'])
            x,y,r,b = bbox
            boxes[item['id']] = dict(x=x,y=y,width=r-x,height=b-y,bounds_kind='visible_ink')
            masks[item['id']] = mask
    # Permit only known premultiplied edge rounding; alpha and opaque RGB are exact.
    diff = ImageChops.difference(image, combined)
    if diff.getchannel('A').getbbox():
        raise ValueError('Final alpha differs from rendered layers (background/paint changed)')
    extrema = diff.getextrema()
    if any(high>1 for low,high in extrema[:3]):
        raise ValueError('Final colors differ from rendered layers')
    opaque = image.getchannel('A').point(lambda a:255 if a==255 else 0)
    if any(ImageChops.multiply(channel, opaque).getbbox() for channel in diff.split()[:3]):
        raise ValueError('Opaque colors differ from rendered layers')
    alpha = image.getchannel('A')
    if plan['background']=='transparent':
        w,h=image.size
        if any(alpha.getpixel(p)!=0 for p in ((0,0),(w-1,0),(0,h-1),(w-1,h-1))):
            raise ValueError('Transparent background required at all four canvas corners')
    elif alpha.getextrema() != (255,255):
        raise ValueError('Opaque background required')
    if plan['mode']=='layout':
        observed=dict(version=1,kind='observed',canvas=dict(width=image.width,height=image.height),
                      pixel_ratio=1,evidence=dict(method='manual',image_sha256=bindings[str(candidate)],
                      uncertainty_px=0,note='Computed from raster layer alpha>=128; not manually annotated'),boxes=boxes)
        # Inventory coverage is separate from merely having four categories.
        referenced=set()
        for rule in contract['rules']:
            for key in ('a','b','mark','wordmark','tagline','glyph','container','from','to','before','after'):
                value=rule.get(key)
                if isinstance(value,str): referenced.add(value)
                elif isinstance(value,dict) and isinstance(value.get('box'),str): referenced.add(value['box'])
            if isinstance(rule.get('ref'),dict): referenced.add(rule['ref'].get('box'))
            referenced.update(rule.get('group',[]))
        if set(boxes)-referenced:
            raise ValueError('Every geometry layer needs a declared relation')
        report=verify(contract,observed,candidate)
    else:
        scene_path=resolve(root,plan['scene']); scene=load_json(scene_path)
        bindings[str(scene_path)]=digest(scene_path)
        if scene['camera'] != plan['camera']:
            raise ValueError('Camera differs from the sealed plan')
        if set(scene['objects']) != set(boxes):
            raise ValueError('Rendered geometry layers and scene objects must match exactly')
        if scene['camera']['viewport'] != list(image.size):
            raise ValueError('Camera viewport and PNG canvas differ')
        report=verify_scene(contract,scene)
        # Cross-check each isolated object's actual raster silhouette against its
        # exported projected faces. This does not claim optical or texture fidelity.
        for name,obj in scene['objects'].items():
            expected=Image.new('L',image.size); draw=ImageDraw.Draw(expected)
            if not obj.get('faces'):
                raise ValueError('Faces required to bind scene to raster')
            for face in obj['faces']:
                if len(face)<3 or any(isinstance(i,bool) or not isinstance(i,int) or i<0 or i>=len(obj['vertices']) for i in face):
                    raise ValueError('Invalid mesh face')
                draw.polygon([tuple(project(obj['vertices'][i],scene['camera'])) for i in face],fill=255)
            actual=masks[name]
            # At most one pixel of rasterization boundary variation; no missing
            # interior and no pixels beyond the expanded geometric silhouette.
            outer=expected.filter(ImageFilter.MaxFilter(3)); inner=expected.filter(ImageFilter.MinFilter(3))
            if ImageChops.subtract(actual,outer).getbbox() or ImageChops.subtract(inner,actual).getbbox():
                raise ValueError('Raster silhouette does not match projected 3D geometry: '+name)
        report['projection_silhouettes']='PASS'
    return dict(version=2,status=report['status'],job=str(Path(job_path).resolve()),job_sha256=digest(job_path),
                scope=plan['scope'],mode=plan['mode'],image=str(candidate),bindings=bindings,
                geometry=report,measurement_method='computed_raster_alpha_128_and_exported_vertices' if plan['mode']=='scene' else 'computed_raster_alpha_128',
                layer_composition='PASS',background=plan['background'],
                global_composition_conformity='NOT_ESTABLISHED')


def export(job_path, output):
    output=Path(output).resolve(); receipt=Path(str(output)+'.golden.json')
    if output.exists() or receipt.exists():
        raise ValueError('Export paths must be new')
    report=check(job_path)
    if report['status']!='PASS':
        return report
    data=Path(report['image']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=report['bindings'][report['image']]:
        raise ValueError('Candidate changed during export')
    report.update(output=str(output),output_sha256=hashlib.sha256(data).hexdigest())
    with output.open('xb') as stream: stream.write(data)
    save_new(receipt,report)
    job=load_json(job_path)
    if job.get('session_id'):
        from codex_guard import register_receipt
        register_receipt(job['session_id'],job_path,receipt)
    return report


def validate_receipt(path):
    receipt=load_json(path)
    if receipt.get('version')!=2 or receipt.get('status')!='PASS':
        raise ValueError('Not a strict PASS receipt')
    if digest(receipt['job'])!=receipt['job_sha256']:
        raise ValueError('Prepared job changed')
    fresh=check(receipt['job'])
    if fresh['status']!='PASS' or fresh['bindings']!=receipt['bindings']:
        raise ValueError('Evidence changed after validation')
    if digest(receipt['output'])!=receipt['output_sha256'] or receipt['output_sha256']!=fresh['bindings'][fresh['image']]:
        raise ValueError('Delivered image changed')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('begin');p.add_argument('--plan',required=True);p.add_argument('--job',required=True)
    p=sub.add_parser('check');p.add_argument('--job',required=True)
    p=sub.add_parser('export');p.add_argument('--job',required=True);p.add_argument('--out',required=True)
    p=sub.add_parser('receipt');p.add_argument('--path',required=True)
    args=parser.parse_args()
    try:
        if args.action=='begin': result=begin(args.plan,args.job,track=True)
        elif args.action=='check': result=check(args.job)
        elif args.action=='export': result=export(args.job,args.out)
        else: result=validate_receipt(args.path)
    except (ValueError,LookupError,TypeError,OSError,ImportError,OverflowError) as error:
        result=dict(status='UNVERIFIED',error=str(error))
    print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
    return {'PASS':0,'PREPARED':0,'FAIL':1,'UNVERIFIED':2}.get(result['status'],2)


if __name__=='__main__': sys.exit(main())
