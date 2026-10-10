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
        // v0.11: particle lasers. Udon emits every particle (rate 0 here) so density and
        // brightness follow the music; world-space simulation leaves sweeping trails.
        Shader laser=Shader.Find("The Commons/Laser Particle");
        if(laser==null) throw new System.InvalidOperationException("Shader not compiled: The Commons/Laser Particle. Check the Console for shader errors.");
        Material a=new Material(laser),b=new Material(a);a.name="LaserParticle_A";b.name="LaserParticle_B";
        a.enableInstancing=true;b.enableInstancing=true;
        AssetDatabase.CreateAsset(a,output+"/Materials/LaserParticle_A.mat");AssetDatabase.CreateAsset(b,output+"/Materials/LaserParticle_B.mat");modes.beamMaterials=new[]{a,b};
        int count=mobile?6:12;Transform[] beams=new Transform[count];ParticleSystem[] emitters=new ParticleSystem[count];
        for(int i=0;i<count;i++)
        {
            GameObject beam=new GameObject("LaserEmitter_"+i);beam.transform.SetParent(rootLaser.transform);
            beam.transform.position=new Vector3(i<count/2?10.2f:17.8f,4.3f,5.3f);
            ParticleSystem ps=beam.AddComponent<ParticleSystem>();
            ParticleSystem.MainModule main=ps.main;main.loop=true;main.playOnAwake=true;main.duration=1f;
            main.startLifetime=.28f;main.startSpeed=26f;main.startSize=.045f;main.startColor=Color.white;
            main.simulationSpace=ParticleSystemSimulationSpace.World;main.maxParticles=mobile?40:64;main.scalingMode=ParticleSystemScalingMode.Hierarchy;
            ParticleSystem.EmissionModule emission=ps.emission;emission.rateOverTime=0f;
            ParticleSystem.ShapeModule shape=ps.shape;shape.enabled=true;shape.shapeType=ParticleSystemShapeType.Cone;shape.angle=0f;shape.radius=.004f;
            ParticleSystemRenderer renderer=beam.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode=ParticleSystemRenderMode.Stretch;renderer.lengthScale=1f;renderer.velocityScale=.018f;
            renderer.sharedMaterial=i%2==0?a:b;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;
            renderer.maxParticleSize=1f;
            beams[i]=beam.transform;emitters[i]=ps;
        }
        modes.beamEmitters=emitters;
        modes.beams=beams;modes.Refresh();time.ApplyProxyModifications();modes.ApplyProxyModifications();return modes;
    }
}
#endif
