Shader "The Commons/Disco Beam"
{
 Properties
 {
  _Color("Beam color",Color)=(.05,.7,1,1)
  _Intensity("Intensity",Range(0,1))=.65
 }
 SubShader
 {
  Tags {"Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True"}
  Blend SrcAlpha One
  ZWrite Off ZTest LEqual Cull Off
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #pragma multi_compile_fog
   #include "UnityCG.cginc"
   fixed4 _Color;half _Intensity;
   struct appdata {float4 vertex:POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v2f {float4 vertex:SV_POSITION;float2 uv:TEXCOORD0;UNITY_FOG_COORDS(1) UNITY_VERTEX_OUTPUT_STEREO};
   v2f vert(appdata v)
   {
    v2f o;UNITY_SETUP_INSTANCE_ID(v);UNITY_INITIALIZE_OUTPUT(v2f,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    o.vertex=UnityObjectToClipPos(v.vertex);o.uv=v.uv;UNITY_TRANSFER_FOG(o,o.vertex);return o;
   }
   fixed4 frag(v2f i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    half core=pow(saturate(1-abs(i.uv.x*2-1)),2);
    half fade=smoothstep(0,.025,i.uv.y)*(1-smoothstep(.85,1,i.uv.y));
    fixed4 c=fixed4(_Color.rgb*1.8,core*fade*_Intensity);
    UNITY_APPLY_FOG_COLOR(i.fogCoord,c,fixed4(0,0,0,0));return c;
   }
   ENDCG
  }
 }
}
