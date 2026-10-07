from pathlib import Path
import json,struct,math,collections
import numpy as np
import bpy,ezdxf
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'Unity/Assets/TheCommons'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
S=bpy.context.scene;report={'checks':[],'runtime_tests':'NOT RUN: Unity Editor and VRChat client are not available in this environment.'}
def check(name,ok,detail):
 report['checks'].append({'name':name,'pass':bool(ok),'detail':detail})
 if not ok:print('FAIL',name,detail)
def bounds(name):
 o=bpy.data.objects[name];a=np.array([list(o.matrix_world@Vector(v)) for v in o.bound_box]);return a.min(0),a.max(0)
lo,hi=bounds('Ground');check('Footprint',np.allclose(hi[:2]-lo[:2],[28,18]),(hi-lo).tolist())
for name in ['WestMezzanine','SouthBridge','NorthBridge','QuietFloor','DJFloor']:
 lo,hi=bounds(name);check(name+' datum',abs(hi[2]-4.8)<1e-5,hi.tolist())
lo,hi=bounds('AV_Stage');check('Stage dimensions',np.allclose(hi-lo,[4.8,4.8,.25]),(hi-lo).tolist())
lo,hi=bounds('AV_MainScreen');check('Main screen dimensions',abs(hi[0]-lo[0]-7.1)<1e-5 and abs(hi[2]-lo[2]-4)<1e-5,(hi-lo).tolist())
im=[i for i in bpy.data.images if i.source=='FILE'];check('Texture images resolve',all(i.packed_file is not None or Path(bpy.path.abspath(i.filepath)).is_file() for i in im),len(im))
# Intersect real horizontal face polygons, rather than relying on floor bbox checks.
# This catches the former nested landing, stage cap, and riser/tread z-fighting.
from shapely.geometry import Polygon
from shapely.strtree import STRtree
planes=collections.defaultdict(list)
names={c['name'][4:] for c in json.loads((ROOT/'Documentation/model_manifest.json').read_text())['colliders'] if c['kind']=='box' and abs(c['position'][2]+c['size'][2]/2-4.8)<1e-4}
names|={'Ground','AV_Stage','AV_StageDeck'}
for o in bpy.data.objects:
 if o.type!='MESH' or not (o.name in names or o.name.startswith(('EastStair_Tread','WestStair_Tread','EastStair_Riser','WestStair_Riser','EastStair_Nosing','WestStair_Nosing'))):continue
 for p in o.data.polygons:
  if p.normal.z<.99999:continue
  vs=[o.matrix_world@o.data.vertices[i].co for i in p.vertices]
  planes[round(vs[0].z,4)].append((o.name,Polygon([(v.x,v.y) for v in vs])))
overlaps=[]
for z,items in planes.items():
 tree=STRtree([p for _,p in items])
 for i,(name,p) in enumerate(items):
  for j in tree.query(p):
   if j<=i or name==items[j][0]:continue
   area=p.intersection(items[j][1]).area
   if area>1e-5:overlaps.append({'a':name,'b':items[j][0],'z':z,'area_m2':area})
check('No coplanar overlapping floor/stage/stair top faces',not overlaps,overlaps)
check('No floor overlay strips',not any(o.name.startswith('ARCH_FloorJoint') for o in bpy.data.objects),'Texture detail uses the floor surface itself')
labels=[o for o in bpy.data.objects if 'label_variant' in o]
check('Six label variants mapped to all 93 bottles',len(labels)==93 and {o['label_variant'] for o in labels}==set(range(6)),{'labels':len(labels),'variants':sorted({o['label_variant'] for o in labels})})
for name in ['MAT_DJPanel','MAT_BottleLabels','MAT_PropPrint']:
 m=bpy.data.materials[name];users=[o for o in bpy.data.objects if o.type=='MESH' and name in o.data.materials]
 check(name+' artwork UVs and clamp mode',len(users)>0 and m.get('wrap')=='clamp' and all(o.data.uv_layers.active for o in users),{'mesh_objects':len(users),'texture':m.get('texture_key')})
for fn in ['TheCommons_PC','TheCommons_Quest']:
 with open(A/'Models'/f'{fn}.tcmesh.bytes','rb') as f:
  assert f.read(4)==b'TCM2';num=struct.unpack('<I',f.read(4))[0];tri=0;vtotal=0;bad=0;badnorm=0
  def st():n=struct.unpack('<i',f.read(4))[0];return f.read(n).decode()
  for i in range(num):
   name,g,m=st(),st(),st();nv,ni=struct.unpack('<II',f.read(8));v=np.frombuffer(f.read(nv*32),'<f4').reshape(nv,8);ix=np.frombuffer(f.read(ni*4),'<i4').reshape(-1,3)
   bad+=int(not np.all(np.isfinite(v)) or ix.min()<0 or ix.max()>=nv)
   face=np.cross(v[ix[:,1],:3]-v[ix[:,0],:3],v[ix[:,2],:3]-v[ix[:,0],:3]);dot=np.einsum('ij,ij->i',face,v[ix[:,0],3:6]);badnorm+=int(np.sum(dot<-.0001));tri+=ni//3;vtotal+=nv
  check(fn+' binary',bad==0,dict(meshes=num,triangles=tri,vertices=vtotal,invalid_meshes=bad))
  check(fn+' handedness',badnorm==0,dict(inverted_triangles=badnorm))
  check(fn+' end of file',f.read()==b'',str(f.tell()))
# Visibility is checked against the actual evaluated geometry; this is not a substitute for headset testing.
deps=bpy.context.evaluated_depsgraph_get()
for o in bpy.data.collections['MODE_Academic'].objects:o.hide_set(True);o.hide_render=True
origins={'Entry':[14,1.25,1.6],'Stage approach':[14,9.65,1.6],'Upper overlook':[17.95,4.05,6.4]}
for n,origin in origins.items():
 target=Vector((14,16.80,2.4)) if n!='Upper overlook' else Vector((14,17.3,7.22))
 origin=Vector(origin);vec=target-origin
 hit,point,normal,idx,obj,matrix=S.ray_cast(deps,origin,vec.normalized(),distance=vec.length+.15)
 report.setdefault('sightlines',[]).append({'view':n,'target':'Main screen' if n!='Upper overlook' else 'Upper repeater','first_hit':obj.name if hit else None,'distance_m':float((point-origin).length) if hit else None})
# 2F connectivity, using actual floor/guard colliders. 0.4m diameter navigation probe.
raw=json.loads((ROOT/'Documentation/model_manifest.json').read_text());cols=raw['colliders'];step=.1
xs=np.arange(.05,28,.1);ys=np.arange(.05,18,.1);xx,yy=np.meshgrid(xs,ys);floor=np.zeros_like(xx,dtype=bool);block=np.zeros_like(xx,dtype=bool)
for c in cols:
 if c['kind']!='box':continue
 x,y,z=c['position'];sx,sy,sz=c['size'];top=z+sz/2;bottom=z-sz/2
 if abs(top-4.8)<.001:floor|=(abs(xx-x)<=sx/2+.0001)&(abs(yy-y)<=sy/2+.0001)
 if bottom<6.4 and top>4.9:block|=(abs(xx-x)<sx/2+.20)&(abs(yy-y)<sy/2+.20)
# Erode floor by the collision probe radius to detect narrow unsupported crossings.
from scipy.ndimage import binary_erosion
floor=binary_erosion(floor,iterations=2);walk=floor&~block
def cell(p):return (int(round((p[1]-.05)/step)),int(round((p[0]-.05)/step)))
start=cell((18,3.65));seen={start};queue=collections.deque([start])
while queue:
 y,x=queue.popleft()
 for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
  q=(y+dy,x+dx)
  if 0<=q[0]<walk.shape[0] and 0<=q[1]<walk.shape[1] and walk[q] and q not in seen:seen.add(q);queue.append(q)
for name,p in [('Orbit Cafe',(3,6.8)),('DJ Booth',(14,14.5)),('Archive',(24,4.2)),('Horizon',(25,12)),('West Stair Landing',(8,16.8))]:check('2F route: '+name,cell(p) in seen,list(p))
check('Academic chair anchors',sum(s['group']=='MODE_Academic' for s in raw['seat_anchors'])==24,24)
check('PC total mesh target',len(bpy.data.objects)>3000,'Editable objects: '+str(len(bpy.data.objects)))
# FPV geometry and travel checks against authored collider records.
fpv=raw['fpv'];origin=np.array(fpv['origin']);size=np.array(fpv['size'])
lo,hi=bounds('FPV_Floor')
check('FPV independent floor',np.allclose(hi[:2]-lo[:2],size[:2]) and hi[0]<-20 and abs(hi[2])<1e-5,{'size':size.tolist(),'bounds':[lo.tolist(),hi.tolist()]})
box_cols=[c for c in cols if c['kind']=='box']
centers=np.array([c['position'] for c in box_cols]);half=np.array([c['size'] for c in box_cols])*.5
bmin=centers-half;bmax=centers+half
def sphere_hits(p,r):
 d=np.maximum(np.maximum(bmin-p,p-bmax),0)
 return [box_cols[i]['name'] for i in np.where(np.sum(d*d,axis=1)<r*r-1e-7)[0]]
failures=[]
for g in fpv['gates']:
 center=np.array(g['world_center']);d=np.array(g['direction']);side=np.array([-d[1],d[0],0])
 for u in np.linspace(-fpv['gate_clear_width']/2+.17,fpv['gate_clear_width']/2-.17,9):
  for z in np.linspace(-fpv['gate_clear_height']/2+.17,fpv['gate_clear_height']/2-.17,9):
   hits=sphere_hits(center+side*u+np.array([0,0,z]),.16)
   if hits:failures.append({'gate':g['id'],'hits':hits})
check('FPV 8 clear gate openings',len(fpv['gates'])==8 and not failures,{'radius_m':.16,'failures':failures[:12]})
failures=[];points=[np.array(g['world_center']) for g in fpv['gates']]
for i,a in enumerate(points):
 b=points[(i+1)%len(points)]
 for t in np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/.15)+1)):
  hits=sphere_hits(a+(b-a)*t,.16)
  if hits:failures.append({'segment':i+1,'hits':hits})
check('FPV loop centerline clearance',not failures,{'radius_m':.16,'failures':failures[:12]})
failures=[]
for portal in fpv['portals']:
 p=np.array(portal['destination'])
 for h in [.22,.9,1.5]:
  hits=sphere_hits(p+np.array([0,0,h]),.22)
  if hits:failures.append({'portal':portal['name'],'hits':hits})
check('FPV return and arrival capsule clearance',not failures,{'radius_m':.22,'failures':failures})
f=fpv['flight_bounds_local'];p=fpv['pilot_bounds_local'];v=fpv['spectator_bounds_local']
check('FPV flight pilot spectator separation',p[3]<f[1] and v[3]<f[1] and p[2]<v[0],{'flight':f,'pilot':p,'spectator':v})
geo=json.loads((ROOT/'Documentation/geometry_report.json').read_text())
for platform,limit in [('pc',30000),('quest',25000)]:
 meshes=[m for m in geo[platform]['meshes'] if m['group'].startswith('FPV_')]
 total=sum(m['triangles'] for m in meshes)
 check('FPV '+platform+' geometry budget',total<=limit and len(meshes)<=24,{'triangles':total,'meshes':len(meshes),'triangle_budget':limit,'runtime_frame_timing':'not measured'})
report['notes']=['West stair is 48.14 degrees in the retained CAD envelope; use its adjacent portal if movement is blocked by the VRChat slope limit.','Room and player audio levels, shader compilation, lightmap bake, network late join, Quest performance and VR playtest remain unverified.','Six architectural textures use Mirror wrap, not exact raw Repeat edge matching. Three new printed artwork atlases use Clamp and individual UV regions.','Coplanar test covers walkable floor, stage and stair top faces. It is not a claim that all intentional object contacts or all realtime artifacts are eliminated.']
(ROOT/'Documentation/validation_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
# Actual floor and collider layout, in millimetres, separate from the original CAD.
doc=ezdxf.new('R2010');doc.units=4;ms=doc.modelspace()
for name,color in [('IMPL_FLOOR_2F',4),('IMPL_COLLIDER',8),('IMPL_GUARD',3),('SOURCE_ZONE',7),('NOTES',2)]:doc.layers.new(name,dxfattribs={'color':color})
spec=json.loads((ROOT/'SourceDesign/world_spec.json').read_text())
for zone in spec['zones_2f']:
 b=zone['bbox'];ms.add_lwpolyline([(b[0]*1000,b[1]*1000),(b[2]*1000,b[1]*1000),(b[2]*1000,b[3]*1000),(b[0]*1000,b[3]*1000)],close=True,dxfattribs={'layer':'SOURCE_ZONE'})
for c in cols:
 if c['kind']!='box':continue
 x,y,z=c['position'];sx,sy,sz=c['size'];layer='IMPL_FLOOR_2F' if abs(z+sz/2-4.8)<.001 else 'IMPL_GUARD' if 'Balustrade' in c['name'] else 'IMPL_COLLIDER'
 ms.add_lwpolyline([((x-sx/2)*1000,(y-sy/2)*1000),((x+sx/2)*1000,(y-sy/2)*1000),((x+sx/2)*1000,(y+sy/2)*1000),((x-sx/2)*1000,(y+sy/2)*1000)],close=True,dxfattribs={'layer':layer})
ms.add_text('THE COMMONS - v0.5 IMPLEMENTATION OVERLAY / PROPOSED CHANGES - NOT SOURCE CAD',dxfattribs={'height':240,'insert':(0,19000),'layer':'NOTES'})
doc.saveas(ROOT/'CAD/The_Commons_Implementation_Overlay_v05.dxf')
print(json.dumps(report,ensure_ascii=False,indent=2))
if any(not c['pass'] for c in report['checks']):raise SystemExit(1)
