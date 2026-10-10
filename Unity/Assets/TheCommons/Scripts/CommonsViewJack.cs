using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

// Local "view jack": a head-locked overlay sphere driven by channels.
// Channels: 0 WARP, 1 GLITCH, 2 SCAN, 3 STARS, 4 DATA RAIN, 5 FADE,
//           6 TINY, 7 DREAM, 8 PULSE, 9 COMFORT.
// Categories: 0 transition, 1 attraction, 2 ambient, 3 comfort.
// Other behaviours call Pulse() for timed effects and SetHold() for effects
// that last while a condition is true. Settings decide what is allowed.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsViewJack : UdonSharpBehaviour
{
    public Renderer overlay;
    public Material material;
    public CommonsExperienceSettings settings;
    public CommonsLightingModes lighting;
    public CommonsWorldState state;
    public CommonsAdaptiveMusic music;
    public float transitionLead = .55f;   // seconds from button press to teleport
    public float transitionTail = .7f;    // fade-out after the teleport
    private string[] props = new string[] { "_Warp", "_Glitch", "_Scan", "_Stars", "_Rain", "_Fade", "_Tiny", "_Dream", "_Pulse", "_Comfort" };
    private float[] hold = new float[10];
    private int[] holdCategory = new int[10];
    private float[] pulseStart = new float[10];
    private float[] pulseEnd = new float[10];
    private int[] pulseCategory = new int[10];
    private float[] current = new float[10];
    private float[] ambient = new float[10];
    private bool visible;
    private float nextAmbient;
    private bool riding;

    void Start()
    {
        for (int i = 0; i < 10; i++) { pulseEnd[i] = -1f; holdCategory[i] = 1; }
        if (overlay != null) overlay.enabled = false;
    }

    public void Pulse(int channel, float seconds, int category)
    {
        if (channel < 0 || channel > 9) return;
        pulseStart[channel] = Time.time;
        pulseEnd[channel] = Time.time + Mathf.Max(.2f, seconds);
        pulseCategory[channel] = category;
    }
    public void SetHold(int channel, float weight, int category)
    {
        if (channel < 0 || channel > 9) return;
        hold[channel] = Mathf.Clamp01(weight);
        holdCategory[channel] = category;
    }
    public void ClearAttractionHolds()
    {
        for (int i = 0; i < 10; i++) if (holdCategory[i] == 1 || holdCategory[i] == 3) hold[i] = 0f;
    }
    public void SetRiding(bool value) { riding = value; }
    public bool TransitionsEnabled() { return settings != null && settings.CategoryAllowed(0); }
    // Portal / lift helper: warp in, black-out at the teleport, warp out.
    public void BeginTransition(Color fadeColor)
    {
        if (material != null) material.SetColor("_FadeColor", fadeColor);
        Pulse(0, transitionLead + transitionTail + .3f, 0);
        Pulse(5, transitionLead + transitionTail, 0);
    }

    private float Envelope(int i)
    {
        if (pulseEnd[i] < 0f || Time.time > pulseEnd[i]) return 0f;
        float length = pulseEnd[i] - pulseStart[i];
        float k = (Time.time - pulseStart[i]) / length;
        // FADE peaks at the teleport moment; other channels rise fast and decay.
        if (i == 5)
        {
            float peak = Mathf.Clamp01(transitionLead / length);
            return k < peak ? Mathf.SmoothStep(0f, 1f, k / Mathf.Max(.01f, peak)) : 1f - Mathf.SmoothStep(0f, 1f, (k - peak) / Mathf.Max(.01f, 1f - peak));
        }
        return Mathf.Clamp01(k * 6f) * (1f - Mathf.SmoothStep(.55f, 1f, k));
    }
    private void UpdateAmbient()
    {
        for (int i = 0; i < 10; i++) ambient[i] = 0f;
        if (riding || settings == null || !settings.CategoryAllowed(2) || !Utilities.IsValid(Networking.LocalPlayer)) return;
        Vector3 p = Networking.LocalPlayer.GetPosition();
        if (p.x < -15f || p.x >= 100f || p.y > 30f) return;   // cafe only
        int mode = lighting == null ? 0 : lighting.lightingMode;
        if (mode == 0) ambient[7] = .2f;
        if (mode == 1) ambient[2] = .22f;
        if (mode == 2 && settings.fxBeatPulse) ambient[8] = .6f;
        if (state != null && state.mode == 2 && settings.fxBeatPulse) ambient[8] = .6f;
    }
    void Update()
    {
        if (settings == null || material == null) return;
        if (Time.time >= nextAmbient) { nextAmbient = Time.time + .5f; UpdateAmbient(); }
        float gain = settings.ViewFxGain();
        bool reduced = settings.ReducedMotion();
        float k = Mathf.Min(1f, Time.deltaTime * 5f);
        bool any = false;
        for (int i = 0; i < 10; i++)
        {
            float target = 0f;
            if (settings.CategoryAllowed(holdCategory[i])) target = hold[i];
            if (pulseEnd[i] >= 0f && settings.CategoryAllowed(pulseCategory[i])) target = Mathf.Max(target, Envelope(i));
            target = Mathf.Max(target, ambient[i]);
            if (i != 9 && i != 5) target *= gain;
            if (i == 5 && !settings.CategoryAllowed(0)) target = 0f;
            if (reduced && (i == 0 || i == 1 || i == 4)) target *= .6f;
            float rate = i == 5 ? 1f : k;
            current[i] = Mathf.Lerp(current[i], target, rate);
            if (current[i] < .002f) current[i] = 0f;
            if (current[i] > 0f) any = true;
        }
        if (any != visible) { visible = any; if (overlay != null) overlay.enabled = any; }
        if (!any) return;
        for (int i = 0; i < 10; i++) material.SetFloat(props[i], current[i]);
        material.SetFloat("_Motion", reduced ? 0f : 1f);
        if (current[8] > 0f && music != null) material.SetFloat("_Beat", music.BeatPhase());
        if (lighting != null && lighting.lightingMode == 2)
            material.SetColor("_PulseColor", Color.Lerp(new Color(.08f, .7f, 1f), new Color(1f, .12f, .49f), .5f + .5f * Mathf.Sin(Time.time * .3f)));
    }
    public override void PostLateUpdate()
    {
        if (!visible || overlay == null) return;
        VRCPlayerApi p = Networking.LocalPlayer;
        if (!Utilities.IsValid(p)) return;
        VRCPlayerApi.TrackingData head = p.GetTrackingData(VRCPlayerApi.TrackingDataType.Head);
        Transform t = overlay.transform;
        t.SetPositionAndRotation(head.position, head.rotation);
        // Keep the sphere outside the near clip for giant avatars and inside tiny ones.
        float scale = Mathf.Clamp(p.GetAvatarEyeHeightAsMeters() / 1.6f, .25f, 5f) * 1.6f;
        t.localScale = new Vector3(scale, scale, scale);
    }
}
