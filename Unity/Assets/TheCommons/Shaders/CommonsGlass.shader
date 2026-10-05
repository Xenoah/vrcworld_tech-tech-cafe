Shader "The Commons/Smoked Glass"
{
 Properties { _Color("Tint",Color)=(.1,.18,.2,.07) }
 SubShader { Tags {"Queue"="Transparent" "RenderType"="Transparent"} Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Off
  Pass {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   fixed4 _Color;
   struct a {float4 vertex:POSITION;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v {float4 pos:SV_POSITION;UNITY_VERTEX_OUTPUT_STEREO};
   v vert(a i){v o;UNITY_SETUP_INSTANCE_ID(i);UNITY_INITIALIZE_OUTPUT(v,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);o.pos=UnityObjectToClipPos(i.vertex);return o;}
   fixed4 frag(v i):SV_Target {UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);return _Color;}
   ENDCG
  }
 }
}
