Shader "The Commons/Media"
{
 Properties { _MainTex("Media",2D)="black"{} _Color("Brightness",Color)=(.8,.8,.8,1) }
 SubShader { Tags {"RenderType"="Opaque"} Cull Off
  Pass {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   sampler2D _MainTex;float4 _Color;
   struct a {float4 vertex:POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v {float4 pos:SV_POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_OUTPUT_STEREO};
   v vert(a i) {v o;UNITY_SETUP_INSTANCE_ID(i);UNITY_INITIALIZE_OUTPUT(v,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);o.pos=UnityObjectToClipPos(i.vertex);o.uv=i.uv;return o;}
   fixed4 frag(v i):SV_Target {UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);return fixed4(tex2D(_MainTex,i.uv).rgb*_Color.rgb,1);}
   ENDCG
  }
 }
}
