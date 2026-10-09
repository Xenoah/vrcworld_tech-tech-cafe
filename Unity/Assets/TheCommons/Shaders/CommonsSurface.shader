Shader "The Commons/Surface"
{
 Properties
 {
  _MainTex("Albedo",2D)="white"{}
  _Color("Tint",Color)=(1,1,1,1)
  _Metallic("Metallic",Range(0,1))=0
  _Smoothness("Smoothness",Range(0,1))=.3
  _DetailStrength("Micro relief",Range(0,.5))=.16
  [HDR] _EmissionColor("Emission",Color)=(0,0,0,0)
  _LocalEmission("Local emission",Range(0,1))=1
  _TimeEmission("Time emission",Range(0,1))=1
  _TimeTint("Time tint",Color)=(1,1,1,1)
  _DayFill("Day fill",Color)=(0,0,0,0)
  _RoomTint("Cafe lighting tint",Color)=(1,1,1,1)
  _RoomFill("Cafe lighting fill",Color)=(0,0,0,0)
 }
 SubShader
 {
  Tags {"RenderType"="Opaque"} Cull Off
  CGPROGRAM
  #pragma surface surf Standard fullforwardshadows addshadow
  #pragma target 3.0
  #pragma shader_feature_local _DETAIL_BUMP
  #pragma multi_compile_instancing
  sampler2D _MainTex;
  float4 _MainTex_TexelSize;
  fixed4 _Color,_TimeTint,_RoomTint;
  half3 _DayFill,_EmissionColor,_RoomFill;
  half _Metallic,_Smoothness,_DetailStrength,_LocalEmission,_TimeEmission;
  struct Input {float2 uv_MainTex;};
  void surf(Input IN,inout SurfaceOutputStandard o)
  {
   half3 tex=tex2D(_MainTex,IN.uv_MainTex).rgb;
   half l=dot(tex,half3(.2126,.7152,.0722));
   o.Albedo=tex*_Color.rgb*_TimeTint.rgb*_RoomTint.rgb;
   o.Metallic=_Metallic;
   o.Smoothness=saturate(_Smoothness+(l-.5)*.12);
   #ifdef _DETAIL_BUMP
    half dx=dot(tex2D(_MainTex,IN.uv_MainTex+float2(_MainTex_TexelSize.x,0)).rgb,half3(.2126,.7152,.0722))-l;
    half dy=dot(tex2D(_MainTex,IN.uv_MainTex+float2(0,_MainTex_TexelSize.y)).rgb,half3(.2126,.7152,.0722))-l;
    o.Normal=normalize(half3(-dx*_DetailStrength,-dy*_DetailStrength,1));
   #endif
   o.Emission=min(_EmissionColor*_LocalEmission*_TimeEmission,3)+tex*_Color.rgb*(_DayFill+_RoomFill);
   o.Alpha=1;
  }
  ENDCG
 }
 FallBack "The Commons/Flat Light"
}
