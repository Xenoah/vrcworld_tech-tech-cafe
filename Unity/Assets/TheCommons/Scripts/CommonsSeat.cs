using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsSeat : UdonSharpBehaviour
{
    public VRCStation station;
    public override void Interact()
    { if (station != null && Utilities.IsValid(Networking.LocalPlayer)) station.UseStation(Networking.LocalPlayer); }
}
