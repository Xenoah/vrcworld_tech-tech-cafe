"""Actual v0.9 geometry / Blender Cycles previews; lighting design visualization.
The palette and finite laser layout follow the Unity controller. Baked/realtime
Unity shading, UI interaction, and networking still require runtime validation.
"""
from pathlib import Path
import bpy,math,sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
PALETTES=[((1,.49,.18),(1,.76,.40)),((.05,.78,1),(.82,.13,1)),((.54,.41,.745),(.39,.55,.8))]
VIEWS={
 '30_Activity_Portals':(0,(14,.48,1.65),(14,3.45,1.98),12),
 '31_Cafe_Warm':(0,(14,2.4,1.65),(14,12,3.7),18),
 '32_Cafe_Cyber':(1,(14,2.4,1.65),(14,12,3.7),18),
 '33_Cafe_Disco':(2,(14,2.4,1.65),(14,12,3.7),18),
 '34_Stage_iwaSync':(0,(14,9.65,1.6),(14,16.8,2.5),22),
}
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for name in args or VIEWS:
 mode,pos,target,lens=VIEWS[name];bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'));s=bpy.context.scene
 s.render.threads_mode='FIXED';s.render.threads=6;s.cycles.samples=20;s.cycles.use_denoising=True
 s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=100
 primary,secondary=PALETTES[mode]
 clones={}
 for o in bpy.data.objects:
  group=o.users_collection[0].name if o.users_collection else ''
  o.hide_render=group.startswith(('KART_','FPV_')) or group=='MODE_Academic'
  if o.type=='LIGHT' and not o.hide_render and 0<o.location.x<28:
   i=sum(ord(c) for c in o.name);o.data.color=primary if i%2 else secondary
   if mode>0:o.data.energy*=.75
  if group.startswith(('ENV_','WAY_')) or o.type not in {'MESH','FONT'}:continue
  for slot in o.material_slots:
   mat=slot.material
   if not mat or not mat.use_nodes:continue
   if mat.name not in clones:
    copy=mat.copy();clones[mat.name]=copy;p=copy.node_tree.nodes.get('Principled BSDF')
    if p:
     strength=p.inputs['Emission Strength'].default_value
     if strength>0:p.inputs['Emission Color'].default_value=(*(primary if len(clones)%2 else secondary),1)
   slot.material=clones[mat.name]
 if mode==2:
  for i in range(12):
   origin=Vector((10.2 if i<6 else 17.8,5.3,4.3));spread=(i%6)/5*2-1
   end=Vector((14+2.6*math.sin(spread*1.15),10+math.cos(i*.8),2.8+.7*math.sin(i*.72)))
   # Same 4-triangle crossed ribbon as Unity's BeamMesh, at its static phase.
   d=end-origin;rotation=d.to_track_quat('Z','Y');w=.024
   vs=[origin+rotation@Vector(v) for v in [(-w,0,0),(w,0,0),(w,0,d.length),(-w,0,d.length),(0,-w,0),(0,w,0),(0,w,d.length),(0,-w,d.length)]]
   me=bpy.data.meshes.new('Laser');me.from_pydata(vs,[],[(0,1,2),(0,2,3),(4,5,6),(4,6,7)])
   o=bpy.data.objects.new('LaserPreview',me);s.collection.objects.link(o)
   m=bpy.data.materials.new('Beam');m.use_nodes=True;n=m.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(*(primary if i%2==0 else secondary),1);e.inputs[1].default_value=2.1;out=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],out.inputs[0]);me.materials.append(m)
   o.visible_shadow=False
 cam=bpy.data.cameras.new(name);cam.lens=lens;cam.clip_end=300;camera=bpy.data.objects.new(name,cam);s.collection.objects.link(camera);camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();s.camera=camera
 s.use_nodes=True;n=s.node_tree.nodes;n.clear();render=n.new('CompositorNodeRLayers');glare=n.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='HIGH';glare.threshold=1.1;glare.size=8;glare.mix=-.55;out=n.new('CompositorNodeComposite');s.node_tree.links.new(render.outputs['Image'],glare.inputs['Image']);s.node_tree.links.new(glare.outputs['Image'],out.inputs['Image'])
 output=ROOT/'Preview'/f'{name}.png';temp=output.with_suffix('.rendering.png');s.render.filepath=str(temp);bpy.ops.render.render(write_still=True);temp.replace(output);print('COMPLETE',name,flush=True)
