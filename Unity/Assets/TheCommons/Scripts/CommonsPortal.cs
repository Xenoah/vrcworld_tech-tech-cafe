using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsPortal : UdonSharpBehaviour
{
    public Transform destination;
    public override void Interact()
    {
        if (destination == null || !Utilities.IsValid(Networking.LocalPlayer)) return;
        Networking.LocalPlayer.TeleportTo(destination.position, destination.rotation);
        Networking.LocalPlayer.SetVelocity(Vector3.zero);
    }
}
