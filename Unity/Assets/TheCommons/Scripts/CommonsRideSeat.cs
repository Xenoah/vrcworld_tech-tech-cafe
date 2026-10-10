using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

// One seat of a DATA STREAM car. Boarding is an explicit Interact during the
// boarding window; leaving is always allowed and the ride puts the player
// back on the dock instead of dropping them into the city.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsRideSeat : UdonSharpBehaviour
{
    public CommonsRide ride;
    public VRCStation station;
    public int car;
    private bool boardable = true;

    public override void Interact()
    {
        if (ride == null || station == null || !ride.CanBoard(car)) return;
        if (Utilities.IsValid(Networking.LocalPlayer)) station.UseStation(Networking.LocalPlayer);
    }
    public void SetBoardable(bool value)
    {
        if (value == boardable) return;
        boardable = value;
        DisableInteractive = !value;
    }
    public void Eject()
    {
        if (station != null && Utilities.IsValid(Networking.LocalPlayer)) station.ExitStation(Networking.LocalPlayer);
    }
    public override void OnStationEntered(VRCPlayerApi player)
    {
        if (ride != null && Utilities.IsValid(player) && player.isLocal) ride.OnLocalSeated(this);
    }
    public override void OnStationExited(VRCPlayerApi player)
    {
        if (ride != null && Utilities.IsValid(player) && player.isLocal) ride.OnLocalExited(this);
    }
}
