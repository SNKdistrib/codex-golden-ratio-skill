#!/usr/bin/env python3
"""Measure exported 3D vertices, not dimensions claimed in a prompt.

World-space constraints and projected-image constraints are deliberately separate.
A mesh report alone is not proof of a rendered image; golden_delivery binds both.
"""
import math

PHI = (1 + math.sqrt(5)) / 2
EXPONENTS = {-2, -1, -0.5, 0.5, 1, 2, 3, 4, 5, 6}


def vector(value, size=3):
    if not isinstance(value, list) or len(value) != size:
        raise ValueError('Invalid vector dimension')
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in value):
        raise ValueError('Finite numeric coordinates required')
    return value


def project(point, camera):
    """OpenGL-style row-major world-to-clip matrix, top-left raster origin."""
    matrix = vector(camera['world_to_clip'], 16)
    width, height = vector(camera['viewport'], 2)
    if min(width, height) <= 0:
        raise ValueError('Invalid viewport')
    p = vector(point) + [1]
    clip = [sum(matrix[row*4+j]*p[j] for j in range(4)) for row in range(4)]
    if clip[3] <= 0:
        raise ValueError('Vertex behind camera; clipped geometry needs a dedicated exporter')
    ndc = [v/clip[3] for v in clip[:3]]
    if any(abs(v) > 1 + 1e-9 for v in ndc):
        raise ValueError('Clipped vertex; cannot certify a complete silhouette')
    return [(ndc[0]+1)*width/2, (1-ndc[1])*height/2]


def verify_scene(contract, scene):
    if contract.get('version') != 1 or scene.get('version') != 1:
        raise ValueError('Scene/contract version must be 1')
    if scene.get('coordinate_space') != 'world':
        raise ValueError('Export evaluated vertices after transforms in world coordinates')
    objects = scene['objects']
    inventory = contract['inventory']
    if not isinstance(objects, dict) or not objects or len(set(inventory)) != len(inventory):
        raise ValueError('Nonempty, unique object inventory required')
    if set(inventory) != set(objects):
        raise ValueError('Contract must inventory every exported object')
    for obj in objects.values():
        if not obj['vertices']:
            raise ValueError('Empty mesh')
        for p in obj['vertices']:
            vector(p)
    checks, used, ids = [], set(), set()
    structural = False

    def point(ref, space):
        name, index = ref['object'], ref['vertex']
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ValueError('Vertex index must be a nonnegative integer')
        used.add(name)
        p = objects[name]['vertices'][index]
        return p if space == 'world' else project(p, scene['camera'])

    def length(ref, space):
        a, b = ref['vertices']
        return math.dist(point({'object': ref['object'], 'vertex': a}, space),
                         point({'object': ref['object'], 'vertex': b}, space))

    for rule in contract['rules']:
        ident, space = rule['id'], rule['space']
        if not ident or ident in ids or space not in ('world', 'projected'):
            raise ValueError('Unique rule ID and explicit world/projected space required')
        ids.add(ident)
        if rule['type'] == 'ratio':
            exponent = rule.get('exponent', 1)
            if isinstance(exponent, bool) or exponent not in EXPONENTS:
                raise ValueError('Nontrivial supported phi exponent required')
            tolerance = rule.get('tolerance_pct', 1)
            vector([tolerance], 1)
            if not 0 <= tolerance <= 2:
                raise ValueError('Ratio tolerance must be between 0 and 2 percent')
            a, b = length(rule['a'], space), length(rule['b'], space)
            if min(a, b) <= 0:
                raise ValueError('Positive segment lengths required')
            actual, expected = a/b, PHI**exponent
            error = 100*abs(actual-expected)/expected
            checks.append(dict(id=ident, space=space, status='PASS' if error <= tolerance else 'FAIL',
                               actual=actual, expected=expected, error_pct=error))
            structural |= rule.get('structural') is True and exponent == 1
        elif rule['type'] == 'align':
            axis = rule['axis']
            if axis not in range(3 if space == 'world' else 2):
                raise ValueError('Alignment axis does not exist in this space')
            pts = [point(ref, space) for ref in rule['points']]
            if len(pts) < 2:
                raise ValueError('Alignment needs at least two points')
            tolerance = rule['tolerance']
            vector([tolerance], 1)
            if tolerance < 0 or (space == 'projected' and tolerance > 2):
                raise ValueError('Invalid alignment tolerance')
            delta = max(p[axis] for p in pts)-min(p[axis] for p in pts)
            checks.append(dict(id=ident, space=space, status='PASS' if delta <= tolerance else 'FAIL', delta=delta))
        else:
            raise ValueError('Unknown scene rule')
    if not structural:
        raise ValueError('At least one explicit structural phi ratio is mandatory')
    preserved = contract.get('preserved', {})
    if any(not isinstance(reason, str) or not reason.strip() for reason in preserved.values()):
        raise ValueError('Preserved objects need specific reasons')
    if set(objects) != used | set(preserved) or not set(preserved) <= set(objects):
        raise ValueError('Every object needs a checked relation or a preservation reason')
    return dict(status='FAIL' if any(c['status']=='FAIL' for c in checks) else 'PASS',
                scope='declared_world_and_projected_vertex_relations', checks=checks,
                global_composition_conformity='NOT_ESTABLISHED')
