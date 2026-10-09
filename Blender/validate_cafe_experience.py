"""Regression gate against Claude's v0.8.0. Standard library only.
Compare exported geometry byte-for-byte, collider/layout data and removed media.
This does not claim Unity/Udon compilation or a VRChat playtest.
"""
from pathlib import Path
import io,struct,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE='65c185ad0158e93db5023b1ae793313393ac2017'
report={'base_commit':BASE,'checks':[],'runtime':'Unity/Udon/VRChat not run'}
def check(name,passed,detail):
 report['checks'].append({'name':name,'pass':bool(passed),'detail':detail})
 if not passed:print('FAIL',name,detail)
def base(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
def records(data):
 f=io.BytesIO(data);assert f.read(4)==b'TCM2';count=struct.unpack('<I',f.read(4))[0];out={}
 def string():return f.read(struct.unpack('<I',f.read(4))[0]).decode()
 for _ in range(count):
  start=f.tell();name,group,mat=string(),string(),string();nv,ni=struct.unpack('<II',f.read(8));f.seek(nv*32+ni*4,1)
  out[name]={'group':group,'material':mat,'triangles':ni//3,'sha256':hashlib.sha256(data[start:f.tell()]).hexdigest()}
 assert f.tell()==len(data);return out
for platform in ['PC','Quest']:
 path=f'Unity/Assets/TheCommons/Models/TheCommons_{platform}.tcmesh.bytes';old=records(base(path));new=records((ROOT/path).read_bytes())
 for prefix in ['KART_','FPV_','ARCH_','FURN_','MODE_','ENV_','AV_DJ']:
  a={k:v for k,v in old.items() if v['group'].startswith(prefix)};b={k:v for k,v in new.items() if v['group'].startswith(prefix)}
  changed=[k for k in a if a[k]!=b.get(k)]
  check(platform+' '+prefix+' mesh bytes preserved',a==b,{'meshes':len(a),'changed':changed,'extra':sorted(set(b)-set(a))})
 check(platform+' activity signage exported',all(any(v['group']==group for v in new.values()) for group in ['WAY_FPV_Cafe','WAY_KART_Cafe','WAY_FPV_Return','WAY_KART_Return','WAY_EntryDirectory']),len(new))
path='Unity/Assets/TheCommons/Data/world_manifest.json';old=json.loads(base(path));new=json.loads((ROOT/path).read_text())
for key in ['colliders','lights','seat_anchors','city','stage','screen','stair_design']:
 check(key+' unchanged',old[key]==new[key],{'entries':len(new[key])})
for area in ['kart','fpv']:
 a={k:v for k,v in old[area].items() if k!='portals'};b={k:v for k,v in new[area].items() if k!='portals'}
 check(area+' course manifest preserved',a==b,'Only portal locations/return landings change')
 check(area+' course arrival preserved',old[area]['portals'][0]['destination']==new[area]['portals'][0]['destination'],new[area]['portals'][0]['destination'])
 check(area+' return interact preserved',old[area]['portals'][1]['position']==new[area]['portals'][1]['position'],new[area]['portals'][1]['position'])
for path in ['Blender/build_kart_circuit.py','Blender/kart_layout.py','SourceDesign/kart_circuit.json','Blender/FPV_Field_Module.json']:
 check(path+' unchanged',base(path)==(ROOT/path).read_bytes(),'Exact original source bytes')
check('Legacy player retired and slides removed','class CommonsVideoSync : UdonSharpBehaviour\n{\n}' in (ROOT/'Unity/Assets/TheCommons/Scripts/CommonsVideoSync.cs').read_text() and not list((ROOT/'Unity/Assets/TheCommons/Media').glob('slide_*')),'Inert upgrade tombstone only; no video player or slides included')
allcs='\n'.join(p.read_text() for p in (ROOT/'Unity/Assets/TheCommons').rglob('*.cs'))
check('No references to removed presentation API',not any(x in allcs for x in ['.videoSync','.presentationMaterial','.NextSlide','.timerLabel','VRCUnityVideoPlayer','VRCUrlInputField']),'Generated scene no longer creates presentation or URL UI')
check('Portal interaction enlarged', 'new Vector3(2.1f,.72f,.12f)' in allcs,'2.1 x 0.72 m, explicit Interact, 2.5 m proximity')
check('Late join lighting state is serialized','[UdonSynced] public int lightingMode' in allcs and 'public override void OnDeserialization() { Refresh(); }' in (ROOT/'Unity/Assets/TheCommons/Scripts/CommonsLightingModes.cs').read_text(),'Source inspection; multiplayer playtest pending')
report['passed']=all(c['pass'] for c in report['checks'])
(ROOT/'Documentation/cafe_update_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f"Cafe regression: {sum(c['pass'] for c in report['checks'])}/{len(report['checks'])}")
assert report['passed'], 'Cafe regression gate failed'
