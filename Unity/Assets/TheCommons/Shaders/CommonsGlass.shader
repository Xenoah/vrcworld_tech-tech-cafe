Shader "The Commons/Smoked Glass"
{
 Properties { _Color("Tint",Color)=(.1,.18,.2,.07) _TimeTint("Time tint",Color)=(1,1,1,1) _DayFill("Day fill",Color)=(0,0,0,0) }
 SubShader { Tags {"Queue"="Transparent" "RenderType"="Transparent"} Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Off
  Pass {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   fixed4 _Color;half3 _TimeTint,_DayFill;
   struct a {float4 vertex:POSITION;float3 normal:NORMAL;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v {float4 pos:SV_POSITION;float3 world:TEXCOORD0;float3 n:TEXCOORD1;UNITY_VERTEX_OUTPUT_STEREO};
   v vert(a i){v o;UNITY_SETUP_INSTANCE_ID(i);UNITY_INITIALIZE_OUTPUT(v,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);o.pos=UnityObjectToClipPos(i.vertex);o.world=mul(unity_ObjectToWorld,i.vertex).xyz;o.n=UnityObjectToWorldNormal(i.normal);return o;}
   fixed4 frag(v i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float3 view=normalize(_WorldSpaceCameraPos-i.world),n=normalize(i.n);
    half fresnel=pow(1-saturate(abs(dot(view,n))),4);
    half4 cube=UNITY_SAMPLE_TEXCUBE(unity_SpecCube0,reflect(-view,n));
    half3 reflection=DecodeHDR(cube,unity_SpecCube0_HDR);
    return fixed4(_Color.rgb*_TimeTint+_DayFill*.25+reflection*(.15+.65*fresnel),saturate(_Color.a+.18*fresnel));
   }
   ENDCG
  }
 }
}
