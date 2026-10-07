Shader "The Commons/Flat Light"
{
 Properties
 {
  _MainTex("Albedo",2D)="white"{}
  _Color("Tint",Color)=(1,1,1,1)
  [HDR] _EmissionColor("Emission",Color)=(0,0,0,0)
  _LocalEmission("Local emission",Range(0,1))=1
  _TimeEmission("Time emission",Range(0,1))=1
  _TimeTint("Time tint",Color)=(1,1,1,1)
  _DayFill("Day fill",Color)=(0,0,0,0)
  _Metallic("Metallic",Range(0,1))=0
  _Smoothness("Smoothness",Range(0,1))=.3
  _SunDirection("Sun direction",Vector)=(0,1,0,0)
  _SunColor("Sun color",Color)=(1,1,1,1)
 }
 SubShader
 {
  Tags {"RenderType"="Opaque"} Cull Off
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
   sampler2D _MainTex; float4 _MainTex_ST; fixed4 _Color; float4 _EmissionColor; float _LocalEmission,_TimeEmission,_Metallic,_Smoothness; float3 _TimeTint,_DayFill,_SunDirection,_SunColor;
   struct appdata { float4 vertex:POSITION; float3 normal:NORMAL; float2 uv:TEXCOORD0; float2 uv2:TEXCOORD1; float4 color:COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };
   struct v2f { float4 pos:SV_POSITION; float2 uv:TEXCOORD0; float2 lm:TEXCOORD1; float3 n:TEXCOORD2; float3 ambient:TEXCOORD3; float3 world:TEXCOORD5; UNITY_FOG_COORDS(4) UNITY_VERTEX_OUTPUT_STEREO };
   v2f vert(appdata v)
   {
    v2f o; UNITY_SETUP_INSTANCE_ID(v); UNITY_INITIALIZE_OUTPUT(v2f,o); UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
    o.pos=UnityObjectToClipPos(v.vertex);o.uv=TRANSFORM_TEX(v.uv,_MainTex);o.lm=v.uv2*unity_LightmapST.xy+unity_LightmapST.zw;
    o.world=mul(unity_ObjectToWorld,v.vertex).xyz;o.n=UnityObjectToWorldNormal(v.normal);o.ambient=v.color.rgb;UNITY_TRANSFER_FOG(o,o.pos);return o;
   }
   fixed4 frag(v2f i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float3 albedo=tex2D(_MainTex,i.uv).rgb*_Color.rgb;
    float3 light;
    #ifdef LIGHTMAP_ON
      light=DecodeLightmap(UNITY_SAMPLE_TEX2D(unity_Lightmap,i.lm));
    #else
      float n=saturate(dot(normalize(i.n),normalize(float3(.25,.85,-.4)))*.5+.5);
      float bands=.32 + .30*smoothstep(.31,.39,n)+.38*smoothstep(.65,.73,n);
      light=(.6+.55*bands)*max(i.ambient,float3(.32,.35,.4));
    #endif
    float3 nrm=normalize(i.n);
    float3 halfDir=normalize(normalize(_WorldSpaceCameraPos-i.world)+normalize(_SunDirection));
    float spec=pow(saturate(dot(nrm,halfDir)),lerp(8,64,_Smoothness))*_Smoothness*.3*saturate(dot(nrm,normalize(_SunDirection)));
    float3 result=albedo*(light*_TimeTint+_DayFill*(.55+.45*saturate(nrm.y)));
    result+=spec*lerp(float3(.04,.04,.04),albedo,_Metallic)*_SunColor;
    fixed4 col=fixed4(result+min(_EmissionColor.rgb*_LocalEmission*_TimeEmission,3),1);
    UNITY_APPLY_FOG(i.fogCoord,col);return col;
   }
   ENDCG
  }
  Pass
  {
   Name "META" Tags {"LightMode"="Meta"} Cull Off
   CGPROGRAM
   #pragma vertex vert_meta
   #pragma fragment frag_meta
   #include "UnityStandardMeta.cginc"
   ENDCG
  }
  UsePass "Legacy Shaders/VertexLit/SHADOWCASTER"
 }
 Fallback "Mobile/VertexLit"
}
