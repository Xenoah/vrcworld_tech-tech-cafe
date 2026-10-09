using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.Manual)]
public class CommonsWorldState : UdonSharpBehaviour
{
    [UdonSynced] public int mode; // Lounge, Audience seating, DJ, Quiet Night
    [UdonSynced] public bool houseMusicMuted = true;
    public bool hostLocked = true;
    public GameObject loungeRoot;
    public GameObject academicRoot;
    public GameObject hologramRoot;
    public TextMesh modeLabel;
    public TextMesh musicLabel;
    public CommonsComfort comfort;
    public CommonsAudioZones audioZones;

    void Start() { ApplyState(); }
    public override void OnDeserialization() { ApplyState(); }
    public bool CanControl()
    {
        VRCPlayerApi p = Networking.LocalPlayer;
        return Utilities.IsValid(p) && (!hostLocked || p.isMaster || p.isInstanceOwner);
    }
    private bool BeginChange()
    {
        if (!CanControl()) return false;
        if (!Networking.IsOwner(gameObject)) Networking.SetOwner(Networking.LocalPlayer, gameObject);
        return Networking.IsOwner(gameObject);
    }
    public void Lounge() { SetMode(0); }
    public void Academic() { SetMode(1); }
    public void DJ() { SetMode(2); }
    public void QuietNight() { SetMode(3); }
    private void SetMode(int value)
    {
        if (!BeginChange()) return;
        mode = value; ApplyState(); RequestSerialization();
    }
    public void ToggleHouseMusic()
    {
        if (!BeginChange()) return;
        houseMusicMuted = !houseMusicMuted; ApplyState(); RequestSerialization();
    }
    public void ApplyState()
    {
        mode = Mathf.Clamp(mode, 0, 3);
        if (loungeRoot != null) loungeRoot.SetActive(mode == 0 || mode == 3);
        if (academicRoot != null) academicRoot.SetActive(mode == 1);
        if (hologramRoot != null) hologramRoot.SetActive(mode != 1);
        if (modeLabel != null) modeLabel.text = mode == 0 ? "LOUNGE" : mode == 1 ? "AUDIENCE" : mode == 2 ? "DJ / LIVE" : "QUIET NIGHT";
        if (musicLabel != null) musicLabel.text = "HOUSE MUSIC / " + (houseMusicMuted ? "OFF" : "ON");
        if (comfort != null) comfort.Refresh();
        if (audioZones != null) audioZones.Refresh();
    }
    public override bool OnOwnershipRequest(VRCPlayerApi requestingPlayer, VRCPlayerApi newOwner)
    { return !hostLocked || (Utilities.IsValid(requestingPlayer) && (requestingPlayer.isMaster || requestingPlayer.isInstanceOwner)); }
}
