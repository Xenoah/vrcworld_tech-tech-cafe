"""Store the same assets in Git without duplicate embedded texture data.

Run with Blender's Python (or Python with bpy installed):
    python Blender/prepare_repository_assets.py
Use --gltf-only to externalize a generated GLB without importing bpy.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]


def externalize_gltf():
    source = ROOT / 'Preview/The_Commons_Compact.glb'
    if not source.exists():
        return {'status': 'already_external_or_not_generated'}
    raw = source.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    json_length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    data = json.loads(raw[20:20 + json_length])
    start = 20 + json_length
    bin_length, kind = struct.unpack_from('<II', raw, start)
    assert kind == 0x004E4942
    binary = raw[start + 8:start + 8 + bin_length]
    old_views = data['bufferViews']
    image_views = set()
    for image in data['images']:
        index = image.pop('bufferView')
        image_views.add(index)
        view = old_views[index]
        offset = view.get('byteOffset', 0)
        embedded = binary[offset:offset + view['byteLength']]
        relative = f"Unity/Assets/TheCommons/Textures/{image['name']}.png"
        # Exact PNG equality, not re-encoding or a visual approximation.
        assert (ROOT / relative).read_bytes() == embedded, relative
        image['uri'] = '../' + relative
    output = bytearray()
    mapping, views = {}, []
    for index, view in enumerate(old_views):
        if index in image_views:
            continue
        offset = view.get('byteOffset', 0)
        payload = binary[offset:offset + view['byteLength']]
        assert len(payload) == view['byteLength']
        output.extend(b'\0' * (-len(output) % 4))
        mapping[index] = len(views)
        views.append({**view, 'buffer': 0, 'byteOffset': len(output)})
        output.extend(payload)
    def remap(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'bufferView':
                    value[key] = mapping[child]
                else:
                    remap(child)
        elif isinstance(value, list):
            for child in value:
                remap(child)
    remap(data)
    data['bufferViews'] = views
    data['buffers'] = [{'uri': 'The_Commons_Compact.bin', 'byteLength': len(output)}]
    for old_index, new_index in mapping.items():
        old, new = old_views[old_index], views[new_index]
        a = binary[old.get('byteOffset', 0):old.get('byteOffset', 0) + old['byteLength']]
        b = output[new['byteOffset']:new['byteOffset'] + new['byteLength']]
        assert a == b
    target = ROOT / 'Preview/The_Commons_Compact.bin'
    target.write_bytes(output)
    (ROOT / 'Preview/The_Commons_Compact.gltf').write_text(json.dumps(data, separators=(',', ':')) + '\n')
    return {'geometry_buffer_bytes': len(output), 'geometry_views_verified': len(mapping),
            'texture_files_exactly_reused': len(image_views)}


def externalize_blend():
    import bpy
    from array import array
    source = ROOT / 'Blender/The_Commons_Compact.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    def fingerprint():
        digest = hashlib.sha256()
        for obj in sorted(bpy.data.objects, key=lambda o: o.name):
            digest.update((obj.name + '\0' + obj.type).encode())
            digest.update(struct.pack('<16f', *(v for row in obj.matrix_world for v in row)))
            if obj.type == 'MESH':
                coordinates = array('f', [0.0]) * (len(obj.data.vertices) * 3)
                obj.data.vertices.foreach_get('co', coordinates)
                indices = array('i', [0]) * len(obj.data.loops)
                obj.data.loops.foreach_get('vertex_index', indices)
                digest.update(coordinates.tobytes())
                digest.update(indices.tobytes())
            elif obj.type == 'FONT':
                digest.update(obj.data.body.encode())
        return digest.hexdigest()
    before = fingerprint()
    image_count = font_count = 0
    for image in bpy.data.images:
        if image.type != 'IMAGE' or not image.packed_file:
            continue
        name = Path(image.filepath).name
        target = ROOT / 'Unity/Assets/TheCommons/Textures' / name
        assert target.exists(), target
        assert bytes(image.packed_file.data) == target.read_bytes(), name
        image.unpack(method='REMOVE')
        image.filepath = '//../Unity/Assets/TheCommons/Textures/' + name
        image_count += 1
    for font in bpy.data.fonts:
        if not font.packed_file:
            continue
        name = Path(font.filepath).name
        target = ROOT / 'Blender/Fonts' / name
        assert target.exists(), target
        assert bytes(font.packed_file.data) == target.read_bytes(), name
        font.unpack(method='REMOVE')
        font.filepath = '//Fonts/' + name
        font_count += 1
    bpy.ops.wm.save_as_mainfile(filepath=str(source), compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    assert fingerprint() == before, 'Geometry changed during file packaging'
    for collection in (bpy.data.images, bpy.data.fonts):
        for asset in collection:
            if asset.filepath.startswith('//'):
                assert Path(bpy.path.abspath(asset.filepath)).is_file(), asset.filepath
    return {'compressed_bytes': source.stat().st_size, 'external_images': image_count,
            'external_fonts': font_count, 'geometry_sha256_before_and_after': before,
            'relative_asset_paths_verified_after_reopen': True}


if __name__ == '__main__':
    result = {'gltf': externalize_gltf()}
    if '--gltf-only' not in sys.argv:
        result['blend'] = externalize_blend()
    (ROOT / 'Documentation/repository_asset_packaging.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
