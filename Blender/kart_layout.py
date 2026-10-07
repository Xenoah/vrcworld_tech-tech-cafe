"""Original metric switchbacks, circular corners and eased straight ramps.
The control vertices are authored independently of the photographic reference.
"""
import numpy as np

def layout(spec):
    cfg=spec['layout'];vertices=np.array(cfg['control_vertices'],dtype=float)
    radius,step=cfg['corner_radius'],cfg['sample_distance'];corners=[]
    for i,b in enumerate(vertices):
        a,c=vertices[(i-1)%len(vertices)],vertices[(i+1)%len(vertices)]
        incoming,outgoing=b[:2]-a[:2],c[:2]-b[:2]
        incoming/=np.linalg.norm(incoming);outgoing/=np.linalg.norm(outgoing)
        angle=np.arccos(np.clip(incoming@outgoing,-1,1))
        sign=np.sign(incoming[0]*outgoing[1]-incoming[1]*outgoing[0])
        assert sign!=0,'Every control vertex must define a corner'
        trim=radius*np.tan(angle/2);entry,exit=b[:2]-incoming*trim,b[:2]+outgoing*trim
        center=entry+np.array([-incoming[1],incoming[0]])*sign*radius
        corners.append((entry,exit,center,np.arctan2(*(entry-center)[::-1]),sign*angle,b[2]))
    points=[]
    for i,(entry,exit,center,start,sweep,height) in enumerate(corners):
        end,_,_,_,_,next_height=corners[(i+1)%len(corners)]
        direction=vertices[(i+1)%len(vertices),:2]-vertices[i,:2]
        assert (end-exit)@direction>=-1e-7,'Corner fillets consume the straight'
        n=max(3,int(np.ceil(abs(sweep)*radius/step)))
        for angle in start+np.arange(n)*sweep/n:
            points.append([*(center+radius*np.array([np.cos(angle),np.sin(angle)])),height])
        length=np.linalg.norm(end-exit)
        if length>1e-7:
            n=max(1,int(np.ceil(length/step)))
            for u in np.arange(n)/n:
                smooth=u*u*(3-2*u)
                points.append([*(exit+(end-exit)*u),height+(next_height-height)*smooth])
    p=np.array(points);p[:,:2]+=np.array(cfg['offset'])+np.array(spec['origin'][:2]);p[:,2]+=spec['origin'][2]
    tangent=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0)
    tangent=tangent[:,:2]/np.linalg.norm(tangent[:,:2],axis=1)[:,None]
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    distance=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);stations=np.r_[0,np.cumsum(distance[:-1])]
    return p,tangent,normal,stations,stations/distance.sum()*2*np.pi
