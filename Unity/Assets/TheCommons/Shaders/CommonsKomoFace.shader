Shader "The Commons/Komo Face"
{
 // Procedural face screen for the companion bot. No textures: eyes and mouth
 // are signed distance shapes so expressions change by a single float.
 // 0 neutral, 1 happy, 2 sleepy, 3 surprised, 4 sparkle, 5 wink, 6 focus.
 Properties
 {
  _Expression("Expression",Float)=0
  _Look("Look offset (xy)",Vector)=(0,0,0,0)
  _Talk("Talk",Range(0,1))=0
  _Seed("Blink seed",Float)=0
  _EyeColor("Eye color",Color)=(.35,.95,1,1)
  _ScreenColor("Screen color",Color)=(.02,.035,.06,1)
  _Blush("Blush",Range(0,1))=0
  _LocalEmission("Local emission",Range(0,1))=1
 }
 SubShader
 {
  Tags {"RenderType"="Opaque" "Queue"="Geometry+1"}
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_fog
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   float _Expression,_Talk,_Seed,_Blush,_LocalEmission;float4 _Look;half4 _EyeColor,_ScreenColor;
   struct appdata {float4 vertex:POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v2f {float4 pos:SV_POSITION;float2 uv:TEXCOORD0;UNITY_FOG_COORDS(1) UNITY_VERTEX_OUTPUT_STEREO};
   v2f vert(appdata v)
   {
    v2f o;UNITY_SETUP_INSTANCE_ID(v);UNITY_INITIALIZE_OUTPUT(v2f,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    o.pos=UnityObjectToClipPos(v.vertex);o.uv=v.uv;UNITY_TRANSFER_FOG(o,o.pos);return o;
   }
   float box(float2 p,float2 b,float r){float2 q=abs(p)-b+r;return length(max(q,0))+min(max(q.x,q.y),0)-r;}
   float arc(float2 p,float rad,float w){return p.y<0?length(float2(abs(p.x)-rad,p.y))-w:abs(length(p)-rad)-w;}
   float eye(float2 p,float e,float blink,float side)
   {
    if(e<.5) return box(p*float2(1,1/max(blink,.08)),float2(.075,.11),.06);
    if(e<1.5) return arc(p+float2(0,.03),.075,.022);                       // ^ ^
    if(e<2.5) return box(p+float2(0,.02),float2(.085,.016),.016);          // - -
    if(e<3.5) return abs(length(p)-.095)-.028;                             // O O
    if(e<4.5){float2 a=abs(p);return pow(a.x,.5)+pow(a.y,.5)-.36;}         // sparkle
    if(e<5.5) return side<0?arc(p+float2(0,.03),.075,.022):box(p*float2(1,1/max(blink,.08)),float2(.075,.11),.06);
    return box(p,float2(.085,.045),.04);                                   // focus
   }
   half4 frag(v2f i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float2 p=i.uv-.5;
    float t=_Time.y;
    float cycle=frac(t*.23+_Seed);
    float blink=cycle>.965?.1:1;
    float2 look=clamp(_Look.xy,-1,1)*float2(.05,.035);
    float2 q=p-look-float2(0,.05);
    float d=min(eye(q-float2(-.17,0),_Expression,blink,-1),eye(q-float2(.17,0),_Expression,blink,1));
    float2 m=p-look*.5-float2(0,-.17);
    float mouth=_Talk>.05?box(m,float2(.05,.012+.03*_Talk),.02):abs(length(m-float2(0,.06))-.075)-.012;
    if(_Talk<=.05 && m.y>-.005)mouth=1;
    d=min(d,mouth);
    float edge=1-smoothstep(0,.012,d);
    float glow=exp(-max(d,0)*38)*.35;
    float scan=.92+.08*sin(i.uv.y*240);
    float vign=smoothstep(.72,.35,length(p*float2(1,1.15)));
    half3 c=_ScreenColor.rgb*(.6+.4*vign);
    c+=_EyeColor.rgb*(edge*1.35+glow)*scan*_LocalEmission;
    float blush=exp(-pow(length((p-float2(.27,-.08))*float2(1,1.6))*9,2))+exp(-pow(length((p-float2(-.27,-.08))*float2(1,1.6))*9,2));
    c+=half3(1,.35,.45)*blush*_Blush*.5;
    half4 col=half4(c,1);UNITY_APPLY_FOG(i.fogCoord,col);return col;
   }
   ENDCG
  }
 }
}
