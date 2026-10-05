Shader "The Commons/DJ Bands"
{
 Properties { _Intensity("Intensity",Range(0,1))=.2 _Motion("Motion",Range(0,1))=0 }
 SubShader {Tags {"RenderType"="Opaque"} Cull Off
  Pass {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_instancing
   #include "UnityCG.cginc"
   sampler2D _AudioTexture;float4 _AudioTexture_TexelSize;float _Intensity,_Motion;
   struct a {float4 vertex:POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct v {float4 pos:SV_POSITION;float2 uv:TEXCOORD0;UNITY_VERTEX_OUTPUT_STEREO};
   v vert(a i){v o;UNITY_SETUP_INSTANCE_ID(i);UNITY_INITIALIZE_OUTPUT(v,o);UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);o.pos=UnityObjectToClipPos(i.vertex);o.uv=i.uv;return o;}
   fixed4 frag(v i):SV_Target
   {
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);
    float band=min(3,floor(i.uv.x*4));
    // AudioLink global 128x64 data texture. No optional package include dependency.
    float audio=_AudioTexture_TexelSize.z>64 ? tex2Dlod(_AudioTexture,float4(float2(.5,band+.5)*_AudioTexture_TexelSize.xy,0,0)).r : .28;
    float energy=lerp(.28,saturate(audio),_Motion);
    float h=.14+.64*energy+.035*sin(i.uv.x*26+_Time.y*.65)*_Motion;
    float stripe=step(.2,frac(i.uv.x*48));
    float bars=step(i.uv.y,h)*stripe;
    return fixed4(float3(.005,.012,.018)+float3(.02,.55,.85)*bars*_Intensity,1);
   }
   ENDCG
  }
 }
}
