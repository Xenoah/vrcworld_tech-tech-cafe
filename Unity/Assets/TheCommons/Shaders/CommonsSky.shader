Shader "The Commons/Time Sky"
{
 Properties
 {
  _Top("Zenith",Color)=(.01,.02,.05,1)
  _Horizon("Horizon",Color)=(.08,.12,.18,1)
  _Ground("Ground",Color)=(.02,.025,.04,1)
  _SunDirection("Sun direction",Vector)=(0,1,0,0)
  [HDR] _SunColor("Sun",Color)=(1,.8,.5,1)
 }
 SubShader
 {
  Tags {"Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox"} Cull Off ZWrite Off
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   float3 _Top,_Horizon,_Ground,_SunDirection,_SunColor;
   struct a {float4 vertex:POSITION;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v {float4 pos:SV_POSITION;float3 dir:TEXCOORD0;UNITY_VERTEX_OUTPUT_STEREO};
   v vert(a i){v o;UNITY_SETUP_INSTANCE_ID(i);UNITY_INITIALIZE_OUTPUT(v,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);o.pos=UnityObjectToClipPos(i.vertex);o.dir=i.vertex.xyz;return o;}
   half4 frag(v i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float3 d=normalize(i.dir);float h=pow(saturate(abs(d.y)),.55);
    float3 c=lerp(_Horizon,d.y>=0?_Top:_Ground,h);
    float s=saturate(dot(d,normalize(_SunDirection)));
    c+=_SunColor*(smoothstep(.9996,.99985,s)+pow(s,64)*.06);
    return half4(c,1);
   }
   ENDCG
  }
 }
}
