"""Build a deterministic documentation appendix; --publish appends to v0.6.0.

The original tag, Unity package, Full.zip and existing assets are preserved.
Publishing uses gh with the repository-scoped GitHub Actions token.
"""
from pathlib import Path
import json,hashlib,re,struct,zlib,zipfile,subprocess,sys
from xml.etree import ElementTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent
CFG=json.loads((ROOT/'Documentation/Design/release_appendix.json').read_text())
MODEL=CFG['model_commit'];BASE='https://github.com/Xenoah/vrcworld_tech-tech-cafe'
DOWNLOAD=BASE+'/releases/download/v0.6.0/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(*args):return subprocess.check_output(list(args),cwd=ROOT,text=True)

# Keep the detailed README and the release body in sync, using usable remote links.
source=(ROOT/'README.md').read_text()
asset_paths=set(CFG['append_assets'])|{x['path'] for x in json.loads((ROOT/'Documentation/release_screenshots.json').read_text())['images']}
def link(m):
    marker,label,path=m.groups()
    if path.startswith(('https://','http://','#')):return m.group(0)
    target=ROOT/path.split('#')[0];assert target.exists(),f'Broken README link: {path}'
    if path in asset_paths:url=DOWNLOAD+target.name
    elif marker=='!':url='https://raw.githubusercontent.com/Xenoah/vrcworld_tech-tech-cafe/'+MODEL+'/'+path
    else:url=BASE+'/blob/main/'+path
    return marker+'['+label+']('+url+')'
notes=re.sub(r'(!?)\[([^\]]*)\]\(([^)]+)\)',link,source)
notes=notes.replace('# The Commons — Compact Edition','# v0.6.0 — NEON SWITCHYARD / 詳細仕様・図面付き',1)
notes=notes.replace('このREADMEは現在の','このリリース説明は現在の')
notes=notes.replace('モデル版 **v0.6.0** ／','**2026-10-07追補: カフェ・FPV・カートの詳細仕様、平面図5枚、デザインシート3枚、A3図面集PDFを追加。**\n\nモデル版 **v0.6.0** ／',1)
(ROOT/CFG['notes_path']).write_text(notes)

# Verify that this is exclusively a documentation update of the published model.
subprocess.run(['git','diff','--exit-code',MODEL,'--','Unity','SourceDesign',
                'Blender/The_Commons_Compact.blend','Blender/FPV_Field_Module.json',
                'Blender/build_world.py','Blender/build_fpv_field.py','Blender/build_kart_circuit.py',
                'Blender/kart_layout.py','Blender/export_world.py',':(glob)Preview/*.png'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
atlas=json.loads((ROOT/'Documentation/Design/atlas_manifest.json').read_text())
assert atlas['model_commit']==MODEL and len(atlas['sheets'])==8
for name,digest in atlas['inputs_sha256'].items():assert sha(ROOT/name)==digest,f'Atlas source changed: {name}'
for s in atlas['sheets']:
    p=ROOT/'Preview/Design'/(s['file']+'.png');data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n'
    w,h=struct.unpack('>II',data[16:24]);assert w==2400 and h>=1600
    offset=8;complete=False
    while offset+12<=len(data):
        size=struct.unpack_from('>I',data,offset)[0];end=offset+12+size;assert end<=len(data)
        chunk=data[offset+4:offset+8+size];crc=struct.unpack_from('>I',data,offset+8+size)[0]
        assert zlib.crc32(chunk)&0xffffffff==crc
        offset=end
        if chunk[:4]==b'IEND':complete=True;break
    assert complete and offset==len(data)
    if s['kind']=='dimensioned plan':ElementTree.parse(ROOT/'CAD/Plans'/(s['file']+'.svg'))
pdf=ROOT/'Documentation/Design/The_Commons_v0.6.0_Design_Atlas.pdf';pdfdata=pdf.read_bytes()
assert pdfdata.startswith(b'%PDF-') and pdfdata.rstrip().endswith(b'%%EOF')
assert len(re.findall(rb'/Type\s*/Page\b',pdfdata))==8
assert len(list((ROOT/'Preview').glob('*.png')))==19

# Include all referenced repository documentation so relative README links also work offline.
paths={ROOT/'README.md',ROOT/'README_JA.md',ROOT/'UNITY_MCP_HANDOFF.md'}
for directory in ['Documentation','CAD','SourceDesign']:
    paths.update(p for p in (ROOT/directory).rglob('*') if p.is_file())
paths.update((ROOT/'Preview').glob('*.png'));paths.update((ROOT/'Preview/Design').glob('*.png'))
paths.update([ROOT/'Preview/The_Commons_Compact.gltf',ROOT/'Preview/The_Commons_Compact.bin'])
# glTF references the original texture set; include these to keep the preview usable.
paths.update((ROOT/'Unity/Assets/TheCommons/Textures').glob('*.png'))
paths.update([ROOT/'Blender/build_design_atlas.py',ROOT/'Blender/package_documentation.py'])
# Documentation describes generated scene files, not a standalone editable Blender scene.
bundle=OUT/'The_Commons_v0.6.0_Docs_r1.zip'
hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    def add(name,data):
        entry=zipfile.ZipInfo(name,date_time=(2026,10,7,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o100644<<16;z.writestr(entry,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=7)
    for name in hashes:add('The_Commons_v0.6.0_Docs_r1/'+name,(ROOT/name).read_bytes())
    add('The_Commons_v0.6.0_Docs_r1/SHA256SUMS-DOCS.txt',''.join(v+'  '+k+'\n' for k,v in hashes.items()).encode())
with zipfile.ZipFile(bundle) as z:
    assert len(z.namelist())==len(hashes)+1
    for name,digest in hashes.items():assert hashlib.sha256(z.read('The_Commons_v0.6.0_Docs_r1/'+name)).hexdigest()==digest
assets=[ROOT/p for p in CFG['append_assets']]+[bundle]
report={'passed':True,'model_version':'0.6.0','documentation_revision':'r1','model_commit':MODEL,
        'documentation_commit':run('git','rev-parse','HEAD').strip(),'model_unchanged':True,
        'pdf_pages':8,'plan_sheets':5,'design_sheets':3,'original_screenshots':19,
        'checks':['model_unchanged','atlas_input_hashes','8_PNG_CRC_and_dimensions','5_SVG_XML','8_PDF_pages','README_links','exact_zip_content'],
        'bundle_files':len(hashes),'assets':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in assets}}
report_path=OUT/'documentation-validation-v0.6.0-r1.json';report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assets.append(report_path)
checksum=OUT/'SHA256SUMS-v0.6.0-docs-r1.txt';checksum.write_text(''.join(sha(p)+'  '+p.name+'\n' for p in assets));assets.append(checksum)
print(json.dumps(report,ensure_ascii=False,indent=2))

if '--publish' in sys.argv:
    repo='Xenoah/vrcworld_tech-tech-cafe'
    current=json.loads(run('gh','api','repos/'+repo+'/releases/tags/v0.6.0'))
    tag=json.loads(run('gh','api','repos/'+repo+'/git/ref/tags/v0.6.0'))
    assert tag['object']['sha']==MODEL and not current['draft'] and not current.get('immutable',False)
    existing={x['name']:x for x in current['assets']}
    for original in CFG['original_assets']:
        asset=existing[original['name']];assert asset['digest']==original['digest'] and asset['size']==original['size']
    missing=[]
    for p in assets:
        if p.name in existing:
            assert existing[p.name]['digest']=='sha256:'+sha(p),f'Existing appendix differs; refusing replacement: {p.name}'
        else:missing.append(str(p))
    if missing:run('gh','release','upload','v0.6.0',*missing,'--repo',repo)
    run('gh','release','edit','v0.6.0','--repo',repo,'--notes-file',str(ROOT/CFG['notes_path']))
    published=json.loads(run('gh','api','repos/'+repo+'/releases/tags/v0.6.0'))
    assert published['body'].strip()==notes.strip()
    remote={x['name']:x for x in published['assets']}
    for p in assets:assert remote[p.name]['digest']=='sha256:'+sha(p)
    for original in CFG['original_assets']:assert remote[original['name']]['digest']==original['digest']
    print('Published documentation appendix; original model tag and all original asset digests preserved.')
