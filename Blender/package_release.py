"""Deterministic Unity metadata and install package, plus the complete authoring archive."""
from pathlib import Path
import uuid,json,tarfile,io,zipfile,hashlib,sys,subprocess,gzip
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'Unity/Assets';A=ASSETS/'TheCommons'
def guid(path):return uuid.uuid5(uuid.NAMESPACE_URL,'thecommons-v02/'+path).hex
def metadata(p):
 rel=p.relative_to(ROOT/'Unity').as_posix();g=guid(rel);s='fileFormatVersion: 2\nguid: '+g+'\n'
 meta=Path(str(p)+'.meta')
 if meta.exists():return next(line.split(': ',1)[1] for line in meta.read_text().splitlines() if line.startswith('guid: '))
 if p.is_dir():s+='folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n'
 elif p.suffix=='.cs':s+='MonoImporter:\n  externalObjects: {}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n'
 elif p.suffix=='.asset':s+='NativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 11400000\n'
 elif p.suffix=='.shader':s+='ShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n'
 elif p.suffix=='.png':s+='TextureImporter:\n  externalObjects: {}\n  serializedVersion: 12\n  mipmaps:\n    enableMipMap: 1\n    sRGBTexture: 1\n  maxTextureSize: 2048\n  textureSettings:\n    serializedVersion: 2\n    filterMode: 1\n    aniso: 4\n    mipBias: 0\n    wrapU: '+('2' if '/Textures/' in rel else '1')+'\n    wrapV: '+('2' if '/Textures/' in rel else '1')+'\n    wrapW: 1\n  textureType: 0\n  textureShape: 1\n  alphaIsTransparency: 0\n  platformSettings: []\n'
 elif p.suffix=='.wav':s+='AudioImporter:\n  externalObjects: {}\n  serializedVersion: 7\n  defaultSettings:\n    serializedVersion: 2\n    loadType: 1\n    sampleRateSetting: 0\n    sampleRateOverride: 44100\n    compressionFormat: 1\n    quality: 0.55\n    conversionMode: 0\n  platformSettingOverrides: {}\n  forceToMono: 0\n  normalize: 1\n  preloadAudioData: 1\n  loadInBackground: 0\n  ambisonic: 0\n'
 elif p.suffix=='.fbx':s+='ModelImporter:\n  serializedVersion: 22200\n  internalIDToNameTable: []\n  externalObjects: {}\n  materials:\n    materialImportMode: 2\n  meshes:\n    globalScale: 1\n    useFileScale: 1\n    addColliders: 0\n    generateSecondaryUV: 1\n'
 elif p.suffix in ['.bytes','.json','.txt']:s+='TextScriptImporter:\n  externalObjects: {}\n'
 else:s+='DefaultImporter:\n  externalObjects: {}\n'
 s+='  userData: \n  assetBundleName: \n  assetBundleVariant: \n'
 if p.name in {'relay_controller_albedo.png','bar_labels_albedo.png','cafe_props_albedo.png'}:
  s=s.replace('wrapU: 2','wrapU: 1').replace('wrapV: 2','wrapV: 1').replace('maxTextureSize: 2048','maxTextureSize: 1024')
 Path(str(p)+'.meta').write_text('\n'.join(line.rstrip() for line in s.splitlines())+'\n')
 return g
# Udon program assets pair scripts with the SDK's canonical program-asset type.
for script in (A/'Scripts').glob('*.cs'):
 cg=guid(script.relative_to(ROOT/'Unity').as_posix())
 asset=script.with_suffix('.asset')
 asset.write_text('''%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 0}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: c333ccfdd0cbdbc4ca30cef2dd6e6b9b, type: 3}
  m_Name: NAME
  m_EditorClassIdentifier: 
  serializedUdonProgramAsset: {fileID: 0}
  udonAssembly: 
  assemblyError: 
  sourceCsScript: {fileID: 11500000, guid: GUID, type: 3}
  scriptVersion: 2
  compiledVersion: 0
  behaviourSyncMode: 0
  hasInteractEvent: 0
  scriptID: 0
  serializationData:
    SerializedFormat: 2
    SerializedBytes: 
    ReferencedUnityObjects: []
    SerializedBytesString: 
    Prefab: {fileID: 0}
    PrefabModificationsReferencedUnityObjects: []
    PrefabModifications: []
    SerializationNodes: []
'''.replace('NAME',script.stem).replace('GUID',cg))
paths=sorted([A]+[p for p in A.rglob('*') if p.suffix!='.meta' and 'Generated' not in p.parts and not p.name.endswith('.tmp')])
for p in paths:metadata(p)
if '--metadata-only' in sys.argv:
 print('Unity metadata ready; existing GUIDs/import settings preserved.');raise SystemExit(0)
version=json.loads((A/'Data/world_manifest.json').read_text()).get('version','0.3.0')
release=ROOT.parent/f'The_Commons_Compact_v{version}.unitypackage'
pending=release.with_suffix(release.suffix+'.tmp')
# Close all compression layers before publishing the complete archive.
with pending.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=7,mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w') as tar:
 def add(name,data):
  t=tarfile.TarInfo(name);t.size=len(data);t.mtime=0;tar.addfile(t,io.BytesIO(data))
 for p in paths:
  rel=p.relative_to(ROOT/'Unity').as_posix();g=metadata(p)
  add(g+'/pathname',rel.encode());add(g+'/asset.meta',Path(str(p)+'.meta').read_bytes())
  if p.is_file():add(g+'/asset',p.read_bytes())
  else:add(g+'/asset',b'')
pending.replace(release)
# Remove only generated Blender backups from the delivery tree.
for p in ROOT.rglob('*.blend1'):p.unlink()
# Only Git-visible project files, never repository internals, caches or generated scenes.
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
files=sorted({ROOT/n for n in names if n and n!='SHA256SUMS.txt' and (ROOT/n).is_file()})
(ROOT/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix() for p in files)+'\n')
bundle=ROOT.parent/f'The_Commons_Compact_v{version}_Full.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for p in files+[ROOT/'SHA256SUMS.txt']:z.write(p,p.relative_to(ROOT.parent))
print(json.dumps({'unitypackage':{'path':str(release),'bytes':release.stat().st_size},'full':{'path':str(bundle),'bytes':bundle.stat().st_size}},indent=2))
