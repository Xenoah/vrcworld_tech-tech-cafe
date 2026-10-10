using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

// DATA STREAM: a rail ride from the sky deck, down a helix, through the cafe
// atrium (phasing through glass and roof), between the towers and back up.
// Every client derives car positions from the server clock and the same
// baked sample table, so the ride needs no synced variables at all. Seated
// avatars follow their station on every client because the car transform is
// identical everywhere.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsRide : UdonSharpBehaviour
{
    [Header("Baked by CommonsExperienceBuilder")]
    public Vector3[] samplePositions;
    public Vector3[] sampleTangents;
    public float[] sampleTimes;
    public float[] sampleSpeeds;
    public float[] sampleRoll;
    public int[] sampleSegments;
    public int[] cueEffects;      // per control point: view-jack channel, -1 none
    public float[] cueSeconds;
    public int[] cueSfx;          // per control point: CommonsAdaptiveMusic SFX id, -1 none
    public float rideSeconds = 110f;
    [Header("Schedule")]
    public float boardingSeconds = 30f;
    public float unloadSeconds = 4f;
    [Header("Scene")]
    public Transform[] cars;
    public Transform[] komoMounts;
    public CommonsRideSeat[] seats;
    public AudioSource[] carAudio;
    public Transform exitPoint;
    public TextMesh[] boards;
    public Vector3 cafeMin = new Vector3(0f, 0f, 0f);
    public Vector3 cafeMax = new Vector3(28f, 9.8f, 18f);
    public Vector3 deckCenter = new Vector3(14f, 120f, 9f);
    public float deckFieldRadius = 18.3f;
    [Header("Systems")]
    public CommonsViewJack viewJack;
    public CommonsAdaptiveMusic music;
    public CommonsPlayerMotion motion;
    public CommonsExperienceSettings settings;
    public CommonsComfort comfort;

    private int localCar = -1;
    private CommonsRideSeat localSeat;
    private int lastSegment = -1;
    private int lastZone = -1;
    private Vector3 lastTangent = Vector3.forward;
    private float nextBoard;
    private bool[] boardableState;
    private bool exitingByRide;

    void Start()
    {
        boardableState = new bool[cars == null ? 0 : cars.Length];
        for (int i = 0; i < boardableState.Length; i++) boardableState[i] = true;
    }
    public float CycleSeconds() { return boardingSeconds + rideSeconds + unloadSeconds; }
    public float CarPhase(int car)
    {
        int count = cars == null || cars.Length == 0 ? 1 : cars.Length;
        double cycle = CycleSeconds();
        double t = Networking.GetServerTimeInSeconds() + car * cycle / count;
        return (float)(t % cycle);
    }
    public float RideTime(int car) { return CarPhase(car) - boardingSeconds; }
    public bool CanBoard(int car) { return CarPhase(car) < boardingSeconds - 1.5f; }
    public bool LocalRiding() { return localCar >= 0; }
    public int LocalCar() { return localCar; }

    private int FindSample(float t)
    {
        int lo = 0;
        int hi = sampleTimes.Length - 1;
        if (t <= sampleTimes[0]) return 0;
        if (t >= sampleTimes[hi]) return hi - 1;
        while (hi - lo > 1)
        {
            int mid = (lo + hi) / 2;
            if (sampleTimes[mid] <= t) lo = mid; else hi = mid;
        }
        return lo;
    }
    private void Place(int car, float t, bool level)
    {
        Transform tr = cars[car];
        if (tr == null || sampleTimes == null || sampleTimes.Length < 2) return;
        int i = FindSample(Mathf.Clamp(t, 0f, rideSeconds));
        float span = Mathf.Max(.0001f, sampleTimes[i + 1] - sampleTimes[i]);
        float f = Mathf.Clamp01((t - sampleTimes[i]) / span);
        Vector3 pos = Vector3.Lerp(samplePositions[i], samplePositions[i + 1], f);
        Vector3 tan = Vector3.Lerp(sampleTangents[i], sampleTangents[i + 1], f);
        if (level) tan.y = 0f;
        if (tan.sqrMagnitude < .0001f) tan = tr.forward;
        Quaternion rot = Quaternion.LookRotation(tan.normalized, Vector3.up);
        if (!level) rot = rot * Quaternion.Euler(0f, 0f, Mathf.Lerp(sampleRoll[i], sampleRoll[i + 1], f));
        tr.SetPositionAndRotation(pos, rot);
        if (carAudio != null && car < carAudio.Length && carAudio[car] != null)
        {
            float speed = Mathf.Lerp(sampleSpeeds[i], sampleSpeeds[i + 1], f);
            carAudio[car].pitch = .75f + speed / 22f;
            carAudio[car].volume = .12f + Mathf.Clamp01(speed / 12f) * .5f;
        }
    }
    void Update()
    {
        if (cars == null || sampleTimes == null || sampleTimes.Length < 2) return;
        bool reduced = comfort != null && comfort.reducedMotion;
        for (int c = 0; c < cars.Length; c++)
        {
            float t = RideTime(c);
            bool onTrack = t >= 0f && t < rideSeconds;
            Place(c, onTrack ? t : 0f, c == localCar && reduced);
            if (!onTrack && carAudio != null && c < carAudio.Length && carAudio[c] != null) { carAudio[c].pitch = .7f; carAudio[c].volume = .08f; }
            bool boardable = CanBoard(c);
            if (boardableState != null && c < boardableState.Length && boardable != boardableState[c])
            {
                boardableState[c] = boardable;
                if (seats != null) for (int s = 0; s < seats.Length; s++) if (seats[s] != null && seats[s].car == c) seats[s].SetBoardable(boardable);
            }
        }
        if (localCar >= 0) UpdateRider();
        if (Time.time >= nextBoard) { nextBoard = Time.time + .5f; UpdateBoards(); }
    }
    private void UpdateRider()
    {
        float t = RideTime(localCar);
        if (t >= rideSeconds)
        {
            // Arrived: the car is back at the dock; hand the player to the platform.
            exitingByRide = true;
            if (localSeat != null) localSeat.Eject();
            return;
        }
        if (t < 0f) return;
        int i = FindSample(t);
        int segment = sampleSegments[i];
        if (segment != lastSegment)
        {
            lastSegment = segment;
            if (cueEffects != null && segment < cueEffects.Length && cueEffects[segment] >= 0 && viewJack != null)
                viewJack.Pulse(cueEffects[segment], cueSeconds[segment], 1);
            if (cueSfx != null && segment < cueSfx.Length && cueSfx[segment] >= 0 && music != null) music.PlaySfx(cueSfx[segment]);
        }
        Vector3 pos = samplePositions[i];
        int zone = Inside(pos) ? 1 : 0;
        Vector2 flat = new Vector2(pos.x - deckCenter.x, pos.z - deckCenter.z);
        if (pos.y > deckCenter.y - 10f && flat.magnitude < deckFieldRadius) zone += 2;
        if (lastZone >= 0 && zone != lastZone)
        {
            // Passing through glass, the roof or the deck field: a short phase glitch.
            if (viewJack != null) viewJack.Pulse(1, .9f, 1);
            if (music != null) music.PlaySfx(1);
        }
        lastZone = zone;
        float speed = sampleSpeeds[i];
        Vector3 tan = sampleTangents[i];
        float turn = Vector3.Angle(lastTangent, tan) / Mathf.Max(.016f, Time.deltaTime);
        lastTangent = tan;
        if (viewJack != null && settings != null)
        {
            float k = Mathf.Clamp01((speed - 3f) / 12f * .7f + turn / 90f * .5f);
            viewJack.SetHold(9, settings.comfortVignette ? .25f + .55f * k : 0f, 3);
        }
        if (music != null) music.SetRideEnergy(Mathf.Clamp01(speed / 10f), zone == 1);
    }
    private bool Inside(Vector3 p)
    {
        return p.x > cafeMin.x && p.x < cafeMax.x && p.y > cafeMin.y && p.y < cafeMax.y && p.z > cafeMin.z && p.z < cafeMax.z;
    }
    public void OnLocalSeated(CommonsRideSeat seat)
    {
        localSeat = seat; localCar = seat.car; lastSegment = -1; lastZone = -1; exitingByRide = false;
        if (motion != null) motion.SetRiding(true);
        if (viewJack != null) { viewJack.SetRiding(true); viewJack.Pulse(2, 2.5f, 1); }
        if (music != null) { music.SetRiding(true); music.PlaySfx(2); }
    }
    public void OnLocalExited(CommonsRideSeat seat)
    {
        if (seat != localSeat) return;
        float t = RideTime(localCar);
        bool midRide = t >= 0f && t < rideSeconds && !exitingByRide;
        localCar = -1; localSeat = null;
        if (motion != null) motion.SetRiding(false);
        if (viewJack != null) { viewJack.SetRiding(false); viewJack.ClearAttractionHolds(); }
        if (music != null) music.SetRiding(false);
        if (exitPoint == null || !Utilities.IsValid(Networking.LocalPlayer)) return;
        if (midRide && viewJack != null && viewJack.TransitionsEnabled())
        {
            viewJack.BeginTransition(new Color(.02f, .03f, .08f));
            SendCustomEventDelayedSeconds("ReturnToDock", viewJack.transitionLead);
        }
        else ReturnToDock();
    }
    public void ReturnToDock()
    {
        exitingByRide = false;
        if (exitPoint == null || !Utilities.IsValid(Networking.LocalPlayer)) return;
        Networking.LocalPlayer.TeleportTo(exitPoint.position, exitPoint.rotation);
        Networking.LocalPlayer.SetVelocity(Vector3.zero);
    }
    private string Clock(float seconds)
    {
        int s = Mathf.Max(0, Mathf.CeilToInt(seconds));
        return (s / 60).ToString() + ":" + (s % 60).ToString("00");
    }
    private void UpdateBoards()
    {
        if (boards == null || cars == null) return;
        string text = "DATA STREAM";
        for (int c = 0; c < cars.Length; c++)
        {
            float phase = CarPhase(c);
            string name = c == 0 ? "A" : c == 1 ? "B" : (c + 1).ToString();
            if (phase < boardingSeconds) text += "\nCAR " + name + "  BOARDING  departs " + Clock(boardingSeconds - phase);
            else if (phase < boardingSeconds + rideSeconds) text += "\nCAR " + name + "  ON THE STREAM  back " + Clock(boardingSeconds + rideSeconds - phase);
            else text += "\nCAR " + name + "  ARRIVING";
        }
        text += "\nSit to board. Leave any time: you return to this dock.";
        for (int i = 0; i < boards.Length; i++) if (boards[i] != null) boards[i].text = text;
    }
    public Transform KomoMount(int car)
    {
        if (komoMounts == null || car < 0 || car >= komoMounts.Length) return null;
        return komoMounts[car];
    }
}
