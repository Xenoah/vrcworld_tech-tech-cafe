using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.Manual)]
public class CommonsLightingModes : UdonSharpBehaviour
{
    [UdonSynced] public int lightingMode; // Warm / Cyber / Disco, independent of seating and time.
    public CommonsWorldState state;
    public CommonsComfort comfort;
    public Material[] roomMaterials;
    public float[] emissionStrengths;
    public Material[] haloMaterials;
    public Material[] beamMaterials;
    public Light[] accentLights;
    public Transform[] beams;
    public GameObject laserRoot;
    public TextMesh[] labels;
    public Vector3 targetCenter = new Vector3(14f,2.8f,10f);
    public Vector3 targetRadius = new Vector3(2.6f,.7f,1f);
    private float nextColorTick;
    private bool inCafe = true;

    void Start() { Refresh(); }
    public override void OnDeserialization() { Refresh(); }
    public void Warm() { Select(0); }
    public void Cyber() { Select(1); }
    public void Disco() { Select(2); }
    private void Select(int value)
    {
        if (state == null || !state.CanControl()) return;
        if (!Networking.IsOwner(gameObject)) Networking.SetOwner(Networking.LocalPlayer,gameObject);
        if (!Networking.IsOwner(gameObject)) return;
        lightingMode = value; Refresh(); RequestSerialization();
    }
    public void Refresh()
    {
        lightingMode = Mathf.Clamp(lightingMode,0,2);
        if (Utilities.IsValid(Networking.LocalPlayer))
        {
            float x = Networking.LocalPlayer.GetPosition().x;
            inCafe = x > -15f && x < 100f;
        }
        if (laserRoot != null) laserRoot.SetActive(lightingMode == 2 && inCafe && (comfort == null || comfort.lasersEnabled));
        if (labels != null) for (int i=0;i<labels.Length;i++)
            if (labels[i]!=null) labels[i].text = "LIGHTING / " + (lightingMode == 0 ? "WARM" : lightingMode == 1 ? "CYBER" : "DISCO + LASERS");
        ApplyColors(Phase()); MoveBeams(Phase());
    }
    private float Phase()
    {
        // Use the server clock so late joiners and the owner see the same slow sweep.
        // All harmonics complete an integer number of turns in 120 seconds.
        if (comfort != null && comfort.reducedMotion) return 0f;
        return Utilities.IsValid(Networking.LocalPlayer) ? (float)(Networking.GetServerTimeInSeconds()%120.0)*Mathf.PI/60f : 0f;
    }
    private void ApplyColors(float phase)
    {
        Color primary = new Color(1f,.49f,.18f);
        Color secondary = new Color(1f,.76f,.40f);
        Color tint = new Color(1f,.91f,.77f);
        Color fill = new Color(.065f,.035f,.014f);
        if (lightingMode == 1)
        {
            primary = new Color(.05f,.78f,1f); secondary = new Color(.82f,.13f,1f);
            tint = new Color(.70f,.83f,1f); fill = new Color(.015f,.045f,.09f);
        }
        if (lightingMode == 2)
        {
            float blend = .5f+.5f*Mathf.Sin(phase*6f);
            primary = Color.Lerp(new Color(.08f,.70f,1f),new Color(1f,.12f,.49f),blend);
            secondary = Color.Lerp(new Color(.70f,.10f,1f),new Color(.08f,1f,.60f),blend);
            tint = new Color(.69f,.68f,.88f); fill = primary*.045f;
        }
        float gain = (comfort != null && comfort.lowEmission ? .35f : 1f) * (state != null && state.mode == 3 ? .4f : 1f);
        if (roomMaterials != null) for (int i=0;i<roomMaterials.Length;i++)
        {
            Material m = roomMaterials[i]; if (m == null) continue;
            m.SetColor("_RoomTint",tint); m.SetColor("_RoomFill",fill*gain);
            if (emissionStrengths != null && i < emissionStrengths.Length && emissionStrengths[i] > 0)
                m.SetColor("_EmissionColor",(i%2==0 ? primary : secondary)*emissionStrengths[i]);
        }
        if (haloMaterials != null) for (int i=0;i<haloMaterials.Length;i++)
            if (haloMaterials[i]!=null) haloMaterials[i].SetColor("_Color",i%2==0?primary:secondary);
        if (accentLights != null) for (int i=0;i<accentLights.Length;i++)
            if (accentLights[i]!=null)
            {
                accentLights[i].enabled=inCafe;
                accentLights[i].color=i%2==0?primary:secondary;
                accentLights[i].intensity=(lightingMode==0?.65f:1.1f)*gain;
            }
        if (beamMaterials != null) for (int i=0;i<beamMaterials.Length;i++)
            if (beamMaterials[i]!=null)
            {
                beamMaterials[i].SetColor("_Color",i%2==0?primary:secondary);
                beamMaterials[i].SetFloat("_Intensity",.65f*gain);
            }
    }
    private void MoveBeams(float phase)
    {
        if (lightingMode != 2 || !inCafe || beams == null || (comfort != null && !comfort.lasersEnabled)) return;
        for (int i=0;i<beams.Length;i++)
        {
            Transform beam=beams[i]; if (beam==null) continue;
            float spread=(i%6)/5f*2f-1f;
            Vector3 target=targetCenter+new Vector3(targetRadius.x*Mathf.Sin(phase*4f+spread*1.15f),targetRadius.y*Mathf.Sin(phase*3f+i*.72f),targetRadius.z*Mathf.Cos(phase*2f+i*.8f));
            Vector3 direction=target-beam.position;
            beam.rotation=Quaternion.LookRotation(direction);
            beam.localScale=new Vector3(1f,1f,direction.magnitude);
        }
    }
    void Update()
    {
        if (Utilities.IsValid(Networking.LocalPlayer))
        {
            float x=Networking.LocalPlayer.GetPosition().x;bool inside=x > -15f && x < 100f;
            if (inside!=inCafe) { inCafe=inside; Refresh(); }
        }
        if (lightingMode != 2 || !inCafe) return;
        float phase=Phase();MoveBeams(phase);
        if (Time.time < nextColorTick) return;
        nextColorTick=Time.time+.1f;ApplyColors(phase);
    }
    public override bool OnOwnershipRequest(VRCPlayerApi requestingPlayer,VRCPlayerApi newOwner)
    { return state != null && (!state.hostLocked || (Utilities.IsValid(requestingPlayer) && (requestingPlayer.isMaster || requestingPlayer.isInstanceOwner))); }
}
