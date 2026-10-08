"""Architectural background district. Run inside build_world.py.

Opaque glazing, four shared city materials, no textures, physics or realtime
lights. Shared window/crown geometry is retained on Quest at reduced density.
"""
group('ENV_City')
mat('MAT_CityStone',(.30,.37,.45),rough=.58,metal=.18)
mat('MAT_CityGlazing',(.055,.15,.22),rough=.22,metal=.55)
mat('MAT_CityWarm',(.95,.61,.29),rough=.4,emit=1.65)
mat('MAT_CityCool',(.14,.58,.80),rough=.36,emit=1.8)

def outline(name,x,y,z,w,d,material,th=.06):
 # One closed ring: 32 triangles instead of four intersecting 12-triangle
 # boxes. Keep every facade band while removing hidden corner faces.
 vs=[]
 for zz in [z-th/2,z+th/2]:
  for inset in [-th/2,th/2]:
   a=w/2-inset;b=d/2-inset
   vs.extend([(x-a,y-b,zz),(x+a,y-b,zz),(x+a,y+b,zz),(x-a,y+b,zz)])
 fs=[]
 for i in range(4):
  j=(i+1)%4
  fs.extend([(i,j,8+j,8+i),(4+j,4+i,12+i,12+j),
             (8+i,8+j,12+j,12+i),(i,4+i,4+j,j)])
 mesh(name,vs,fs,material)

def window(name,center,w,h,axis,material):
 x,y,z=center
 vs=[(x,y-w/2,z-h/2),(x,y+w/2,z-h/2),(x,y+w/2,z+h/2),(x,y-w/2,z+h/2)] if axis==0 else [(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)]
 mesh(name,vs,[(0,1,2,3)],material)

# Position/height are intentional: staggered masses, breathing room between
# towers, and a skyline visible through both east and new south glazing.
towers=[]
for row,(x,ys,heights) in enumerate([
 (40,[-20,-7,6,19,32,45],[25,32,39,28,35,24]),
 (55,[-24,-10,4,18,32,46],[36,44,55,40,49,34]),
 (72,[-22,-8,6,20,34,48],[43,52,62,46,57,39])]):
 for j,(y,h) in enumerate(zip(ys,heights)):
  towers.append((x,y,7.4+row*.8,8.0,h,(row+j)%3))
for j,(x,y,h) in enumerate([(2,-13,22),(14,-13,29),(26,-13,24),(-2,-28,34),(13,-28,42),(28,-30,37)]):
 towers.append((x,y,7.5,7.5,h,j%3))

CITY={'style':'Terraced glass-and-stone towers, illuminated crowns, roof gardens and two skybridges',
 'origin_z':-8,'background_only':True,'realtime_lights':0,
 'triangle_budget_pc':36000,'triangle_budget_quest':28000,'buildings':[],'skybridges':[]}
for i,(x,y,w,d,h,style) in enumerate(towers):
 base=-8;accent='MAT_CityCool' if style==1 else 'MAT_CityWarm'
 box('ENV_Podium',(x,y,base+1.4),(w+1.6,d+1.6,2.8),'MAT_CityStone')
 outline('ENV_PodiumCornice',x,y,base+2.86,w+1.7,d+1.7,accent,.085)
 bottom=base+2.9
 for level,(fraction,scale) in enumerate([(.50,1),(.29,.80),(.21,.60)]):
  height=(h-2.9)*fraction;ww=w*scale;dd=d*scale
  box('ENV_TowerGlazing',(x,y,bottom+height/2),(ww,dd,height),'MAT_CityGlazing')
  for xx in [x-ww/2,x+ww/2]:
   for yy in [y-dd/2,y+dd/2]:box('ENV_StonePier',(xx,yy,bottom+height/2),(.18,.18,height),'MAT_CityStone')
  # Sparse opaque window planes and floor bands, batched at export by material.
  for floor in range(max(1,int(height/2.6))):
   zz=bottom+.85+floor*2.6
   if zz+1>bottom+height:continue
   outline('ENV_FloorBand',x,y,zz-.65,ww+.04,dd+.04,'MAT_CityStone',.07)
   for side in [-1,1]:
    for col in range(3):
     if (i+floor+col+(1 if side>0 else 0))%5==0:continue
     window('ENV_LitWindow',(x+side*(ww/2+.015),y+(col-1)*dd*.27,zz),dd*.19,1.05,0,accent)
     window('ENV_LitWindow',(x+(col-1)*ww*.27,y+side*(dd/2+.015),zz),ww*.19,1.05,1,accent)
  top=bottom+height
  box('ENV_SetbackCornice',(x,y,top+.06),(ww+.55,dd+.55,.12),'MAT_CityStone')
  outline('ENV_SetbackLight',x,y,top+.15,ww+.38,dd+.38,accent,.06)
  if level<2:
   for side in [-1,1]:
    box('ENV_RoofPlanter',(x+side*ww*.40,y,top+.30),(.45,dd*.65,.30),'MAT_CityStone')
    box('ENV_RoofGarden',(x+side*ww*.40,y,top+.53),(.48,dd*.64,.30),'MAT_LeafLight')
  bottom=top
 crown_z=base+h
 for dz,sc in [(.4,.63),(1.35,.54)]:outline('ENV_IlluminatedCrown',x,y,crown_z+dz,w*sc,d*sc,accent,.11)
 for xx in [-1,1]:
  for yy in [-1,1]:beam('ENV_CrownFin',(x+xx*w*.27,y+yy*d*.27,crown_z),(x+xx*w*.27,y+yy*d*.27,crown_z+1.45),.055,'MAT_Brass',6)
 if style==1:
  beam('ENV_CrownSpire',(x,y,crown_z),(x,y,crown_z+4),.07,'MAT_CityStone',8)
  cyl('ENV_SpireBeacon',(x,y,crown_z+4),.12,.22,'MAT_CityCool',8)
 CITY['buildings'].append({'id':i+1,'center':[x,y],'width':w,'depth':d,'height':h,'tiers':3,'roof_gardens':4})

for a,b,z in [((40,6),(55,4),10),((55,32),(72,34),15)]:
 # Two parallel beams form an architectural skybridge; visual backdrop only.
 av=Vector((a[0],a[1],z));bv=Vector((b[0],b[1],z));side=(bv-av).normalized().cross(Vector((0,0,1)))*.7
 for offset in [-1,1]:
  beam('ENV_SkybridgeDeck',av+side*offset,bv+side*offset,.20,'MAT_CityStone',4)
  beam('ENV_SkybridgeLight',av+side*offset+Vector((0,0,.65)),bv+side*offset+Vector((0,0,.65)),.04,'MAT_CityCool',6)
 for t in [.2,.4,.6,.8]:
  mid=av.lerp(bv,t)
  for sign in [-1,1]:beam('ENV_SkybridgePost',mid+side*sign,mid+side*sign+Vector((0,0,.68)),.035,'MAT_Brass',6)
 CITY['skybridges'].append({'from':list(a),'to':list(b),'z':z})
