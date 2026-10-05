"""Typeset exact demonstration slides/posters and synthesize original quiet loops.
AI material albedos are copied unmodified; no raster retouching is performed.
"""
from pathlib import Path
import json,math,wave,shutil
import numpy as np
from scipy.ndimage import gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'Unity/Assets/TheCommons'
FONT=str(ROOT/'Blender/Fonts/DejaVuSans.ttf');BOLD=str(ROOT/'Blender/Fonts/DejaVuSans-Bold.ttf')
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def text(d,p,s,n=28,c='#dfdfd2',b=False):d.text(p,s,font=font(n,b),fill=c)
slides=[('THE COMMONS','IDEAS TASTE BETTER TOGETHER.',['A shared room for curious people.','TALK  /  BUILD  /  SHARE']),('OPEN FORUM','15 MIN TALK  +  5 MIN Q&A',['One idea. One experiment. One question.','Continue the conversation at Anchor Bar.']),('COMMUNITY NOTES','KEEP THE ROOM COMFORTABLE',['Leave the center aisle open.','Quiet conversation: ARCHIVE / Level 2.','Local comfort controls are beside the entrance.']),('BUILD SOMETHING SMALL','SAME ROOM. DIFFERENT WORLDS.',['Posters and demos: OPEN LAB.','Observe, ask, try, compare.'])]
for i,(title,sub,body) in enumerate(slides):
 im=Image.new('RGB',(1600,900),'#101c24');d=ImageDraw.Draw(im)
 d.line((90,110,1510,110),fill='#bd8d53',width=3);text(d,(90,58),'THE COMMONS   /   COMPACT EDITION',24,'#ae906c')
 text(d,(90,236),title,68,b=True);text(d,(94,359),sub,32,'#57c5db')
 for j,s in enumerate(body):text(d,(94,508+j*65),s,29)
 text(d,(94,805),'FORUM   /   ANCHOR BAR   /   ORBIT CAFE   /   ARCHIVE',22,'#7a8f98')
 for k in range(3):d.ellipse((1180+k*36,470+k*22,1410+k*36,700+k*22),outline='#276272',width=2)
 im.save(A/'Media'/f'slide_{i}.png')
posters=[('01','SYSTEMS','Small parts. Shared purpose.','Observe a system before changing it.'),('02','SIGNALS','Find the structure in noise.','What can we measure?'),('03','ORBIT','Different paths. One room.','A place to remain curious.'),('04','MAKING','Start with one experiment.','Build, compare, and iterate.'),('05','CONVERSATION','Good questions travel.','A question can open a new direction.'),('06','OPEN DEMO','Bring your next prototype.','This panel is ready for your content.')]
for i,(num,title,sub,foot) in enumerate(posters):
 im=Image.new('RGB',(800,1280),'#14202a');d=ImageDraw.Draw(im)
 text(d,(55,55),'OPEN LAB / '+num,24,'#c8a16c');d.line((55,103,745,103),fill='#466576',width=2)
 text(d,(55,171),title,49 if len(title)<11 else 40,b=True);text(d,(55,260),sub,25,'#d6d6c8')
 if i%3==0:
  pts=[(140,550),(340,455),(620,575),(195,870),(440,850),(650,960)]
  for k,p in enumerate(pts):
   for q in pts[k+1:]:d.line((*p,*q),fill='#375a67',width=2)
   d.ellipse((p[0]-15,p[1]-15,p[0]+15,p[1]+15),fill='#55bdd2')
 elif i%3==1:
  for k in range(4):
   pts=[(70+x*2,570+k*85+int(math.sin(x*.033+k)*math.sin(x*.009)*70)) for x in range(330)]
   d.line(pts,fill=['#54b8d3','#b6905f','#698d8e','#d4cebc'][k],width=3)
 else:
  for k in range(7):d.ellipse((90+k*28,440+k*30,720-k*28,1050-k*30),outline='#55bad1' if k%2 else '#9e814f',width=3)
 text(d,(55,1140),foot,22);text(d,(55,1200),'THE COMMONS / REPLACEABLE POSTER',18,'#6d8592');im.save(A/'Media'/f'poster_{i}.png')
# Periodic signals, so the loop endpoints share phase. No licensed recordings.
sr=24000
def save_audio(name,data):
 data=np.clip(data,-.90,.90)
 with wave.open(str(A/'Audio'/f'{name}.wav'),'w') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((data*32767).astype('<i2').tobytes())
duration=60;n=int(sr*duration);t=np.arange(n)/sr
rng=np.random.default_rng(461)
noise=gaussian_filter1d(rng.normal(0,1,n),20,mode='wrap');noise/=np.std(noise)
room=.018*noise+.009*np.sin(2*np.pi*72*t)+.004*np.sin(2*np.pi*109*t)
save_audio('commons_roomtone',room)
drone=np.zeros(n)
for i,f in enumerate([146.8333,220,261.6333,329.6333]):
 f=round(f*duration)/duration;drone+=(.011+.006*np.sin(2*np.pi*t/duration+i))*np.sin(2*np.pi*f*t+i)
for i,start in enumerate(np.arange(0,duration,7.5)):
 tau=(t-start)%duration;env=np.exp(-tau/2.1)*(1-np.exp(-tau*35));f=[587.3333,440,523.2667,659.25][i%4];f=round(f*duration)/duration
 drone+=.025*env*np.sin(2*np.pi*f*t)
save_audio('commons_ambient',drone)
duration=40;n=int(sr*duration);t=np.arange(n)/sr;beat=.625;dj=np.zeros(n)
for k in range(64):
 tau=(t-k*beat)%duration;env=np.exp(-tau*22);kick=np.sin(2*np.pi*(47*tau+1.3*(1-np.exp(-tau*35))))*env;dj+=.18*kick
 if k%2: dj+=.023*gaussian_filter1d(rng.normal(0,1,n),.5,mode='wrap')*np.exp(-tau*35)
 f=[73.4167,73.4167,110,65.4][(k//4)%4];dj+=.038*np.sin(2*np.pi*f*tau)*np.exp(-tau*5)*(1-np.exp(-tau*80))
save_audio('commons_dj',dj)
# Convert only the manifest structure needed by Unity JsonUtility (no dictionaries/jagged arrays).
raw=json.loads((ROOT/'Documentation/model_manifest.json').read_text())
raw['materials']=[dict(name=n,**v) for n,v in raw['materials'].items()]
for c in raw['colliders']:
 if 'vertices' in c:c['vertices']=[v for row in c['vertices'] for v in row]
(A/'Data/world_manifest.json').write_text(json.dumps(raw,indent=2))
print('4 slides, 6 posters, 3 original audio loops, Unity manifest prepared')
