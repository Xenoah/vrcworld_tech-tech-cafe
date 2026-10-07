Shader "The Commons/Soft Fixture Glow"
{
 Properties
 {
  [HDR] _Color("Glow color",Color)=(1,.55,.22,1)
  _Intensity("Intensity",Range(0,.2))=.045
  _LocalEmission("Local emission",Range(0,1))=1
  _TimeGlow("Time glow",Range(0,1))=1
 }
 SubShader
 {
  Tags {"Queue"="Transparent+10" "RenderType"="Transparent" "DisableBatching"="True"}
  Blend One One ZWrite Off ZTest LEqual Cull Off
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   half4 _Color;half _Intensity,_LocalEmission,_TimeGlow;
   struct a {float4 vertex:POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v {float4 pos:SV_POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_OUTPUT_STEREO};
   v vert(a i)
   {
    v o;UNITY_SETUP_INSTANCE_ID(i);UNITY_INITIALIZE_OUTPUT(v,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    float3 center=mul(UNITY_MATRIX_MV,float4(0,0,0,1)).xyz;
    float2 scale=float2(length(unity_ObjectToWorld._m00_m10_m20),length(unity_ObjectToWorld._m01_m11_m21));
    o.pos=mul(UNITY_MATRIX_P,float4(center+float3(i.vertex.xy*scale,0),1));o.uv=i.uv;return o;
   }
   half4 frag(v i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    half r=saturate(1-length(i.uv*2-1));
    return half4(_Color.rgb*r*r*r*_Intensity*_LocalEmission*_TimeGlow,0);
   }
   ENDCG
  }
 }
}
