"""Editable three-level circuit; no vehicle or racing-system dependency.
Run from build_world.py with its authoring helpers.
"""
import importlib.util
import numpy as np
from shapely.geometry import Polygon,Point
spec=json.loads((ROOT/'SourceDesign/kart_circuit.json').read_text())
loader=importlib.util.spec_from_file_location('kart_layout',ROOT/'Blender/kart_layout.py')
layout_module=importlib.util.module_from_spec(loader);loader.loader.exec_module(layout_module)
P,T,N,D,PHASE=layout_module.layout(spec);count=len(P);origin=np.array(spec['origin']);center=np.array(spec['center_local'])+origin[:2]
pit=spec['pit'];pit_i=int(round(pit['phase']*count/(2*math.pi)))%count
pit_indices=[i for i in range(count) if abs(PHASE[i]-pit['phase'])<=pit['half_phase']]
pit_set=set(pit_indices)
mat('MAT_KartAsphalt',(.19,.22,.25),'basalt_terrazzo',.88)
mat('MAT_KartConcrete',(.48,.52,.54),'mineral_plaster',.86)
mat('MAT_KartGrass',(.085,.13,.115),rough=.98)
mat('MAT_KartWhite',(.83,.87,.86),rough=.74)
mat('MAT_KartCyan',(.035,.51,.62),rough=.58,emit=.12)
mat('MAT_KartAmber',(.96,.49,.09),rough=.58,emit=.10)
mat('MAT_KartLime',(.56,.76,.16),rough=.58,emit=.10)
COLORS=['MAT_KartCyan','MAT_KartAmber','MAT_KartLime']
def level(i):return min(range(3),key=lambda j:abs(P[i,2]-spec['levels'][j]))
def point(i,offset,zoff=0):return (float(P[i,0]+N[i,0]*offset),float(P[i,1]+N[i,1]*offset),float(P[i,2]+zoff))
DECOR={}
def strip(name,indices,a,b,material,top=0,bottom=None,collision=False):
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
    if name in {'KART_Kerb','KART_BarrierCap'}:
        saved=DECOR.setdefault((name,material),[[],[]]);offset=len(saved[0]);saved[0].extend(vs);saved[1].extend([tuple(v+offset for v in face) for face in fs]);return None
    ob=mesh(name,vs,fs,material,.3)
    if collision:
        triangles=[];ob.data.calc_loop_triangles()
        for tri in ob.data.loop_triangles:triangles.extend(list(tri.vertices))
        COL.append({'name':'COL_'+name,'kind':'mesh','group':ob.users_collection[0].name,'vertices':vs,'triangles':triangles})
    return ob
# Separate open-air venue, with a roof only over the stand.
group('KART_Plaza')
slab('KART_Foundation',(origin[0],origin[1],origin[0]+spec['size'][0],origin[1]+spec['size'][1]),0,.5,'MAT_KartGrass')
for x in [origin[0]+.35,origin[0]+spec['size'][0]-.35]:
    box('KART_Perimeter',(x,150,.8),(.7,300,1.6),'MAT_KartConcrete');colbox('KART_Perimeter',(x,150,.8),(.7,300,1.6))
for y in [.35,299.65]:
    box('KART_Perimeter',(origin[0]+160,y,.8),(320,.7,1.6),'MAT_KartConcrete');colbox('KART_Perimeter',(origin[0]+160,y,.8),(320,.7,1.6))
group('KART_Road')
road=strip('KART_ContinuousRoad',range(count),-4.95,4.95,'MAT_KartConcrete',bottom=-spec['deck_thickness'],collision=True)
road.data.materials.append(M['MAT_KartAsphalt'])
for face in road.data.polygons:
    if face.index%4==0:face.material_index=1
group('KART_Barriers')
strip('KART_LeftBarrier',range(count),4.6,4.95,'MAT_KartConcrete',top=1.05,bottom=0,collision=True)
segments=list(range(max(pit_indices),count))+list(range(0,min(pit_indices)+1))
strip('KART_RightBarrier',segments,-4.95,-4.6,'MAT_KartConcrete',top=1.05,bottom=0,collision=True)
group('KART_Markings')
for side in [-1,1]:
    for i in range(count):
        j=(i+1)%count
        if side==-1 and i in pit_set:continue
        a,b=sorted([side*4.0,side*4.55]);c=COLORS[level(i)] if int(D[i]/4)%2==0 else 'MAT_KartWhite'
        strip('KART_Kerb',[i,j],a,b,c,top=.014)
        a,b=sorted([side*4.60,side*4.95]);strip('KART_BarrierCap',[i,j],a,b,COLORS[level(i)],top=1.057)
for (name,material),(vs,fs) in DECOR.items():mesh(name,vs,fs,material,.3)
for side in [-1,1]:strip('KART_EdgeLine',range(count),side*3.76-.065,side*3.76+.065,'MAT_KartWhite',top=.017)
def arrow(i):
    c=P[i]+np.array([0,0,.025]);forward=np.array([T[i,0],T[i,1],0]);left=np.array([N[i,0],N[i,1],0])
    xy=[(-.26,-1.5),(.26,-1.5),(.26,.35),(.72,.35),(0,1.55),(-.72,.35),(-.26,.35)]
    vs=[list(c+left*x+forward*y) for x,y in xy];mesh('KART_Direction',vs,[tuple(reversed(range(7)))],COLORS[level(i)])
for i in range(0,count,34):arrow(i)
start_i=pit_indices[0]
for lane in range(16):
    off=-4+lane*.5;i=start_i;j=(i+2)%count
    strip('KART_StartFinish',[i,j],off,off+.5,'MAT_KartWhite' if lane%2 else 'MAT_Black',top=.026)
group('KART_Structure');support_count=0;last_s=-100
pit_footprint=Polygon([point(i,-22)[:2] for i in pit_indices]+[point(i,-4.95)[:2] for i in reversed(pit_indices)]).buffer(.8)
for i in range(count):
    if D[i]-last_s<15 or P[i,2]<1.5:continue
    last_s=D[i]
    for side in [-1,1]:
        q=np.array(point(i,side*4.72));dist=np.linalg.norm(P[:,:2]-q[:2],axis=1)
        if pit_footprint.covers(Point(q[:2])):continue
        far=np.minimum((np.arange(count)-i)%count,(i-np.arange(count))%count)>30
        if np.any((dist<6.0)&far&(P[:,2]<q[2]-.2)):continue
        height=q[2]-.45
        box('KART_BridgeColumn',(q[0],q[1],height/2),(.55,.55,height),'MAT_Steel')
        colbox('KART_BridgeColumn',(q[0],q[1],height/2),(.55,.55,height));support_count+=1
        box('KART_ColumnFoot',(q[0],q[1],.12),(1,1,.24),'MAT_KartConcrete')
group('KART_Pits')
strip('KART_PitApron',pit_indices,-pit['outside_offset'],-4.95,'MAT_KartConcrete',bottom=-.35,collision=True)
strip('KART_PitOutsideGuard',pit_indices[7:-7],-22.35,-22,'MAT_KartConcrete',top=1.05,bottom=0,collision=True)
for indices in [pit_indices[:8],pit_indices[-8:]]:
    strip('KART_PitWalkway',indices,-28,-22,'MAT_KartConcrete',bottom=-.35,collision=True)
anchors=[]
for k,i in enumerate(np.linspace(pit_indices[3],pit_indices[-4],6).astype(int)):
    i=int(i);p=point(i,-16,.10);yaw=math.degrees(math.atan2(T[i,0],T[i,1]))
    anchors.append({'name':'CVS2_Bay_%02d'%(k+1),'position':list(p),'yaw':yaw})
    empty=link(bpy.data.objects.new(anchors[-1]['name'],None));empty.location=p;empty.empty_display_type='ARROWS'
    for off in [-18.6,-13.4]:strip('KART_PitBayLine',range(i-5,i+6),off-.05,off+.05,'MAT_KartWhite',top=.023)
    text_obj('KART_PitNumber','%02d'%(k+1),point(i,-18.8,.028),.65,'MAT_KartWhite',rot=(0,0,math.atan2(T[i,1],T[i,0])-math.pi/2))
mid=P[pit_i];axis=np.array([T[pit_i,0],T[pit_i,1],0]);normal=np.array([N[pit_i,0],N[pit_i,1],0]);yaw=math.atan2(axis[1],axis[0])
def local_box(name,u,v,z,size,material,collision=True):
    pos=mid+axis*u+normal*v;pos[2]=z
    ob=box(name,(0,0,0),size,material);ob.location=pos;ob.rotation_euler.z=yaw
    if collision:colbox(name,pos,size,rot=(0,0,yaw))
    return ob
local_box('KART_VisitorDeck',0,-29,.15,(46,12,.3),'MAT_KartConcrete')
for k in range(3):local_box('KART_GrandstandTier',0,-29.5-k*1.5,.35+k*.25,(32,1.5,.7+k*.5),'MAT_Steel')
local_box('KART_PitCanopy',0,-29,5.5,(47,13,.35),'MAT_Steel')
for u in [-21,21]:
    for v in [-24,-34]:local_box('KART_CanopyColumn',u,v,2.65,(.25,.25,5.3),'MAT_Steel')
label_pos=mid+normal*-23;label_pos[2]=4.8
text_obj('KART_Title','APEX / TRI-LAYER KART',label_pos,1.25,'MAT_KartWhite',rot=(math.pi/2,0,yaw+math.pi))
visitor=mid+axis*-19+normal*-29;visitor[2]=.42
portal_position=mid+axis*-20+normal*-27;portal_position[2]=1.2
portals=[{'name':'APEX / KART','position':[23.8,2.8,1.15],'destination':visitor.tolist(),'yaw':math.degrees(math.atan2(normal[0],normal[1]))},
         {'name':'RETURN / CAFE','position':portal_position.tolist(),'destination':[23.8,4.1,.12],'yaw':0,'facing_yaw':-math.degrees(yaw)}]
for u in [-18,0,18]:
    p=mid+axis*u+normal*-28;p[2]=5.15
    area('LGT_KartCanopy',list(p),[p[0],p[1],0],380,(.83,.9,1),8)
panel=mid+axis*19+normal*-26;panel[2]=1.55
probes=[list(P[i]+np.array([0,0,1.1])) for i in range(0,count,32)]
cameras={
 '16_Kart_Overview':{'position':[center[0]+242,center[1]-277,220],'target':[center[0],center[1],2.8],'lens':49},
 '17_Kart_Overpass':{'position':list(P[int(count/12)]+np.array([12,-28,13])),'target':list(P[int(count/12)]+np.array([0,0,-3])),'lens':29},
 '18_Kart_Driver':{'position':list(P[pit_i]+np.array([0,0,1.0])),'target':list(P[(pit_i+35)%count]+np.array([0,0,.6])),'lens':22},
 '19_Kart_Pits':{'position':list(mid+axis*15+normal*8+np.array([0,0,4])),'target':list(mid+normal*-18+np.array([0,0,1.3])),'lens':26}
}
KART={**spec,'centerline':P.tolist(),'tangents':T.tolist(),'stations':D.tolist(),'length_m':float(np.linalg.norm(np.roll(P,-1,axis=0)-P,axis=1).sum()),'pit_indices':pit_indices,'vehicle_anchors':anchors,'portals':portals,'light_probes':probes,'support_columns':support_count,'cameras':cameras,'time_panel':{'position':panel.tolist(),'yaw':-math.degrees(yaw)}}
print('KART: %.1fm, %d supports, %d samples'%(KART['length_m'],support_count,count),flush=True)
