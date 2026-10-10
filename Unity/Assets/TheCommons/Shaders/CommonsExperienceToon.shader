Shader "The Commons/Experience Toon"
{
 // Dynamic, non-lightmapped props (ride cars, the sky deck, the companion).
 // Light probes + a soft two-band ramp keep them readable on PC and Quest
 // without realtime lights; the floor value keeps them visible 120 m above the
 // probe-baked city at night.
 Properties
 {
  _Color("Albedo",Color)=(.9,.9,.9,1)
  [HDR] _EmissionColor("Emission",Color)=(0,0,0,0)
  _RimColor("Rim",Color)=(.35,.75,1,1)
  _Rim("Rim strength",Range(0,1))=.25
  _MinLight("Minimum light",Range(0,1))=.32
  _LocalEmission("Local emission",Range(0,1))=1
 }
 SubShader
 {
  Tags {"RenderType"="Opaque" "Queue"="Geometry"}
  Pass
  {
   Tags {"LightMode"="ForwardBase"}
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_fwdbase
   #pragma multi_compile_fog
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   #include "Lighting.cginc"
   half4 _Color,_EmissionColor,_RimColor;half _Rim,_MinLight,_LocalEmission;
   struct appdata {float4 vertex:POSITION;float3 normal:NORMAL;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v2f {float4 pos:SV_POSITION;float3 n:TEXCOORD0;float3 world:TEXCOORD1;half3 sh:TEXCOORD2;UNITY_FOG_COORDS(3) UNITY_VERTEX_OUTPUT_STEREO};
   v2f vert(appdata v)
   {
    v2f o;UNITY_SETUP_INSTANCE_ID(v);UNITY_INITIALIZE_OUTPUT(v2f,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    o.pos=UnityObjectToClipPos(v.vertex);o.n=UnityObjectToWorldNormal(v.normal);
    o.world=mul(unity_ObjectToWorld,v.vertex).xyz;o.sh=ShadeSH9(float4(o.n,1));
    UNITY_TRANSFER_FOG(o,o.pos);return o;
   }
   half4 frag(v2f i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float3 n=normalize(i.n);
    float3 v=normalize(_WorldSpaceCameraPos-i.world);
    float3 l=_WorldSpaceLightPos0.w>0?normalize(_WorldSpaceLightPos0.xyz-i.world):normalize(_WorldSpaceLightPos0.xyz+float3(0,.0001,0));
    half key=saturate(dot(n,l)*.5+.5);
    half ramp=.55+.45*smoothstep(.45,.55,key);
    half3 ambient=max(i.sh,_MinLight.xxx);
    half3 direct=_LightColor0.rgb*ramp*.6;
    half3 shade=ambient*(.75+.25*saturate(n.y*.5+.5))+direct;
    half rim=pow(1-saturate(dot(n,v)),3)*_Rim;
    half4 c=half4(_Color.rgb*shade+_RimColor.rgb*rim+_EmissionColor.rgb*_LocalEmission,1);
    UNITY_APPLY_FOG(i.fogCoord,c);return c;
   }
   ENDCG
  }
 }
 Fallback "Diffuse"
}
