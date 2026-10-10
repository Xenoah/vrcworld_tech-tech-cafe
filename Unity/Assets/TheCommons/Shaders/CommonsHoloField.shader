Shader "The Commons/Holo Field"
{
 // Additive hologram surface: the sky-deck force field, floor rings, the holo
 // planet and ride light strips. Motion follows the local REDUCED MOTION
 // setting through _Motion; no flashing, only slow scrolling.
 Properties
 {
  _Color("Color",Color)=(.05,.75,1,1)
  _Intensity("Intensity",Range(0,2))=.6
  _Grid("Grid density (u,v)",Vector)=(24,8,0,0)
  _Line("Line width",Range(.005,.5))=.06
  _FadeTop("Fade towards uv.y=1",Range(0,1))=1
  _Scroll("Scroll speed",Float)=.05
  _Fresnel("Fresnel",Range(0,4))=1
  _Motion("Motion (0 = reduced)",Range(0,1))=0
  _LocalEmission("Local emission",Range(0,1))=1
 }
 SubShader
 {
  Tags {"Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True"}
  Blend One One ZWrite Off ZTest LEqual Cull Off
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_fog
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   half4 _Color;half _Intensity,_Line,_FadeTop,_Scroll,_Fresnel,_Motion,_LocalEmission;float4 _Grid;
   struct appdata {float4 vertex:POSITION;float3 normal:NORMAL;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v2f {float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float3 n:TEXCOORD1;float3 world:TEXCOORD2;UNITY_FOG_COORDS(3) UNITY_VERTEX_OUTPUT_STEREO};
   v2f vert(appdata v)
   {
    v2f o;UNITY_SETUP_INSTANCE_ID(v);UNITY_INITIALIZE_OUTPUT(v2f,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    o.pos=UnityObjectToClipPos(v.vertex);o.uv=v.uv;o.n=UnityObjectToWorldNormal(v.normal);o.world=mul(unity_ObjectToWorld,v.vertex).xyz;
    UNITY_TRANSFER_FOG(o,o.pos);return o;
   }
   half4 frag(v2f i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float2 g=i.uv*_Grid.xy;g.y+=_Time.y*_Scroll*_Motion*_Grid.y;
    float2 f=abs(frac(g)-.5);
    float lines=max(1-smoothstep(0,_Line,.5-f.x),1-smoothstep(0,_Line,.5-f.y));
    float3 v=normalize(_WorldSpaceCameraPos-i.world);
    float fres=pow(1-abs(dot(normalize(i.n),v)),2)*_Fresnel;
    float fade=lerp(1,1-smoothstep(0,1,i.uv.y),_FadeTop);
    half3 c=_Color.rgb*(lines*.8+.12+fres)*fade*_Intensity*_LocalEmission;
    UNITY_APPLY_FOG_COLOR(i.fogCoord,c,half4(0,0,0,0));
    return half4(c,0);
   }
   ENDCG
  }
 }
}
