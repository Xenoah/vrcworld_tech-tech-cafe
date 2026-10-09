"""Reuse already-verified untouched mesh records after Blender export.
Blender's material splitting and Quest decimation can reorder unrelated records;
the authored .blend object proof is required before preserving the base bytes.
Only the edited AV_Stage and new WAY_ groups use regenerated geometry.
"""
from pathlib import Path
import json,hashlib,struct,io,subprocess
ROOT=Path(__file__).resolve().parents[1];proof=json.loads((ROOT/'Documentation/cafe_source_preservation.json').read_text())
assert proof['passed'] and proof['blend_sha256']==hashlib.sha256((ROOT/'Blender/The_Commons_Compact.blend').read_bytes()).hexdigest(), 'Verify authored objects first'
def records(data):
 f=io.BytesIO(data);assert f.read(4)==b'TCM2';count=struct.unpack('<I',f.read(4))[0];out={}
 def string():return f.read(struct.unpack('<I',f.read(4))[0]).decode()
 for _ in range(count):
  start=f.tell();name,group,mat=string(),string(),string();nv,ni=struct.unpack('<II',f.read(8));f.seek(nv*32+ni*4,1)
  out[name]=(group,data[start:f.tell()],dict(name=name,group=group,vertices=nv,triangles=ni//3))
 return out
stats=json.loads((ROOT/'Documentation/geometry_report.json').read_text())
for target in ['PC','Quest']:
 path=ROOT/f'Unity/Assets/TheCommons/Models/TheCommons_{target}.tcmesh.bytes'
 old=records(subprocess.check_output(['git','show',proof['base_commit']+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT));new=records(path.read_bytes());preserved=0
 for name,(group,data,info) in old.items():
  if group=='AV_Stage' or group.startswith('WAY_'):continue
  assert name in new, name
  new[name]=(group,data,info);preserved+=1
 path.write_bytes(b'TCM2'+struct.pack('<I',len(new))+b''.join(v[1] for k,v in sorted(new.items())))
 meshes=[v[2] for k,v in sorted(new.items())];stats[target.lower()]={'triangles':sum(m['triangles'] for m in meshes),'render_meshes':len(meshes),'meshes':meshes,'base_meshes_preserved':preserved}
 print(target,'preserved',preserved,'records')
stats['measurement']='Exported geometry with untouched v0.8.0 mesh records reused after authored-object proof. Not runtime FPS / draw-call measurement.'
(ROOT/'Documentation/geometry_report.json').write_text(json.dumps(stats,indent=2)+'\n')
