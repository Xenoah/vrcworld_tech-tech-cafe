"""Prove that the targeted edit preserved every existing non-presentation object."""
from pathlib import Path
from array import array
from mathutils import Vector
import bpy,json,hashlib,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1];spec=json.loads((ROOT/'SourceDesign/cafe_experience.json').read_text());base=spec['base_commit']
current=ROOT/'Blender/The_Commons_Compact.blend'
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.view_layer.update();result={}
 for o in bpy.data.objects:
  if o.name.startswith(tuple(spec['removed_object_prefixes'])) or o.name.startswith(('WAY_','IwaSync_')):continue
  h=hashlib.sha256();h.update((o.type+'\0'+str(sorted(c.name for c in o.users_collection))).encode());h.update(struct.pack('<16f',*(v for row in o.matrix_world for v in row)))
  if o.type=='MESH':
   co=array('f',[0])*len(o.data.vertices)*3;o.data.vertices.foreach_get('co',co);h.update(co.tobytes())
   ix=array('i',[0])*len(o.data.loops);o.data.loops.foreach_get('vertex_index',ix);h.update(ix.tobytes())
   mi=array('i',[0])*len(o.data.polygons);o.data.polygons.foreach_get('material_index',mi);h.update(mi.tobytes())
   for uv in o.data.uv_layers:
    a=array('f',[0])*len(uv.data)*2;uv.data.foreach_get('uv',a);h.update(a.tobytes())
   h.update(str([m.name if m else None for m in o.data.materials]).encode())
   h.update(str([(m.type,getattr(m,'width',None),getattr(m,'segments',None),getattr(m,'ratio',None)) for m in o.modifiers]).encode())
  if o.type=='FONT':h.update(str((o.data.body,o.data.size,o.data.extrude,o.data.font.name)).encode())
  if o.type=='LIGHT':h.update(str((o.data.type,o.data.energy,tuple(o.data.color),o.data.size)).encode())
  result[o.name]=h.hexdigest()
 return result
with tempfile.TemporaryDirectory() as temp:
 (Path(temp)/'Fonts').symlink_to(ROOT/'Blender/Fonts',target_is_directory=True)
 old=Path(temp)/'base.blend';old.write_bytes(subprocess.check_output(['git','show',base+':Blender/The_Commons_Compact.blend'],cwd=ROOT))
 before=snapshot(old);after=snapshot(current)
changed=[n for n in before if before[n]!=after.get(n)];extra=sorted(set(after)-set(before))
remaining=[o.name for o in bpy.data.objects if o.name.startswith(tuple(spec['removed_object_prefixes']))]
# Entry and return portal buttons must be visible at eye level from their approach.
s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();sightlines=[]
for area in ['fpv','kart']:
 r=next(r for r in spec['portals'] if r['area']==area);target=Vector(r['position'])+Vector((0,-.08,.15));origin=Vector((14,1.2,1.6));d=target-origin
 hit,point,normal,idx,obj,matrix=s.ray_cast(deps,origin,d.normalized(),distance=d.length+.12)
 sightlines.append({'area':area,'first_hit':obj.name if hit else None,'clear':hit and any(c.name=='WAY_'+area.upper()+'_Cafe' for c in obj.users_collection)})
report={'base_commit':base,'blend_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'preserved_objects':len(before),'changed':changed,'unexpected':extra,'presentation_objects_remaining':remaining,'entry_sightlines':sightlines,'passed':not changed and not extra and not remaining and all(x['clear'] for x in sightlines)}
(ROOT/'Documentation/cafe_source_preservation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
