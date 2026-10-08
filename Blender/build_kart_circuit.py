"""APEX Neon Switchyard: original indoor technical route, static architecture only.
Corner characters are adapted from real circuits; see SourceDesign/kart_circuit.json.
Run from build_world.py with its material, mesh, light and collider helpers.
"""
import importlib.util
import numpy as np
from shapely.geometry import Polygon, Point
spec=json.loads((ROOT/'SourceDesign/kart_circuit.json').read_text())
# runpy copies immutable globals; mirror the host helper's active group locally.
host_group=group
def group(name):
    global GROUP
    GROUP=name;host_group(name)
loader=importlib.util.spec_from_file_location('kart_layout',ROOT/'Blender/kart_layout.py')
layout_module=importlib.util.module_from_spec(loader);loader.loader.exec_module(layout_module)
P,T,N,D,PHASE,BANK,MARKS=layout_module.layout(spec);count=len(P);origin=np.array(spec['origin']);center=np.array(spec['center_local'])+origin[:2]
shift=origin[:2]+np.array(spec['layout']['offset']);half=spec['deck_half_width'];rw=spec['road_width']/2;bh=spec['barrier_height']
pit=spec['pit'];pit_indices=[i for i in range(count) if abs(P[i,1]-shift[1]-pit['straight_y'])<1e-5 and pit['straight_x'][0]<=P[i,0]-shift[0]<=pit['straight_x'][1] and abs(P[i,2]-spec['levels'][0])<1e-5 and T[i,0]>.99]
pit_i=pit_indices[len(pit_indices)//2];pit_set=set(pit_indices)
# Cross-slope from banking and centreline grade keep deck details on the actual surface.
TB=np.tan(BANK);G=(np.roll(P[:,2],-1)-np.roll(P[:,2],1))/np.linalg.norm((np.roll(P,-1,axis=0)-np.roll(P,1,axis=0))[:,:2],axis=1)
mat('MAT_KartAsphalt',(.13,.15,.21),'basalt_terrazzo',.26,.2)
mat('MAT_KartConcrete',(.25,.28,.36),'mineral_plaster',.72)
mat('MAT_KartRubber',(.019,.025,.043),rough=.52)
mat('MAT_KartSteel',(.22,.25,.34),'blackened_steel',.34,.72)
mat('MAT_KartFloor',(.075,.085,.12),'basalt_terrazzo',.43,.14)
mat('MAT_KartWhite',(.65,.73,.86),rough=.5)
mat('MAT_KartPink',(.6,.025,.18),rough=.45,emit=.22)
mat('MAT_KartBlue',(.008,.09,1),rough=.25,emit=5)
mat('MAT_KartViolet',(.47,.009,1),rough=.25,emit=4)
mat('MAT_KartCyan',(.008,.68,1),rough=.25,emit=4)
mat('MAT_KartGold',(.95,.32,.012),rough=.35,emit=2)
mat('MAT_KartLEDWhite',(.65,.8,1),rough=.3,emit=3)
COLORS=['MAT_KartBlue','MAT_KartViolet','MAT_KartCyan']
LIGHT_COLORS=[(.045,.18,1),(.42,.04,1),(.025,.75,1)]
def level(i):return min(range(3),key=lambda j:abs(P[i,2]-spec['levels'][j]))
def point(i,offset,zoff=0):return (float(P[i,0]+N[i,0]*offset),float(P[i,1]+N[i,1]*offset),float(P[i,2]-offset*TB[i]+zoff))
DECOR={}
def strip(name,indices,a,b,material,top=0,bottom=None,collision=False,batch=False):
    indices=list(indices);closed=len(indices)==count;vs=[];fs=[]
    for i in indices:
        vs.extend([point(i,a,top),point(i,b,top)])
        if bottom is not None:vs.extend([point(i,a,bottom),point(i,b,bottom)])
    stride=4 if bottom is not None else 2;segments=len(indices) if closed else len(indices)-1
    for j in range(segments):
        k=(j+1)%len(indices);u=j*stride;v=k*stride
        fs.append((u,v,v+1,u+1))
        if bottom is not None:fs.extend([(u+2,u+3,v+3,v+2),(u,u+2,v+2,v),(u+1,v+1,v+3,u+3)])
    if bottom is not None and not closed:
        e=(len(indices)-1)*stride;fs.extend([(0,1,3,2),(e,e+2,e+3,e+1)])
    if batch:
        saved=DECOR.setdefault((GROUP,name,material),[[],[]]);offset=len(saved[0]);saved[0].extend(vs);saved[1].extend([tuple(v+offset for v in face) for face in fs]);return None
    ob=mesh(name,vs,fs,material,.4)
    if collision:
        ob.data.calc_loop_triangles();triangles=[v for tri in ob.data.loop_triangles for v in tri.vertices]
        COL.append({'name':'COL_'+name,'kind':'mesh','group':ob.users_collection[0].name,'vertices':vs,'triangles':triangles})
    return ob
def wall_band(name,indices,offset,low,high,material):
    # Only the visible inner face: no hidden backs or duplicate end caps per sample.
    vs=[];fs=[]
    for i in indices:vs.extend([point(i,offset,low),point(i,offset,high)])
    for j in range(len(indices)-1):
        u=j*2;v=u+2;face=(u,v,v+1,u+1)
        fs.append(face if offset>0 else tuple(reversed(face)))
    saved=DECOR.setdefault((GROUP,name,material),[[],[]]);base=len(saved[0]);saved[0].extend(vs)
    saved[1].extend([tuple(v+base for v in face) for face in fs])
# Entirely enclosed industrial hall; roof and two walls are removable only in the cutaway camera.
group('KART_Hall')
slab('KART_Foundation',(origin[0],origin[1],origin[0]+spec['size'][0],origin[1]+spec['size'][1]),0,.45,'MAT_KartFloor')
for side,x in [('West',origin[0]),('East',origin[0]+spec['size'][0])]:
    group('KART_Shell'+side);box('KART_Wall'+side,(x,80,7.75),(.55,160,15.5),'MAT_KartConcrete');colbox('KART_Wall'+side,(x,80,7.75),(.55,160,15.5))
for side,y in [('South',0),('North',160)]:
    group('KART_Shell'+side);box('KART_Wall'+side,(center[0],y,7.75),(148,.55,15.5),'MAT_KartConcrete');colbox('KART_Wall'+side,(center[0],y,7.75),(148,.55,15.5))
group('KART_Roof');box('KART_RoofSkin',(center[0],80,15.65),(149,161,.3),'MAT_KartSteel');colbox('KART_RoofSkin',(center[0],80,15.65),(149,161,.3))
group('KART_Trusses')
for y in range(8,160,16):
    for z in [14.25,15.25]:box('KART_TrussChord',(center[0],y,z),(148,.18,.18),'MAT_KartSteel')
    for x in range(0,144,8):beam('KART_TrussWeb',(origin[0]+x,y,14.25 if (x//8)%2==0 else 15.25),(origin[0]+x+8,y,15.25 if (x//8)%2==0 else 14.25),.06,'MAT_KartSteel',6)
for x in range(8,148,16):box('KART_RoofPurlin',(origin[0]+x,80,15.12),(.12,160,.16),'MAT_KartSteel')
# Wall ribs and continuous light bars make the venue read as an enclosed machine hall.
group('KART_HallDetails')
for y in range(8,160,12):
    for x in [origin[0]+.5,origin[0]+147.5]:
        box('KART_WallRib',(x,y,7.1),(.45,.45,14.2),'MAT_KartSteel')
        box('KART_WallLight',(x+(1 if x<center[0] else -1)*.25,y,9),(.055,.17,7),'MAT_KartViolet')
for y in [.34,159.66]:
    for z in [2.4,11.8]:box('KART_WallNeon',(center[0],y,z),(147,.05,.08),'MAT_KartBlue')
group('KART_Road')
road=strip('KART_ContinuousRoad',range(count),-half,half,'MAT_KartConcrete',bottom=-spec['deck_thickness'],collision=True)
road.data.materials.append(M['MAT_KartAsphalt'])
for face in road.data.polygons:
    if face.index%4==0:face.material_index=1
# Continuous low barriers keep the close kart viewpoint without hiding upcoming turns.
group('KART_Barriers')
strip('KART_LeftBarrier',range(count),3.0,half,'MAT_KartRubber',top=bh,bottom=0,collision=True)
segments=list(range(max(pit_indices),count))+list(range(0,min(pit_indices)+1))
strip('KART_RightBarrier',segments,-half,-3.0,'MAT_KartRubber',top=bh,bottom=0,collision=True)
group('KART_Markings')
for side in [-1,1]:
    for i in range(count):
        j=(i+1)%count
        if side==-1 and i in pit_set:continue
        a,b=sorted([side*rw,side*2.98]);c='MAT_KartWhite' if int(D[i]/2.4)%2 else 'MAT_KartPink'
        strip('KART_Kerb',[i,j],a,b,c,top=.014,batch=True)
        a,b=sorted([side*3.01,side*3.18]);strip('KART_LED_Rail',[i,j],a,b,COLORS[level(i)],top=bh+.009,batch=True)
        wall_band('KART_BarrierPanel',[i,j],side*2.985,.25,.52,'MAT_KartWhite' if int(D[i]/3)%2 else 'MAT_KartPink')
        wall_band('KART_LED_InnerFace',[i,j],side*2.98,bh-.12,bh-.035,COLORS[level(i)])
        a,b=sorted([side*(rw-.06),side*(rw-.01)]);strip('KART_LED_RoadGuide',[i,j],a,b,COLORS[level(i)],top=.028,batch=True)
    strip('KART_EdgeLine',range(count),side*(rw-.17)-.045,side*(rw-.17)+.045,'MAT_KartWhite',top=.02)
def arrow(i,off=0,material='MAT_KartGold'):
    c=np.array(point(i,off,.027));f=np.r_[T[i],G[i]];left=np.r_[N[i],-TB[i]]
    xy=[(-.17,-.65),(.17,-.65),(.17,.2),(.47,.2),(0,.9),(-.47,.2),(-.17,.2)]
    mesh('KART_Direction',[list(c+left*x+f*y) for x,y in xy],[tuple(reversed(range(7)))],material)
last=-99
for i in range(count):
    if D[i]-last>=11:arrow(i);last=D[i]
start_i=pit_indices[-1]
for row in range(2):
    for lane in range(12):
        off=-rw+lane*spec['road_width']/12
        strip('KART_StartFinish',range(start_i+row*2,start_i+row*2+3),off,off+spec['road_width']/12,'MAT_KartWhite' if (lane+row)%2 else 'MAT_KartRubber',top=.028)
# Structural supports are screened against all lower driving surfaces and the pit apron.
pit_footprint=Polygon([point(i,-pit['outside_offset'])[:2] for i in pit_indices]+[point(i,-half)[:2] for i in reversed(pit_indices)]).buffer(.9)
group('KART_Structure');support_count=0;last_s=-100
for i in range(count):
    if D[i]-last_s<11 or P[i,2]<1.5:continue
    last_s=D[i]
    for side in [-1,1]:
        q=np.array(point(i,side*3.12));dist=np.linalg.norm(P[:,:2]-q[:2],axis=1)
        if pit_footprint.covers(Point(q[:2])):continue
        far=np.minimum((np.arange(count)-i)%count,(i-np.arange(count))%count)>24
        if np.any((dist<4.3)&far&(P[:,2]<q[2]-.15)):continue
        height=q[2]-spec['deck_thickness']
        box('KART_BridgeColumn',(q[0],q[1],height/2),(.42,.42,height),'MAT_KartSteel')
        colbox('KART_BridgeColumn',(q[0],q[1],height/2),(.42,.42,height));support_count+=1
# Tyre bundles stand on the hall floor inside ground-level corners, outside the deck.
group('KART_TyreBundles');tyre_count=0
for mark in MARKS:
    near=mark['apex'];side=1 if mark['sweep_deg']>0 else -1
    if abs(mark['sweep_deg'])<40 or abs(P[near,2]-spec['levels'][0])>1e-6:continue
    for offset in [-.85,0,.85]:
        q=np.array(point(near,side*4.0));q[:2]+=T[near]*offset;q[2]=0
        far=np.minimum((np.arange(count)-near)%count,(near-np.arange(count))%count)>20
        if np.any((np.linalg.norm(P[:,:2]-q[:2],axis=1)<3.8)&far&(P[:,2]<6)):continue
        for h in [.135,.405]:ring('KART_Tyre',q+np.array([0,0,h]),.29,.135,'MAT_KartRubber',12,5);tyre_count+=1
# Pit lane and protected pedestrian stand; only empty CVS2 placement guides are authored.
group('KART_Pits')
strip('KART_PitApron',pit_indices,-pit['outside_offset'],-half,'MAT_KartConcrete',bottom=-.35,collision=True)
strip('KART_PitOutsideGuard',pit_indices[7:-7],-13.65,-13.4,'MAT_KartRubber',top=bh,bottom=0,collision=True)
for indices in [pit_indices[:8],pit_indices[-8:]]:strip('KART_PitWalkway',indices,-28,-13.4,'MAT_KartConcrete',bottom=-.35,collision=True)
anchors=[]
for k,i in enumerate(np.linspace(pit_indices[4],pit_indices[-5],6).astype(int)):
    i=int(i);p=point(i,-8.4,.12);yaw=math.degrees(math.atan2(T[i,0],T[i,1]));anchors.append({'name':'CVS2_Bay_%02d'%(k+1),'position':list(p),'yaw':yaw})
    empty=link(bpy.data.objects.new(anchors[-1]['name'],None));empty.location=p;empty.empty_display_type='ARROWS'
    for off in [-11.4,-5.4]:strip('KART_PitBayLine',range(i-3,i+4),off-.06,off+.06,'MAT_KartGold',top=.025)
    text_obj('KART_PitNumber','%02d'%(k+1),point(i,-12,.028),.7,'MAT_KartWhite',rot=(0,0,0))
mid=P[pit_i];axis=np.r_[T[pit_i],0];normal=np.r_[N[pit_i],0];yaw=math.atan2(axis[1],axis[0])
def local_box(name,u,v,z,size,material,collision=True):
    pos=mid+axis*u+normal*v;pos[2]=z;ob=box(name,(0,0,0),size,material);ob.location=pos;ob.rotation_euler.z=yaw
    if collision:colbox(name,pos,size,rot=(0,0,yaw))
    return ob
local_box('KART_VisitorDeck',0,-22,.15,(48,15,.3),'MAT_KartConcrete')
for k in range(3):local_box('KART_GrandstandTier',0,-23-k*1.5,.35+k*.25,(34,1.5,.7+k*.5),'MAT_KartRubber')
local_box('KART_PitCanopy',0,-22,4.4,(49,15,.25),'MAT_KartSteel')
for u in [-22,22]:
    for v in [-15.5,-28.5]:local_box('KART_CanopyColumn',u,v,2.15,(.22,.22,4.3),'MAT_KartSteel')
local_box('KART_PitCanopyNeon',0,-14.5,4.27,(48,.09,.075),'MAT_KartViolet',False)
label_pos=mid+normal*-15;label_pos[2]=3.3
text_obj('KART_Title','APEX / NEON SWITCHYARD',label_pos,1.05,'MAT_KartLEDWhite',rot=(math.pi/2,0,yaw+math.pi))
visitor=mid+axis*-20+normal*-19;visitor[2]=.42
portal_position=mid+axis*-20+normal*-17;portal_position[2]=1.2
portals=[{'name':'APEX / KART','position':[23.8,2.8,1.15],'destination':visitor.tolist(),'yaw':math.degrees(math.atan2(normal[0],normal[1]))}, {'name':'RETURN / CAFE','position':portal_position.tolist(),'destination':[23.8,4.1,.12],'yaw':0,'facing_yaw':-math.degrees(yaw)}]
panel=mid+axis*19+normal*-17;panel[2]=1.55
# Authored colour pools are baked in Unity; emissive guide rails also work without bloom.
group('KART_Lighting');last=-100;lamp_count=0
for i in range(count):
    if D[i]-last<12:continue
    last=D[i];side=-1 if lamp_count%2 else 1;p=np.array(point(i,side*3.38,1.1));target=P[i]+np.array([0,0,.02])
    area('LGT_KartRailWash',p.tolist(),target.tolist(),430,LIGHT_COLORS[level(i)],3.5);lamp_count+=1
for x in range(20,148,28):
    for y in range(20,160,28):
        p=[origin[0]+x,y,13.6];area('LGT_KartCeiling',p,[p[0],p[1],0],3000,(.25,.30,.50),7)
        box('KART_CeilingFixture',(p[0],p[1],13.65),(3,.14,.1),'MAT_KartLEDWhite')
for u in [-17,0,17]:
    p=mid+axis*u+normal*-21;p[2]=4.05;area('LGT_KartPits',list(p),[p[0],p[1],0],900,(.36,.27,1),6)
# Original signage: sector titles and painted turn numbers only; no circuit names or logos.
group('KART_Signage')
for label,xy,z,color in [('01 / REACTOR',[62,41.5],2.4,'MAT_KartBlue'),('02 / CROSSFIRE',[40,140.5],7.0,'MAT_KartViolet'),('03 / SKYLINE',[100,118],11.5,'MAT_KartCyan')]:
    p=np.array(xy)+shift;text_obj('KART_Sector',label,[p[0],p[1],z],1.0,color)
text_obj('KART_BackWallTitle','NEON SWITCHYARD',[center[0],159.65,10.2],3.3,'MAT_KartCyan')
text_obj('KART_BackWallSub','%d TURNS  /  3 LEVELS  /  FIND YOUR LINE'%len(spec['corners']),[center[0],159.63,6.9],1.15,'MAT_KartWhite')
# Turn numbers painted 5 m before each corner, tilted to the local grade and bank.
first={};turn_markers=[];loop=float(D[-1]+np.linalg.norm(P[0]-P[-1]))
for vertex,mark in zip(spec['layout']['control_vertices'],MARKS):first.setdefault(vertex['turn'],mark)
for corner in spec['corners']:
    mark=first[corner['id']];i=int(np.argmin((D-D[mark['entry']]+5)%loop));c=point(i,1.35,.03)
    text_obj('KART_TurnNumber',corner['id'],c,.8,'MAT_KartGold',rot=(math.atan(G[i]),-BANK[i],math.atan2(-T[i,0],T[i,1])))
    turn_markers.append({'id':corner['id'],'name':corner['name'],'position':list(c),'apex':P[mark['apex']].tolist(),'radius_m':mark['radius'],'station_m':float(D[mark['apex']])})
# Jump crests: painted JUMP 10 m before and a white take-off line across the crest.
jump_markers=[]
for vertex,mark in zip(spec['layout']['control_vertices'],MARKS):
    bump=vertex.get('bump')
    if not bump or bump.get('shape','crest')!='crest' or bump['height']<.5:continue
    k=mark['bump'];i=int(np.argmin((D-D[k]+10)%loop));c=point(i,-1.35,.03)
    text_obj('KART_JumpMark','JUMP',c,.75,'MAT_KartGold',rot=(math.atan(G[i]),-BANK[i],math.atan2(-T[i,0],T[i,1])))
    strip('KART_JumpLine',[(k-1)%count,k,(k+1)%count],-rw+.1,rw-.1,'MAT_KartWhite',top=.03)
    jump_markers.append({'crest':P[k].tolist(),'height_m':bump['height'],'length_m':bump['length'],'station_m':float(D[k])})
# A start gantry above the full 3.5 m vehicle envelope.
i=start_i;p=P[i];angle=math.atan2(T[i,1],T[i,0])
for side in [-1,1]:
    q=point(i,side*3.65,2);box('KART_StartPost',q,(.16,.16,4),'MAT_KartSteel')
beam('KART_StartBeam',point(i,-3.65,4),point(i,3.65,4),.14,'MAT_KartSteel',6)
for offset in [-.6,-.3,0,.3,.6]:cyl('KART_ReadyLamp',point(i,offset,3.95),.09,.12,'MAT_KartCyan',10)
# Flush the batched kerbs/rails after all group-specific geometry has been authored.
for (g,name,material),(vs,fs) in DECOR.items():group(g);mesh(name,vs,fs,material,.4)
probes=[list(P[i]+np.array([0,0,1.0])) for i in range(0,count,20)]
def world(local):return [local[0]+shift[0],local[1]+shift[1],local[2]]
cameras={
 '16_Kart_Overview':{'position':world([213,-109,178]),'target':world([74,84,3.4]),'lens':43,'cutaway':True},
 '17_Kart_Overpass':{'position':world([101,78,5.7]),'target':world([95,108,8.6]),'lens':20},
 '18_Kart_Driver':{'position':world([84,34,1.25]),'target':world([114,30,1.5]),'lens':22},
 '19_Kart_Pits':{'position':world([98,42,3.2]),'target':world([66,22,1.4]),'lens':24},
 '20_Kart_Castle':{'position':world([132,86,13.2]),'target':world([92,112,7.4]),'lens':24},
 '24_Kart_Carousel':{'position':world([104,146,12.4]),'target':world([134,113,2.6]),'lens':24},
 '25_Kart_Hairpins':{'position':world([92,40,13.0]),'target':world([40,94,1.5]),'lens':24},
 '26_Kart_SpaHairpin':{'position':world([44,157,12.0]),'target':world([12,140,4.6]),'lens':22},
 '27_Kart_Corkscrew':{'position':world([137,95,11.8]),'target':world([116,83,5.6]),'lens':22},
 '28_Kart_Nordschleife':{'position':world([128,150,5.8]),'target':world([92,144,5.0]),'lens':22},
 '29_Kart_Jump':{'position':world([139,46.5,2.3]),'target':world([140.4,72,1.0]),'lens':24}
}
KART={**spec,'centerline':P.tolist(),'tangents':T.tolist(),'stations':D.tolist(),'length_m':float(np.linalg.norm(np.roll(P,-1,axis=0)-P,axis=1).sum()),'pit_indices':pit_indices,'vehicle_anchors':anchors,'portals':portals,'light_probes':probes,'support_columns':support_count,'tyres':tyre_count,'rail_wash_lights':lamp_count,'turns':len(spec['corners']),'turn_markers':turn_markers,'jump_markers':jump_markers,'maximum_bank_deg':float(np.degrees(np.abs(BANK).max())),'cameras':cameras,'time_panel':{'position':panel.tolist(),'yaw':-math.degrees(yaw)}}
print('KART: %.1fm, %d turns, %d apexes, %d supports, %d samples'%(KART['length_m'],KART['turns'],len(MARKS),support_count,count),flush=True)
