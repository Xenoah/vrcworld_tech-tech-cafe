Shader "The Commons/Laser Particle"
{
 // Additive stretched-billboard particle for the DISCO lasers. Colour and
 // intensity come from CommonsLightingModes (music-synchronous); a soft core
 // across the streak keeps beams readable without bloom. Quest-safe.
 Properties
 {
  _Color("Beam color",Color)=(.05,.7,1,1)
  _Intensity("Intensity",Range(0,2))=.6
  _LocalEmission("Local emission",Range(0,1))=1
 }
 SubShader
 {
  Tags {"Queue"="Transparent+20" "RenderType"="Transparent" "IgnoreProjector"="True" "PreviewType"="Plane"}
  Blend One One
  ZWrite Off ZTest LEqual Cull Off
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #pragma multi_compile_fog
   #include "UnityCG.cginc"
   half4 _Color;half _Intensity,_LocalEmission;
   struct appdata {float4 vertex:POSITION;half4 color:COLOR;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v2f {float4 pos:SV_POSITION;half4 color:COLOR;float2 uv:TEXCOORD0;UNITY_FOG_COORDS(1) UNITY_VERTEX_OUTPUT_STEREO};
   v2f vert(appdata v)
   {
    v2f o;UNITY_SETUP_INSTANCE_ID(v);UNITY_INITIALIZE_OUTPUT(v2f,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    o.pos=UnityObjectToClipPos(v.vertex);o.color=v.color;o.uv=v.uv;UNITY_TRANSFER_FOG(o,o.pos);return o;
   }
   half4 frag(v2f i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    half across=1-abs(i.uv.y*2-1);
    half along=smoothstep(0,.2,i.uv.x)*smoothstep(1,.6,i.uv.x);
    half core=across*across*(1+2*pow(across,8));
    half3 c=_Color.rgb*i.color.rgb*i.color.a*core*along*_Intensity*_LocalEmission*1.6;
    UNITY_APPLY_FOG_COLOR(i.fogCoord,c,half4(0,0,0,0));
    return half4(c,0);
   }
   ENDCG
  }
 }
}
