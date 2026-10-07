"""Audit actual collision meshes and integration data; not a CVS2 runtime test."""
from pathlib import Path
from collections import Counter
import json,math
import numpy as np
from shapely.geometry import Polygon,Point,box
from shapely.strtree import STRtree
import ezdxf
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'Documentation/model_manifest.json').read_text());spec=manifest['kart'];P=np.array(spec['centerline']);n=len(P)
cols=manifest['colliders'];road=next(c for c in cols if c['name']=='COL_KART_ContinuousRoad');V=np.array(road['vertices']);tris=np.array(road['triangles']).reshape(-1,3)
checks=[]
def check(name,ok,detail):checks.append({'name':name,'pass':bool(ok),'detail':detail})
delta=np.roll(P,-1,axis=0)-P;ds=np.linalg.norm(delta[:,:2],axis=1);lengths=np.linalg.norm(delta,axis=1);D=np.r_[0,np.cumsum(lengths[:-1])];total=float(lengths.sum())
tangent=np.roll(P,-1,axis=0)-np.roll(P,1,axis=0);tangent=tangent[:,:2]/np.linalg.norm(tangent[:,:2],axis=1)[:,None]
angles=np.arccos(np.clip((tangent*np.roll(tangent,-1,axis=0)).sum(1),-1,1));radius=ds/np.maximum(angles,1e-8);limits=spec['design_limits']
check('Kart finite collision mesh',np.isfinite(V).all() and tris.min()>=0 and tris.max()<len(V),{'vertices':len(V),'triangles':len(tris)})
edges=Counter(tuple(sorted((int(a),int(b)))) for tri in tris for a,b in zip(tri,np.roll(tri,-1)))
check('Kart watertight continuous deck',all(v==2 for v in edges.values()),{'nonmanifold_edges':sum(v!=2 for v in edges.values())})
check('Kart authored road agrees with course samples',len(V)==4*n and np.allclose((V[::4]+V[1::4])/2,P,atol=1e-5),{'samples':n})
widths=np.linalg.norm(V[::4,:2]-V[1::4,:2],axis=1)
check('Kart width and nondegenerate track',widths.min()>spec['road_width'] and ds.min()>.1,{'road_width_m':spec['road_width'],'deck_width_m':float(widths.min())})
check('Kart maximum grade',float(np.max(abs(delta[:,2])/ds)*100)<=limits['maximum_grade_percent'],{'maximum_percent':float(np.max(abs(delta[:,2])/ds)*100),'limit_percent':limits['maximum_grade_percent']})
check('Kart turn radius',float(radius.min())>=limits['minimum_center_radius'],{'minimum_center_radius_m':float(radius.min()),'inside_driving_radius_m':float(radius.min()-spec['road_width']/2)})
check('Kart collision sampling',float(ds.max())<=limits['maximum_sample_distance'],{'maximum_segment_m':float(ds.max())})
levels={str(h):float(lengths[np.abs(P[:,2]-h)<1e-6].sum()) for h in spec['levels']}
check('Kart three drivable level plateaus',len(levels)==3 and min(levels.values())>60,{'flat_length_per_level_m':levels})
lo=np.array(spec['origin'][:2]);hi=lo+spec['size'][:2]
check('Kart road inside independent floor',np.all(V[:,:2]>=lo) and np.all(V[:,:2]<=hi) and lo[0]>=100,{'floor_size_m':spec['size'][:2],'road_bounds':[V[:,:2].min(0).tolist(),V[:,:2].max(0).tolist()]})
cross=np.cross(V[tris[:,1]]-V[tris[:,0]],V[tris[:,2]]-V[tris[:,0]])
mask=cross[:,2]>1e-7;top=V[tris[mask]];polys=[Polygon(t[:,:2]) for t in top];tree=STRtree(polys)
check('Kart collision faces point upward',len(top)==2*n,{'upward_top_triangles':len(top),'expected':2*n})
plane=np.linalg.solve(np.concatenate([top[:,:,:2],np.ones((len(top),3,1))],axis=2),top[:,:,2])
seg=np.repeat(np.arange(n),2);minimum=1e6;pairs=0
def coordinates(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return list(g.exterior.coords)
    if hasattr(g,'geoms'):return [p for child in g.geoms for p in coordinates(child)]
    return list(g.coords)
for i,poly in enumerate(polys):
    for j in tree.query(poly,predicate='intersects'):
        if j<=i:continue
        separation=abs(D[seg[i]]-D[seg[j]])
        if min(separation,total-separation)<30:continue
        overlap=poly.intersection(polys[j]);coords=coordinates(overlap)
        if not coords:continue
        xy=np.column_stack([np.array(coords),np.ones(len(coords))]);difference=xy@(plane[i]-plane[j])
        clear=0 if difference.min()<=0<=difference.max() else float(abs(difference).min())-spec['deck_thickness']
        minimum=min(minimum,clear);pairs+=1
check('Kart bridge crossing clearance',pairs>0 and minimum>=limits['minimum_crossing_clearance'],{'minimum_underside_clearance_m':minimum,'intersecting_triangle_pairs':pairs,'required_m':limits['minimum_crossing_clearance']})
pit=next(c for c in cols if c['name']=='COL_KART_PitApron');pv=np.array(pit['vertices']);pt=np.array(pit['triangles']).reshape(-1,3)
pcross=np.cross(pv[pt[:,1]]-pv[pt[:,0]],pv[pt[:,2]]-pv[pt[:,0]]);pit_top=pv[pt[pcross[:,2]>1e-7]]
driving=np.concatenate([top,pit_top]);drive_polys=[Polygon(t[:,:2]) for t in driving];drive_tree=STRtree(drive_polys)
drive_plane=np.linalg.solve(np.concatenate([driving[:,:,:2],np.ones((len(driving),3,1))],axis=2),driving[:,:,2])
conflicts=[]
for c in cols:
    if c['name']!='COL_KART_BridgeColumn':continue
    x,y,z=c['position'];sx,sy,sz=c['size'];foot=box(x-sx/2,y-sy/2,x+sx/2,y+sy/2)
    for j in drive_tree.query(foot,predicate='intersects'):
        coords=coordinates(foot.intersection(drive_polys[j]));h=np.column_stack([np.array(coords),np.ones(len(coords))])@drive_plane[j]
        if h.min()<z+sz/2+.12 and h.max()>z-sz/2:conflicts.append(c['position']);break
check('Kart bridge columns clear driving surfaces',not conflicts,{'columns':spec['support_columns'],'conflicts':conflicts[:10]})
flat_top=np.all(np.abs(pv[pt,2]-spec['levels'][0])<1e-6,axis=1);folded=int(np.sum(pcross[flat_top,2]<=1e-7))
check('Kart pit apron has no folded top faces',folded==0 and flat_top.sum()==2*(len(spec['pit_indices'])-1),{'folded_top_triangles':folded,'top_triangles':int(flat_top.sum())})
supported=[]
for anchor in spec['vehicle_anchors']:
    pos=anchor['position'];supported.append(any(Polygon(t[:,:2]).buffer(1e-6).contains(Point(pos[:2])) and pos[2]>t[:,2].mean() for t in pit_top))
check('Kart six supported CVS2 placement guides',len(supported)==6 and all(supported) and not spec['vehicle_assets_included'],{'anchors':len(supported),'supported':sum(supported),'vehicle_system_included':False})
blocks=[]
for portal in spec['portals']:
    p=np.array(portal['destination']);radius_player=.22
    for c in cols:
        if c['kind']!='box':continue
        center=np.array(c['position']);size=np.array(c['size']);angle=c.get('rotation',[0,0,0])[2]
        d=p[:2]-center[:2];local=np.array([math.cos(angle)*d[0]+math.sin(angle)*d[1],-math.sin(angle)*d[0]+math.cos(angle)*d[1]])
        nearest=np.maximum(abs(local)-size[:2]/2,0)
        if np.linalg.norm(nearest)<radius_player and center[2]+size[2]/2>p[2]+.02 and center[2]-size[2]/2<p[2]+1.7:blocks.append({'portal':portal['name'],'collider':c['name']})
check('Kart pedestrian warp capsule clearance',not blocks and len(spec['portals'])==2,{'blocked':blocks})
report={'version':'0.6.0','length_m':total,'checks':checks,'passed':all(c['pass'] for c in checks),'scope':'Geometric collision/layout checks only. Unity, CVS2 and VRChat runtime not tested.'}
(ROOT/'Documentation/kart_validation.json').write_text(json.dumps(report,indent=2)+'\n')
doc=ezdxf.new('R2010');doc.units=4;ms=doc.modelspace()
for name,color in [('LOWER',4),('MIDDLE',30),('UPPER',3),('FLOOR',8),('CVS2_GUIDES',2)]:doc.layers.new(name,dxfattribs={'color':color})
for i in range(n):
    k=(i+1)%n;name=['LOWER','MIDDLE','UPPER'][int(np.argmin(abs(np.array(spec['levels'])-P[i,2])))]
    ms.add_line(tuple(P[i]*1000),tuple(P[k]*1000),dxfattribs={'layer':name})
ms.add_lwpolyline([(lo[0]*1000,lo[1]*1000),(hi[0]*1000,lo[1]*1000),(hi[0]*1000,hi[1]*1000),(lo[0]*1000,hi[1]*1000)],close=True,dxfattribs={'layer':'FLOOR'})
for a in spec['vehicle_anchors']:ms.add_point(tuple(np.array(a['position'])*1000),dxfattribs={'layer':'CVS2_GUIDES'})
doc.saveas(ROOT/'CAD/APEX_Kart_Neon_Switchyard_v06.dxf')
print(json.dumps(report,indent=2))
if not report['passed']:raise SystemExit(1)
