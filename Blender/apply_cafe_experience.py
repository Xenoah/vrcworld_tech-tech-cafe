"""Idempotent v0.9 cafe update on the latest .blend, preserving the authored kart.
Also called by build_world.py, so a clean rebuild includes the same changes.
"""
from pathlib import Path
import json,math,sys
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'SourceDesign/cafe_experience.json'


def apply():
 spec=json.loads(SPEC.read_text());scene=bpy.context.scene
 for obj in list(bpy.data.objects):
  if obj.name.startswith(tuple(spec['removed_object_prefixes'])) or any(c.name.startswith('WAY_') for c in obj.users_collection):
   bpy.data.objects.remove(obj,do_unlink=True)
 for col in list(bpy.data.collections):
  if col.name.startswith('WAY_'):bpy.data.collections.remove(col)
 materials={}
 def material(name,rgb,emission=0):
  m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
  p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.65
  p.inputs['Emission Color'].default_value=(*rgb,1);p.inputs['Emission Strength'].default_value=emission
  m['emission']=emission;m['texture_key']='';m['wrap']='clamp';materials[name]=m;return m
 dark=material('MAT_WayDark',(.012,.021,.032));white=material('MAT_WayWhite',(.9,.94,1),.25)
 colors={x['area']:material('MAT_Way_'+x['label'],tuple(x['color']),1.1) for x in spec['portals']}
 def group(name):
  c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
 def box(c,name,p,size,mat,yaw=0):
  x,y,z=[s/2 for s in size];verts=[(i*x,j*y,k*z) for i,j,k in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update();mesh.materials.append(mat)
  uv=mesh.uv_layers.new(name='UVMap')
  for poly in mesh.polygons:
   for i,li in enumerate(poly.loop_indices):uv.data[li].uv=[(0,0),(1,0),(1,1),(0,1)][i%4]
  o=bpy.data.objects.new(name,mesh);c.objects.link(o);o.location=p;o.rotation_euler.z=-math.radians(yaw);return o
 font=next((f for f in bpy.data.fonts if Path(f.filepath).name=='DejaVuSans-Bold.ttf'),None) or bpy.data.fonts.load(str(ROOT/'Blender/Fonts/DejaVuSans-Bold.ttf'),check_existing=True)
 font.filepath='//Fonts/DejaVuSans-Bold.ttf'
 def text(c,name,body,p,size,mat,yaw=0):
  curve=bpy.data.curves.new(name,'FONT');curve.body=body;curve.size=size;curve.align_x='CENTER';curve.align_y='CENTER';curve.font=font;curve.extrude=.0006;curve.resolution_u=2;curve.materials.append(mat)
  o=bpy.data.objects.new(name,curve);c.objects.link(o);o.location=p;o.rotation_euler=(math.pi/2,0,-math.radians(yaw));return o
 manifest=json.loads((ROOT/'Documentation/model_manifest.json').read_text())
 def station(area,index):
  route=next(x for x in spec['portals'] if x['area']==area);p=manifest[area]['portals'][index]
  if index==0:p['position']=route['position']
  else:p['destination']=route['return_destination']
  return p,route
 for area in ['fpv','kart']:
  for index in [0,1]:
   rec,route=station(area,index);p=Vector(rec['position']);yaw=rec.get('facing_yaw',0);rot=Matrix.Rotation(-math.radians(yaw),3,'Z')
   c=group('WAY_'+area.upper()+('_Cafe' if index==0 else '_Return'));color=colors[area]
   def pt(v):return p+rot@Vector(v)
   def block(n,v,s,m):return box(c,'WAY_'+n,pt(v),s,m,yaw)
   def caption(n,t,v,s,m):return text(c,'WAY_'+n,t,pt(v),s,m,yaw)
   block('PortalBack',(0,.08,.3),(2.8,.16,2.6),dark)
   for x in [-1.44,1.44]:block('PortalEdge',(x,-.025,.3),(.065,.045,2.76),color)
   for z in [-1.08,1.68]:block('PortalEdge',(0,-.025,z),(2.94,.045,.065),color)
   # Runtime interaction occupies the lower recess; its button is added in Unity.
   block('ButtonRecess',(0,-.025,0),(2.2,.035,.82),color)
   block('ButtonBlank',(0,-.05,0),(2.1,.035,.72),dark)
   caption('Destination',route['label'] if index==0 else 'CAFE',(0,-.035,1.22),.58,white)
   caption('Area',route['subtitle'] if index==0 else 'RETURN TO THE COMMONS',(0,-.035,.76),.145,color)
   caption('Action',('GO TO '+route['label']) if index==0 else 'RETURN TO CAFE',(0,-.076,0),.235,white)
   caption('Instruction','SELECT PANEL TO TRAVEL',(0,-.035,-.61),.14,white)
   caption('Floor',('01 / DRONE FIELD' if area=='fpv' else '02 / KART CIRCUIT') if index==0 else 'BACK TO THE CAFE',(0,-.035,-.88),.13,color)
   block('ArrivalPad',(0,-.7,-p.z+.012),(2.94,1.5,.016),color)
 c=group('WAY_EntryDirectory')
 box(c,'WAY_DirectoryBack',(14,3.45,3.65),(9.0,.12,.42),dark)
 text(c,'WAY_DirectoryTitle','ACTIVITY PORTALS  /  SELECT TO TRAVEL',(14,3.375,3.65),.22,white)
 # Stable destination colors and large floor chevrons visible from spawn.
 for route in spec['portals']:
  color=colors[route['area']];x=route['position'][0];y=2.0;direction=-1 if x<14 else 1
  box(c,'WAY_Path',((14+x)/2,y,.014),(abs(x-14),.065,.014),color)
  for xx in [14+direction*.6,14+direction*1.4]:
   for side in [-1,1]:
    o=box(c,'WAY_Arrow',(xx,y+side*.11,.025),(.35,.05,.018),color);o.rotation_euler.z=-direction*side*math.radians(40)
  floor_label=text(c,'WAY_FloorLabel',route['label'],(x,2.7,.028),.32,color)
  floor_label.rotation_euler=(0,0,0)
 # External player placement guides are empty; no third-party prefab is bundled.
 for name,pos in [('IwaSync_PlayerAnchor',(24.35,15.4,1.7)),('IwaSync_MainScreenAnchor',spec['iwasync']['main_screen']),('IwaSync_UpperScreenAnchor',spec['iwasync']['upper_screen'])]:
  old=bpy.data.objects.get(name)
  if old:bpy.data.objects.remove(old,do_unlink=True)
  o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.location=pos;o.empty_display_type='CUBE';o.empty_display_size=.3
 for file in [ROOT/'Documentation/model_manifest.json',ROOT/'Unity/Assets/TheCommons/Data/world_manifest.json']:
  data=json.loads(file.read_text());data['version']=spec['version'];data['experience']=spec
  for area in ['fpv','kart']:
   data[area]['portals']=manifest[area]['portals']
  additions={n:dict(color=list(m.diffuse_color),texture='',emission=m['emission'],wrap='clamp',roughness=.65,metallic=0) for n,m in materials.items()}
  if isinstance(data['materials'],dict):data['materials'].update(additions)
  else:
   data['materials']=[m for m in data['materials'] if m['name'] not in additions]+[dict(name=n,**m) for n,m in additions.items()]
  file.write_text(json.dumps(data,indent=2)+'\n')
 (ROOT/'Unity/Assets/TheCommons/Data/cafe_experience.json').write_text(SPEC.read_text())
 scene['revision']=spec['version'];bpy.context.view_layer.update()
 print('Cafe update applied. Kart/FPV mesh objects untouched.',flush=True)

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
 apply()
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'),compress=True)
