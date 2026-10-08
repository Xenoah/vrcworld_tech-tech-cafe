"""Render actual v0.6.1 geometry; no generated concept art or image edits.
The bloom compositor illustrates the design, not Unity's post-processing.
"""
from pathlib import Path
import bpy,sys,argparse
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--draft',action='store_true');p.add_argument('views',nargs='*')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=8
s.render.resolution_x=960 if a.draft else 1440;s.render.resolution_y=600 if a.draft else 900
s.cycles.samples=12 if a.draft else 32;s.cycles.use_denoising=True
s.use_nodes=True;nodes=s.node_tree.nodes;nodes.clear()
source=nodes.new('CompositorNodeRLayers');glare=nodes.new('CompositorNodeGlare')
glare.glare_type='FOG_GLOW';glare.quality='HIGH';glare.threshold=1.05;glare.size=8;glare.mix=-.45
out=nodes.new('CompositorNodeComposite');s.node_tree.links.new(source.outputs['Image'],glare.inputs['Image']);s.node_tree.links.new(glare.outputs['Image'],out.inputs['Image'])
for name in a.views or ['01_Entrance_160cm','04_Mezzanine_160cm','21_Spawn_Glass','22_Horizon_Skyline','23_City_Architecture','11_FPV_Course']:
 for o in bpy.data.objects:
  g=o.users_collection[0].name if o.users_collection else ''
  o.hide_render=g=='MODE_Academic' or (not g.startswith('FPV_') if name=='11_FPV_Course' else g.startswith(('KART_','FPV_')))
 s.camera=bpy.data.objects[name]
 target=(ROOT.parent/'v061-drafts'/f'{name}.png') if a.draft else ROOT/'Preview'/f'{name}.png'
 target.parent.mkdir(parents=True,exist_ok=True)
 pending=target.with_suffix('.rendering.png');s.render.filepath=str(pending)
 bpy.ops.render.render(write_still=True);pending.replace(target)
 print('COMPLETE',name,flush=True)
