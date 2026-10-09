"""Release gates shared by local packaging and GitHub Actions; standard library only."""
import json,struct,zlib

def validate_inputs(root,manifest):
    kart=manifest['kart']
    assert len(kart['levels'])==3 and len(kart['portals'])==2
    assert len(kart['vehicle_anchors'])==6 and not kart['vehicle_assets_included']
    for name in ('validation_report.json','kart_validation.json'):
        report=json.loads((root/'Documentation'/name).read_text())
        assert report['checks'] and all(c['pass'] for c in report['checks']), name
    if tuple(map(int,manifest['version'].split('.'))) >= (0,9,0):
        import hashlib
        source=json.loads((root/'Documentation/cafe_source_preservation.json').read_text())
        update=json.loads((root/'Documentation/cafe_update_validation.json').read_text())
        assert source['passed'] and update['passed'] and all(c['pass'] for c in update['checks'])
        assert source['blend_sha256']==hashlib.sha256((root/'Blender/The_Commons_Compact.blend').read_bytes()).hexdigest()
    syntax=json.loads((root/'Documentation/csharp_syntax_report.json').read_text())
    assert syntax['checks'] and not any(c['syntax_errors'] for c in syntax['checks'])
    geometry=json.loads((root/'Documentation/geometry_report.json').read_text())
    for target in ('pc','quest'):
        triangles=sum(m['triangles'] for m in geometry[target]['meshes'] if m['group'].startswith('KART_'))
        assert triangles<=kart['design_limits'][f'kart_triangle_budget_{target}']
    screens=json.loads((root/'Documentation/release_screenshots.json').read_text())
    assert screens['version']==manifest['version'] and len(screens['images'])>=2
    paths=[]
    for item in screens['images']:
        p=(root/item['path']).resolve()
        assert p.is_relative_to(root) and item['caption'] and item['renderer']
        data=p.read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR',p
        w,h=struct.unpack('>II',data[16:24]);assert w>=1280 and h>=720,p
        offset,complete=8,False
        while offset+12<=len(data):
            size=struct.unpack_from('>I',data,offset)[0];end=offset+12+size
            assert end<=len(data),f'Truncated PNG: {p}'
            chunk=data[offset+4:offset+8+size];crc=struct.unpack_from('>I',data,offset+8+size)[0]
            assert zlib.crc32(chunk)&0xffffffff==crc,f'PNG checksum mismatch: {p}'
            offset=end
            if chunk[:4]==b'IEND':complete=True;break
        assert complete and offset==len(data),f'Incomplete PNG: {p}'
        paths.append(p)
    assert len({p.name for p in paths})==len(paths)
    return screens,paths
