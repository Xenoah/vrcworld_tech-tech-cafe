using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

// Sky deck 120 m above the cafe: zone detection for the low-gravity well,
// the orbit-star overlay, a fall rescue and slow decorative motion.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsOrbitDeck : UdonSharpBehaviour
{
    public CommonsPlayerMotion motion;
    public CommonsViewJack viewJack;
    public CommonsRide ride;
    public CommonsAdaptiveMusic music;
    public CommonsComfort comfort;
    public Transform arrival;
    public Transform planet;
    public Transform[] spinners;
    public Material[] holoMaterials;
    public Vector3 center = new Vector3(14f, 120f, 9f);
    public float radius = 18.3f;
    public float wellRadius = 7f;
    public float ceiling = 28f;
    public bool onDeck;
    private float nextTick;
    private float lastOnDeck = -100f;
    private int reducedState = -1;
    private bool rescuing;

    void Update()
    {
        if (Time.time >= nextTick) { nextTick = Time.time + .2f; Tick(); }
        if (!onDeck || reducedState == 1) return;
        float dt = Time.deltaTime;
        if (planet != null) planet.Rotate(0f, 5f * dt, 0f, Space.World);
        if (spinners != null)
            for (int i = 0; i < spinners.Length; i++)
                if (spinners[i] != null) spinners[i].Rotate(0f, (i % 2 == 0 ? 3f : -2f) * dt, 0f, Space.World);
    }
    private void Tick()
    {
        int reduced = comfort != null && comfort.reducedMotion ? 1 : 0;
        if (reduced != reducedState)
        {
            reducedState = reduced;
            if (holoMaterials != null)
                for (int i = 0; i < holoMaterials.Length; i++)
                    if (holoMaterials[i] != null) holoMaterials[i].SetFloat("_Motion", reduced == 1 ? 0f : 1f);
        }
        VRCPlayerApi p = Networking.LocalPlayer;
        if (!Utilities.IsValid(p)) return;
        Vector3 rel = p.GetPosition() - center;
        float horizontal = new Vector2(rel.x, rel.z).magnitude;
        bool seated = ride != null && ride.LocalRiding();
        bool now = !seated && rel.y > -3f && rel.y < ceiling + 2f && horizontal < radius + 1.5f;
        if (now) lastOnDeck = Time.time;
        if (now != onDeck)
        {
            onDeck = now;
            if (viewJack != null) viewJack.SetHold(3, onDeck ? .5f : 0f, 1);
            if (music != null) music.Refresh();
        }
        if (motion != null) motion.SetGravityWell(onDeck && horizontal < wellRadius);
        // A player who slips past the field while thrusting is caught before the city.
        if (!seated && !rescuing && Time.time - lastOnDeck < 8f && rel.y < -8f && p.GetVelocity().y < -2f) Rescue();
    }
    public void Rescue()
    {
        if (arrival == null) return;
        rescuing = true;
        if (viewJack != null && viewJack.TransitionsEnabled())
        {
            viewJack.BeginTransition(new Color(.02f, .03f, .08f));
            SendCustomEventDelayedSeconds("RescueTeleport", viewJack.transitionLead);
        }
        else RescueTeleport();
    }
    public void RescueTeleport()
    {
        rescuing = false;
        if (arrival == null || !Utilities.IsValid(Networking.LocalPlayer)) return;
        Networking.LocalPlayer.TeleportTo(arrival.position, arrival.rotation);
        Networking.LocalPlayer.SetVelocity(Vector3.zero);
    }
}
