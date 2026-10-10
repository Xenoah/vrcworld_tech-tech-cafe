using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

// KOMO: an original hovering companion bot (not a third-party character).
// Where KOMO is and what it does comes from the server clock, so every
// visitor sees the same schedule without network traffic: greeting at the
// entrance, pulling espresso at the bar, reading upstairs, DJing at RELAY,
// dancing on stage, studying posters, stargazing on the terrace, people-
// watching from the south bridge, then warping to the sky deck to ride the
// DATA STREAM on the nose of car A. What KOMO looks at and says is local:
// it turns to whoever is close on that player's own screen.
// Activities: 0 greeter, 1 barista, 2 dj, 3 dancer, 4 stargazer, 5 reader,
//             6 lounger, 7 gallery, 8 rider, 9 travel, 10 warp.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsKomo : UdonSharpBehaviour
{
    [Header("Rig")]
    public Transform body;
    public Transform handL;
    public Transform handR;
    public Transform ring;
    public Material faceMaterial;
    public GameObject cup;
    public GameObject book;
    public GameObject headphones;
    public Transform bubble;
    public TextMesh bubbleText;
    public GameObject bubbleRoot;
    public AudioSource voice;
    public AudioClip[] chirps;
    [Header("Places")]
    public Transform[] spots;
    public int[] spotActivity;
    public Transform[] spotDoors;
    public Transform hub;
    public float travelSpeed = 1.6f;
    public int rideEvery = 4;
    [Header("Systems")]
    public CommonsRide ride;
    public CommonsAdaptiveMusic music;
    public CommonsExperienceSettings settings;
    public CommonsWorldState state;
    public CommonsLightingModes lighting;
    public CommonsTimeOfDay timeOfDay;
    public CommonsComfort comfort;
    [Header("Voice")]
    public string displayName = "KOMO";
    public string[] linesEN;
    public string[] linesJP;
    public int[] lineActivity;      // activity code, or -1 for anywhere
    public string[] greetEN;        // 0 morning, 1 day, 2 evening, 3 night, 4 first visit
    public string[] greetJP;

    private Vector3[] path = new Vector3[5];
    private Vector3 pathPos;
    private Vector3 pathDir;
    private int activity = 9;
    private float activityTime;
    private float scale = 1f;
    private Quaternion facing = Quaternion.identity;
    private Quaternion activityFacing = Quaternion.identity;
    private bool lookingAtPlayer;
    private Vector3 lookLocal;
    private float bubbleUntil;
    private float talkUntil;
    private float happyUntil;
    private float hopStart = -10f;
    private int lineCursor;
    private float lastGreet = -1000f;
    private bool greetedOnce;
    private bool wasNear;
    private float farTick;
    private int expression = -1;

    void Start()
    {
        if (bubbleRoot != null) bubbleRoot.SetActive(false);
        if (faceMaterial != null) faceMaterial.SetFloat("_Seed", .37f);
    }
    private float Period()
    {
        if (ride != null) return ride.CycleSeconds() * Mathf.Max(2, rideEvery);
        return 480f;
    }
    private float SlotLength()
    {
        int n = spots == null || spots.Length == 0 ? 1 : spots.Length;
        float rideSlot = ride != null ? ride.CycleSeconds() : 0f;
        return (Period() - rideSlot) / n;
    }
    private float PathLength()
    {
        float length = 0f;
        for (int i = 0; i < 4; i++) length += Vector3.Distance(path[i], path[i + 1]);
        return length;
    }
    private void BuildPath(int from, int to)
    {
        path[0] = spots[from].position;
        path[1] = spotDoors != null && from < spotDoors.Length && spotDoors[from] != null ? spotDoors[from].position : path[0];
        path[2] = hub != null ? hub.position : path[1];
        path[4] = spots[to].position;
        path[3] = spotDoors != null && to < spotDoors.Length && spotDoors[to] != null ? spotDoors[to].position : path[4];
    }
    private void SamplePath(float distance)
    {
        float left = Mathf.Max(0f, distance);
        for (int i = 0; i < 4; i++)
        {
            float seg = Vector3.Distance(path[i], path[i + 1]);
            if (left <= seg || i == 3)
            {
                float f = seg > .0001f ? Mathf.Clamp01(left / seg) : 1f;
                pathPos = Vector3.Lerp(path[i], path[i + 1], f);
                pathDir = path[i + 1] - path[i];
                return;
            }
            left -= seg;
        }
    }
    // Decide position, facing, activity and warp scale from the shared clock.
    private void Schedule()
    {
        if (spots == null || spots.Length == 0) return;
        float period = Period();
        float tau = (float)(Networking.GetServerTimeInSeconds() % period);
        float rideSlot = ride != null ? ride.CycleSeconds() : 0f;
        scale = 1f;
        if (ride != null && tau < rideSlot)
        {
            Transform mount = ride.KomoMount(0);
            float phase = tau;
            if (mount != null)
            {
                transform.SetPositionAndRotation(mount.position, mount.rotation);
                activityFacing = mount.rotation;
            }
            activity = 8; activityTime = phase;
            if (phase < 2f) { scale = Mathf.SmoothStep(0f, 1f, phase / 2f); activity = 10; }
            if (phase > rideSlot - 1.5f) { scale = Mathf.SmoothStep(0f, 1f, (rideSlot - phase) / 1.5f); activity = 10; }
            return;
        }
        float slot = SlotLength();
        float local = tau - rideSlot;
        int k = Mathf.Clamp(Mathf.FloorToInt(local / slot), 0, spots.Length - 1);
        float u = local - k * slot;
        int to = k;
        if (k == 0)
        {
            // First stop after the ride: KOMO warps in on the spot.
            transform.position = spots[to].position;
            activityFacing = spots[to].rotation;
            activity = spotActivity[to]; activityTime = u;
            if (u < 2f) { scale = Mathf.SmoothStep(0f, 1f, u / 2f); activity = 10; }
        }
        else
        {
            BuildPath(k - 1, to);
            float travel = Mathf.Min(PathLength() / Mathf.Max(.2f, travelSpeed), slot * .4f);
            if (u < travel)
            {
                SamplePath(u / travel * PathLength());
                transform.position = pathPos;
                if (pathDir.sqrMagnitude > .0001f) { Vector3 flat = new Vector3(pathDir.x, 0f, pathDir.z); if (flat.sqrMagnitude > .001f) activityFacing = Quaternion.LookRotation(flat); }
                activity = 9; activityTime = u;
            }
            else
            {
                transform.position = spots[to].position;
                activityFacing = spots[to].rotation;
                activity = spotActivity[to]; activityTime = u - travel;
            }
        }
        // Warp out at the end of the last stop: next is the sky deck.
        if (ride != null && k == spots.Length - 1 && u > slot - 1.5f) { scale = Mathf.SmoothStep(0f, 1f, (slot - u) / 1.5f); activity = 10; }
    }
    void Update()
    {
        VRCPlayerApi player = Networking.LocalPlayer;
        if (!Utilities.IsValid(player)) return;
        Vector3 head = player.GetTrackingData(VRCPlayerApi.TrackingDataType.Head).position;
        float distance = Vector3.Distance(head, transform.position);
        if (distance > 45f && activity != 8 && activity != 10)
        {
            // Far away (and not riding the car): keep the schedule but skip animation at 4 Hz.
            if (Time.time < farTick) return;
            farTick = Time.time + .25f;
            Schedule();
            transform.localScale = Vector3.one * Mathf.Max(.001f, scale);
            return;
        }
        Schedule();
        transform.localScale = Vector3.one * Mathf.Max(.001f, scale);
        Animate(head, distance);
        Greet(distance);
        UpdateBubble(head);
    }
    private void Animate(Vector3 head, float distance)
    {
        float t = Time.time;
        bool reduced = comfort != null && comfort.reducedMotion;
        bool canLook = activity != 9 && activity != 10 && activity != 8 && distance < 3.6f;
        Quaternion want = activityFacing;
        if (canLook)
        {
            Vector3 flat = head - transform.position; flat.y = 0f;
            if (flat.sqrMagnitude > .01f) want = Quaternion.LookRotation(flat);
        }
        float dance = 0f;
        bool lively = (lighting != null && lighting.lightingMode == 2) || (state != null && state.mode == 2);
        if (activity == 3) dance = lively ? 1f : .35f;
        if (activity == 3 && !canLook && !reduced) want = want * Quaternion.Euler(0f, Mathf.Sin(t * (lively ? 1.6f : .6f)) * 50f * dance, 0f);
        facing = Quaternion.Slerp(facing, want, Mathf.Min(1f, Time.deltaTime * 3f));
        if (activity == 8) facing = activityFacing;
        transform.rotation = facing;
        float beat = music != null ? music.BeatPhase() : 0f;
        float bob = Mathf.Sin(t * 2.1f) * .035f;
        if (activity == 2 || activity == 3) bob = (1f - Mathf.Abs(Mathf.Sin(beat * Mathf.PI))) * .05f * (activity == 3 ? 1f + dance : 1f);
        float hop = t - hopStart < .5f ? Mathf.Sin((t - hopStart) / .5f * Mathf.PI) * .18f : 0f;
        if (body != null)
        {
            body.localPosition = new Vector3(0f, bob + hop, 0f);
            float tilt = activity == 9 ? 8f : activity == 5 || activity == 7 ? -6f : 0f;
            body.localRotation = Quaternion.Euler(tilt, 0f, activity == 2 ? Mathf.Sin(beat * Mathf.PI * 2f) * 4f : 0f);
        }
        if (ring != null && !reduced) ring.Rotate(0f, (activity == 3 ? 90f * (1f + dance) : 25f) * Time.deltaTime, 0f, Space.Self);
        Vector3 l = new Vector3(-.3f, -.05f, .1f);
        Vector3 r = new Vector3(.3f, -.05f, .1f);
        bool speaking = Time.time < talkUntil;
        if (activity == 0 || (canLook && speaking)) r = new Vector3(.34f, .28f + Mathf.Sin(t * 9f) * .04f, .05f);
        else if (activity == 1) { l = new Vector3(-.12f, -.12f, .3f); r = new Vector3(.08f + Mathf.Cos(t * 3f) * .05f, -.02f, .3f + Mathf.Sin(t * 3f) * .05f); }
        else if (activity == 2) { float s = Mathf.Sin(beat * Mathf.PI * 2f); l = new Vector3(-.25f, -.12f + s * .03f, .3f + s * .05f); r = new Vector3(.25f, -.12f - s * .03f, .3f - s * .05f); }
        else if (activity == 3) { float s = Mathf.Sin(t * (lively ? 6f : 2f)); l = new Vector3(-.34f, .1f + s * .18f * dance, .05f); r = new Vector3(.34f, .1f - s * .18f * dance, .05f); }
        else if (activity == 4) { l = new Vector3(-.28f, -.18f, -.05f); r = new Vector3(.28f, -.18f, -.05f); }
        else if (activity == 5) { l = new Vector3(-.13f, -.1f, .28f); r = new Vector3(.13f, -.1f + (Mathf.Repeat(t, 7f) > 6.4f ? .06f : 0f), .28f); }
        else if (activity == 6) { r = new Vector3(.16f, Mathf.Repeat(t, 9f) > 7.5f ? .08f : -.1f, .28f); }
        else if (activity == 7) { r = new Vector3(.08f, -.06f, .22f); }
        else if (activity == 8) { bool fast = ride != null && ride.RideTime(0) > 0f; l = fast ? new Vector3(-.3f, .45f, 0f) : l; r = fast ? new Vector3(.3f, .45f, 0f) : r; }
        if (handL != null) handL.localPosition = Vector3.Lerp(handL.localPosition, l, Mathf.Min(1f, Time.deltaTime * 8f));
        if (handR != null) handR.localPosition = Vector3.Lerp(handR.localPosition, r, Mathf.Min(1f, Time.deltaTime * 8f));
        if (cup != null) cup.SetActive(activity == 1 || activity == 6);
        if (book != null) book.SetActive(activity == 5);
        if (headphones != null) headphones.SetActive(activity == 2);
        int e = 0;
        if (activity == 0 || activity == 6) e = 1;
        else if (activity == 2) e = beat < .18f ? 4 : 6;
        else if (activity == 3) e = lively ? (beat < .2f ? 4 : 1) : 1;
        else if (activity == 4) e = 2;
        else if (activity == 5) e = 6;
        else if (activity == 7) e = Mathf.Repeat(t, 11f) > 9.8f ? 3 : 0;
        else if (activity == 8) e = ride != null && ride.RideTime(0) > 0f ? 3 : 1;
        else if (activity == 10) e = 4;
        if (Time.time < happyUntil) e = 1;
        if (faceMaterial != null)
        {
            if (e != expression) { expression = e; faceMaterial.SetFloat("_Expression", e); }
            if (canLook)
            {
                Vector3 d = transform.InverseTransformPoint(head);
                faceMaterial.SetVector("_Look", new Vector4(Mathf.Clamp(d.x * 1.5f, -1f, 1f), Mathf.Clamp(d.y * 1.5f, -1f, 1f), 0f, 0f));
            }
            else faceMaterial.SetVector("_Look", Vector4.zero);
            faceMaterial.SetFloat("_Talk", speaking ? .5f + .5f * Mathf.Sin(t * 16f) : 0f);
            faceMaterial.SetFloat("_Blush", canLook ? .8f : 0f);
        }
    }
    private void Greet(float distance)
    {
        bool near = distance < 3f && activity != 9 && activity != 10 && activity != 8;
        if (near && !wasNear && Time.time - lastGreet > 90f)
        {
            lastGreet = Time.time;
            string[] lines = Language() == 1 ? greetJP : greetEN;
            if (lines != null && lines.Length >= 5)
            {
                int index = !greetedOnce ? 4 : HourIndex();
                greetedOnce = true;
                Say(lines[index]);
            }
        }
        wasNear = near;
    }
    private int HourIndex()
    {
        float hour = timeOfDay == null ? 20f : timeOfDay.CurrentHour();
        if (hour >= 5f && hour < 11f) return 0;
        if (hour >= 11f && hour < 17f) return 1;
        if (hour >= 17f && hour < 22f) return 2;
        return 3;
    }
    private int Language() { return settings == null ? 0 : settings.komoLanguage; }
    public override void Interact()
    {
        string[] lines = Language() == 1 ? linesJP : linesEN;
        hopStart = Time.time; happyUntil = Time.time + 2f;
        if (lines == null || lines.Length == 0 || lineActivity == null) { Chirp(); return; }
        // Prefer lines about what KOMO is doing right now, then anything general.
        for (int n = 0; n < lines.Length; n++)
        {
            lineCursor = (lineCursor + 1) % lines.Length;
            int tag = lineCursor < lineActivity.Length ? lineActivity[lineCursor] : -1;
            if (tag == activity || (tag == -1 && n > 2)) { Say(lines[lineCursor]); return; }
        }
        Say(lines[lineCursor]);
    }
    private void Say(string text)
    {
        talkUntil = Time.time + 1.6f;
        if (settings != null && !settings.komoBubbles) { Chirp(); return; }
        if (bubbleText != null) bubbleText.text = text;
        if (bubbleRoot != null) bubbleRoot.SetActive(true);
        bubbleUntil = Time.time + 6.5f;
        Chirp();
    }
    private void Chirp()
    {
        if (voice == null || chirps == null || chirps.Length == 0) return;
        AudioClip clip = chirps[Mathf.Abs(Mathf.FloorToInt(Time.time * 7.3f)) % chirps.Length];
        if (clip != null) voice.PlayOneShot(clip, .7f);
    }
    private void UpdateBubble(Vector3 head)
    {
        if (bubbleRoot == null) return;
        if (Time.time > bubbleUntil) { if (bubbleRoot.activeSelf) bubbleRoot.SetActive(false); return; }
        if (bubble != null)
        {
            Vector3 away = bubble.position - head;
            if (away.sqrMagnitude > .001f) bubble.rotation = Quaternion.LookRotation(away);
        }
    }
    public void RefreshSettings()
    {
        if (settings != null && !settings.komoBubbles && bubbleRoot != null) bubbleRoot.SetActive(false);
    }
}
