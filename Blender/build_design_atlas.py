"""Create the v0.6.0 design atlas from release manifests and actual-model renders.

Python: reportlab, Pillow, numpy, ezdxf. System: pdftoppm, pdftocairo.
No Blender model, Unity asset or existing screenshot is modified.
"""
from pathlib import Path
import json, math, hashlib, subprocess, tempfile, shutil, os
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from fontTools.ttLib import TTFont as FontToolsFont
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Documentation/Design';PNG=ROOT/'Preview/Design';SVG=ROOT/'CAD/Plans'
for d in [OUT,PNG,SVG]:d.mkdir(parents=True,exist_ok=True)
M=json.loads((ROOT/'Documentation/model_manifest.json').read_text());K=M['kart'];F=M['fpv']
G=json.loads((ROOT/'Documentation/geometry_report.json').read_text())
KV=json.loads((ROOT/'Documentation/kart_validation.json').read_text())
assert M['version']==K['version']=='0.6.0'
assert KV['passed'] and all(c['pass'] for c in json.loads((ROOT/'Documentation/validation_report.json').read_text())['checks'])
W,H=1190.551,841.890 # A3 landscape, points
PAPER='#F5F4EF';INK='#16263A';MUTED='#5C6B7B';RULE='#CAD3D8';TEAL='#117F8C'
BLUE='#237DE0';VIOLET='#9261C9';CYAN='#13ACB5';GOLD='#B47C25';PINK='#C95487'
LEVEL_COLORS=[BLUE,VIOLET,CYAN]
pdfmetrics.registerFont(TTFont('InterDoc',str(ROOT/'Blender/Fonts/DejaVuSans.ttf')))
TMP=tempfile.TemporaryDirectory(prefix='commons-design-');T=Path(TMP.name)
(T/'output/pdf').mkdir(parents=True)
# Embed a compact TrueType subset so Japanese works without viewer font fallback.
font_path=Path(os.environ.get('COMMONS_JAPANESE_FONT',str(Path.home()/'.local/share/fonts/NotoSansCJKjp-Regular.otf')))
if not font_path.exists():raise FileNotFoundError('Install Noto Sans CJK JP or set font_path to its OpenType file.')
otf=FontToolsFont(font_path)
subset_chars=Path(__file__).read_text()+''.join(chr(i) for i in range(32,127))
sub=subset.Subsetter();sub.populate(text=subset_chars);sub.subset(otf)
glyphs=otf.getGlyphSet();order=otf.getGlyphOrder();glyf={}
for name in order:
    pen=TTGlyphPen(None);glyphs[name].draw(Cu2QuPen(pen,1.0,reverse_direction=True));glyf[name]=pen.glyph()
fb=FontBuilder(otf['head'].unitsPerEm,isTTF=True);fb.setupGlyphOrder(order);fb.setupCharacterMap(otf.getBestCmap())
fb.setupGlyf(glyf);fb.setupHorizontalMetrics(otf['hmtx'].metrics)
fb.setupHorizontalHeader(ascent=otf['hhea'].ascent,descent=otf['hhea'].descent)
fb.setupNameTable({'familyName':'Commons Noto JP Subset','styleName':'Regular','uniqueFontIdentifier':'CommonsNotoJPSubset','fullName':'Commons Noto JP Subset','psName':'CommonsNotoJPSubset'})
fb.setupOS2(sTypoAscender=otf['OS/2'].sTypoAscender,sTypoDescender=otf['OS/2'].sTypoDescender,usWinAscent=otf['OS/2'].usWinAscent,usWinDescent=otf['OS/2'].usWinDescent)
fb.setupPost();fb.setupMaxp();fb.save(T/'NotoJP.ttf')
pdfmetrics.registerFont(TTFont('NotoJP',str(T/'NotoJP.ttf')))

pdf=T/'output/pdf/The_Commons_v0.6.0_Design_Atlas.pdf'
C=canvas.Canvas(str(pdf),pagesize=(W,H),pageCompression=1,invariant=1)
C.setTitle('The Commons v0.6.0 - Plans and Design Atlas');C.setAuthor('Xenoah / The Commons')
SHEETS=[]

def txt(x,y,s,size=12,color=INK,align='left',jp=False):
    C.setFillColor(HexColor(color));C.setFont('NotoJP' if jp or any(ord(a)>127 for a in s) else 'InterDoc',size)
    getattr(C,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x,y,s)
def line(x1,y1,x2,y2,color=RULE,width=.7,dash=None):
    C.setStrokeColor(HexColor(color));C.setLineWidth(width);C.setDash(dash or []);C.line(x1,y1,x2,y2);C.setDash([])
def rect(x,y,w,h,fill=None,stroke=RULE,width=.7):
    C.setLineWidth(width)
    if fill:C.setFillColor(HexColor(fill))
    if stroke:C.setStrokeColor(HexColor(stroke))
    C.rect(x,y,w,h,fill=int(fill is not None),stroke=int(stroke is not None))
def poly(points,fill=None,stroke=INK,width=.7,close=True):
    if len(points)<2:return
    p=C.beginPath();p.moveTo(*points[0])
    for v in points[1:]:p.lineTo(*v)
    if close:p.close()
    if fill:C.setFillColor(HexColor(fill))
    if stroke:C.setStrokeColor(HexColor(stroke))
    C.setLineWidth(width);C.drawPath(p,fill=int(fill is not None),stroke=int(stroke is not None))
def dot(x,y,r=3,fill=TEAL,stroke=None):
    if fill:C.setFillColor(HexColor(fill))
    if stroke:C.setStrokeColor(HexColor(stroke))
    C.circle(x,y,r,fill=int(fill is not None),stroke=int(stroke is not None))
def arrow(a,b,color=TEAL,width=1.3,size=5):
    line(*a,*b,color,width);v=np.array(b)-a;v=v/max(np.linalg.norm(v),1e-6);n=np.array([-v[1],v[0]])
    poly([b,np.array(b)-v*size+n*size*.4,np.array(b)-v*size-n*size*.4],color,None)
def page(code,title,sub,filename,dark=False):
    SHEETS.append(dict(code=code,title=title,file=filename,kind='design board' if dark else 'dimensioned plan'))
    bg='#0B1322' if dark else PAPER;fg='#E8EFF5' if dark else INK
    rect(0,0,W,H,bg,None);rect(44,H-94,52,50,TEAL,None);txt(70,H-75,code,14,'#FFFFFF','center')
    txt(116,H-64,'THE COMMONS  /  '+title,25,fg);txt(116,H-91,sub,11,'#9CAFC1' if dark else MUTED)
    line(44,H-119,W-44,H-119,'#2D4056' if dark else RULE)
    txt(44,24,'v0.6.0  |  DOCUMENTATION R1  |  2026-10-07  |  A3',8,'#9CAFC1' if dark else MUTED)
    txt(W-44,24,f'{len(SHEETS):02d} / 08   -   Unity / VRChat runtime not validated',8,'#9CAFC1' if dark else MUTED,'right')
def end():C.showPage()
def note(x,y,title,rows,width=330,dark=False):
    fg='#E8EFF5' if dark else INK;sub='#B8C7D4' if dark else MUTED
    txt(x,y,title,13,fg)
    for i,s in enumerate(rows):txt(x,y-22-i*18,s,10,sub)
def label(x,y,s,color=INK,size=10):
    font='NotoJP' if any(ord(a)>127 for a in s) else 'InterDoc';w=pdfmetrics.stringWidth(s,font,size)+10
    rect(x-w/2,y-4,w,size+8,PAPER,None);txt(x,y,s,size,color,'center')
def mapping(box,bounds):
    x,y,w,h=box;x0,y0,x1,y1=bounds;s=min(w/(x1-x0),h/(y1-y0));ox=x+(w-(x1-x0)*s)/2-x0*s;oy=y+(h-(y1-y0)*s)/2-y0*s
    return lambda a,b:(ox+a*s,oy+b*s),s
def grid(f,bounds,step):
    x0,y0,x1,y1=bounds
    for x in np.arange(math.ceil(x0/step)*step,x1+.01,step):line(*f(x,y0),*f(x,y1),'#E0E5E7',.35)
    for y in np.arange(math.ceil(y0/step)*step,y1+.01,step):line(*f(x0,y),*f(x1,y),'#E0E5E7',.35)
def dim(f,a,b,offset,text):
    a=np.array(f(*a));b=np.array(f(*b));v=b-a;n=np.array([-v[1],v[0]])/np.linalg.norm(v);aa=a+n*offset;bb=b+n*offset
    line(*(a+n*3),*(aa+n*4),MUTED,.5);line(*(b+n*3),*(bb+n*4),MUTED,.5);line(*aa,*bb,MUTED,.65)
    for p in [aa,bb]:line(*(p+np.array([-3,-3])),*(p+np.array([3,3])),MUTED,.7)
    p=(aa+bb)/2+n*6;label(*p,text,MUTED,10)
def scale_bar(x,y,s,length):
    for i in range(4):rect(x+i*length*s/4,y,length*s/4,5,INK if i%2==0 else PAPER,INK,.5)
    txt(x,y-15,'0',9,MUTED);txt(x+length*s,y-15,f'{length:g} m',9,MUTED,'right')
def north(x,y):
    arrow((x,y),(x,y+25),INK,1,5);txt(x,y+34,'+Z',9,INK,'center')
def bpoly(c):
    x,y,z=c['position'];sx,sy,sz=c['size'];a=c.get('rotation',[0,0,0])[2]
    return [(x+dx*math.cos(a)-dy*math.sin(a),y+dx*math.sin(a)+dy*math.cos(a)) for dx,dy in [(-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2)]]
def boxes(f,group,height=None,fill='#D8DFDF'):
    for c in M['colliders']:
        if c['kind']!='box' or not group(c):continue
        if height is not None and not c['position'][2]-c['size'][2]/2<height<c['position'][2]+c['size'][2]/2:continue
        poly([f(*p) for p in bpoly(c)],fill,INK,.6)
def photo(name,x,y,w,h):
    p=T/(name+'.jpg')
    if not p.exists():
        im=Image.open(ROOT/'Preview'/f'{name}.png').convert('RGB');im.thumbnail((1600,1200));im.save(p,quality=92,subsampling=0)
    C.drawImage(str(p),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c')

# A01 - three separately positioned areas in the actual horizontal coordinates.
page('A01','WORLD LAYOUT','配置図 / Unity水平座標 X・Z [m]、高さはY。破線はワープ関係であり歩行通路ではありません。','01_World_Layout')
f,s=mapping((83,235,1025,445),(-76,-24,340,175));grid(f,(-70,0,335,160),20)
for x,y,w,h,col,name in [(-64,0,36,26,TEAL,'VECTOR'),(0,0,28,18,GOLD,'COMMONS'),(180,0,148,160,BLUE,'APEX')]:
    poly([f(x,y),f(x+w,y),f(x+w,y+h),f(x,y+h)],'#E6EBEA',col,1.7)
    tx,ty=f(x+w/2,y+h+5);txt(tx,ty,name,12,col,'center')
P=np.array(K['centerline']);poly([f(*v[:2]) for v in P],None,BLUE,1,True)
for source,target in [(F['portals'][0]['position'],F['portals'][0]['destination']),(K['portals'][0]['position'],K['portals'][0]['destination'])]:
    a=f(*source[:2]);b=f(*target[:2]);line(*a,*b,TEAL,1.2,[5,4]);dot(*a,3);dot(*b,3)
txt(105,248,'CAFE <-> FPV / KART',10,TEAL);scale_bar(810,240,s,100);north(1100,620)
note(44,185,'01  THE COMMONS',['カフェ / バー / 発表 / DJ / Quiet','28 × 18 m / 1F 0.00、2F +4.80 m','Unity原点 (0, 0, 0) / 生成定員32人'])
note(410,185,'02  VECTOR / FPV',['屋内飛行・操縦・観戦を分離','36 × 26 × 8 m / ゲート8基','Unity原点 (-64, 0, 0) / VRC+を利用'])
note(775,185,'03  APEX / KART',['オリジナル3層・34コーナー','148 × 160 m / 約1.269 km','Unity原点 (180, 0, 0) / CVS2を別途導入'])
txt(44,63,'座標の変換: Blender (X, Y, Z) → Unity (X, Z, Y)。図面の上方向 +Z は地理的な北を意味しません。',10,MUTED)
end()


# A02 - slabs/walls from collider records, seat symbols from real anchor records.
page('A02','CAFE FLOOR PLANS','カフェ平面図 / 実装の床・壁・カウンター・階段を使用。丸は着席アンカーで、家具外形ではありません。','02_Cafe_Floor_Plans')
for floor,x in [(0,66),(4.8,628)]:
    f,s=mapping((x,293,480,364),(-1,-1,29,19));grid(f,(0,0,28,18),2)
    poly([f(0,0),f(28,0),f(28,18),f(0,18)],'#E1E5E5' if floor else '#EDEAE2',INK,1.2)
    if floor:
        boxes(f,lambda c:c['group']=='ARCH_Mezzanine' and abs(c['position'][2]+c['size'][2]/2-4.8)<.001,fill='#FFFDF8')
    boxes(f,lambda c:c['group']=='ARCH_Shell' and c['name']!='COL_Ground',floor+1,fill='#394958')
    boxes(f,lambda c:c['group']==('FURN_QuietRoom' if floor else 'FURN_Bar'),floor+.8,fill='#C2AC89' if not floor else '#394958')
    if not floor:boxes(f,lambda c:c['group']=='AV_BackOfHouse',1.5,fill='#394958')
    for c in M['colliders']:
        if c['kind']=='ramp' and c['group']=='ARCH_Stairs':
            vs=np.array(c['vertices']);lo=vs.min(0);hi=vs.max(0);poly([f(*v[:2]) for v in vs],'#D7DDD8',MUTED,.5)
            count=28 if 'East' in c['name'] else 25
            for yy in np.linspace(lo[1],hi[1],count+1):line(*f(lo[0],yy),*f(hi[0],yy),MUTED,.4)
            arrow(f((lo[0]+hi[0])/2,lo[1]+.4),f((lo[0]+hi[0])/2,hi[1]-.4),TEAL,.9,4)
    for a in M['seat_anchors']:
        if a['group'].startswith('FPV_') or a['group']=='MODE_Academic':continue
        if abs(a['position'][2]-(floor+.52))<.01:dot(*f(*a['position'][:2]),2.5,GOLD)
    if not floor:
        dot(*f(14,13.2),2.4*s,'#DCC8A7',GOLD);label(*f(14,13.2),'STAGE',GOLD,10)
        for px,py,t in [(4,10,'BAR'),(4,2.4,'CAFE'),(14,6.9,'LOUNGE'),(25,10.8,'GALLERY'),(24.6,4.2,'NOOK'),(24,16.9,'AV')]:label(*f(px,py),t,INK,9)
        line(*f(10.45,16.83),*f(17.55,16.83),TEAL,3)
        arrow(f(14,-.8),f(14,1.0),TEAL);txt(*f(14,-1.4),'ENTRY',9,TEAL,'center')
        for p,t in [(F['portals'][0]['position'],'F'),(K['portals'][0]['position'],'K')]:dot(*f(*p[:2]),7,TEAL);txt(f(*p[:2])[0],f(*p[:2])[1]-3,t,8,'#FFFFFF','center')
    else:
        for px,py,t in [(3.9,10.5,'ORBIT CAFE'),(14,13.9,'RELAY / DJ'),(24.6,12.9,'HORIZON'),(24,5,'ARCHIVE'),(14,3.7,'SOUTH BRIDGE'),(14,16.4,'NORTH BRIDGE'),(14,9,'VOID')]:label(*f(px,py),t,INK if t!='VOID' else MUTED,9)
        line(*f(11.16,17.315),*f(16.84,17.315),TEAL,3)
    dim(f,(0,18),(28,18),25,'28.00 m');dim(f,(0,0),(0,18),26,'18.00 m')
    txt(x,684,('1F / +0.00 m' if not floor else '2F / +4.80 m'),18,TEAL);scale_bar(x+15,281,s,5);north(x+459,662)
note(52,217,'1F / 集まる・発表する',['中央の円形ステージ: 直径4.80 m、高さ0.25 m','主画面 7.10 × 4.00 m / ポスター6面 / 展示台4台','F: FPVワープ、K: カートワープ。上階へは階段とポータル。'])
note(617,217,'2F / 話す・聴く・休む',['西カフェ、吊り下げDJ、東テラス、Quiet Roomを接続','上階補助画面 5.68 × 3.20 m / 開放床端の手すり1.05 m','東階段28段・36.44°、西階段25段・48.14°、各幅1.50 m'])
txt(52,91,'着席: 常設34 + Lounge 12 または Academic 24。別途FPV 7。図はLounge配置。バーの11スツールは装飾です。',11,INK)
txt(52,68,'床の灰色部分は吹抜け・床なし。元のゾーニング矩形ではなく実装の床開口・接続部を示します。西階段脇に代替ポータル。',10,MUTED)
end()

# A03 - gate positions and headings are taken directly from the FPV manifest.
page('A03','VECTOR / FPV PLAN','飛行エリア・操縦席・観戦席の平面図 / 破線はゲート中心を結ぶ案内線。実機の飛行軌跡ではありません。','03_FPV_Floor_Plan')
f,s=mapping((75,210,704,451),(-1,-1,37,27));grid(f,(0,0,36,26),2)
poly([f(0,0),f(36,0),f(36,26),f(0,26)],'#E5ECEB',INK,1.4)
for bounds,color in [(F['flight_bounds_local'],'#DAE9E8'),(F['pilot_bounds_local'],'#E6D7BF'),(F['spectator_bounds_local'],'#DCD5E9')]:
    x0,y0,x1,y1=bounds;poly([f(x0,y0),f(x1,y0),f(x1,y1),f(x0,y1)],color,None)
centers=[g['center'][:2] for g in F['gates']]
for a,b in zip(centers,centers[1:]+centers[:1]):line(*f(*a),*f(*b),TEAL,.8,[4,4]);arrow(f(*(np.array(a)*.45+np.array(b)*.55)),f(*(np.array(a)*.35+np.array(b)*.65)),TEAL,.8,5)
for g in F['gates']:
    p=np.array(g['center'][:2]);d=np.array(g['direction']);side=np.array([-d[1],d[0]]);color={'cyan':TEAL,'amber':GOLD,'lime':'#649034'}[g['sector']]
    line(*f(*(p-side*1.6)),*f(*(p+side*1.6)),color,4);arrow(f(*(p-d*1.2)),f(*(p+d*1.2)),color,1,5)
    label(*f(*(p+side*2.3)),str(g['id']).zfill(2),color,11)
for a in M['seat_anchors']:
    if a['group'].startswith('FPV_'):dot(*f(a['position'][0]+64,a['position'][1]),4,GOLD)
label(*f(10.5,2.2),'PILOT / 4',INK,11);label(*f(28.5,2.2),'SPECTATOR / 3',INK,10)
label(*f(21,3),'WALK',TEAL,9);label(*f(18,16),'FLIGHT / 639.2 m²',TEAL,12)
dim(f,(0,26),(36,26),26,'36.00 m');dim(f,(0,0),(0,26),26,'26.00 m');scale_bar(94,183,s,5);north(744,657)
note(825,667,'VECTOR / Indoor FPV',['天井高 8.00 m / 屋内フロア936 m²','飛行範囲 34.00 × 18.80 m','ゲート内寸 3.20 × 3.00 m','フレーム厚 0.18 m / ゲート8基'])
txt(825,548,'GATE    中心高 / 開口の下端 - 上端',10,INK)
for i,g in enumerate(F['gates']):
    txt(825,523-i*27,f"{g['id']:02d}       {g['center'][2]:.2f} m       {g['opening_min_z']:.2f} - {g['opening_max_z']:.2f} m",10,MUTED)
note(825,281,'利用と確認',['VRC+ Camera Droneを使用','独自操縦・レース計時は同梱なし','カフェとRETURNで往復','操縦感・PC/Quest性能は実機確認'])
txt(77,120,'ゲート番号・色・向き・中心高を設計JSONから取得。飛行エリアは南側の操縦・観戦スペースと分離。',11,INK)
txt(77,94,'図の丸は7か所の着席アンカー。中央の練習台や照明等の装飾は省略しています。寸法はメートル。',10,MUTED)
end()

# A04 - plan view of the original three-dimensional sampled course.
LOCAL=P.copy();LOCAL[:,0]-=K['origin'][0]
Z=np.array(K['levels']);tang=np.array(K['tangents']);norm=np.c_[-tang[:,1],tang[:,0]]
N=len(P);D=np.array(K['stations'])
def level(z):return int(np.argmin(abs(Z-z)))
def roads(f,s,selected=None):
    order=sorted(range(N),key=lambda i:(P[i,2]+P[(i+1)%N,2])/2)
    for i in order:
        j=(i+1)%N;a,b=LOCAL[i],LOCAL[j];z=(a[2]+b[2])/2
        flat=abs(a[2]-b[2])<1e-6 and min(abs(Z-z))<1e-5
        def quad(half):return [f(*(a[:2]-norm[i]*half)),f(*(b[:2]-norm[j]*half)),f(*(b[:2]+norm[j]*half)),f(*(a[:2]+norm[i]*half))]
        if selected is None:
            color=LEVEL_COLORS[level(z)] if flat else GOLD
            poly(quad(3.25),PAPER,PAPER,.15);poly(quad(2.6),color,color,.15)
        elif flat and abs(z-selected)<1e-5:
            poly(quad(2.6),LEVEL_COLORS[level(z)],LEVEL_COLORS[level(z)],.15)

page('A04','APEX / COURSE PLAN','カート総合平面図 / 3次元中心線から走行幅5.2 mを投影。立体交差は高い走路を上に描画。','04_Kart_Overall_Plan')
f,s=mapping((89,170,570,506),(-5,-3,153,163));grid(f,(0,0,148,160),10)
poly([f(0,0),f(148,0),f(148,160),f(0,160)],'#E4E7E5',INK,1.2)
ff=lambda x,y:f(x-K['origin'][0],y)
boxes(ff,lambda c:c['group']=='KART_Pits' and c['name'] in ['COL_KART_VisitorDeck','COL_KART_GrandstandTier'],fill='#CAD5D4')
ids=K['pit_indices'];pitpoly=[LOCAL[i,:2]-norm[i]*13.4 for i in ids]+[LOCAL[i,:2]-norm[i]*3.25 for i in reversed(ids)]
poly([f(*p) for p in pitpoly],'#D8C6A6',GOLD,.5)
roads(f,s)
for i in range(0,N,110):
    p=LOCAL[i,:2];arrow(f(*(p-tang[i]*1.5)),f(*(p+tang[i]*1.5)),INK,.7,4)
for a in K['vehicle_anchors']:dot(*ff(*a['position'][:2]),2.5,INK)
start=ids[-1];p=LOCAL[start,:2];line(*f(*(p-norm[start]*2.6)),*f(*(p+norm[start]*2.6)),INK,2.3)
for xy,t,col in [((62,35),'PIT / 6 BAYS',GOLD),((89,82),'01 / REACTOR',BLUE),((72,132),'02 / CROSSFIRE',VIOLET),((88,100),'03 / SKYLINE',CYAN)]:label(*f(*xy),t,col,8)
arrival=K['portals'][0]['destination'];dot(*ff(*arrival[:2]),4,TEAL)
dim(f,(0,160),(148,160),21,'148.00 m');dim(f,(0,0),(0,160),24,'160.00 m');scale_bar(112,137,s,20);north(653,650)
note(727,671,'NEON SWITCHYARD',['走路全長 1,268.83 m / 円弧コーナー34','幅 5.20 m / 構造デッキ幅 6.50 m','最小中心旋回半径 6.00 m','独自設計。参考写真のコースを複製していません。'])
for i,(name,h) in enumerate(zip(['REACTOR','CROSSFIRE','SKYLINE'],Z)):
    rect(727,520-i*33,15,15,LEVEL_COLORS[i],None);txt(754,523-i*33,f'{name} / +{h:.2f} m',12,INK)
rect(727,421,15,15,GOLD,None);txt(754,424,'RAMPS / 高さを変える接続4本',12,INK)
note(727,372,'高さ・構造',['壁高15.50 m / ガード高0.75 m','デッキ厚0.40 m / 支柱109本','最大勾配11.66% / 橋下面クリアランス3.80 m'])
note(727,269,'ピットと観戦',['CVS2用の空の配置ガイド6か所','ピット両端の歩行動線 / 3段の観戦席','カフェ往復ワープ / 時間操作パネル'])
txt(91,87,'色は高さを識別する図面用表示。金はスロープ。屋根・外壁照明・タイヤ等は省略。全体の実景はD03を参照。',10,MUTED)
txt(91,63,'検査値は幾何形状に対するものです。車体幅・車高・最小旋回・速度・同期は、導入したCVS2車両で確認してください。',10,MUTED)
end()

# A05 - isolated level plans plus the complete longitudinal profile.
page('A05','KART LEVELS + PROFILE','層別平面・縦断図 / 各層の平坦区間を色分け。灰色は他層の中心線、金の破線はスロープ。','05_Kart_Levels_Profile')
for k,z in enumerate(Z):
    x=52+k*371;f,s=mapping((x,375,339,300),(-7,-3,155,165))
    poly([f(0,0),f(148,0),f(148,160),f(0,160)],None,RULE,.8)
    poly([f(*p[:2]) for p in LOCAL],None,'#CDD5D6',.7)
    roads(f,s,float(z))
    for i in range(N):
        j=(i+1)%N
        if abs(P[i,2]-P[j,2])>1e-6 and i%5<3:line(*f(*LOCAL[i,:2]),*f(*LOCAL[j,:2]),GOLD,1)
    txt(x,695,f'{k+1:02d} / {['REACTOR','CROSSFIRE','SKYLINE'][k]}',16,LEVEL_COLORS[k])
    txt(x,351,f'路面 +{z:.2f} m',12,INK);scale_bar(x+204,354,s,40)
line(44,315,W-44,315)
txt(65,288,'LONGITUDINAL PROFILE / 全周の高低差',15,INK)
f,s=mapping((85,109,704,146),(0,0,K['length_m'],10))
# Separate X/Y scales make the height changes legible; explicitly not an equal-scale section.
profile=lambda station,height:(85+704*station/K['length_m'],112+14.5*height)
for z in Z:
    line(*profile(0,z),*profile(K['length_m'],z),RULE,.7);txt(77,profile(0,z)[1]-3,f'{z:.2f}',9,MUTED,'right')
pts=[profile(float(d),float(z)) for d,z in zip(D,P[:,2])]+[profile(K['length_m'],P[0,2])]
poly(pts,None,TEAL,2,False)
for d in [0,200,400,600,800,1000,K['length_m']]:
    x,_=profile(d,0);line(x,109,x,105,MUTED);txt(x,89,f'{d:.0f}',9,MUTED,'center')
txt(438,65,'走行距離 [m] / 高さ [m]。縦軸を拡大して表示。最大勾配11.66%。',10,MUTED,'center')
txt(881,286,'標準断面 / 模式図',13,INK)
for z in Z:
    y=110+z*15;rect(890,y-.4*15,130,.4*15,LEVEL_COLORS[level(z)],None);txt(879,y-3,f'+{z:.2f}',9,MUTED,'right')
    line(891,y,891,y+.75*15,INK,2);line(1019,y,1019,y+.75*15,INK,2)
line(1040,110+.35*15,1040,110+(4.55-.4)*15,INK,.7)
for y in [110+.35*15,110+(4.55-.4)*15]:line(1036,y,1044,y,INK,.7)
txt(1052,140,'3.80 m',11,INK);txt(890,85,'デッキ0.40 m / ガード0.75 m',10,MUTED)
end()

# D01-D03 - document composition of real renders, not generated concept art.
DESIGNS=[
 ('D01','CAFE / WARM INDUSTRIAL','カフェのデザインシート / 暖色の木・真鍮と、黒皮鋼・青緑の光。','06_Cafe_Design',
  ['01_Entrance_160cm','07_Relay_Detail','08_BarLabels_Detail'],
  ['01 / 入口から中央ステージ','02 / RELAYのDJ機材','03 / バーのラベル'],
  [('SPACE',['吹抜けを介して1Fの会話と2Fの滞在をつなぐ。','発表時は中央を24席に変更。Quiet Roomは東側。']),
   ('DETAIL',['2デッキ・4chの装飾DJ機材、93本・6種ラベル。','オーク・左官・テラゾー・鋼・真鍮・織布を使用。'])],
  [('#A77A4F','OAK'),('#B59A68','BRASS'),('#303B46','STEEL'),('#247E83','TEAL'),('#DF9350','AMBER')]),
 ('D02','VECTOR / READABLE FLIGHT','FPVのデザインシート / コースの色・番号・矢印と、操縦／観戦の分離。','07_FPV_Design',
  ['11_FPV_Course','10_FPV_Field'],
  ['01 / ゲートと飛行エリア','02 / 操縦・観戦側から'],
  [('SPACE',['36 × 26 × 8 m。飛行領域639.2 m²。','操縦4席と観戦3席を南側に配置。']),
   ('WAYFINDING',['3色の区間、8ゲート、番号と床の進行矢印。','VRC+のドローンを使用。実機の操縦感は未検証。'])],
  [('#0C8EA0','CYAN'),('#D5A143','AMBER'),('#9AAE51','LIME'),('#27313E','STEEL'),('#CED4D3','CONCRETE')]),
 ('D03','APEX / NEON SWITCHYARD','カートのデザインシート / 近い壁、連続する旋回、頭上の橋、青・紫・シアン。','08_Kart_Design',
  ['17_Kart_Overpass','16_Kart_Overview','20_Kart_UpperTechnical'],
  ['01 / 橋下の低い走行視点','02 / 全景・カットアウェイ','03 / 上層の旋回'],
  [('SPACE',['幅5.2 m、34コーナー、全長約1.269 km。','3層・連続スロープで次の旋回と橋下が迫る構成。']),
   ('LIGHT',['0.75 mのガードに上端・側面LED。黒い光沢路面。','屋内は固定色。眩しさはローカル設定で調整。'])],
  [('#143DE7','BLUE'),('#7752D9','VIOLET'),('#1BBDD6','CYAN'),('#C6518F','PINK'),('#161E2E','ASPHALT')])
]
for code,title,sub,file,names,captions,notes,palette in DESIGNS:
    page(code,title,sub,file,True)
    photo(names[0],44,226,724,453);txt(44,211,captions[0],10,'#B8C7D4')
    photo(names[1],802,466,343,214);txt(802,451,captions[1],10,'#B8C7D4')
    if len(names)>2:photo(names[2],802,226,343,214);txt(802,211,captions[2],10,'#B8C7D4')
    else:
        txt(816,414,'8 GATES / 3 SECTORS',18,'#E8EFF5')
        txt(816,377,'3.2 × 3.0 m の開口',14,'#B8C7D4')
        txt(816,346,'CYAN / AMBER / LIME',12,'#B8C7D4')
        txt(816,298,'区間色と番号で順路を示し、',12,'#B8C7D4')
        txt(816,276,'操縦・観戦場所から見渡せる。',12,'#B8C7D4')
    for k,(title,rows) in enumerate(notes):note(44+k*567,172,title,rows,dark=True)
    for k,(col,name) in enumerate(palette):
        x=44+k*153;rect(x,64,131,21,col,None);txt(x,50,name,8,'#B8C7D4')
    txt(829,77,'Actual model / Blender Cycles',10,'#B8C7D4')
    txt(829,57,'色見本はデザイン意図の概略。',9,'#9CAFC1')
    if code=='D03':txt(829,40,'全景のみ屋根・2面の壁・トラスを非表示。',8,'#9CAFC1')
    end()
C.save()
shutil.copy2(pdf,OUT/pdf.name)
# Rasterize the actual PDF layout so every preview agrees with the printed atlas.
subprocess.run(['pdftoppm','-scale-to','2400','-png',str(pdf),str(T/'page')],check=True)
for i,sheet in enumerate(SHEETS,1):
    source=next(T.glob(f'page-{i}.png'),None) or next(T.glob(f'page-{i:02d}.png'))
    shutil.copy2(source,PNG/(sheet['file']+'.png'))
    if i<=5:
        subprocess.run(['pdftocairo','-svg','-f',str(i),'-l',str(i),str(pdf),str(SVG/(sheet['file']+'.svg'))],check=True)
# Clean, separate DXFs in millimetres (the legacy implementation overlay contains all areas).
import ezdxf
cad=ezdxf.new('R2010');cad.units=4;ms=cad.modelspace()
for name,col in [('FLOOR_1F',8),('FLOOR_2F',4),('WALL',7),('STAIR',3),('FURNITURE',2),('SEAT_ANCHOR',30),('TEXT',7)]:cad.layers.new(name,dxfattribs={'color':col})
for floor,dx in [(0,0),(4.8,38000)]:
    for c in M['colliders']:
        if c['kind']=='box' and not c['group'].startswith(('KART_','FPV_','ENV_')):
            lo=c['position'][2]-c['size'][2]/2;hi=c['position'][2]+c['size'][2]/2
            floor_piece=abs(hi-floor)<.001
            if not floor_piece and not lo<floor+.8<hi:continue
            layer=('FLOOR_2F' if floor else 'FLOOR_1F') if floor_piece else 'WALL' if c['group'].startswith('ARCH_') or 'Wall' in c['name'] else 'FURNITURE'
            ms.add_lwpolyline([(x*1000+dx,y*1000) for x,y in bpoly(c)],close=True,dxfattribs={'layer':layer})
        elif c['kind']=='ramp' and c['group']=='ARCH_Stairs':
            ms.add_lwpolyline([(v[0]*1000+dx,v[1]*1000) for v in c['vertices']],close=True,dxfattribs={'layer':'STAIR'})
    for a in M['seat_anchors']:
        if a['group'].startswith('FPV_') or a['group']=='MODE_Academic' or abs(a['position'][2]-floor-.52)>.01:continue
        ms.add_circle((a['position'][0]*1000+dx,a['position'][1]*1000),150,dxfattribs={'layer':'SEAT_ANCHOR'})
    if not floor:ms.add_circle((14000,13200),2400,dxfattribs={'layer':'FURNITURE'})
    ms.add_text(f'CAFE / {"2F +4.800 m" if floor else "1F +0.000 m"} / LOUNGE / UNITS mm',dxfattribs={'height':500,'insert':(dx,19500),'layer':'TEXT'})
cad.saveas(ROOT/'CAD/The_Commons_Cafe_Floors_v06.dxf')
cad=ezdxf.new('R2010');cad.units=4;ms=cad.modelspace()
for name,col in [('BOUNDARY',7),('ZONES',8),('GATES',4),('ROUTE_GUIDE',3),('TEXT',2)]:cad.layers.new(name,dxfattribs={'color':col})
for b in [[0,0,36,26],F['flight_bounds_local'],F['pilot_bounds_local'],F['spectator_bounds_local']]:
    x0,y0,x1,y1=b;ms.add_lwpolyline([(x0*1000,y0*1000),(x1*1000,y0*1000),(x1*1000,y1*1000),(x0*1000,y1*1000)],close=True,dxfattribs={'layer':'BOUNDARY' if b[0]==0 else 'ZONES'})
ms.add_lwpolyline([(g['center'][0]*1000,g['center'][1]*1000) for g in F['gates']],close=True,dxfattribs={'layer':'ROUTE_GUIDE'})
for g in F['gates']:
    p=np.array(g['center'][:2]);d=np.array(g['direction']);n=np.array([-d[1],d[0]])
    ms.add_line(tuple((p-n*1.6)*1000),tuple((p+n*1.6)*1000),dxfattribs={'layer':'GATES'})
    ms.add_text(f"G{g['id']:02d} / CENTER +{g['center'][2]:.2f} m",dxfattribs={'height':300,'insert':tuple((p+n*2.4)*1000),'layer':'TEXT'})
ms.add_text('VECTOR / LOCAL X-Z / 36 x 26 m / UNITS mm',dxfattribs={'height':550,'insert':(0,28000),'layer':'TEXT'})
cad.saveas(ROOT/'CAD/VECTOR_FPV_Plan_v06.dxf')
inputs=['Documentation/model_manifest.json','Documentation/geometry_report.json','Documentation/kart_validation.json','SourceDesign/world_spec.json','SourceDesign/fpv_field.json','SourceDesign/kart_circuit.json']
images=sorted({n for d in DESIGNS for n in d[4]})
inputs += ['Preview/'+n+'.png' for n in images]
report={'model_version':'0.6.0','documentation_revision':1,'model_commit':'a77e3087fb76f50f59ee3ceb611a5c470e25e9d0',
        'scope':'Plans derive from actual collider / centerline / seat-anchor manifests. Furniture symbols are simplified. Design boards compose actual-model Blender renders; not Unity runtime or AI concept art.',
        'paper':'A3 landscape','sheets':SHEETS,'screenshots_reused':images,
        'inputs_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs}}
(OUT/'atlas_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pdf':str(OUT/pdf.name),'sheets':len(SHEETS),'pngs':len(SHEETS),'svg_plans':5,'new_dxf_plans':2},indent=2))
TMP.cleanup()
