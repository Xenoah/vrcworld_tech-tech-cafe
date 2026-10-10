using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsPortal : UdonSharpBehaviour
{
    public Transform destination;
    // Optional experience layer. Without it (or with WARP off in the local
    // EXPERIENCE panel) the portal teleports immediately, as in v0.9.0.
    public CommonsViewJack viewJack;
    public CommonsAdaptiveMusic music;
    public Color warpColor = new Color(.02f, .03f, .08f, 1f);
    public int sfx = 0;
    private bool pending;
    public override void Interact()
    {
        if (destination == null || !Utilities.IsValid(Networking.LocalPlayer) || pending) return;
        if (viewJack != null && viewJack.TransitionsEnabled())
        {
            pending = true;
            viewJack.BeginTransition(warpColor);
            if (music != null) music.PlaySfx(sfx);
            SendCustomEventDelayedSeconds("Teleport", viewJack.transitionLead);
            return;
        }
        Teleport();
    }
    public void Teleport()
    {
        pending = false;
        if (destination == null || !Utilities.IsValid(Networking.LocalPlayer)) return;
        Networking.LocalPlayer.TeleportTo(destination.position, destination.rotation);
        Networking.LocalPlayer.SetVelocity(Vector3.zero);
    }
}
