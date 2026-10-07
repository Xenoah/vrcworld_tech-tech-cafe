"""Photograph the actual enclosed model. Overview alone removes roof/two walls.
No generated concept imagery or material substitutions are used.
"""
from pathlib import Path
import bpy,json,sys,argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--draft',action='store_true');parser.add_argument('views',nargs='*')
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
s=bpy.context.scene;data=json.loads((ROOT/'Documentation/model_manifest.json').read_text())['kart']
s.world.use_nodes=True;background=s.world.node_tree.nodes.get('Background');background.inputs[0].default_value=(.008,.012,.026,1);background.inputs[1].default_value=.15
s.render.engine='CYCLES';s.render.threads_mode='FIXED';s.render.threads=6;s.cycles.samples=16 if a.draft else 40;s.cycles.use_denoising=True;s.cycles.max_bounces=4
s.render.resolution_x=960 if a.draft else 1600;s.render.resolution_y=600 if a.draft else 1000;s.render.resolution_percentage=100
s.view_settings.exposure=1.5
s.use_nodes=True;nodes=s.node_tree.nodes;nodes.clear();source=nodes.new('CompositorNodeRLayers');glare=nodes.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='HIGH';glare.threshold=1.1;glare.size=7;glare.mix=-.72
out=nodes.new('CompositorNodeComposite');s.node_tree.links.new(source.outputs['Image'],glare.inputs['Image']);s.node_tree.links.new(glare.outputs['Image'],out.inputs['Image'])
for name in a.views or data['cameras']:
    cutaway=data['cameras'][name].get('cutaway',False)
    for o in bpy.data.objects:
        if o.type in {'MESH','FONT','LIGHT'}:
            group=o.users_collection[0].name
            o.hide_render=not group.startswith('KART_') or (cutaway and group in {'KART_Roof','KART_ShellSouth','KART_ShellEast','KART_Trusses'})
    s.camera=bpy.data.objects[name]
    target=(ROOT.parent/'v06-work'/f'{name}-DRAFT.png') if a.draft else ROOT/'Preview'/f'{name}.png'
    pending=target.with_suffix('.rendering.png');s.render.filepath=str(pending);bpy.ops.render.render(write_still=True);pending.replace(target)
    print('COMPLETE',name,str(target),flush=True)
