#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UdonSharpEditor;
using VRC.SDK3.Components;

public static class CommonsAtmosphereBuilder
{
    public static CommonsTimeOfDay Configure(string output,bool mobile,CommonsWorldState state,CommonsComfort comfort,Dictionary<string,Material> materials)
    {
        GameObject go=new GameObject("INT_TimeOfDay");go.transform.SetParent(state.transform.parent);
        CommonsTimeOfDay time=go.AddUdonSharpComponent<CommonsTimeOfDay>();
        time.state=state;
        List<Material> daylightSurfaces=new List<Material>();
        foreach(KeyValuePair<string,Material> pair in materials)
        {
            if(!pair.Key.StartsWith("MAT_Kart")){daylightSurfaces.Add(pair.Value);continue;}
            // The enclosed kart hall keeps its artificial lighting at every outside hour.
            Material interior=pair.Value;
            interior.SetColor("_TimeTint",new Color(.84f,.90f,1f));
            interior.SetColor("_DayFill",new Color(.055f,.065f,.10f));
            interior.SetFloat("_TimeEmission",1f);
            if(interior.HasProperty("_SunColor"))interior.SetColor("_SunColor",Color.black);
        }
        time.surfaces=daylightSurfaces.ToArray();
        Material sky=new Material(Shader.Find("The Commons/Time Sky"));sky.name="Commons_TimeSky";sky.enableInstancing=true;
        AssetDatabase.CreateAsset(sky,output+"/Materials/TimeSky.mat");RenderSettings.skybox=sky;time.sky=sky;
        if(!mobile)
        {
            Light sun=new GameObject("LGT_TimeSun_PC").AddComponent<Light>();sun.type=LightType.Directional;
            sun.lightmapBakeType=LightmapBakeType.Realtime;sun.shadows=LightShadows.Soft;sun.shadowStrength=.7f;sun.renderMode=LightRenderMode.ForcePixel;
            time.sun=sun;RenderSettings.sun=sun;
        }
        GameObject glowRoot=new GameObject("LGT_LocalGlow");comfort.glowRoot=glowRoot;
        Material warm=GlowMaterial(output,"Warm",new Color(1,.55f,.22f),mobile ? .06f : .09f);
        Material cool=GlowMaterial(output,"Cool",new Color(.12f,.65f,.95f),mobile ? .05f : .075f);
        time.glows=new[]{warm,cool};
        foreach(float z in new[]{6.4f,11.3f}) Glow(glowRoot,new Vector3(14,8.55f,z),2.2f,warm);
        foreach(float x in new[]{8.6f,19.85f})foreach(float y in new[]{2.1f,7f}) Glow(glowRoot,new Vector3(x,y,4.74f),1.4f,warm);
        foreach(float x in new[]{-56f,-46f,-36f}) Glow(glowRoot,new Vector3(x,7.48f,10f),2f,cool);
        Glow(glowRoot,new Vector3(14,3.7f,.34f),1.8f,warm);
        foreach(float z in new[]{9.5f,14.5f}) Glow(glowRoot,new Vector3(27.58f,7f,z),1.4f,cool);
        time.ApplyHour(20f);time.ApplyProxyModifications();return time;
    }
    static Material GlowMaterial(string output,string name,Color color,float intensity)
    {
        Material m=new Material(Shader.Find("The Commons/Soft Fixture Glow"));m.name="Glow_"+name;m.enableInstancing=true;
        m.SetColor("_Color",color);m.SetFloat("_Intensity",intensity);
        AssetDatabase.CreateAsset(m,output+"/Materials/Glow_"+name+".mat");return m;
    }
    static void Glow(GameObject parent,Vector3 p,float size,Material material)
    {
        GameObject o=GameObject.CreatePrimitive(PrimitiveType.Quad);o.name="LGT_GlowCard";o.transform.SetParent(parent.transform);
        o.transform.position=p;o.transform.localScale=Vector3.one*size;UnityEngine.Object.DestroyImmediate(o.GetComponent<Collider>());
        Renderer r=o.GetComponent<Renderer>();r.sharedMaterial=material;r.shadowCastingMode=ShadowCastingMode.Off;r.receiveShadows=false;
    }
    public static void ConfigureReferenceCamera(bool mobile,VRCSceneDescriptor descriptor)
    {
        SerializedObject sceneDescriptor=new SerializedObject(descriptor);
        SerializedProperty referenceCamera=sceneDescriptor.FindProperty("ReferenceCamera");
        if(referenceCamera==null)throw new InvalidOperationException("The installed SDK has no ReferenceCamera field.");
        GameObject go=new GameObject(mobile?"LGT_Quest_ReferenceCamera":"LGT_PC_ReferenceCamera");
        Camera camera=go.AddComponent<Camera>();camera.enabled=false;camera.allowHDR=!mobile;
        camera.nearClipPlane=.03f;camera.farClipPlane=900f;
        referenceCamera.objectReferenceValue=go;sceneDescriptor.ApplyModifiedPropertiesWithoutUndo();
    }
    // Reflection keeps PPS optional: missing package does not stop scene generation.
    public static void AddOptionalBloom(string output,GameObject parent,VRCSceneDescriptor descriptor)
    {
        Type profileType=Type.GetType("UnityEngine.Rendering.PostProcessing.PostProcessProfile, Unity.Postprocessing.Runtime");
        Type bloomType=Type.GetType("UnityEngine.Rendering.PostProcessing.Bloom, Unity.Postprocessing.Runtime");
        Type volumeType=Type.GetType("UnityEngine.Rendering.PostProcessing.PostProcessVolume, Unity.Postprocessing.Runtime");
        Type layerType=Type.GetType("UnityEngine.Rendering.PostProcessing.PostProcessLayer, Unity.Postprocessing.Runtime");
        Type resourcesType=Type.GetType("UnityEngine.Rendering.PostProcessing.PostProcessResources, Unity.Postprocessing.Runtime");
        if(profileType==null || bloomType==null || volumeType==null || layerType==null || resourcesType==null)
        {Debug.LogWarning("THE COMMONS: Post Processing Stack v2 is not installed. Soft fixture glow is available; optional PC bloom was omitted.");return;}
        UnityEngine.Object resources=AssetDatabase.LoadAssetAtPath("Packages/com.unity.postprocessing/PostProcessing/PostProcessResources.asset",resourcesType);
        if(resources==null)
        {
            foreach(string guid in AssetDatabase.FindAssets("t:PostProcessResources"))
            {
                resources=AssetDatabase.LoadAssetAtPath(AssetDatabase.GUIDToAssetPath(guid),resourcesType);
                if(resources!=null)break;
            }
        }
        if(resources==null)
        {Debug.LogWarning("THE COMMONS: PostProcessResources was not found. Reimport Post Processing to enable optional PC bloom.");return;}
        SerializedObject sceneDescriptor=new SerializedObject(descriptor);
        SerializedProperty referenceCamera=sceneDescriptor.FindProperty("ReferenceCamera");
        if(referenceCamera==null)throw new InvalidOperationException("The installed SDK has no ReferenceCamera field. Verify its scene descriptor API before building.");
        ScriptableObject profile=ScriptableObject.CreateInstance(profileType);profile.name="Commons_AtmosphereBloom";
        object bloom=profileType.GetMethod("AddSettings",new[]{typeof(Type)}).Invoke(profile,new object[]{bloomType});
        SetParameter(bloom,"enabled",true);SetParameter(bloom,"intensity",.60f);SetParameter(bloom,"threshold",1.05f);
        SetParameter(bloom,"softKnee",.60f);SetParameter(bloom,"diffusion",5f);SetParameter(bloom,"fastMode",true);
        AssetDatabase.CreateAsset(profile,output+"/CommonsBloom.asset");AssetDatabase.AddObjectToAsset((UnityEngine.Object)bloom,profile);
        // VRChat copies this camera's settings and PostProcessLayer to the player camera.
        // Keep it outside the local glow root: the toggle only enables/disables the volume.
        GameObject cameraObject=referenceCamera.objectReferenceValue as GameObject;
        if(cameraObject==null)throw new InvalidOperationException("Configure the reference camera before adding bloom.");
        Component layer=cameraObject.AddComponent(layerType);
        layerType.GetMethod("Init",new[]{resourcesType}).Invoke(layer,new[]{resources});
        LayerMask volumeMask=1<<4; // VRChat's built-in Water layer, commonly used for post processing.
        layerType.GetField("volumeLayer").SetValue(layer,volumeMask);
        referenceCamera.objectReferenceValue=cameraObject;sceneDescriptor.ApplyModifiedPropertiesWithoutUndo();
        GameObject go=new GameObject("LGT_PC_BloomVolume");go.transform.SetParent(parent.transform);go.layer=4;
        Component volume=go.AddComponent(volumeType);
        volumeType.GetField("isGlobal").SetValue(volume,true);volumeType.GetField("weight").SetValue(volume,1f);
        volumeType.GetField("priority").SetValue(volume,5f);volumeType.GetField("sharedProfile").SetValue(volume,profile);
    }
    static void SetParameter(object setting,string field,object value)
    {
        object parameter=setting.GetType().GetField(field).GetValue(setting);
        parameter.GetType().GetField("overrideState").SetValue(parameter,true);
        parameter.GetType().GetField("value").SetValue(parameter,value);
    }
}
#endif
