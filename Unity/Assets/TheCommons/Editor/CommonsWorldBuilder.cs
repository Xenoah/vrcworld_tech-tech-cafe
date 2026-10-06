#if UNITY_EDITOR
using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using UnityEditor;
using UnityEditor.SceneManagement;
using UdonSharp;
using UdonSharpEditor;
using VRC.SDKBase;
using VRC.SDK3.Components;
using VRC.SDK3.Video.Components;

public static class CommonsWorldBuilder
{
    const string Root = "Assets/TheCommons";
    static string Out;
    static bool Mobile;
    static Dictionary<string,Material> materials;
    static Dictionary<string,GameObject> groups;
    [Serializable] public class Manifest { public ColliderRecord[] colliders; public LightRecord[] lights; public SeatRecord[] seat_anchors; public MaterialRecord[] materials; }
    [Serializable] public class ColliderRecord { public string name,kind,group; public float[] position,size,rotation,vertices; public float radius,height; }
    [Serializable] public class LightRecord { public string name; public float[] position,color,target; public float power,size; }
    [Serializable] public class SeatRecord { public float[] position; public float yaw; public string group; }
    [Serializable] public class MaterialRecord { public string name,texture,wrap; public float[] color; public float emission; }

    [MenuItem("The Commons/Build PC World")]
    public static void PC() { Build(false); }
    [MenuItem("The Commons/Build Quest World")]
    public static void Quest() { Build(true); }
    // MCP can call these public static methods or the corresponding menu items.
    // Fail before modifying an unsaved scene; normal interactive builds retain the save dialog.
    [MenuItem("The Commons/MCP/Build PC World (no dialogs)")]
    public static void BuildPCForMCP() { RequireSavedScene(); Build(false,false); }
    [MenuItem("The Commons/MCP/Build Quest World (no dialogs)")]
    public static void BuildQuestForMCP() { RequireSavedScene(); Build(true,false); }
    static void RequireSavedScene()
    {
        for(int i=0;i<UnityEngine.SceneManagement.SceneManager.sceneCount;i++)
            if(UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty)
                throw new InvalidOperationException("Save the current scenes before an MCP build.");
    }
    static Vector3 V(float[] a) { return new Vector3(a[0],a[2],a[1]); }
    static GameObject Group(string name)
    {
        if (!groups.ContainsKey(name)) groups[name]=new GameObject(name);
        return groups[name];
    }
    static void SaveAsset(UnityEngine.Object asset,string path)
    {
        // Build uses a new timestamped directory; existing scenes are never overwritten.
        AssetDatabase.CreateAsset(asset,path);
    }
    static string ReadString(BinaryReader r) { return System.Text.Encoding.UTF8.GetString(r.ReadBytes(r.ReadInt32())); }
    static void Build(bool mobile,bool interactive=true)
    {
        if (interactive && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
        Mobile=mobile;
        string stamp=DateTime.Now.ToString("yyyyMMdd_HHmmss_fff");
        Out=Root+"/Generated/"+(Mobile?"Quest_":"PC_")+stamp;
        Directory.CreateDirectory(Out+"/Meshes");Directory.CreateDirectory(Out+"/Materials");AssetDatabase.Refresh();
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        groups=new Dictionary<string,GameObject>();materials=new Dictionary<string,Material>();
        Manifest data=JsonUtility.FromJson<Manifest>(File.ReadAllText(Root+"/Data/world_manifest.json"));
        if (data == null || data.materials == null) throw new InvalidDataException("Missing world manifest. Reimport the complete TheCommons folder.");
        foreach(MaterialRecord r in data.materials)
        {
            Material m=new Material(Shader.Find("The Commons/Flat Light"));m.name=r.name;
            m.SetColor("_Color",new Color(r.color[0],r.color[1],r.color[2],1));
            m.SetColor("_EmissionColor",new Color(r.color[0]*r.emission,r.color[1]*r.emission,r.color[2]*r.emission,1));
            if (!string.IsNullOrEmpty(r.texture))
            {
                m.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"/Textures/"+r.texture+"_albedo.png");
                if(m.mainTexture==null)throw new InvalidDataException("Missing texture: "+r.texture);
            }
            m.globalIlluminationFlags=MaterialGlobalIlluminationFlags.BakedEmissive;
            if(r.name=="MAT_Window") {m.shader=Shader.Find("The Commons/Smoked Glass");m.SetColor("_Color",new Color(.1f,.18f,.2f,.07f));}
            SaveAsset(m,Out+"/Materials/"+r.name+".mat");materials.Add(r.name,m);
        }
        string meshFile=Root+"/Models/TheCommons_"+(Mobile?"Quest":"PC")+".tcmesh.bytes";
        using(BinaryReader r=new BinaryReader(File.OpenRead(meshFile)))
        {
            if (System.Text.Encoding.ASCII.GetString(r.ReadBytes(4))!="TCM2") throw new InvalidDataException("Unexpected geometry version.");
            int count=r.ReadInt32();
            for(int j=0;j<count;j++)
            {
                string name=ReadString(r),group=ReadString(r),mat=ReadString(r);
                int nv=r.ReadInt32(),ni=r.ReadInt32();
                Vector3[] vs=new Vector3[nv],ns=new Vector3[nv];Vector2[] uv=new Vector2[nv];Color[] colors=new Color[nv];
                for(int i=0;i<nv;i++)
                {
                    vs[i]=new Vector3(r.ReadSingle(),r.ReadSingle(),r.ReadSingle());
                    ns[i]=new Vector3(r.ReadSingle(),r.ReadSingle(),r.ReadSingle());uv[i]=new Vector2(r.ReadSingle(),r.ReadSingle());
                    // Authored ambient tint, a preview fallback until Unity lightmaps are baked.
                    float warm=Mathf.Clamp01((8.5f-vs[i].x)/5f);
                    colors[i]=Color.Lerp(new Color(.66f,.75f,.87f),new Color(1.03f,.79f,.51f),warm);
                }
                int[] ix=new int[ni];for(int i=0;i<ni;i++)ix[i]=r.ReadInt32();
                Mesh mesh=new Mesh();mesh.name=name;mesh.indexFormat=nv>65535?IndexFormat.UInt32:IndexFormat.UInt16;
                mesh.vertices=vs;mesh.normals=ns;mesh.uv=uv;mesh.colors=colors;mesh.triangles=ix;mesh.RecalculateBounds();
                Unwrapping.GenerateSecondaryUVSet(mesh);
                SaveAsset(mesh,Out+"/Meshes/"+name+".asset");
                GameObject o=new GameObject(name);o.transform.SetParent(Group(group).transform,false);
                o.AddComponent<MeshFilter>().sharedMesh=mesh;MeshRenderer mr=o.AddComponent<MeshRenderer>();mr.sharedMaterial=materials[mat];
                mr.shadowCastingMode=ShadowCastingMode.On;
                if (!group.StartsWith("MODE_") && group!="AV_Hologram")
                    GameObjectUtility.SetStaticEditorFlags(o,StaticEditorFlags.ContributeGI|StaticEditorFlags.BatchingStatic|StaticEditorFlags.OccludeeStatic|StaticEditorFlags.OccluderStatic);
            }
        }
        foreach(ColliderRecord c in data.colliders)
        {
            GameObject o=new GameObject(c.name);o.transform.SetParent(Group(c.group).transform,false);
            if (c.kind=="ramp")
            {
                Vector3[] v=new Vector3[4];for(int i=0;i<4;i++)v[i]=new Vector3(c.vertices[i*3],c.vertices[i*3+2],c.vertices[i*3+1]);
                Mesh mesh=new Mesh();mesh.name=c.name;mesh.vertices=v;mesh.triangles=new[]{0,2,1,0,3,2};mesh.RecalculateNormals();
                SaveAsset(mesh,Out+"/Meshes/"+c.name+".asset");o.AddComponent<MeshCollider>().sharedMesh=mesh;
            }
            else if(c.kind=="cylinder")
            {
                UnityEngine.Object.DestroyImmediate(o);
                o=GameObject.CreatePrimitive(PrimitiveType.Cylinder);o.name=c.name;o.transform.SetParent(Group(c.group).transform,false);
                o.transform.position=V(c.position);o.transform.localScale=new Vector3(c.radius*2,c.height/2,c.radius*2);
                UnityEngine.Object.DestroyImmediate(o.GetComponent<Collider>());
                o.AddComponent<MeshCollider>().sharedMesh=o.GetComponent<MeshFilter>().sharedMesh;
                UnityEngine.Object.DestroyImmediate(o.GetComponent<Renderer>());
            }
            else { o.transform.position=V(c.position);o.AddComponent<BoxCollider>().size=V(c.size); }
            o.isStatic=true;
        }
        GameObject systems=Group("INT_Systems");
        GameObject stateObject=new GameObject("INT_SharedState");stateObject.transform.SetParent(systems.transform);
        GameObject comfortObject=new GameObject("INT_LocalComfort");comfortObject.transform.SetParent(systems.transform);
        GameObject audioObject=new GameObject("INT_LocalAudio");audioObject.transform.SetParent(systems.transform);
        CommonsWorldState state=stateObject.AddUdonSharpComponent<CommonsWorldState>();
        CommonsComfort comfort=comfortObject.AddUdonSharpComponent<CommonsComfort>();
        CommonsAudioZones zones=audioObject.AddUdonSharpComponent<CommonsAudioZones>();
        state.loungeRoot=Group("MODE_Lounge");state.academicRoot=Group("MODE_Academic");
        state.hologramRoot=Mobile?null:Group("AV_Hologram");state.comfort=comfort;state.audioZones=zones;
        comfort.state=state;zones.state=state;
        List<Material> em=new List<Material>();foreach(MaterialRecord m in data.materials)if(m.emission>0)em.Add(materials[m.name]);comfort.luminousMaterials=em.ToArray();
        Material media=new Material(Shader.Find("The Commons/Media"));media.name="Presentation";
        state.slides=new Texture[4];for(int i=0;i<4;i++)state.slides[i]=AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"/Media/slide_"+i+".png");
        media.mainTexture=state.slides[0];SaveAsset(media,Out+"/Materials/Presentation.mat");state.presentationMaterial=media;
        Quad("AV_MainMedia",new Vector3(14,2.4f,16.765f),7.1f,4f,0,media);
        Quad("AV_UpperMedia",new Vector3(14,7.22f,17.27f),5.68f,3.2f,0,media);
        for(int i=0;i<6;i++)
        {
            Material p=new Material(Shader.Find("The Commons/Media"));p.name="Poster_"+i;
            p.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"/Media/poster_"+i+".png");SaveAsset(p,Out+"/Materials/Poster_"+i+".mat");
            if(i<5)Quad("AV_Poster_"+i,new Vector3(27.06f,2.06f,8.45f+i*1.5f),1.06f,1.7f,90,p);
            else Quad("AV_Poster_5",new Vector3(24.5f,2.06f,7.405f),1.06f,1.7f,180,p);
        }
        Material dj=new Material(Shader.Find("The Commons/DJ Bands"));SaveAsset(dj,Out+"/Materials/DJ_Bands.mat");comfort.djMaterial=dj;
        Quad("AV_DJVisualizer",new Vector3(14,5.22f,12.801f),3.4f,.34f,0,dj);
        GameObject pointer=GameObject.CreatePrimitive(PrimitiveType.Sphere);pointer.name="INT_StablePointer";pointer.transform.localScale=Vector3.one*.055f;pointer.GetComponent<Renderer>().sharedMaterial=materials["MAT_Amber"];UnityEngine.Object.DestroyImmediate(pointer.GetComponent<Collider>());state.pointerRoot=pointer;state.pointerTransform=pointer.transform;
        state.modeLabel=Label("Mode","LOUNGE",new Vector3(17.1f,1.98f,1.38f),.13f);
        state.timerLabel=Label("Timer","15 MIN TALK / 5 MIN Q&A",new Vector3(10.4f,1.75f,11.12f),.12f);
        state.qaLabel=Label("QA","",new Vector3(14,4.18f,16.72f),.22f);
        string[] mn={"LOUNGE","ACADEMIC","DJ / LIVE","QUIET NIGHT"};string[] me={"Lounge","Academic","DJ","QuietNight"};
        for(int i=0;i<4;i++)
        {
            Button(mn[i],new Vector3(16.6f+(i%2)*1.05f,1.65f-(i/2)*.36f,1.48f),state,me[i]);
            Button(mn[i],new Vector3(20.6f+(i%2)*1.05f,1.65f-(i/2)*.36f,16.0f),state,me[i]);
        }
        Label("Host access","HOST / INSTANCE MASTER",new Vector3(17.12f,.98f,1.38f),.075f);
        string[] actions={"PreviousSlide","NextSlide","StartTalk","StartQA","StopTimer","ToggleQA","TogglePointer","PointerLeft","PointerRight","PointerUp","PointerDown","Lounge"};
        string[] titles={"PREV SLIDE","NEXT SLIDE","15 MIN TALK","5 MIN Q&A","STOP TIMER","Q&A SIGN","POINTER","LEFT","RIGHT","UP","DOWN","END SESSION"};
        for(int i=0;i<actions.Length;i++)Button(titles[i],new Vector3(9.9f+(i%2)*1.02f,1.47f-(i/2)*.21f,11.22f),state,actions[i],.91f,.18f);
        comfort.label=Label("Comfort","LOCAL COMFORT",new Vector3(10.65f,1.92f,1.40f),.09f);
        Button("REDUCED MOTION",new Vector3(10.65f,1.55f,1.49f),comfort,"ToggleMotion",1.6f);
        Button("LOW EMISSION",new Vector3(10.65f,1.21f,1.49f),comfort,"ToggleEmission",1.6f);
        Button("DJ VISUALS",new Vector3(10.65f,.87f,1.49f),comfort,"ToggleDJVisuals",1.6f);
        if(!Mobile)BuildMirror(comfort);
        // Both main portal and stair-side portal remain reachable in every mode.
        Portal("TO 2F",new Vector3(18.75f,1.15f,1.8f),new Vector3(18,4.9f,3.65f));
        Portal("TO 1F",new Vector3(18.7f,5.95f,3.2f),new Vector3(18,.1f,2.3f));
        Portal("ORBIT CAFE",new Vector3(6.6f,1.15f,11.4f),new Vector3(6.35f,4.9f,15.4f));
        Portal("ANCHOR BAR",new Vector3(6.7f,5.95f,15.8f),new Vector3(6.35f,.1f,11.0f));
        int si=0;
        foreach(SeatRecord r in data.seat_anchors)
        {
            GameObject o=new GameObject("INT_Seat_"+(si++));o.transform.SetParent(Group(r.group).transform,false);o.transform.position=V(r.position);o.transform.rotation=Quaternion.Euler(0,180-r.yaw*Mathf.Rad2Deg,0);
            BoxCollider hit=o.AddComponent<BoxCollider>();hit.size=new Vector3(.48f,.15f,.45f);
            VRC.SDK3.Components.VRCStation st=o.AddComponent<VRC.SDK3.Components.VRCStation>();st.PlayerMobility=VRC.SDKBase.VRCStation.Mobility.Immobilize;st.seated=true;hit.isTrigger=true;
            Transform enter=new GameObject("Enter").transform;enter.SetParent(o.transform,false);Transform exit=new GameObject("Exit").transform;exit.SetParent(o.transform,false);exit.localPosition=new Vector3(0,-.42f,.8f);
            st.stationEnterPlayerLocation=enter;st.stationExitPlayerLocation=exit;
            CommonsSeat seat=o.AddUdonSharpComponent<CommonsSeat>();seat.station=st;seat.ApplyProxyModifications();InteractSettings(seat,"Sit (optional)",1.8f);
        }
        // Local topic card: no network spam for decorative affordances.
        TextMesh topic=Label("Topic","WHAT ARE YOU BUILDING?",new Vector3(5.9f,1.38f,6.10f),.075f);
        GameObject tc=GameObject.CreatePrimitive(PrimitiveType.Cube);tc.name="INT_TopicCard";tc.transform.position=new Vector3(5.9f,1.34f,6.14f);tc.transform.localScale=new Vector3(.64f,.22f,.025f);tc.GetComponent<Renderer>().sharedMaterial=materials["MAT_Black"];
        CommonsTopicCard card=tc.AddUdonSharpComponent<CommonsTopicCard>();card.card=topic;card.topics=new[]{"WHAT ARE YOU BUILDING?","WHAT CHANGED YOUR MIND?","SHOW US A SMALL EXPERIMENT.","WHAT WOULD YOU AUTOMATE?"};card.ApplyProxyModifications();InteractSettings(card,"Next topic (local)",2f);
        AudioSource ambience=Audio("Room tone","commons_roomtone",new Vector3(14,3,9),.13f);
        AudioSource music=Audio("Original ambient loop","commons_ambient",new Vector3(14,3,12),.12f);zones.ambience=ambience;zones.music=music;
        zones.dance=Audio("Original DJ loop","commons_dj",new Vector3(14,5.9f,13.3f),0);
        SetupVideo(state,zones,media);
        new GameObject("EventSystem",typeof(EventSystem),typeof(StandaloneInputModule));
        SetupLighting(data);
        GameObject desc=new GameObject("VRCWorld");var descriptor=desc.AddComponent<VRCSceneDescriptor>();
        Transform spawn=new GameObject("Spawn_Entry").transform;spawn.position=new Vector3(14,.1f,1.2f);descriptor.spawns=new[]{spawn};descriptor.capacity=32;
        SerializedObject ds=new SerializedObject(descriptor);SerializedProperty rh=ds.FindProperty("RespawnHeightY");if(rh!=null)rh.floatValue=-12;ds.ApplyModifiedPropertiesWithoutUndo();
        // SDK stores its blueprint only after the owner uploads. No blueprint ID is preassigned.
        LightProbeGroup probes=new GameObject("LGT_LightProbes").AddComponent<LightProbeGroup>();List<Vector3> ps=new List<Vector3>();
        for(int x=2;x<28;x+=4)for(int z=2;z<18;z+=4)foreach(float y in new[]{1f,3f,5.6f,7.8f})ps.Add(new Vector3(x,y,z));probes.probePositions=ps.ToArray();
        if(!Mobile)
        {
            ReflectionProbe rp=new GameObject("LGT_BakedReflection").AddComponent<ReflectionProbe>();rp.transform.position=new Vector3(14,4,9);rp.size=new Vector3(28,10,18);rp.mode=ReflectionProbeMode.Baked;rp.resolution=128;rp.boxProjection=true;
        }
        zones.ApplyProxyModifications();comfort.ApplyProxyModifications();state.ApplyProxyModifications();
        state.academicRoot.SetActive(false);pointer.SetActive(false);comfort.Refresh();
        EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene(Out+"/TheCommons.unity",true)};
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),Out+"/TheCommons.unity");AssetDatabase.SaveAssets();
        Debug.Log("THE COMMONS scene created: "+Out+". Run Bake lighting, then SDK Build & Test. Unity/runtime validation remains required.");
        if(interactive && !Application.isBatchMode)
            EditorUtility.DisplayDialog("THE COMMONS", "Scene created. Next: The Commons > Bake lighting, then VRChat SDK > Build & Test.\n\nNo upload has occurred.", "OK");
    }
    static GameObject Quad(string name,Vector3 center,float w,float h,float yaw,Material m)
    {
        GameObject o=new GameObject(name);o.transform.position=center;o.transform.rotation=Quaternion.Euler(0,yaw,0);
        Mesh mesh=new Mesh();mesh.name=name;mesh.vertices=new[]{new Vector3(-w/2,-h/2,0),new Vector3(w/2,-h/2,0),new Vector3(w/2,h/2,0),new Vector3(-w/2,h/2,0)};mesh.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};mesh.triangles=new[]{0,2,1,0,3,2};mesh.RecalculateNormals();
        SaveAsset(mesh,Out+"/Meshes/"+name+".asset");o.AddComponent<MeshFilter>().sharedMesh=mesh;o.AddComponent<MeshRenderer>().sharedMaterial=m;return o;
    }
    static TextMesh Label(string name,string content,Vector3 p,float size)
    {
        GameObject o=new GameObject("LABEL_"+name);o.transform.position=p;TextMesh text=o.AddComponent<TextMesh>();text.text=content;text.anchor=TextAnchor.MiddleCenter;text.alignment=TextAlignment.Center;text.fontSize=48;text.characterSize=size*10f/48f;text.color=new Color(.87f,.92f,.94f);return text;
    }
    static void Button(string name,Vector3 p,UdonSharpBehaviour target,string method,float w=.95f,float h=.28f)
    {
        GameObject o=GameObject.CreatePrimitive(PrimitiveType.Cube);o.name="INT_"+method;o.transform.position=p;o.transform.localScale=new Vector3(w,h,.075f);o.GetComponent<Renderer>().sharedMaterial=materials["MAT_Steel"];
        Label(name,name,p+new Vector3(0,0,-.046f),h*.35f);
        CommonsButton b=o.AddUdonSharpComponent<CommonsButton>();b.target=target;b.eventName=method;b.ApplyProxyModifications();InteractSettings(b,name,2f);
    }
    static void Portal(string name,Vector3 p,Vector3 destination)
    {
        GameObject o=GameObject.CreatePrimitive(PrimitiveType.Cube);o.name="INT_Portal_"+name;o.transform.position=p;o.transform.localScale=new Vector3(.66f,.5f,.12f);o.GetComponent<Renderer>().sharedMaterial=materials["MAT_Cyan"];
        Label(name,name,p+new Vector3(0,0,-.072f),.10f);
        Transform target=new GameObject("TP_"+name).transform;target.position=destination;
        CommonsPortal portal=o.AddUdonSharpComponent<CommonsPortal>();portal.destination=target;portal.ApplyProxyModifications();InteractSettings(portal,name,2.5f);
    }
    static AudioSource Audio(string name,string clip,Vector3 p,float volume)
    {
        GameObject o=new GameObject("AUD_"+name);o.transform.position=p;AudioSource a=o.AddComponent<AudioSource>();a.clip=AssetDatabase.LoadAssetAtPath<AudioClip>(Root+"/Audio/"+clip+".wav");a.loop=true;a.playOnAwake=true;a.volume=volume;a.spatialBlend=0;return a;
    }
    static void InteractSettings(UdonSharpBehaviour proxy,string text,float distance)
    {var b=UdonSharpEditorUtility.GetBackingUdonBehaviour(proxy);b.interactText=text;b.proximity=distance;EditorUtility.SetDirty(b);}
    static void SetupVideo(CommonsWorldState state,CommonsAudioZones zones,Material media)
    {
        GameObject go=new GameObject("AV_SyncedVideo");VRCUnityVideoPlayer player=go.AddComponent<VRCUnityVideoPlayer>();
        RenderTexture rt=new RenderTexture(Mobile?1024:1920,Mobile?576:1080,0,RenderTextureFormat.ARGB32);rt.name="VideoOutput";SaveAsset(rt,Out+"/VideoOutput.renderTexture");
        AudioSource audio=go.AddComponent<AudioSource>();audio.playOnAwake=false;audio.spatialBlend=0;audio.volume=.7f;
        player.autoPlay=false;player.loop=false;player.renderMode=VRCUnityVideoPlayer.VideoRenderMode.RenderTexture;player.targetTexture=rt;player.targetAudioSources=new[]{audio};player.maximumResolution=Mobile?720:1080;
        CommonsVideoSync sync=go.AddUdonSharpComponent<CommonsVideoSync>();sync.state=state;sync.player=player;sync.output=rt;sync.screen=media;state.videoSync=sync;zones.videoAudio=audio;
        sync.status=Label("VideoStatus","HOST VIDEO / HTTPS URL",new Vector3(24.35f,2.18f,16.05f),.11f);
        GameObject canvasGO=new GameObject("INT_VideoURL",typeof(RectTransform),typeof(Canvas),typeof(GraphicRaycaster));Canvas canvas=canvasGO.GetComponent<Canvas>();canvas.renderMode=RenderMode.WorldSpace;canvasGO.transform.position=new Vector3(24.35f,1.7f,16.12f);canvasGO.transform.localScale=Vector3.one*.003f;
        RectTransform rect=canvasGO.GetComponent<RectTransform>();rect.sizeDelta=new Vector2(800,100);
        canvasGO.AddComponent<VRCUiShape>();BoxCollider click=canvasGO.AddComponent<BoxCollider>();click.size=new Vector3(800,100,1);
        Image background=canvasGO.AddComponent<Image>();background.color=new Color(.06f,.09f,.12f);
        GameObject textGO=new GameObject("URL Text",typeof(RectTransform));textGO.transform.SetParent(canvasGO.transform,false);RectTransform tr=textGO.GetComponent<RectTransform>();tr.anchorMin=Vector2.zero;tr.anchorMax=Vector2.one;tr.offsetMin=new Vector2(15,8);tr.offsetMax=new Vector2(-15,-8);
        Text text=textGO.AddComponent<Text>();text.font=Resources.GetBuiltinResource<Font>("Arial.ttf");text.fontSize=24;text.alignment=TextAnchor.MiddleLeft;text.color=Color.white;
        VRCUrlInputField input=canvasGO.AddComponent<VRCUrlInputField>();input.textComponent=text;input.targetGraphic=background;sync.urlInput=input;
        Button("LOAD URL",new Vector3(23.8f,1.23f,16.12f),sync,"LoadFromField");Button("STOP VIDEO",new Vector3(24.9f,1.23f,16.12f),sync,"StopPlayback");
        sync.ApplyProxyModifications();
    }
    static void BuildMirror(CommonsComfort comfort)
    {
        Shader shader=Shader.Find("FX/MirrorReflection");
        if(shader==null){Debug.LogWarning("SDK mirror shader unavailable; mirror omitted.");return;}
        Material m=new Material(shader);SaveAsset(m,Out+"/Materials/Mirror.mat");
        GameObject o=Quad("INT_Mirror",new Vector3(27.38f,6.35f,3.0f),1.3f,1.6f,90,m);o.AddComponent<VRCMirrorReflection>();comfort.mirrorRoot=o;o.SetActive(false);
        Button("MIRROR (LOCAL)",new Vector3(25.7f,5.8f,2.1f),comfort,"ToggleMirror",1.4f);
    }
    static void SetupLighting(Manifest data)
    {
        RenderSettings.ambientMode=AmbientMode.Trilight;RenderSettings.ambientSkyColor=new Color(.18f,.23f,.30f);RenderSettings.ambientEquatorColor=new Color(.12f,.14f,.17f);RenderSettings.ambientGroundColor=new Color(.08f,.075f,.065f);
        RenderSettings.fog=true;RenderSettings.fogMode=FogMode.ExponentialSquared;RenderSettings.fogDensity=.009f;RenderSettings.fogColor=new Color(.026f,.036f,.06f);
        foreach(LightRecord r in data.lights)
        {
            GameObject o=new GameObject(r.name);o.transform.position=V(r.position);Light l=o.AddComponent<Light>();l.type=LightType.Point;l.lightmapBakeType=LightmapBakeType.Baked;l.range=Mathf.Max(5,r.size*2.5f);l.intensity=Mathf.Clamp(r.power/130f,.5f,6f);l.color=new Color(r.color[0],r.color[1],r.color[2]);l.shadows=LightShadows.Soft;
        }
        LightingSettings settings=new LightingSettings();settings.name="Commons_Lighting";settings.bakedGI=true;settings.realtimeGI=false;settings.lightmapper=LightingSettings.Lightmapper.ProgressiveCPU;settings.lightmapResolution=Mobile?12:20;settings.lightmapMaxSize=Mobile?1024:2048;settings.indirectSampleCount=64;settings.directSampleCount=32;settings.environmentSampleCount=64;
        SaveAsset(settings,Out+"/LightingSettings.lighting");Lightmapping.lightingSettings=settings;
    }
    [MenuItem("The Commons/Bake lighting")]
    public static void Bake() { Lightmapping.BakeAsync(); }
}

public class CommonsAssetImporter : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        if(!assetPath.StartsWith("Assets/TheCommons/"))return;
        TextureImporter t=(TextureImporter)assetImporter;t.mipmapEnabled=true;t.sRGBTexture=true;
        bool artwork=assetPath.EndsWith("relay_controller_albedo.png")||assetPath.EndsWith("bar_labels_albedo.png")||assetPath.EndsWith("cafe_props_albedo.png");
        t.wrapMode=assetPath.Contains("/Textures/")&&!artwork?TextureWrapMode.Mirror:TextureWrapMode.Clamp;
        t.maxTextureSize=assetPath.Contains("/Media/")?2048:1024;t.anisoLevel=4;t.textureCompression=TextureImporterCompression.Compressed;
        TextureImporterPlatformSettings android=t.GetPlatformTextureSettings("Android");android.overridden=true;android.maxTextureSize=assetPath.Contains("/Media/")?1024:512;android.format=TextureImporterFormat.ASTC_6x6;t.SetPlatformTextureSettings(android);
    }
    void OnPreprocessAudio()
    {
        if(!assetPath.StartsWith("Assets/TheCommons/Audio/"))return;
        AudioImporter a=(AudioImporter)assetImporter;AudioImporterSampleSettings settings=a.defaultSampleSettings;settings.loadType=AudioClipLoadType.CompressedInMemory;settings.compressionFormat=AudioCompressionFormat.Vorbis;settings.quality=.55f;a.defaultSampleSettings=settings;
    }
}
#endif
