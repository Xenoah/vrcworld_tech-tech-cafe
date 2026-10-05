from pathlib import Path
import bpy,sys
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/The_Commons_Compact.blend'))
s=bpy.context.scene
s.render.threads_mode='FIXED';s.render.threads=8
s.render.resolution_x=1440;s.render.resolution_y=900;s.cycles.samples=24
names=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['01_Entrance_160cm','02_AnchorBar_160cm','03_Stage_160cm','04_Mezzanine_160cm','05_Archive_160cm']
for name in names:
 s.camera=bpy.data.objects[name];s.render.filepath=str(ROOT/'Preview'/f'{name}.png')
 bpy.ops.render.render(write_still=True)
