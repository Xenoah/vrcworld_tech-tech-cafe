#if UNITY_EDITOR
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UdonSharpEditor;

public static class CommonsLightingBuilder
{
    public static CommonsLightingModes Configure(string output,bool mobile,CommonsWorldState state,CommonsComfort comfort,CommonsTimeOfDay time)
    {
        GameObject go=new GameObject("INT_LightingModes");go.transform.SetParent(state.transform.parent);
        CommonsLightingModes modes=go.AddUdonSharpComponent<CommonsLightingModes>();modes.state=state;modes.comfort=comfort;
        Dictionary<Material,Material> copies=new Dictionary<Material,Material>();
        List<Material> room=new List<Material>(),halos=new List<Material>();List<float> powers=new List<float>();
        List<Material> daylight=new List<Material>(time.surfaces),emissive=new List<Material>(comfort.luminousMaterials),glows=new List<Material>(time.glows);
        foreach(Renderer renderer in Object.FindObjectsOfType<Renderer>(true))
        {
            string root=renderer.transform.root.name;
            if(!(root.StartsWith("ARCH_") || root.StartsWith("FURN_") || root.StartsWith("MODE_") || root.StartsWith("LGT_") || root.StartsWith("AV_")))continue;
            if(renderer.bounds.center.x < -15f || renderer.bounds.center.x >= 100f)continue;
            Material source=renderer.sharedMaterial;if(source==null)continue;
            bool halo=source.shader.name=="The Commons/Soft Fixture Glow";
            if(!halo && source.shader.name!="The Commons/Surface" && source.shader.name!="The Commons/Flat Light")continue;
            // Cafe-only copies prevent shared steel / neon from recoloring the
            // remote FPV course, kart hall, city or portal destination colors.
            if(!copies.ContainsKey(source))
            {
                Material copy=new Material(source);copy.name=source.name+"_Cafe";
                AssetDatabase.CreateAsset(copy,output+"/Materials/"+copy.name+".mat");copies.Add(source,copy);
                if(halo){halos.Add(copy);glows.Add(copy);}
                else
                {
                    Color e=source.GetColor("_EmissionColor");float strength=Mathf.Max(e.r,Mathf.Max(e.g,e.b));
                    room.Add(copy);powers.Add(strength);daylight.Add(copy);
                    if(strength>0)emissive.Add(copy);
                }
            }
            renderer.sharedMaterial=copies[source];
        }
        modes.roomMaterials=room.ToArray();modes.emissionStrengths=powers.ToArray();modes.haloMaterials=halos.ToArray();
        time.surfaces=daylight.ToArray();time.glows=glows.ToArray();comfort.luminousMaterials=emissive.ToArray();
        List<Light> accents=new List<Light>();
        if(!mobile)foreach(Vector3 p in new[]{new Vector3(10.2f,3.8f,6f),new Vector3(17.8f,3.8f,6f),new Vector3(10.2f,3.8f,11f),new Vector3(17.8f,3.8f,11f)})
        {
            Light light=new GameObject("LGT_CafeAccent_PC").AddComponent<Light>();light.transform.SetParent(go.transform);
            light.transform.position=p;light.type=LightType.Point;light.range=7f;light.shadows=LightShadows.None;
            light.lightmapBakeType=LightmapBakeType.Realtime;light.renderMode=LightRenderMode.Auto;accents.Add(light);
        }
        modes.accentLights=accents.ToArray();
        GameObject rootLaser=new GameObject("LGT_DiscoLasers");rootLaser.transform.SetParent(go.transform);modes.laserRoot=rootLaser;
        Mesh mesh=BeamMesh();AssetDatabase.CreateAsset(mesh,output+"/Meshes/DiscoBeam.asset");
        Material a=new Material(Shader.Find("The Commons/Disco Beam")),b=new Material(a);a.name="DiscoBeam_A";b.name="DiscoBeam_B";
        AssetDatabase.CreateAsset(a,output+"/Materials/DiscoBeam_A.mat");AssetDatabase.CreateAsset(b,output+"/Materials/DiscoBeam_B.mat");modes.beamMaterials=new[]{a,b};
        int count=mobile?6:12;Transform[] beams=new Transform[count];
        for(int i=0;i<count;i++)
        {
            GameObject beam=new GameObject("DiscoBeam_"+i);beam.transform.SetParent(rootLaser.transform);
            beam.transform.position=new Vector3(i<count/2?10.2f:17.8f,4.3f,5.3f);
            beam.AddComponent<MeshFilter>().sharedMesh=mesh;MeshRenderer renderer=beam.AddComponent<MeshRenderer>();
            renderer.sharedMaterial=i%2==0?a:b;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;
            beams[i]=beam.transform;
        }
        modes.beams=beams;modes.Refresh();time.ApplyProxyModifications();modes.ApplyProxyModifications();return modes;
    }
    static Mesh BeamMesh()
    {
        // Two crossed, finite ribbons, 8 vertices / 4 triangles per ray. Depth
        // testing and finite lengths prevent beams drawing through walls.
        const float w=.024f;Mesh m=new Mesh();m.name="DiscoBeam";
        m.vertices=new[]{new Vector3(-w,0,0),new Vector3(w,0,0),new Vector3(w,0,1),new Vector3(-w,0,1),new Vector3(0,-w,0),new Vector3(0,w,0),new Vector3(0,w,1),new Vector3(0,-w,1)};
        m.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up,Vector2.zero,Vector2.right,Vector2.one,Vector2.up};
        m.triangles=new[]{0,1,2,0,2,3,4,5,6,4,6,7};m.RecalculateBounds();return m;
    }
}
#endif
