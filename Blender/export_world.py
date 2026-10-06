"""Export render groups, deterministic Unity mesh binary, FBX and GLB."""
from pathlib import Path
import bpy,bmesh,struct,json,collections,math,os
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'Unity/Assets/TheCommons'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
S=bpy.context.scene
# Realizing modifiers and font geometry once; the saved .blend remains fully editable.
for o in list(bpy.data.objects):
 o.hide_set(False);o.hide_render=False
 if o.type not in {'MESH','FONT'}:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.convert(target='MESH')
for o in bpy.data.objects:
 if o.type=='MESH':
  bpy.context.view_layer.objects.active=o
  for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
# Keep face-assigned artwork and stage timber through FBX/TCM export.
# Split by material before batching; a TCM render mesh has exactly one material.
for o in list(bpy.data.objects):
 used=sorted({p.material_index for p in o.data.polygons})
 if len(used)<2:continue
 for index in used:
  me=o.data.copy();bm=bmesh.new();bm.from_mesh(me)
  bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=index],context='FACES')
  for f in bm.faces:f.material_index=0
  bm.to_mesh(me);bm.free();me.materials.clear();me.materials.append(o.data.materials[index])
  piece=bpy.data.objects.new(o.name+'_'+o.data.materials[index].name,me);piece.matrix_world=o.matrix_world.copy();o.users_collection[0].objects.link(piece)
 bpy.data.objects.remove(o,do_unlink=True)
groups=collections.defaultdict(list)
for o in list(bpy.data.objects):
 if o.type=='MESH':groups[(o.users_collection[0].name,o.data.materials[0].name)].append(o)
for (g,m),obs in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=obs[0];o.name=g+'__'+m
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for o in bpy.data.objects:
 if o.type=='MESH':
  # Unity will also generate UV2 during import; this layer is available to Blender users.
  o.data.calc_loop_triangles()
print('COMBINED',len(bpy.data.objects),flush=True)
def st(f,s):
 b=s.encode('utf8');f.write(struct.pack('<i',len(b)));f.write(b)
def savebin(file,objects):
 stats=[]
 temporary=Path(str(file)+'.tmp')
 with open(temporary,'wb') as f:
  f.write(b'TCM2');f.write(struct.pack('<I',len(objects)))
  for o in objects:
   me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data if me.uv_layers else None
   st(f,o.name);st(f,o.users_collection[0].name);st(f,me.materials[0].name)
   # Face loops preserve UV and flat normals. Indexed dedup reduces file size.
   vertices=[];tris=[];lookup={}
   for tri in me.loop_triangles:
    ids=[]
    for li in tri.loops:
     vi=me.loops[li].vertex_index;p=me.vertices[vi].co;n=me.polygons[tri.polygon_index].normal;t=uv[li].uv if uv else (0,0)
     key=tuple(round(a,6) for a in (p.x,p.z,p.y,n.x,n.z,n.y,t[0],t[1]))
     if key not in lookup:lookup[key]=len(vertices);vertices.append(key)
     ids.append(lookup[key])
    tris.extend([ids[0],ids[2],ids[1]]) # Right-handed Blender -> left-handed Unity.
   f.write(struct.pack('<II',len(vertices),len(tris)))
   for v in vertices:f.write(struct.pack('<8f',*v))
   f.write(struct.pack('<%di'%len(tris),*tris))
   stats.append(dict(name=o.name,group=o.users_collection[0].name,vertices=len(vertices),triangles=len(tris)//3))
  f.flush();os.fsync(f.fileno());written=f.tell()
 os.replace(temporary,file)
 assert Path(file).stat().st_size==written
 print('BINARY SAVED',file.name,written,flush=True)
 return stats
objects=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda x:x.name)
pc=savebin(A/'Models/TheCommons_PC.tcmesh.bytes',objects)
# Standard exports for other DCC applications. Assets use material-name mapping in Unity.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=str(A/'Models/TheCommons_PC.fbx'),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE')
# GLB material graph: direct image + factor yields universal glTF support.
for m in bpy.data.materials:
 key=m.get('texture_key','')
 if key:
  p=m.node_tree.nodes.get('Principled BSDF');img=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
  for l in list(p.inputs['Base Color'].links):m.node_tree.links.remove(l)
  m.node_tree.links.new(img.outputs['Color'],p.inputs['Base Color'])
# Hide inactive academic group in the GLB through selection.
bpy.ops.object.select_all(action='DESELECT')
for o in objects:
 if o.users_collection[0].name not in ['MODE_Academic']:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Preview/The_Commons_Compact.glb'),export_format='GLB',use_selection=True,export_materials='EXPORT',export_image_format='AUTO',export_yup=True)
# Mobile geometry: city window detail and hanging garden are optional, curves decimated conservatively.
qobjs=[]
for o in objects:
 g=o.users_collection[0].name
 if g in ['FURN_HangingGarden','AV_Hologram']:continue
 if o.data.materials[0].name=='MAT_Window':continue
 if g=='ENV_City' and o.data.materials[0].name in ['MAT_Amber','MAT_Cyan']:continue
 if len(o.data.polygons)>1500:
  bpy.context.view_layer.objects.active=o;d=o.modifiers.new('Mobile decimation','DECIMATE');d.ratio=.56;bpy.ops.object.modifier_apply(modifier=d.name)
 qobjs.append(o)
q=savebin(A/'Models/TheCommons_Quest.tcmesh.bytes',qobjs)
bpy.ops.object.select_all(action='DESELECT')
for o in qobjs:o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(A/'Models/TheCommons_Quest.fbx'),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE')
report={'pc':{'triangles':sum(x['triangles'] for x in pc),'render_meshes':len(pc),'meshes':pc},'quest':{'triangles':sum(x['triangles'] for x in q),'render_meshes':len(q),'meshes':q},'measurement':'Exported whole-scene geometry. Not runtime FPS / draw-call measurement.'}
(ROOT/'Documentation/geometry_report.json').write_text(json.dumps(report,indent=2))
print({k:{x:v[x] for x in ['triangles','render_meshes']} for k,v in report.items() if isinstance(v,dict)},flush=True)
