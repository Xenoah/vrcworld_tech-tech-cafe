using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

// Adaptive house music. Seven key- and tempo-locked stems loop together and
// cross-fade by activity mode, lighting, time of day, where the local player
// is and whether they are on the DATA STREAM ride. Playback position follows
// the server clock so everyone in the instance hears the same bar.
// Stems: 0 pad, 1 keys, 2 bass, 3 soft beat, 4 dance beat, 5 arp, 6 sparkle.
// SFX:   0 whoosh, 1 glitch, 2 chime, 3 grow, 4 shrink, 5 click, 6 lift.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsAdaptiveMusic : UdonSharpBehaviour
{
    public AudioSource[] stems;
    public float[] stemTrim = new float[] { .8f, .7f, .75f, .65f, .7f, .55f, .6f };
    public AudioSource sfxSource;
    public AudioClip[] sfx;
    public float bpm = 96f;
    public float masterVolume = .5f;
    public float fadeSpeed = .8f;
    public CommonsWorldState state;
    public CommonsLightingModes lighting;
    public CommonsTimeOfDay timeOfDay;
    public CommonsExperienceSettings settings;
    public CommonsOrbitDeck deck;
    private float[] target;
    private float[] mix = new float[7];
    private bool riding;
    private float rideEnergy;
    private bool rideInCafe;
    private float nextRefresh;
    private float nextSync;

    void Start()
    {
        target = new float[stems == null ? 0 : stems.Length];
        if (stems != null) for (int i = 0; i < stems.Length; i++) if (stems[i] != null) { stems[i].volume = 0f; stems[i].loop = true; }
        SendCustomEventDelayedSeconds("Resync", 1f);
        Refresh();
    }
    public float BeatPhase()
    {
        double seconds = stems != null && stems.Length > 0 && stems[0] != null && stems[0].isPlaying ? stems[0].time : Networking.GetServerTimeInSeconds();
        double beats = seconds * bpm / 60.0;
        return (float)(beats % 1.0);
    }
    public void Resync()
    {
        SendCustomEventDelayedSeconds("Resync", 8f);
        if (stems == null || stems.Length == 0 || stems[0] == null || stems[0].clip == null) return;
        float length = stems[0].clip.length;
        float expected = (float)(Networking.GetServerTimeInSeconds() % length);
        float drift = Mathf.Abs(Mathf.DeltaAngle(stems[0].time / length * 360f, expected / length * 360f)) / 360f * length;
        bool jump = drift > .08f || !stems[0].isPlaying;
        int reference = stems[0].timeSamples;
        for (int i = 0; i < stems.Length; i++)
        {
            AudioSource s = stems[i];
            if (s == null || s.clip == null) continue;
            if (!s.isPlaying) s.Play();
            if (jump) s.time = Mathf.Min(expected, s.clip.length - .01f);
            else if (i > 0 && Mathf.Abs(s.timeSamples - reference) > 1024) s.timeSamples = Mathf.Min(reference, s.clip.samples - 1);
        }
    }
    public void SetRiding(bool value) { riding = value; Refresh(); }
    public void SetRideEnergy(float energy, bool inCafe) { rideEnergy = energy; rideInCafe = inCafe; }
    public void PlaySfx(int id)
    {
        if (sfxSource == null || sfx == null || id < 0 || id >= sfx.Length || sfx[id] == null) return;
        sfxSource.PlayOneShot(sfx[id], .6f);
    }
    private int Area()
    {
        if (!Utilities.IsValid(Networking.LocalPlayer)) return 0;
        Vector3 p = Networking.LocalPlayer.GetPosition();
        if (p.x < -15f) return 1;
        if (p.x >= 100f) return 2;
        if (p.y > 60f) return 3;
        if (p.x > 20.1f && p.x < 27.5f && p.y > 4.65f && p.y < 8.5f && p.z > 1f && p.z < 7.8f) return 4;   // ARCHIVE quiet room
        if (p.x > 21.3f && p.x < 27.8f && p.y > 4.6f && p.y < 9f && p.z > 9f && p.z < 16.7f) return 5;   // HORIZON terrace
        return 0;
    }
    public void Refresh()
    {
        // Other behaviours may call this before Start(); Udon start order is not defined.
        if (stems == null) return;
        if (target == null || target.Length != stems.Length) target = new float[stems.Length];
        for (int i = 0; i < 7; i++) mix[i] = 0f;
        int area = Area();
        if (riding)
        {
            float e = rideEnergy;
            mix[0] = .55f; mix[1] = .2f; mix[2] = .45f + .45f * e; mix[5] = .75f; mix[6] = .55f - .3f * e;
            if (rideInCafe) mix[3] = .8f; else mix[4] = .35f + .6f * e;
        }
        else if (area == 3)
        {
            mix[0] = .75f; mix[1] = .3f; mix[2] = .3f; mix[5] = .35f; mix[6] = .75f;
        }
        else if (area == 0 || area == 4 || area == 5)
        {
            bool muted = state != null && state.houseMusicMuted;
            int mode = state == null ? 0 : state.mode;
            if (!muted)
            {
                if (mode == 0) { mix[0] = .6f; mix[1] = .75f; mix[2] = .55f; mix[3] = .5f; mix[6] = .15f; }
                else if (mode == 1) { mix[0] = .45f; mix[1] = .2f; }
                else if (mode == 2) { mix[0] = .35f; mix[2] = .85f; mix[4] = .9f; mix[5] = .6f; }
                else { mix[0] = .55f; mix[1] = .45f; mix[6] = .25f; }
                int light = lighting == null ? 0 : lighting.lightingMode;
                if (light == 1) { mix[5] = Mathf.Max(mix[5], .5f); mix[1] *= .6f; }
                if (light == 2) { mix[4] = Mathf.Max(mix[4], .8f); mix[2] = Mathf.Max(mix[2], .8f); mix[5] = Mathf.Max(mix[5], .55f); mix[3] *= .3f; }
                float hour = timeOfDay == null ? 20f : timeOfDay.CurrentHour();
                if (hour < 5f || hour >= 23f) { mix[3] *= .5f; if (mode != 2) mix[4] *= .7f; mix[6] += .15f; }
                else if (hour >= 5.5f && hour < 10.5f) { mix[1] += .1f; mix[6] += .2f; mix[3] *= .8f; }
                if (area == 4) { for (int i = 1; i < 7; i++) mix[i] *= .2f; mix[0] = Mathf.Min(mix[0], .3f); }
                if (area == 5) { mix[6] += .3f; mix[3] *= .7f; mix[4] *= .7f; }
            }
        }
        float gain = masterVolume * (settings == null ? .8f : settings.MusicGain());
        for (int i = 0; i < stems.Length && i < target.Length; i++)
            target[i] = Mathf.Clamp01(mix[i < 7 ? i : 0]) * gain * (stemTrim != null && i < stemTrim.Length ? stemTrim[i] : 1f);
    }
    void Update()
    {
        if (stems == null || target == null) return;
        if (Time.time >= nextRefresh) { nextRefresh = Time.time + .5f; Refresh(); }
        float step = fadeSpeed * Time.deltaTime;
        for (int i = 0; i < stems.Length && i < target.Length; i++)
        {
            AudioSource s = stems[i];
            if (s == null) continue;
            s.volume = Mathf.MoveTowards(s.volume, target[i], step * Mathf.Max(.15f, Mathf.Abs(target[i] - s.volume) + .1f));
        }
    }
}
