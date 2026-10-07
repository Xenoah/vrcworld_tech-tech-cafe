"""Restore the authored FPV module into build_world.py's scene.

FPV_Field_Module.json preserves the editable meshes, face UVs, text and lights.
The main .blend remains the artist-facing source; this module makes a complete
world rebuild independent of the prior output .blend. Layout edits belong in
the module and SourceDesign/fpv_field.json together, including colliders.
"""
import json
from mathutils import Matrix

module = json.loads((ROOT / 'Blender/FPV_Field_Module.json').read_text())
FPV = module['fpv']
spec = json.loads((ROOT / 'SourceDesign/fpv_field.json').read_text())
for key in ['origin', 'size', 'flight_bounds_local', 'pilot_bounds_local', 'spectator_bounds_local']:
    assert spec[key] == FPV[key], 'Update FPV module geometry/colliders when changing ' + key
assert [(g['id'],g['center'],g['direction']) for g in spec['gates']] == [(g['id'],g['center'],g['direction']) for g in FPV['gates']], 'FPV module and course specification differ'
for name, r in module['materials'].items():
    mat(name, tuple(r['color'][:3]), r['texture'] or None, r['roughness'], r['metallic'], r['emission'], wrap=r['wrap'])
for r in module['objects']:
    name, kind = r['name'], r['type']
    group(r['group'])
    if kind == 'MESH':
        data = bpy.data.meshes.new(name)
        data.from_pydata(r['vertices'], [], r['faces']); data.update()
        for material in r['materials']: data.materials.append(M[material])
        for polygon, index in zip(data.polygons, r['material_indices']): polygon.material_index = index
        if r['uv']:
            uv = data.uv_layers.new(name='UVMap')
            for loop, value in zip(uv.data, r['uv']): loop.uv = value
    elif kind == 'FONT':
        data = bpy.data.curves.new(name, 'FONT')
        for key, value in r['font'].items(): setattr(data, key, value)
        if FONT: data.font = FONT
        for material in r['materials']: data.materials.append(M[material])
    elif kind == 'LIGHT':
        data = bpy.data.lights.new(name, r['light']['type'])
        for key, value in r['light'].items():
            if key != 'type': setattr(data, key, value)
    else:
        raise ValueError('Unsupported authored FPV object: ' + kind)
    obj = link(bpy.data.objects.new(name, data))
    obj.matrix_world = Matrix(r['matrix'])
    for modifier in r.get('modifiers', []):
        mod = obj.modifiers.new(modifier['name'], modifier['type'])
        mod.width = modifier['width']; mod.segments = modifier['segments']
COL.extend(module['colliders'])
LIGHTS.extend(module['lights'])
SEATS.extend(module['seat_anchors'])
