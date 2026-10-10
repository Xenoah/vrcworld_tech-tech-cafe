Shader "The Commons/View Jack"
{
 // Local-only full-view overlay. The mesh is a sphere that follows the local
 // head; directions are evaluated in head space, so both eyes agree and the
 // overlay reads as "on the visor" instead of a flat screen quad. Cameras
 // outside the sphere (mirrors, the VRChat photo camera, other players' views
 // of this client) collapse the mesh and never see it.
 Properties
 {
  _Warp("Warp tunnel",Range(0,1))=0
  _Glitch("Phase glitch",Range(0,1))=0
  _Scan("Holo scan",Range(0,1))=0
  _Stars("Orbit stars",Range(0,1))=0
  _Rain("Data rain",Range(0,1))=0
  _Fade("Fade",Range(0,1))=0
  _Tiny("Miniature",Range(0,1))=0
  _Dream("Warm dream",Range(0,1))=0
  _Pulse("Beat pulse",Range(0,1))=0
  _Comfort("Comfort vignette",Range(0,1))=0
  _Beat("Beat phase",Range(0,1))=0
  _Motion("Motion (0 = reduced)",Range(0,1))=0
  _FadeColor("Fade color",Color)=(0,0,0,1)
  _PulseColor("Pulse color",Color)=(.9,.2,.8,1)
  _AccentA("Accent A",Color)=(.05,.78,1,1)
  _AccentB("Accent B",Color)=(.82,.25,1,1)
 }
 SubShader
 {
  Tags {"Queue"="Overlay+100" "RenderType"="Transparent" "IgnoreProjector"="True" "DisableBatching"="True" "PreviewType"="Sphere"}
  Blend One OneMinusSrcAlpha
  ZWrite Off ZTest Always Cull Front
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #pragma target 3.0
   #include "UnityCG.cginc"
   half _Warp,_Glitch,_Scan,_Stars,_Rain,_Fade,_Tiny,_Dream,_Pulse,_Comfort,_Beat,_Motion;
   half4 _FadeColor,_PulseColor,_AccentA,_AccentB;
   struct appdata {float4 vertex:POSITION;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v2f {float4 pos:SV_POSITION;float3 dir:TEXCOORD0;float3 wdir:TEXCOORD1;UNITY_VERTEX_OUTPUT_STEREO};
   v2f vert(appdata v)
   {
    v2f o;UNITY_SETUP_INSTANCE_ID(v);UNITY_INITIALIZE_OUTPUT(v2f,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    float3 center=mul(unity_ObjectToWorld,float4(0,0,0,1)).xyz;
    float radius=length(unity_ObjectToWorld._m00_m10_m20)*.5;
    o.pos=UnityObjectToClipPos(v.vertex);
    // Degenerate every vertex for cameras that are not inside the head sphere.
    if(distance(_WorldSpaceCameraPos,center)>radius*.8)o.pos=float4(0,0,0,1);
    o.dir=v.vertex.xyz;
    o.wdir=mul((float3x3)unity_ObjectToWorld,v.vertex.xyz);
    return o;
   }
   // Sin-free hashes keep mobile GPUs stable.
   float hash11(float p){p=frac(p*.1031);p*=p+33.33;p*=p+p;return frac(p);}
   float hash21(float2 p){float3 q=frac(float3(p.xyx)*.1031);q+=dot(q,q.yzx+33.33);return frac((q.x+q.y)*q.z);}
   float hash31(float3 p){p=frac(p*.1031);p+=dot(p,p.zyx+31.32);return frac((p.x+p.y)*p.z);}
   float2 hash22(float2 p){float3 q=frac(float3(p.xyx)*float3(.1031,.1030,.0973));q+=dot(q,q.yzx+33.33);return frac((q.xx+q.yz)*q.zy);}
   void over(inout half4 acc,half3 c,half a){a=saturate(a);acc.rgb=c*a+acc.rgb*(1-a);acc.a=a+acc.a*(1-a);}
   half4 frag(v2f i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float3 d=normalize(i.dir);
    float3 w=normalize(i.wdir);
    float r=acos(clamp(d.z,-1,1))/1.5708;       // 0 at the centre of view, 1 at 90 degrees
    float2 p=d.xy/max(d.z,.12);                  // visor plane
    float phi=atan2(d.y,d.x)/6.28318+.5;
    float t=_Time.y*_Motion;
    half4 acc=half4(0,0,0,0);
    half3 add=0;
    if(_Warp>.001)
    {
     float lanes=96;
     float lane=floor(phi*lanes);
     float h=hash11(lane+7.3);
     float flow=frac(r*2.4-t*(1.1+h*1.7)+h*9.1);
     float streak=smoothstep(0,.06,flow)*(1-smoothstep(.06,.5,flow));
     streak*=smoothstep(.15,.85,1-abs(frac(phi*lanes)-.5)*2)*step(.52,h)*smoothstep(.12,.8,r);
     over(acc,half3(.004,.012,.035),smoothstep(.22,.78,r)*.6*_Warp);
     add+=lerp(_AccentA.rgb,_AccentB.rgb,h)*streak*1.7*_Warp;
     add+=_AccentA.rgb*exp(-r*r*36)*.45*_Warp;
    }
    if(_Glitch>.001)
    {
     float slot=floor(t*2.0);                     // pattern changes at most twice a second
     float band=floor(d.y*14+slot*3.7);
     float hb=hash11(band+slot*13.1);
     half3 g=hb>.88?_AccentB.rgb:_AccentA.rgb;
     float on=step(.74,hb);
     over(acc,g*.55,on*.28*_Glitch);
     add+=g*on*pow(.5+.5*sin(d.y*900),4)*.22*_Glitch;
     float hk=hash21(floor(p*float2(18,10)+slot));
     add+=half3(.6,.9,1)*step(.968,hk)*.45*_Glitch;
     over(acc,half3(0,0,0),smoothstep(.45,.85,r)*.35*_Glitch);
    }
    if(_Scan>.001)
    {
     add+=_AccentA.rgb*pow(.5+.5*sin(d.y*520),8)*.05*_Scan;
     float sweep=frac(t*.3)*2.6-1.3;
     add+=_AccentA.rgb*exp(-pow((d.y-sweep)*18,2))*.22*_Scan;
     float ring=exp(-pow((r-.27)*95,2));
     float ticks=step(.78,frac(phi*48));
     add+=_AccentA.rgb*ring*(.3+.7*ticks)*.32*_Scan;
     over(acc,_AccentA.rgb*.04,smoothstep(.35,.75,r)*.25*_Scan);
    }
    if(_Stars>.001)
    {
     float3 sw=w*150;float3 cell=floor(sw);
     float hs=hash31(cell);
     float3 off=float3(hash31(cell+1.7),hash31(cell+3.1),hash31(cell+5.3))-.5;
     float star=step(.982,hs)*smoothstep(.3,0,length(frac(sw)-.5-off*.4));
     float twinkle=.65+.35*sin(t*2.1+hs*60);
     float mask=smoothstep(.2,.62,r);
     over(acc,half3(0,.008,.03),mask*.55*_Stars);
     add+=half3(.82,.9,1)*star*twinkle*mask*1.2*_Stars;
    }
    if(_Rain>.001)
    {
     float2 q=p*float2(26,14);
     float col=floor(q.x);
     float hc=hash11(col*1.7+.3);
     float y=q.y*.16+t*(.7+hc*1.5)+hc*10;
     float trail=pow(1-frac(y),5);
     float glyph=step(.42,hash21(float2(col,floor(q.y*1.6))));
     float thin=smoothstep(.36,0,abs(frac(q.x)-.5));
     add+=half3(.25,1,.72)*trail*thin*glyph*step(.38,hc)*smoothstep(.14,.55,r)*.55*_Rain;
    }
    if(_Tiny>.001)
    {
     float band=smoothstep(.16,.55,abs(d.y));
     over(acc,half3(.05,.04,.03),band*.35*_Tiny);
     float2 bq=p*4.6;float2 bc=floor(bq);
     float disc=smoothstep(.31,.26,length(frac(bq)-.5-(hash22(bc)-.5)*.3))*step(.72,hash21(bc));
     add+=lerp(half3(1,.74,.4),half3(.5,.8,1),hash21(bc+3.3))*disc*band*.13*_Tiny;
    }
    if(_Dream>.001)
    {
     over(acc,half3(.24,.11,.03),smoothstep(.25,.78,r)*.32*_Dream);
     add+=half3(1,.6,.25)*smoothstep(.2,1,d.y)*.07*_Dream;
    }
    if(_Pulse>.001)
    {
     float beat=exp(-_Beat*4.0);
     add+=_PulseColor.rgb*smoothstep(.3,.78,r)*(.25+.75*beat)*.2*_Pulse;
    }
    acc.rgb+=add*(1-acc.a*.5);
    if(_Comfort>.001)
    {
     float inner=lerp(.95,.24,_Comfort);
     over(acc,half3(0,0,0),smoothstep(inner,inner+.22,r)*saturate(_Comfort*1.4));
    }
    if(_Fade>.001)over(acc,_FadeColor.rgb,_Fade);
    return acc;
   }
   ENDCG
  }
 }
}
