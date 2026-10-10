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
    public Material[] beamMaterials;      // laser particle materials (A / B)
    public Light[] accentLights;
    public Transform[] beams;             // particle emitters; particles leave along local +Z
    public ParticleSystem[] beamEmitters;
    public GameObject laserRoot;
    public TextMesh[] labels;
    public Vector3 targetCenter = new Vector3(14f,2.8f,10f);
    public Vector3 targetRadius = new Vector3(2.6f,.7f,1f);
    [Header("Music sync (v0.11)")]
    public CommonsAdaptiveMusic music;    // optional; without it the lasers follow the server clock
    public float beamRate = 70f;          // particles per second per beam at rest
    private float nextColorTick;
    private bool inCafe = true;
    private float[] emitCarry;

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
    private bool LasersOn() { return lightingMode == 2 && inCafe && (comfort == null || comfort.lasersEnabled); }
    private bool Reduced() { return comfort != null && comfort.reducedMotion; }
    public void Refresh()
    {
        lightingMode = Mathf.Clamp(lightingMode,0,2);
        if (Utilities.IsValid(Networking.LocalPlayer))
        {
            float x = Networking.LocalPlayer.GetPosition().x;
            inCafe = x > -15f && x < 100f;
        }
        if (laserRoot != null) laserRoot.SetActive(LasersOn());
        if (labels != null) for (int i=0;i<labels.Length;i++)
            if (labels[i]!=null) labels[i].text = "LIGHTING / " + (lightingMode == 0 ? "WARM" : lightingMode == 1 ? "CYBER" : "DISCO + LASERS");
        ApplyColors(Phase()); MoveBeams();
    }
    private float Phase()
    {
        // Use the server clock so late joiners and the owner see the same slow sweep.
        // All harmonics complete an integer number of turns in 120 seconds.
        if (Reduced()) return 0f;
        return Utilities.IsValid(Networking.LocalPlayer) ? (float)(Networking.GetServerTimeInSeconds()%120.0)*Mathf.PI/60f : 0f;
    }
    private float Kick() { return music == null || Reduced() ? 0f : music.KickPulse(); }
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
            if (music != null)
            {
                // DISCO follows the chord of each bar (cross-faded over one beat).
                primary = music.ChordColor(false); secondary = music.ChordColor(true);
            }
            else
            {
                float blend = .5f+.5f*Mathf.Sin(phase*6f);
                primary = Color.Lerp(new Color(.08f,.70f,1f),new Color(1f,.12f,.49f),blend);
                secondary = Color.Lerp(new Color(.70f,.10f,1f),new Color(.08f,1f,.60f),blend);
            }
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
        float kick = lightingMode == 2 ? Kick() : 0f;
        if (accentLights != null) for (int i=0;i<accentLights.Length;i++)
            if (accentLights[i]!=null)
            {
                accentLights[i].enabled=inCafe;
                accentLights[i].color=i%2==0?primary:secondary;
                // A soft swell on the kick (decays in ~0.3 s; never an on/off strobe).
                accentLights[i].intensity=(lightingMode==0?.65f:1.1f)*gain*(1f+.35f*kick);
            }
        if (beamMaterials != null) for (int i=0;i<beamMaterials.Length;i++)
            if (beamMaterials[i]!=null)
            {
                beamMaterials[i].SetColor("_Color",i%2==0?primary:secondary);
                beamMaterials[i].SetFloat("_Intensity",(.55f+.4f*kick)*gain);
            }
    }
    // Four bar-long laser figures, chosen by the bar of the music and blended over
    // the first beat of each bar: fan, cross, tunnel and chase.
    private Vector3 Figure(int figure, int i, int count, float beat)
    {
        int half = Mathf.Max(1, count / 2);
        int side = i < half ? -1 : 1;
        int j = i % half;
        float s = half > 1 ? j / (half - 1f) * 2f - 1f : 0f;
        float tau = Mathf.PI * 2f;
        Vector3 r = targetRadius;
        if (figure == 0) return targetCenter + new Vector3(s * r.x, r.y * Mathf.Sin(tau * beat / 2f) * .6f, side * r.z * Mathf.Sin(tau * beat / 4f));
        if (figure == 1) return targetCenter + new Vector3(-side * r.x * (.3f + .7f * Mathf.Abs(s)), r.y * Mathf.Sin(tau * beat + j), r.z * s);
        if (figure == 2)
        {
            float a = tau * beat / 4f + j * tau / half + (side > 0 ? Mathf.PI : 0f);
            return targetCenter + new Vector3(r.x * .65f * Mathf.Cos(a), r.y * .5f * Mathf.Sin(a * 2f), r.z * Mathf.Sin(a));
        }
        float lane = beat / 2f + j / (float)half;
        return targetCenter + new Vector3(-r.x + 2f * r.x * (lane - Mathf.Floor(lane)), -.3f, side * r.z * .6f);
    }
    private void MoveBeams()
    {
        if (!LasersOn() || beams == null) return;
        int bar; float beat;
        if (Reduced())
        {
            // REDUCED MOTION: a still fan, no sweeping.
            bar = 0; beat = 0f;
        }
        else if (music != null) { bar = music.Bar(); beat = music.BeatInBar(); }
        else
        {
            double beats = Networking.GetServerTimeInSeconds() * 96.0 / 60.0;
            bar = (int)(beats / 4.0 % 16.0); beat = (float)(beats % 4.0);
        }
        float blend = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(beat));
        int figure = bar % 4, previous = (bar + 3) % 4;
        for (int i=0;i<beams.Length;i++)
        {
            Transform beam=beams[i]; if (beam==null) continue;
            Vector3 target = Reduced() ? Figure(0, i, beams.Length, 0f) : Vector3.Lerp(Figure(previous, i, beams.Length, beat + 4f), Figure(figure, i, beams.Length, beat), blend);
            Vector3 direction=target-beam.position;
            if (direction.sqrMagnitude > .001f) beam.rotation=Quaternion.LookRotation(direction);
        }
    }
    private void EmitParticles()
    {
        if (!LasersOn() || beamEmitters == null) return;
        if (emitCarry == null || emitCarry.Length != beamEmitters.Length) emitCarry = new float[beamEmitters.Length];
        // Dashed beams between beats; each kick fires a dense, brighter burst that runs
        // out along the beam. REDUCED MOTION keeps a steady, unpulsed stream.
        float rate = beamRate * (Reduced() ? .8f : .45f + 1.8f * Kick());
        float add = rate * Time.deltaTime;
        for (int i=0;i<beamEmitters.Length;i++)
        {
            ParticleSystem p = beamEmitters[i]; if (p == null) continue;
            emitCarry[i] += add;
            int n = Mathf.FloorToInt(emitCarry[i]);
            if (n > 0) { emitCarry[i] -= n; p.Emit(Mathf.Min(n, 12)); }
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
        MoveBeams(); EmitParticles();
        if (Time.time < nextColorTick) return;
        nextColorTick=Time.time+.05f;ApplyColors(Phase());
    }
    public override bool OnOwnershipRequest(VRCPlayerApi requestingPlayer,VRCPlayerApi newOwner)
    { return state != null && (!state.hostLocked || (Utilities.IsValid(requestingPlayer) && (requestingPlayer.isMaster || requestingPlayer.isInstanceOwner))); }
}
