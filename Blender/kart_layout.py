"""Original metric layout: per-corner arc radius, banking and through-corner grades.
Each control vertex is a polygon corner rounded by its own circular arc. A vertex
with a height holds it over the whole arc ("arc") or at its "apex", "entry" or "exit";
a null height lets a ramp run through that corner. Ramps ease with smoothstep.
A "bump" on a vertex shapes the straight after it: a sharp "crest" (jump point,
eased feet, pointed top) or a rounded "swell"/"dip" (compression). Real circuits
inform corner character only; the control vertices are original.
"""
import numpy as np

def smooth(u):
    u=np.clip(u,0,1);return u*u*(3-2*u)

def layout(spec):
    cfg=spec['layout'];raw=cfg['control_vertices'];step=cfg['sample_distance']
    xy=np.array([[v['x'],v['y']] for v in raw],dtype=float);count=len(raw);corners=[]
    for i,b in enumerate(xy):
        a,c=xy[(i-1)%count],xy[(i+1)%count]
        incoming,outgoing=b-a,c-b
        incoming/=np.linalg.norm(incoming);outgoing/=np.linalg.norm(outgoing)
        angle=np.arccos(np.clip(incoming@outgoing,-1,1))
        sign=np.sign(incoming[0]*outgoing[1]-incoming[1]*outgoing[0])
        assert sign!=0,'Every control vertex must define a corner'
        radius=raw[i].get('r',cfg['default_radius'])
        trim=radius*np.tan(angle/2);entry,exit=b-incoming*trim,b+outgoing*trim
        center=entry+np.array([-incoming[1],incoming[0]])*sign*radius
        corners.append(dict(entry=entry,exit=exit,center=center,start=np.arctan2(*(entry-center)[::-1]),sweep=sign*angle,radius=radius,sign=sign))
    points=[];stations=[];s=0.0
    for i,k in enumerate(corners):
        arc=abs(k['sweep'])*k['radius'];k.update(s_entry=s,s_apex=s+arc/2,s_exit=s+arc)
        n=max(3,int(np.ceil(arc/step)))
        for j in range(n):
            angle=k['start']+j*k['sweep']/n
            points.append(k['center']+k['radius']*np.array([np.cos(angle),np.sin(angle)]));stations.append(s+arc*j/n)
        s+=arc;end=corners[(i+1)%count]['entry'];direction=xy[(i+1)%count]-xy[i]
        assert (end-k['exit'])@direction>=-1e-3,'Corner fillets consume the straight after vertex %d'%i
        length=float(np.linalg.norm(end-k['exit']));k['straight']=(s,s+length)
        if length>1e-3:
            n=max(1,int(np.ceil(length/step)))
            for j in range(n):
                points.append(k['exit']+(end-k['exit'])*j/n);stations.append(s+length*j/n)
        s+=length
    total=s;S=np.array(stations)
    # Height keyframes: flat holds at fixed vertices, smoothstep ramps between them.
    keys=[]
    for v,k in zip(raw,corners):
        if v.get('z') is None:continue
        a,b={'arc':(k['s_entry'],k['s_exit']),'apex':(k['s_apex'],k['s_apex']),'entry':(k['s_entry'],k['s_entry']),'exit':(k['s_exit'],k['s_exit'])}[v.get('hold','arc')]
        keys.append((a,b,float(v['z'])))
    assert keys,'At least one control vertex must fix the course height'
    keys=[(a-total,b-total,z) for a,b,z in keys[-1:]]+keys+[(a+total,b+total,z) for a,b,z in keys[:1]]
    Z=np.full(len(S),np.nan)
    for (a0,b0,z0),(a1,b1,z1) in zip(keys,keys[1:]):
        Z[(S>=a0)&(S<=b0)]=z0
        ramp=(S>b0)&(S<a1);Z[ramp]=z0+(z1-z0)*smooth((S[ramp]-b0)/(a1-b0))
    assert np.isfinite(Z).all(),'Station outside the height keyframes'
    for v,k in zip(raw,corners):
        bump=v.get('bump')
        if not bump:continue
        a,b=k['straight'];c=a+(b-a)*bump.get('at',.5);w=bump['length']/2
        assert a<=c-w and c+w<=b,'Bump must fit inside its straight'
        t=np.clip(1-np.abs(S-c)/w,0,1)
        Z+=bump['height']*(t*t if bump.get('shape','crest')=='crest' else np.sin(t*np.pi/2)**2)
        k['bump']=int(np.argmin(np.abs(S-c)))
    # Signed bank angle: inside edge lower, full over the arc, eased either side.
    # Neighbouring banked arcs share the strongest value instead of stacking.
    bank=np.zeros(len(S));blend=cfg.get('bank_transition',8.0)
    for v,k in zip(raw,corners):
        if not v.get('bank'):continue
        for shift in (-total,0,total):
            outside=np.maximum(k['s_entry']+shift-S,S-k['s_exit']-shift)
            value=np.radians(v['bank'])*k['sign']*(1-smooth(outside/blend))
            bank=np.where(np.abs(value)>np.abs(bank),value,bank)
    p=np.column_stack([np.array(points),Z]);p[:,:2]+=np.array(cfg['offset'])+np.array(spec['origin'][:2]);p[:,2]+=spec['origin'][2]
    tangent=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0)
    tangent=tangent[:,:2]/np.linalg.norm(tangent[:,:2],axis=1)[:,None]
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    distance=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);D=np.r_[0,np.cumsum(distance[:-1])]
    marks=[{key:int(np.argmin(np.abs(S-k['s_'+key]))) for key in ('entry','apex','exit')}|{'radius':float(k['radius']),'sweep_deg':float(np.degrees(k['sweep'])),'bump':k.get('bump')} for k in corners]
    return p,tangent,normal,D,D/distance.sum()*2*np.pi,bank,marks
