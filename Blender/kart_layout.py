"""Metric closed course samples shared by authoring and geometry checks."""
import numpy as np

def layout(spec):
    cfg=spec['layout'];n=cfg['samples'];t=np.arange(n)*2*np.pi/n;phase=3*t
    radius=cfg['major_radius']+cfg['minor_radius']*np.cos(phase)
    xy=np.column_stack([radius*np.cos(2*t)*cfg['x_scale'],radius*np.sin(2*t)])
    tangent=np.roll(xy,-1,axis=0)-np.roll(xy,1,axis=0)
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    local=phase%np.pi-np.pi/2
    u=(local+.30)/.60;inside=(u>0)&(u<1);offset=np.zeros(n)
    # The wide pit apron needs a smooth approach, with no tight chicane.
    inside &= np.abs(t-spec['pit']['phase'])>.20
    offset[inside]=cfg['chicane_amplitude']*np.sin(u[inside]*2*np.pi)*np.sin(u[inside]*np.pi)**2
    xy+=normal*offset[:,None]
    u=np.arcsin(np.abs(np.sin(phase)))
    q=np.clip((u-cfg['ramp_begin'])/(cfg['plateau_begin']-cfg['ramp_begin']),0,1)
    q=q*q*(3-2*q)
    low,mid,high=spec['levels'];z=mid+(high-mid)*np.sign(np.sin(phase))*q
    xy+=np.array(spec['center_local'])+np.array(spec['origin'][:2])
    p=np.column_stack([xy,z+spec['origin'][2]])
    tangent=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0)
    tangent=tangent[:,:2]/np.linalg.norm(tangent[:,:2],axis=1)[:,None]
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    distance=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    return p,tangent,normal,np.r_[0,np.cumsum(distance[:-1])],t
