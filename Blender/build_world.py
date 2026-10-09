import runpy
"""THE COMMONS / editable art source. Blender 4.5 LTS, Python 3.11 bpy.
Run: blender --background --python build_world.py
Meters, CAD +X east / +Y north / +Z up. Original CAD remains unchanged.
"""
from pathlib import Path
import bpy, math, json, random, sys, os
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT/'Unity/Assets/TheCommons'
random.seed(104)
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
S.unit_settings.system='METRIC'; S.unit_settings.scale_length=1
M={}; GROUPS={}; COL=[]; LIGHTS=[]; SEATS=[]; CAMS={}; COUNTS={}
GROUP='ARCH_Shell'
def group(name):
 global GROUP
 GROUP=name
 if name not in GROUPS:
  c=bpy.data.collections.new(name); S.collection.children.link(c); GROUPS[name]=c
def link(o):
 if GROUP not in GROUPS: group(GROUP)
 GROUPS[GROUP].objects.link(o)
 return o
def mat(name,color,texture=None,rough=.72,metal=0,emit=0,wrap='mirror'):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
 p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emit
 if texture:
  n=m.node_tree.nodes.new('ShaderNodeTexImage'); n.image=bpy.data.images.load(str(ASSET/'Textures'/f'{texture}_albedo.png'),check_existing=True); n.extension='MIRROR' if wrap=='mirror' else 'EXTEND'
  mix=m.node_tree.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=1; mix.inputs[2].default_value=(*color,1)
  m.node_tree.links.new(n.outputs['Color'],mix.inputs[1]); m.node_tree.links.new(mix.outputs[0],p.inputs['Base Color'])
 m['texture_key']=texture or ''; m['emission']=emit; m['wrap']=wrap; M[name]=m
 return m
mat('MAT_Steel',(.70,.77,.82),'blackened_steel',.65,.45)
mat('MAT_Oak',(.87,.73,.59),'warm_oak',.65)
mat('MAT_Plaster',(.56,.59,.62),'mineral_plaster',.9)
mat('MAT_Stone',(.67,.70,.74),'basalt_terrazzo',.58)
mat('MAT_Brass',(.72,.56,.37),'satin_brass',.48,.65)
mat('MAT_Fabric',(.85,.86,.86),'teal_woven',.96)
mat('MAT_Cream',(.53,.43,.28),'teal_woven',.98)
mat('MAT_Black',(.012,.019,.026),rough=.8)
mat('MAT_Ceramic',(.63,.59,.49),rough=.7)
mat('MAT_Leaf',(.055,.18,.10),rough=.91)
mat('MAT_LeafLight',(.14,.28,.105),rough=.88)
mat('MAT_BottleGreen',(.018,.12,.075),rough=.28,metal=.15)
mat('MAT_BottleAmber',(.25,.077,.022),rough=.26,metal=.12)
mat('MAT_Label',(.52,.43,.30),rough=.9)
mat('MAT_Glass',(.065,.13,.155),rough=.25,metal=.22)
glass=mat('MAT_Window',(.11,.19,.22),rough=.25)
gn=glass.node_tree.nodes;gl=glass.node_tree.links;gp=gn.get('Principled BSDF');go=gn.get('Material Output');gt=gn.new('ShaderNodeBsdfTransparent');gm=gn.new('ShaderNodeMixShader');gm.inputs[0].default_value=.07;gl.new(gt.outputs[0],gm.inputs[1]);gl.new(gp.outputs[0],gm.inputs[2]);gl.new(gm.outputs[0],go.inputs['Surface'])
glass=mat('MAT_SafetyGlass',(.20,.36,.40),rough=.18,metal=.12)
gn=glass.node_tree.nodes;gl=glass.node_tree.links;gp=gn.get('Principled BSDF');go=gn.get('Material Output');gt=gn.new('ShaderNodeBsdfTransparent');gm=gn.new('ShaderNodeMixShader');gm.inputs[0].default_value=.12;gl.new(gt.outputs[0],gm.inputs[1]);gl.new(gp.outputs[0],gm.inputs[2]);gl.new(gm.outputs[0],go.inputs['Surface'])
mat('MAT_Amber',(.95,.42,.115),rough=.5,emit=2.3)
mat('MAT_Cyan',(.02,.48,.72),rough=.5,emit=1.6)
mat('MAT_White',(.72,.82,.86),rough=.6,emit=.5)
mat('MAT_Holo',(.018,.3,.48),rough=.3,emit=1.0)
mat('MAT_DJPanel',(1,1,1),'relay_controller',.8,0,wrap='clamp')
M['MAT_DJPanel'].node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.16
mat('MAT_BottleLabels',(1,1,1),'bar_labels',.84,wrap='clamp')
mat('MAT_PropPrint',(1,1,1),'cafe_props',.73,wrap='clamp')
def uv_planar(mesh,scale=1):
 uv=mesh.uv_layers.new(name='UVMap')
 for poly in mesh.polygons:
  normal=poly.normal; axis=max(range(3),key=lambda i:abs(normal[i])); ij=[i for i in range(3) if i!=axis]
  for li in poly.loop_indices:
   p=mesh.vertices[mesh.loops[li].vertex_index].co
   uv.data[li].uv=(p[ij[0]]*scale,p[ij[1]]*scale)
def mesh(name,vs,fs,material,uvscale=1):
 me=bpy.data.meshes.new(name); me.from_pydata(vs,[],fs); me.update()
 o=link(bpy.data.objects.new(name,me)); me.materials.append(M[material]); uv_planar(me,uvscale)
 return o
def box(name,pos,size,material='MAT_Steel',bevel=0):
 x,y,z=pos; a,b,c=[v/2 for v in size]
 vs=[(x+i*a,y+j*b,z+k*c) for i,j,k in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 o=mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,2 if material=='MAT_Fabric' else .5)
 if bevel:
  m=o.modifiers.new('Small edge chamfer','BEVEL'); m.width=bevel; m.segments=2
 return o
def print_face(o,face,material,rect=(0,0,1,1),axes=(0,2),flip_u=False,flip_v=False):
 """Replace one existing face's material/UV; no overlapping decal geometry.
 rect uses Blender UV origin (bottom left). Atlas margins prevent adjacent ink bleeding.
 """
 if M[material].name not in o.data.materials:o.data.materials.append(M[material])
 p=o.data.polygons[face];p.material_index=o.data.materials.find(material)
 u0,v0,u1,v1=rect;points=[o.data.vertices[i].co for i in p.vertices]
 lo=[min(v[a] for v in points) for a in axes];hi=[max(v[a] for v in points) for a in axes]
 for li in p.loop_indices:
  v=o.data.vertices[o.data.loops[li].vertex_index].co
  u=(v[axes[0]]-lo[0])/(hi[0]-lo[0]);t=(v[axes[1]]-lo[1])/(hi[1]-lo[1])
  if flip_u:u=1-u
  if flip_v:t=1-t
  o.data.uv_layers.active.data[li].uv=(u0+u*(u1-u0),v0+t*(v1-v0))
 return o
def atlas_rect(index,columns=3,rows=2,inset=.012):
 c=index%columns;r=index//columns
 return ((c+inset)/columns,1-(r+1-inset)/rows,(c+1-inset)/columns,1-(r+inset)/rows)
def bottle_label(x,y,z,variant,r=.052,height=.092):
 """Curved label facing +X. Side-only strip, 3 mm outside the glass, no hidden box.
 Six brand cells share one material. Cropped guard pixels isolate mip boundaries.
 """
 vs=[];n=6;angle=.86
 for zz in [z-height/2,z+height/2]:
  for i in range(n+1):
   a=-angle+2*angle*i/n;vs.append((x+(r+.003)*math.cos(a),y+(r+.003)*math.sin(a),zz))
 o=mesh('FURN_BottleLabel',vs,[(i,i+1,i+1+n+1,i+n+1) for i in range(n)],'MAT_BottleLabels')
 u0,v0,u1,v1=atlas_rect(variant)
 for p in o.data.polygons:
  for li in p.loop_indices:
   vi=o.data.loops[li].vertex_index;o.data.uv_layers.active.data[li].uv=(u0+(vi%(n+1))/n*(u1-u0),v0+(vi//(n+1))*(v1-v0))
 o['label_variant']=variant
 return o
def slab(name,b,z,th=.2,matn='MAT_Stone',collision=True):
 x1,y1,x2,y2=b
 o=box(name,((x1+x2)/2,(y1+y2)/2,z-th/2),(x2-x1,y2-y1,th),matn)
 if collision: colbox(name,((x1+x2)/2,(y1+y2)/2,z-th/2),(x2-x1,y2-y1,th))
 return o
def colbox(name,pos,size,rot=(0,0,0),kind='box'):
 COL.append(dict(name='COL_'+name,position=list(pos),size=list(size),rotation=list(rot),kind=kind,group=GROUP))
def cyl(name,pos,r,depth,material='MAT_Steel',segments=20,r2=None):
 if r2 is None:r2=r
 x,y,z=pos; vs=[]
 for zz,rad in [(z-depth/2,r),(z+depth/2,r2)]:
  vs.extend((x+rad*math.cos(2*math.pi*i/segments),y+rad*math.sin(2*math.pi*i/segments),zz) for i in range(segments))
 fs=[tuple(reversed(range(segments))),tuple(range(segments,segments*2))]+[(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
 return mesh(name,vs,fs,material)
def beam(name,a,b,r=.025,material='MAT_Steel',segments=8):
 a=Vector(a); b=Vector(b); d=b-a; u=d.cross(Vector((0,0,1)))
 if u.length<.01:u=d.cross(Vector((1,0,0)))
 u.normalize(); v=d.normalized().cross(u); vs=[]
 for p in [a,b]:
  for i in range(segments):
   pt=p+r*(u*math.cos(i*2*math.pi/segments)+v*math.sin(i*2*math.pi/segments));vs.append(tuple(pt))
 fs=[tuple(reversed(range(segments))),tuple(range(segments,2*segments))]+[(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
 return mesh(name,vs,fs,material)
def ring(name,pos,r,minor=.025,material='MAT_Brass',n=64,k=6):
 x,y,z=pos; vs=[]
 for i in range(n):
  a=i*2*math.pi/n
  for j in range(k):
   b=j*2*math.pi/k;vs.append((x+(r+minor*math.cos(b))*math.cos(a),y+(r+minor*math.cos(b))*math.sin(a),z+minor*math.sin(b)))
 return mesh(name,vs,[(i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k) for i in range(n) for j in range(k)],material)
font_path=ROOT/'Blender/Fonts/DejaVuSans.ttf'
if not font_path.exists():font_path=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
FONT=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
def text_obj(name,body,pos,size=.22,matn='MAT_White',rot=(math.pi/2,0,0),align='CENTER'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x=align;cu.align_y='CENTER';cu.extrude=.0008;cu.resolution_u=2
 if FONT:cu.font=FONT
 o=link(bpy.data.objects.new(name,cu));o.location=pos;o.rotation_euler=rot;cu.materials.append(M[matn]); return o
RAIL_POSTS=set()
def rail(name,a,b,z):
 a=Vector((*a,z));b=Vector((*b,z));length=(b-a).length;n=max(1,math.ceil(length/1.15))
 for i in range(n+1):
  p=a.lerp(b,i/n);key=tuple(round(v,5) for v in p)
  if key in RAIL_POSTS:continue
  RAIL_POSTS.add(key)
  beam(name+'_post',p+Vector((0,0,.05)),p+Vector((0,0,1.05)),.026);cyl(name+'_foot',p+Vector((0,0,.025)),.065,.05,'MAT_Brass',12)
 beam(name+'_top',a+Vector((0,0,1.05)),b+Vector((0,0,1.05)),.039,'MAT_Brass',10)
 for h in [.28,.54,.8]:beam(name+'_cable',a+Vector((0,0,h)),b+Vector((0,0,h)),.008,'MAT_Steel',6)
 mid=(a+b)/2
 if abs(a.x-b.x)<.01:colbox(name,(mid.x,mid.y,z+.65),(.09,length,1.3))
 elif abs(a.y-b.y)<.01:colbox(name,(mid.x,mid.y,z+.65),(length,.09,1.3))
def area(name,pos,target,power,color,size=2):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
 o=link(bpy.data.objects.new(name,data));o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 LIGHTS.append(dict(name=name,position=list(pos),color=list(color),power=power,size=size,target=list(target)))
def pendant(x,y,z=3.9):
 beam('LGT_PendantDrop',(x,y,z+.15),(x,y,4.56),.009)
 cyl('LGT_Shade',(x,y,z+.1),.24,.22,'MAT_Steel',24,r2=.10)
 cyl('LGT_Diffuser',(x,y,z-.005),.205,.018,'MAT_Amber',24)
 area('LGT_WarmPendant',(x,y,z-.05),(x,y,0),75,(1,.59,.31),1.1)
def cup(x,y,z):
 cyl('FURN_CoffeeCup',(x,y,z+.065),.048,.12,'MAT_Ceramic',12,r2=.055);cyl('FURN_Coffee',(x,y,z+.126),.047,.003,'MAT_BottleAmber',12)
 ring('FURN_Saucer',(x,y,z+.008),.071,.007,'MAT_Ceramic',16,4)
def stool(x,y,z=0):
 cyl('FURN_StoolBase',(x,y,z+.035),.23,.07,'MAT_Steel',20)
 cyl('FURN_StoolStem',(x,y,z+.36),.045,.62,'MAT_Brass',12)
 ring('FURN_StoolFootrest',(x,y,z+.26),.17,.014,'MAT_Brass',20,5)
 cyl('FURN_StoolSeat',(x,y,z+.755),.24,.095,'MAT_Fabric',24)
def seat(x,y,z=0,angle=0,kind='chair',width=.62,material='MAT_Fabric'):
 start=set(bpy.data.objects)
 w=width;box('FURN_SeatCushion',(0,0,z+.46),(w,.62,.14),material,.04)
 box('FURN_BackCushion',(0,.27,z+.77),(w,.12,.55),material,.04)
 for dx in [-w/2+.06,w/2-.06]:
  for dy in [-.22,.22]:beam('FURN_SeatLeg',(dx,dy,z+.02),(dx,dy,z+.41),.018,'MAT_Brass')
 if kind=='sofa':
  for dx in [-w/2,w/2]:box('FURN_SofaArm',(dx,0,z+.61),(.16,.7,.28),material,.035)
 for o in set(bpy.data.objects)-start:
  o.rotation_euler[2]=angle;o.location.x=x;o.location.y=y
 SEATS.append(dict(position=[x,y,z+.52],yaw=angle,group=GROUP))
def table(x,y,z=0,r=.45,ht=.74):
 cyl('FURN_TableTop',(x,y,z+ht),r,.065,'MAT_Oak',32)
 ring('FURN_TableTrim',(x,y,z+ht-.03),r-.01,.012,'MAT_Brass',32,5)
 cyl('FURN_TableBase',(x,y,z+.04),r*.55,.06,'MAT_Steel',20);cyl('FURN_TableStem',(x,y,z+ht/2),.045,ht-.08,'MAT_Steel',12)
 cup(x-.12,y+.06,z+ht+.033);cup(x+.17,y-.08,z+ht+.033)
 cyl('LGT_TableCandle',(x,y,z+ht+.11),.032,.14,'MAT_Ceramic',12);cyl('LGT_CandleGlow',(x,y,z+ht+.186),.018,.02,'MAT_Amber',10)
def plant(x,y,z=0,height=1.4,r=.31):
 cyl('FURN_Planter',(x,y,z+.22),r*.78,.44,'MAT_Ceramic',16,r2=r)
 cyl('FURN_Soil',(x,y,z+.442),r*.9,.012,'MAT_Black',16)
 for j in range(9):
  a=j*2.4;h=height*random.uniform(.5,1);a0=(x,y,z+.4);b=(x+math.cos(a)*r*1.1,y+math.sin(a)*r*1.1,z+h)
  beam('FURN_PlantStem',a0,b,.01,'MAT_Leaf',5)
  p=Vector(b);side=Vector((math.cos(a+1.4),math.sin(a+1.4),.13))*r*.53;tip=p+Vector((math.cos(a),math.sin(a),.1))*r*.85
  mesh('FURN_Leaf',[tuple(p-Vector((0,0,.13))),tuple(p+side),tuple(tip),tuple(p-side),tuple(p+Vector((0,0,.025)))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'MAT_LeafLight' if j%3==0 else 'MAT_Leaf')
def stair(name,x1,x2,y0,y1,steps=28):
 h=4.8/steps;run=(y1-y0)/steps
 for i in range(steps):
  ht=(i+1)*h;box(name+'_Tread',((x1+x2)/2,y0+(i+.5)*run,ht-.05),(x2-x1,run,.10),'MAT_Oak')
  box(name+'_Riser',((x1+x2)/2,y0+i*run+.015,ht-h/2-.05),(x2-x1,.03,h-.10),'MAT_Steel')
  box(name+'_Nosing',((x1+x2)/2,y0+i*run-.007,ht-.012),(x2-x1,.014,.018),'MAT_Amber')
 for x in [x1+.04,x2-.04]:
  beam(name+'_Stringer',(x,y0,-.1),(x,y1,4.7),.085)
  beam(name+'_Handrail',(x,y0,1.05),(x,y1,5.85),.036,'MAT_Brass')
  for i in range(0,steps,4):
   yy=y0+i*run;zz=(i+1)*h;beam(name+'_Post',(x,yy,zz),(x,yy,zz+1.05),.02)
 vs=[(x1,y0,0),(x2,y0,0),(x2,y1,4.8),(x1,y1,4.8)]
 COL.append(dict(name='COL_'+name,kind='ramp',vertices=vs,group=GROUP))
 COUNTS[name]=dict(risers=steps,rise=h,run=run,slope_degrees=math.degrees(math.atan2(4.8,y1-y0)),clear_width=x2-x1)

# ARCHITECTURE: footprint and floor datums from authoritative JSON.
group('ARCH_Shell')
slab('Ground',(0,0,28,18),0,.2)
# Stone texture supplies floor detail; intersecting 2 mm overlay strips were removed.
for pos,size in [((.125,9,4.8),(.25,17.5,9.6)),((14,17.875,4.8),(28,.25,9.6)),((5.75,.125,4.8),(11.5,.25,9.6)),((22.25,.125,4.8),(11.5,.25,9.6))]:
 box('ARCH_Wall',pos,size,'MAT_Plaster');colbox('Wall',pos,size)
# East curtain wall: opaque lower plinth, columns, minimal smoked panes.
box('ARCH_EastPlinth',(27.875,9,.42),(.25,17.5,.84),'MAT_Plaster');colbox('EastEnvelope',(27.875,9,4.8),(.25,18,9.6))
for y in [.33,3.5,7,10.5,14,17.67]:box('ARCH_EastMullion',(27.84,y,4.8),(.3,.16,9.6),'MAT_Steel')
for z in [4.6,9.45]:box('ARCH_EastTransom',(27.85,9,z),(.25,17.5,.18),'MAT_Steel')
for y in [1.9,5.25,8.75,12.25,15.8]:
 for z in [2.7,7.0]:box('ARCH_WindowPane',(27.91,y,z),(.008,3.1,4.1),'MAT_Window')
slab('Roof',(0,0,28,18),9.8,.2,'MAT_Steel',False)
for x in [.5,8.65,19.85,27.5]:
 for y in [4.9,15.65]:
  box('ARCH_Column',(x,y,4.8),(.28,.3,9.6),'MAT_Steel')
  for z in [.08,4.52,9.25]:
   box('ARCH_ColumnShoe',(x,y,z),(.42,.44,.1),'MAT_Steel')
   for dx in [-.14,.14]:
    for dy in [-.15,.15]:cyl('ARCH_Bolt',(x+dx,y+dy,z+.064),.022,.025,'MAT_Brass',6)
for y in [2.6,5,10.2,15.3,17.6]:box('ARCH_RoofBeam',(14,y,9.22),(27.6,.18,.36),'MAT_Steel')
for x in range(1,28,2):box('ARCH_CeilingBatten',(x,9,9.51),(.06,17.5,.08),'MAT_Oak')
box('ARCH_EntranceHeader',(14,.14,3.7),(5,.28,.32),'MAT_Steel')
text_obj('ARCH_EntrySign','THE  COMMONS',(14,.32,3.7),.28,'MAT_Amber',rot=(math.pi/2,0,math.pi))
# Seal the unsupported south opening behind spawn. The continuous collider
# overlaps both side walls, the ground and roof: panel joints never create gaps.
# Keep this glass in BOTH exports; decorative east panes may be omitted on Quest.
group('ARCH_EntrySafety')
colbox('EntrySafetyGlass',(14,.125,4.8),(5.12,.24,9.8))
for x in [11.53,14,16.47]:box('ARCH_EntryMullion',(x,.15,4.8),(.065,.14,9.6),'MAT_Brass')
for z in [.10,4.68,9.51]:box('ARCH_EntryTransom',(14,.15,z),(5,.16,.10),'MAT_Steel')
for x in [12.765,15.235]:
 for low,high in [(.15,3.54),(3.86,4.63),(4.73,9.46)]:
  box('ARCH_EntrySafetyPane',(x,.125,(low+high)/2),(2.405,.028,high-low),'MAT_SafetyGlass')
 # Fine brass manifestation stripes make the clear barrier visible at eye level.
 box('ARCH_EntryGlassStripe',(x,.149,1.15),(2.38,.012,.018),'MAT_Brass')
box('LGT_EntrySill',(14,.245,.10),(4.9,.025,.018),'MAT_Amber')

group('ARCH_Mezzanine')
# Tile the slabs around CAD stair openings; surface top is exactly 4.800.
slab('WestMezzanine',(0.5,4.2,7,16.8),4.8)
slab('WestMezzanineSouth',(7,4.2,8.8,11.8),4.8)
slab('WestMezzanineLanding',(7,16.1,8.8,17.55),4.8)
# NorthBridge already covers the former WestStairTop rectangle.
slab('WestNorthLink',(.5,16.8,7,17.55),4.8)
slab('SouthBridge',(8.8,2.6,20,5),4.8)
slab('SouthWestAdapter',(7,2.6,8.8,4.2),4.8)
slab('NorthBridge',(8.8,15.3,19.5,17.55),4.8)
slab('NorthEastAdapter',(19.5,15.0,21.3,17.55),4.8)
slab('TerraceEast',(21.3,9,27.5,16.8),4.8)
slab('TerraceLanding',(20,13.5,21.3,15.0),4.8)
slab('EastConnector',(21.3,7.8,27.5,9),4.8)
slab('QuietFloor',(20,1,27.5,7),4.8)
slab('QuietNorthFloor',(21.3,7,27.5,7.8),4.8)
slab('DJFloor',(11,12.6,17,15.3),4.8,.2,'MAT_Steel')
for a,b in [((8.8,5),(8.8,11.8)),((8.8,5),(20,5)),((7,2.6),(20,2.6)),((11,12.6),(17,12.6)),((11,12.6),(11,15.3)),((17,12.6),(17,15.3)),((17,15.3),(19.5,15.3)),((8.8,15.3),(11,15.3)),((21.3,7),(21.3,13.5)),((20,13.5),(20,15.0)),((.5,4.2),(7,4.2)),((7,2.6),(7,4.2)),((.5,17.55),(8.8,17.55)),((7,11.8),(7,16.1)),((7,11.8),(8.8,11.8)),((20,7),(21.3,7)),((21.3,16.8),(27.5,16.8))]:rail('ARCH_Balustrade',a,b,4.8)
for a,b in [((8.8,5,4.55),(8.8,11.8,4.55)),((8.8,5,4.55),(20,5,4.55)),((11,12.6,4.55),(17,12.6,4.55))]:beam('LGT_EdgeCyan',a,b,.015,'MAT_Cyan')
for x in [11.12,16.88]:
 for y in [12.73,15.0]:beam('ARCH_DJSuspension',(x,y,4.6),(x,y,9.4),.035,'MAT_Steel')
group('ARCH_Stairs')
stair('EastStair',19.65,21.15,7.0,13.5,28)
stair('WestStair',7.15,8.65,11.8,16.1,25)
# Stage and AV
group('AV_Stage')
stage=cyl('AV_Stage',(14,13.2,.125),2.4,.25,'MAT_Steel',96)
stage.data.materials.append(M['MAT_Oak']);stage.data.polygons[1].material_index=1
ring('AV_StageEdge',(14,13.2,.225),2.39,.017,'MAT_Cyan',96,6)
COL.append(dict(name='COL_Stage',kind='cylinder',position=[14,13.2,.125],radius=2.4,height=.25,group=GROUP))
COL.append(dict(name='COL_StageRamp',kind='ramp',vertices=[(13.25,10.0,0),(14.75,10.0,0),(14.75,10.92,.25),(13.25,10.92,.25)],group=GROUP))
box('AV_ScreenFrame',(14,16.95,2.4),(7.4,.2,4.25),'MAT_Steel')
box('AV_MainScreen',(14,16.83,2.4),(7.1,.025,4.0),'MAT_Black')
text_obj('AV_ScreenTitle','THE  COMMONS',(14,16.80,3.53),.38,'MAT_White')
text_obj('AV_ScreenSub','TALK   /   BUILD   /   SHARE',(14,16.80,2.9),.17,'MAT_Cyan')
text_obj('AV_ScreenCaption','IDEAS TASTE BETTER TOGETHER.',(14,16.80,1.25),.16,'MAT_White')
for i in range(15):box('AV_ScreenTick',(11+i*.43,16.798,1.78),(.015,.012,.12+math.sin(i*.8)*.10),'MAT_Cyan')
for x in [12.6,14,15.4]:ring('AV_PresenterMark',(x,12.5,.255),.24,.008,'MAT_Brass',32,4)
box('AV_LecternBase',(11.4,12.4,.035),(.58,.48,.07),'MAT_Steel');box('AV_LecternStem',(11.4,12.4,.53),(.12,.10,1.0),'MAT_Steel');box('AV_LecternTop',(11.4,12.4,1.12),(.62,.48,.08),'MAT_Oak',.02)
beam('AV_Mic',(11.5,12.4,1.17),(11.5,12.55,1.46),.014,'MAT_Steel')
cyl('AV_DemoPedestal',(17.8,13.3,.5),.56,1,'MAT_Steel',32);ring('AV_DemoRim',(17.8,13.3,1.015),.55,.015,'MAT_Cyan')
for x in [9.5,18.5]:
 box('AV_Speaker',(x,16.2,2.3),(.48,.4,1.3),'MAT_Black',.02)
 for z in [2.05,2.55]:
  # simple grille silhouette
  for j in range(7):box('AV_Grille',(x-.18+j*.06,15.99,z),(.012,.01,.38),'MAT_Steel')
# Upper repeater uses same media surface, justified as screen occlusion mitigation.
box('AV_UpperRepeaterFrame',(14,17.42,7.22),(5.92,.18,3.44),'MAT_Steel')
box('AV_UpperRepeater',(14,17.315,7.22),(5.68,.022,3.2),'MAT_Black')
text_obj('AV_UpperIdentity','THE  COMMONS',(14,17.293,7.6),.36,'MAT_White')
text_obj('AV_UpperTag','SAME ROOM. DIFFERENT WORLDS.',(14,17.293,6.87),.17,'MAT_Cyan')
group('AV_Hologram')
for z,r in [(7.0,1.05),(7.8,1.05),(8.5,.75)]:ring('AV_OrbitRing',(14,13.6,z),r,.018,'MAT_Cyan',64,6)
for angle in [0,math.pi/3,2*math.pi/3]:
 o=ring('AV_HoloMeridian',(0,0,0),.7,.012,'MAT_Holo',48,5);o.rotation_euler=(math.pi/2,angle,0);o.location=(14,13.6,7.75)
group('AV_DJ')
box('AV_DJDesk',(14,13.32,5.85),(4.9,1.12,.12),'MAT_Oak',.035)
box('AV_DJFascia',(14,12.9,5.36),(4.9,.14,.85),'MAT_Steel')
text_obj('AV_DJSign','R E L A Y',(14,12.812,5.43),.28,'MAT_Cyan')
for x in [11.75,16.25]:box('AV_DJLeg',(x,13.4,5.3),(.1,.6,1),'MAT_Steel')
# Controller front faces its operator on +Y. The entire artwork uses one UV frame.
controller=box('AV_RelayController',(14,13.32,5.965),(2,1,.10),'MAT_Black',.009)
print_face(controller,1,'MAT_DJPanel',axes=(0,1),flip_u=True,flip_v=True)
def dj_pos(u,v):return (15-2*u,12.82+v)
def dj_top(o):
 # Place the corresponding artwork onto raised controls, not a second coplanar sheet.
 o.data.materials.append(M['MAT_DJPanel'])
 for p in o.data.polygons:
  if p.normal.z>.99:
   p.material_index=len(o.data.materials)-1
   for li in p.loop_indices:
    v=o.data.vertices[o.data.loops[li].vertex_index].co;o.data.uv_layers.active.data[li].uv=((15-v.x)/2,1-(v.y-12.82))
 return o
for u in [.206,.793]:
 x,y=dj_pos(u,.485)
 dj_top(cyl('AV_Jog',(x,y,6.046),.25,.054,'MAT_Steel',48))
 ring('AV_JogTrim',(x,y,6.04),.253,.007,'MAT_Brass',48,5)
for u in [.407,.454,.501,.548]:
 for v in [.158,.264,.371,.466]:
  x,y=dj_pos(u,v);dj_top(cyl('AV_MixerKnob',(x,y,6.038),.022,.042,'MAT_Black',12))
 x,y=dj_pos(u,.637);dj_top(box('AV_FaderCap',(x,y,6.032),(.055,.036,.030),'MAT_Steel'))
for u in [.358,.644]:
 for v in [.17,.278,.39,.505,.628]:
  x,y=dj_pos(u,v);dj_top(cyl('AV_DeckKnob',(x,y,6.038),.020,.042,'MAT_Black',12))
for u in [.124,.190,.256,.322,.679,.744,.811,.878]:
 x,y=dj_pos(u,.837);dj_top(box('AV_PerformancePad',(x,y,6.026),(.103,.080,.018),'MAT_Black'))
x,y=dj_pos(.5,.88);dj_top(box('AV_Crossfader',(x,y,6.034),(.052,.064,.034),'MAT_Black'))
for u in [.045,.954]:
 x,y=dj_pos(u,.267);dj_top(box('AV_PitchFader',(x,y,6.032),(.040,.050,.030),'MAT_Steel'))
for x in [11.9,16.1]:box('AV_DJMonitor',(x,13.63,6.21),(.28,.27,.50),'MAT_Black',.02)

# BAR follows the two exact CAD L-counter polygons.
group('FURN_Bar')
for name,b in [('Return',(1.3,5.6,6.6,6.5)),('Long',(1.3,6.5,2.2,13.9))]:
 x1,y1,x2,y2=b;box('FURN_Bar'+name,((x1+x2)/2,(y1+y2)/2,.5275),(x2-x1,y2-y1,1.055),'MAT_Steel')
 slab('BarTop'+name,b,1.13,.075,'MAT_Oak',False);colbox('Bar'+name,((x1+x2)/2,(y1+y2)/2,.57),(x2-x1,y2-y1,1.14))
for x in [1.42+i*.145 for i in range(35)]:box('FURN_BarFlute',(x,5.55,.62),(.057,.10,.82),'MAT_Oak')
for y in [6.58+i*.145 for i in range(50)]:box('FURN_BarFlute',(2.23,y,.62),(.10,.057,.82),'MAT_Oak')
beam('FURN_BarFootRail',(2.55,6.65,.24),(2.55,13.65,.24),.025,'MAT_Brass')
beam('FURN_BarFootRail',(1.6,5.28,.24),(6.35,5.28,.24),.025,'MAT_Brass')
for y in [7.0,8.05,9.1,10.15,11.2,12.25,13.3]:stool(2.9,y)
for x in [2.8,3.85,4.9,5.95]:stool(x,4.89)
# Backbar on west, shallow enough to leave staff access from north.
box('FURN_BackbarBacking',(.41,10.2,2.05),(.18,7.8,3.3),'MAT_Steel')
for z in [1.22,1.94,2.66,3.38]:
 box('FURN_BackbarShelf',(.76,10.2,z),(.66,7.75,.05),'MAT_Oak');box('LGT_ShelfAmber',(.96,10.2,z-.035),(.035,7.7,.02),'MAT_Amber')
for y in [6.4,8.3,10.2,12.1,14.0]:box('FURN_ShelfUpright',(.7,y,2.25),(.52,.045,2.35),'MAT_Brass')
for zi,z in enumerate([1.26,1.98,2.70]):
 for j in range(31):
  y=6.65+j*.235;h=random.uniform(.23,.37);x=.84
  cyl('FURN_Bottle',(x,y,z+h*.39),.052,h*.78,'MAT_BottleGreen' if j%3 else 'MAT_BottleAmber',10,r2=.052)
  cyl('FURN_BottleNeck',(x,y,z+h*.88),.022,h*.25,'MAT_BottleGreen',10)
  cyl('FURN_BottleCap',(x,y,z+h*1.025),.024,.035,'MAT_Brass',10)
  bottle_label(x,y,z+h*.43,(j+zi*2)%6)
text_obj('FURN_BarTitle','ANCHOR BAR',(1.02,10.2,3.74),.25,'MAT_Amber',rot=(math.pi/2,0,math.pi/2))
for y in [7.5,9.7,12.0]:pendant(3.6,y,3.8)
for x in [3.4,5.5]:pendant(x,6.1,3.75)
box('FURN_Espresso',(4.4,6.02,1.40),(.72,.43,.49),'MAT_Steel',.035)
o=box('FURN_EspressoFace',(4.4,5.79,1.4),(.60,.018,.29),'MAT_Brass')
print_face(o,2,'MAT_PropPrint',(.006,.566,.494,.994))
for x in [4.24,4.52]:
 beam('FURN_Portafilter',(x,5.77,1.35),(x,5.58,1.35),.022,'MAT_Black');cup(x,5.77,1.15)
cyl('FURN_Grinder',(5.2,6.02,1.36),.115,.44,'MAT_Steel',16);cyl('FURN_BeanHopper',(5.2,6.02,1.66),.14,.2,'MAT_BottleAmber',16,r2=.1)
for x in [3.36,3.58,3.80]:
 o=box('FURN_CoffeeBag',(x,6.03,1.28),(.17,.11,.29),'MAT_Ceramic',.008)
 print_face(o,2,'MAT_PropPrint',(.506,.009,.994,.546))
 box('FURN_BagFold',(x,6.03,1.431),(.16,.035,.012),'MAT_Brass')
for y in [7.3,9.2,11.4,13.1]:cup(1.86,y,1.133)
plant(6.4,13.9,height=1.8,r=.38)

group('FURN_Cafe')
for x,y in [(2,2.4),(5.0,2.4)]:
 table(x,y,r=.48)
 for dx,dy,a in [(-.85,0,math.pi/2),(.85,0,-math.pi/2),(0,.88,0)]:seat(x+dx,y+dy,angle=a)
plant(.85,1.0,height=1.8)
text_obj('FURN_CafeSign','COMMON TABLES',(4,.29,2.6),.22,'MAT_Amber',rot=(math.pi/2,0,math.pi))

group('MODE_Lounge')
# 4 compact, open clusters; entry axis and outer circulation remain open.
for x,y in [(10.1,5.6),(17.9,5.6),(10.1,8.7),(17.9,8.7)]:
 table(x,y,r=.43,ht=.44)
 seat(x,y-1.05,angle=math.pi,kind='sofa',width=1.5)
 seat(x-.98,y+.2,angle=math.pi/2);seat(x+.95,y+.26,angle=-math.pi/2)
for x,y in [(8.4,9.8),(19.2,4.0)]:plant(x,y,height=1.4)
group('MODE_Academic')
for row in range(4):
 for x in [10.1,11.05,12.0,16.0,16.95,17.9]:seat(x,5.75+row*1.10,angle=math.pi,width=.52)

group('FURN_UpstairsCafe')
for x,y in [(3.0,6.8),(5.8,9.3),(3.0,12.0)]:
 table(x,y,4.8,r=.58)
 for dx,dy,a in [(-.95,0,math.pi/2),(.95,0,-math.pi/2),(0,-.95,math.pi),(0,.95,0)]:seat(x+dx,y+dy,4.8,a)
for y in [7,9.2,10.8]:
 box('FURN_OverlookDesk',(8.32,y,5.56),(.63,1.4,.07),'MAT_Oak');stool(7.65,y,4.8);cup(8.3,y,5.61)
for y in [6.6,10,14]:plant(1.2,y,4.8,height=1.5,r=.32)
text_obj('FURN_OrbitSign','ORBIT CAFE',(3.8,16.68,7.8),.32,'MAT_Amber')
for x,y in [(3.2,7),(5.6,12)]:
 area('LGT_CafeUpper',(x,y,8.4),(x,y,4.8),210,(1,.64,.34),3)
 ring('LGT_CafeHalo',(x,y,8.5),.75,.028,'MAT_Amber')

group('FURN_QuietNook')
for x in [22.4,25.2]:
 table(x,3.25,r=.44,ht=.48);seat(x,2.1,angle=math.pi,kind='sofa',width=1.5,material='MAT_Cream');seat(x,4.4,kind='sofa',width=1.5,material='MAT_Cream')
for y in [1.15+i*.24 for i in range(18)]:box('ARCH_NookSlat',(21.5,y,1.45),(.09,.08,2.9),'MAT_Oak')
plant(26.7,5.7,height=1.7)
area('LGT_QuietNook',(24,3.1,3.8),(24,3.1,0),160,(1,.55,.27),3.3)
text_obj('FURN_NookSign','A QUIETER CORNER',(24,6.0,2.6),.16,'MAT_Amber')

group('FURN_QuietRoom')
slab('QuietCeiling',(20,1,27.5,7.8),8.46,.16,'MAT_Plaster',False)
for pos,size in [((20.05,2.50,6.55),(.10,2.8,3.5)),((20.05,6.2,6.55),(.10,1.6,3.5)),((23.75,1.05,6.55),(7.5,.10,3.5)),((24.4,7.75,6.55),(6.2,.10,3.5))]:
 box('ARCH_QuietWall',pos,size,'MAT_Plaster');colbox('QuietWall',pos,size)
box('ARCH_QuietDoorHeader',(20.05,4.65,8.05),(.14,1.6,.5),'MAT_Oak')
text_obj('FURN_ArchiveSign','ARCHIVE',(19.94,4.65,7.81),.24,'MAT_Amber',rot=(math.pi/2,0,-math.pi/2))
for x in [22.4,25.1]:
 table(x,4.2,4.8,r=.47,ht=.49)
 seat(x,3.0,4.8,math.pi,'sofa',1.65,'MAT_Cream');seat(x,5.4,4.8,0,'sofa',1.65,'MAT_Fabric')
for z in [5.7,6.5,7.3]:
 box('FURN_ArchiveShelf',(24,1.4,z),(4.5,.48,.06),'MAT_Oak')
 for j in range(24):
  h=random.uniform(.20,.36);o=box('FURN_Book',(21.9+j*.175,1.4,z+h/2+.03),(.06+random.random()*.05,.25,h),['MAT_Oak','MAT_Fabric','MAT_Ceramic','MAT_Black'][j%4])
  c=j%6;print_face(o,4,'MAT_PropPrint',((c+.05)/12,.012,(c+.95)/12,.543),flip_u=True)
plant(26.8,6.8,4.8,height=1.5)
area('LGT_Archive',(23.8,4.0,8.1),(23.8,4,4.8),220,(1,.61,.36),3.8)

group('FURN_Terrace')
for y in [10.9,14.5]:
 table(25.0,y,4.8,r=.56,ht=.53)
 for dx,dy,a in [(-1.03,0,math.pi/2),(1.02,0,-math.pi/2),(0,-1.03,math.pi),(0,1.03,0)]:seat(25+dx,y+dy,4.8,a)
for y in [9.5,12.6,16.1]:plant(27.0,y,4.8,height=1.35,r=.26)
text_obj('FURN_HorizonSign','HORIZON',(24.9,16.66,7.8),.32,'MAT_Amber')
for y in [11,14.5]:area('LGT_Terrace',(25,y,8.3),(25,y,4.8),200,(1,.62,.32),2.4)

group('AV_Gallery')
# Five CAD bays plus sixth on the south return, each independently replaceable.
for i,y in enumerate([8.45,9.95,11.45,12.95,14.45]):
 box('AV_PosterFrame_%02d'%i,(27.18,y,2.06),(.12,1.2,1.84),'MAT_Brass')
 box('AV_PosterFace_%02d'%i,(27.107,y,2.06),(.025,1.06,1.70),'MAT_Black')
 text_obj('AV_PosterHeading',str(i+1).zfill(2)+' / OPEN LAB',(27.086,y,2.71),.105,'MAT_White',rot=(math.pi/2,0,-math.pi/2))
 for j in range(5):beam('AV_PosterDiagram',(27.08,y-.33,1.55+j*.14),(27.08,y+.33,1.72+j*.08),.007,'MAT_Cyan')
 text_obj('AV_PosterFooter','TALK  /  BUILD  /  SHARE',(27.083,y,1.45),.07,'MAT_White',rot=(math.pi/2,0,-math.pi/2))
box('AV_PosterFrame_05',(24.5,7.3,2.06),(1.2,.12,1.84),'MAT_Brass')
box('AV_PosterFace_05',(24.5,7.371,2.06),(1.06,.025,1.70),'MAT_Black')
text_obj('AV_SixthPoster','06 / OPEN LAB',(24.5,7.387,2.4),.12,'MAT_Cyan',rot=(math.pi/2,0,math.pi))
for y in [8.5,10.5,12.5,14.5]:
 cyl('AV_DemoPlinth',(23.7,y,.48),.30,.96,'MAT_Steel',24);ring('AV_PlatformLED',(23.7,y,.965),.29,.012,'MAT_Cyan',24,5)
 # Geometric demonstration artifacts, modeled rather than placeholder cubes.
 for a in [0,1,2]:
  o=ring('AV_DemoOrbit',(0,0,0),.23,.012,'MAT_Brass',28,5);o.rotation_euler=(a*.7,1.0,a);o.location=(23.7,y,1.3)
text_obj('AV_OpenLabSign','OPEN LAB',(26.9,11.4,3.65),.25,'MAT_Amber',rot=(math.pi/2,0,-math.pi/2))
for y in [9.5,13.5]:area('LGT_Gallery',(25.5,y,4),(27.1,y,2),150,(.48,.72,1),2)

group('AV_BackOfHouse')
box('ARCH_AVPartition',(23.2,15.65,1.9),(7.7,.14,3.8),'MAT_Plaster');colbox('AVWall',(23.2,15.65,1.9),(7.7,.14,3.8))
for x in [21,22.2,23.4]:
 box('AV_Rack',(x,17.1,1.05),(.72,.65,2.1),'MAT_Black')
 for j in range(9):
  o=box('AV_RackUnit',(x,16.765,.2+j*.205),(.66,.028,.165),'MAT_Steel')
  print_face(o,2,'MAT_PropPrint',(.506,.565,.994,.994))
  for k in range(4):box('AV_StatusLED',(x-.22+k*.04,16.744,.2+j*.205),(.014,.008,.014),'MAT_Cyan')
text_obj('AV_BackOfHouseLabel','AV / HOST',(20.0,16.6,2.7),.17,'MAT_Amber')

group('LGT_Main')
area('LGT_AtriumSoft',(14,8.7,8.8),(14,9,0),1300,(.55,.71,1),6.5)
area('LGT_StageNeutral',(14,12.3,4.45),(14,13.2,.25),420,(.85,.86,1),3)
area('LGT_BarFill',(5,10.4,4.35),(1,10,1),330,(1,.60,.33),4)
area('LGT_EntryFill',(14,1.6,3.4),(14,2.7,0),270,(1,.79,.58),3.5)
area('LGT_LoungeFill',(14,6.2,4.4),(14,6.2,0),380,(.85,.91,1),4.5)
area('LGT_UpperWalkFill',(14,3.8,8.9),(14,3.8,4.8),400,(1,.82,.62),4.5)
for z in [4.43,9.31]:
 box('LGT_EastCove',(27.64,9,z),(.04,17,.045),'MAT_Amber')
 box('LGT_NorthCove',(14,17.67,z),(27,.04,.045),'MAT_Cyan')
for y in [6.4,11.3]:
 ring('LGT_Halo',(14,y,8.65),1.7,.045,'MAT_Brass',80,6);ring('LGT_HaloLight',(14,y,8.60),1.68,.022,'MAT_Amber',80,5)
for x,y in [(8.6,5),(19.85,5),(8.65,15.65),(19.85,15.65)]:
 for z in [2.1,7]:box('LGT_ColumnSconce',(x,y-.18,z),(.13,.08,.54),'MAT_Amber')
# Draped geometric foliage along cafe fascia; opaque leaves, no alpha overdraw.
group('FURN_HangingGarden')
for y in [5.8,8.5,10.8]:
 for j in range(3):plant(8.25,y+j*.4,4.8,height=.70,r=.14)
for x in [10,18.6]:plant(x,3.5,4.8,height=.9,r=.25)

# Deterministic architectural skyline, separately batched from indoor geometry.
CITY=runpy.run_path(str(ROOT/'Blender/build_city.py'),init_globals=globals())['CITY']

# Transparent marker collections not exported as render geometry.
group('INT_Markers')
for name,p in [('SPAWN_Entry',(14,1.2,.10)),('TP_Lower',(18.0,1.5,.1)),('TP_Upper',(18.0,3.65,4.9)),('TP_WestLower',(6.5,11.1,.1)),('TP_WestUpper',(6.4,15.4,4.9))]:
 o=link(bpy.data.objects.new(name,None));o.location=p;o.empty_display_type='ARROWS';o.empty_display_size=.5

FPV=runpy.run_path(str(ROOT/'Blender/build_fpv_field.py'),init_globals=globals())['FPV']
KART=runpy.run_path(str(ROOT/'Blender/build_kart_circuit.py'),init_globals=globals())['KART']

# Match Blender and the Unity light manifest. Raise usable illumination rather
# than only raising preview exposure. No additional realtime Unity point lights.
def light_gain(name):return 1.35 if name.startswith(('FPV_','LGT_FPV','KART_')) else 1.65
for o in bpy.data.objects:
 if o.type=='LIGHT':o.data.energy*=light_gain(o.name)
for r in LIGHTS:r['power']*=light_gain(r['name'])

world=bpy.data.worlds.new('The Commons blue hour');S.world=world;world.use_nodes=True
world.node_tree.nodes.get('Background').inputs[0].default_value=(.12,.17,.26,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.48
group('OPT_Cameras')
def camera(name,pos,target,lens):
 data=bpy.data.cameras.new(name);data.lens=lens;data.clip_end=180;data.clip_start=.06
 o=link(bpy.data.objects.new(name,data));o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();CAMS[name]=o
camera('01_Entrance_160cm',(14,1.25,1.6),(14,11.5,3.55),19)
camera('02_AnchorBar_160cm',(6.75,4.1,1.6),(1.6,10.0,1.85),22)
camera('03_Stage_160cm',(14,9.65,1.6),(14,16.8,2.5),22)
camera('04_Mezzanine_160cm',(17.95,4.05,6.4),(12.6,11.8,3.05),20)
camera('05_Archive_160cm',(20.65,6.65,6.4),(24,3.2,6.1),21)
camera('06_Overview',(36,-27,28),(14,9,3.8),49)
camera('07_Relay_Detail',(14,14.8,7.4),(14,13.3,6.0),32)
camera('08_BarLabels_Detail',(2.40,7.35,2.90),(.84,7.35,2.85),54)
camera('09_Coffee_Detail',(4.5,4.75,1.98),(4.35,6.00,1.41),48)
camera('10_FPV_Field',(-42.5,3,1.6),(-46,16,2.7),19)
camera('11_FPV_Course',(-33,23,6.7),(-49,14,1.7),22)
camera('21_Spawn_Glass',(15.4,4.7,1.6),(13.8,.125,1.8),20)
camera('22_Horizon_Skyline',(21.7,9.1,6.4),(45,23,10),22)
camera('23_City_Architecture',(-14,-70,50),(32,10,12),32)
for n,c in KART['cameras'].items():
 camera(n,c['position'],c['target'],c['lens']);CAMS[n].data.clip_end=1000
S.camera=CAMS['01_Entrance_160cm']
S.render.engine='CYCLES';S.cycles.samples=32;S.cycles.use_denoising=True;S.cycles.max_bounces=5
S.render.resolution_x=1600;S.render.resolution_y=1000;S.render.resolution_percentage=100
S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast';S.view_settings.exposure=1.05
S.render.image_settings.file_format='PNG';S.render.film_transparent=False
S['project']='THE COMMONS - Compact Edition';S['revision']='0.9.0';S['source']='SourceDesign/world_spec.json';S['world_test_status']='Unity and VRChat runtime tests pending'
# Hide only inactive mode, preserving authoring editability.
for o in GROUPS['MODE_Academic'].objects:o.hide_render=True;o.hide_set(True)
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
for o in bpy.data.objects:
 if o.type=='MESH':o['commons_group']=o.users_collection[0].name
report={'version':'0.8.0','city':CITY,'fpv':FPV,'kart':KART,'footprint':[28,18],'level_tops':[0,4.8,9.6],'stage':{'center':[14,13.2],'diameter':4.8,'height':.25},'screen':[7.1,4.0],'stair_design':COUNTS,'colliders':COL,'lights':LIGHTS,'seat_anchors':SEATS,'cameras':{n:{'position':list(o.location),'eye_height':1.6 if '160cm' in n else None} for n,o in CAMS.items()},'materials':{n:{'color':list(m.diffuse_color),'texture':m.get('texture_key',''),'emission':m.get('emission',0),'wrap':m.get('wrap','mirror'),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'metallic':m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value} for n,m in M.items()}}
(ASSET/'Data/world_manifest.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item() if hasattr(x,'item') else list(x)))
(ROOT/'Documentation/model_manifest.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item() if hasattr(x,'item') else list(x)))
runpy.run_path(str(ROOT/'Blender/apply_cafe_experience.py'),run_name='commons_build')['apply']()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
print('AUTHORING SAVED:',len(bpy.data.objects),'objects',flush=True)
if '--render' in sys.argv:
 for n,o in CAMS.items():
  if n=='06_Overview':continue
  S.camera=o;S.render.filepath=str(ROOT/'Preview'/f'{n}.png');bpy.ops.render.render(write_still=True)
print('DONE',flush=True)
