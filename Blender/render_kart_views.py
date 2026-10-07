"""Render the actual authored kart model for release previews, not a mock-up."""
from pathlib import Path
import bpy,json,math,sys
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
s=bpy.context.scene;data=json.loads((ROOT/'Documentation/model_manifest.json').read_text())['kart']
for o in bpy.data.objects:
    if o.type in {'MESH','FONT','LIGHT'}:o.hide_render=not o.users_collection[0].name.startswith('KART_')
s.world.use_nodes=True;background=s.world.node_tree.nodes.get('Background');background.inputs[0].default_value=(.38,.51,.68,1);background.inputs[1].default_value=.65
sun=bpy.data.lights.new('PREVIEW_Daylight','SUN');sun.energy=2.0;sun.angle=.12
obj=bpy.data.objects.new('PREVIEW_Daylight',sun);s.collection.objects.link(obj);obj.rotation_euler=(math.radians(28),math.radians(-22),math.radians(-35))
s.render.engine='CYCLES';s.render.threads_mode='FIXED';s.render.threads=8;s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.max_bounces=4
s.render.resolution_x=1600;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.view_settings.exposure=.1
names=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(data['cameras'])
for name in names:
    s.camera=bpy.data.objects[name]
    if name=='16_Kart_Overview':s.camera.data.lens=36
    # Publish only complete images, even if a render is interrupted.
    pending=ROOT/'Preview'/f'{name}.rendering.png'
    s.render.filepath=str(pending);bpy.ops.render.render(write_still=True)
    pending.replace(ROOT/'Preview'/f'{name}.png')
print('Rendered',len(names),'actual-model previews; Unity/VRChat rendering remains unverified.')
