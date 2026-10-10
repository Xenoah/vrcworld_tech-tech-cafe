using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
using VRC.Udon.Common;

// The only behaviour that changes the local player's locomotion or avatar
// scale. Attractions ask for a state (size mode, gravity well, riding) and
// this script composes the final values from a captured baseline, so nothing
// leaks when players leave an attraction, respawn or change avatar.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsPlayerMotion : UdonSharpBehaviour
{
    public CommonsViewJack viewJack;
    public CommonsAdaptiveMusic music;
    public TextMesh[] labels;
    public float tinyScale = .1f;
    public float smallScale = .5f;
    public float giantScale = 4f;
    public float minEyeHeight = .12f;
    public float maxEyeHeight = 8f;
    public Vector3 deckCenter = new Vector3(14f, 120f, 9f);
    public float deckRadius = 19f;
    public float wellGravity = .16f;
    public float wellJump = 3.2f;
    public float thrustAcceleration = 7f;
    public float thrustMaxRise = 2.6f;
    public int sizeMode;              // 0 normal, 1 tiny, 2 small, 3 giant
    public bool inWell;
    public bool riding;
    private bool ready;
    private float baseWalk = 2f;
    private float baseRun = 4f;
    private float baseStrafe = 2f;
    private float baseJump = 3f;
    private float baseGravity = 1f;
    private float normalEye = 1.6f;
    private float expectedEye = 1.6f;
    private bool jumpHeld;
    private float nextCheck;

    void Start() { SendCustomEventDelayedSeconds("CaptureBaseline", 2f); }
    public void CaptureBaseline()
    {
        VRCPlayerApi p = Networking.LocalPlayer;
        if (!Utilities.IsValid(p)) return;
        baseWalk = p.GetWalkSpeed(); baseRun = p.GetRunSpeed(); baseStrafe = p.GetStrafeSpeed();
        baseJump = p.GetJumpImpulse(); baseGravity = p.GetGravityStrength();
        if (baseWalk <= 0f) baseWalk = 2f;
        if (baseRun <= 0f) baseRun = 4f;
        if (baseStrafe <= 0f) baseStrafe = 2f;
        if (baseGravity <= 0f) baseGravity = 1f;
        normalEye = p.GetAvatarEyeHeightAsMeters();
        expectedEye = normalEye;
        p.SetAvatarEyeHeightMinimumByMeters(minEyeHeight);
        p.SetAvatarEyeHeightMaximumByMeters(maxEyeHeight);
        ready = true; Apply(); RefreshLabels();
    }

    public void Tiny() { SetSize(1); }
    public void Small() { SetSize(2); }
    public void Normal() { SetSize(0); }
    public void Giant() { SetSize(3); }
    public bool OnDeck()
    {
        if (!Utilities.IsValid(Networking.LocalPlayer)) return false;
        Vector3 p = Networking.LocalPlayer.GetPosition() - deckCenter;
        return p.y > -4f && p.y < 32f && new Vector2(p.x, p.z).magnitude < deckRadius;
    }
    private float ScaleFor(int mode) { return mode == 1 ? tinyScale : mode == 2 ? smallScale : mode == 3 ? giantScale : 1f; }
    private void SetSize(int mode)
    {
        VRCPlayerApi p = Networking.LocalPlayer;
        if (!ready || !Utilities.IsValid(p)) return;
        if (riding && mode != 0) return;
        if (mode == 3 && !OnDeck()) return;   // giants only fit under the sky-deck field
        if (mode == sizeMode) return;
        if (sizeMode == 0) normalEye = p.GetAvatarEyeHeightAsMeters();
        bool shrinking = ScaleFor(mode) < ScaleFor(sizeMode);
        sizeMode = mode;
        expectedEye = Mathf.Clamp(normalEye * ScaleFor(mode), minEyeHeight, maxEyeHeight);
        if (mode == 0) expectedEye = normalEye;
        p.SetAvatarEyeHeightByMeters(expectedEye);
        if (viewJack != null)
        {
            viewJack.Pulse(0, .9f, 1);
            viewJack.SetHold(6, mode == 1 ? .9f : mode == 2 ? .45f : 0f, 1);
        }
        if (music != null) music.PlaySfx(shrinking ? 4 : 3);
        Apply(); RefreshLabels();
    }
    public void SetGravityWell(bool value)
    {
        if (value == inWell) return;
        inWell = value; Apply(); RefreshLabels();
    }
    public void SetRiding(bool value)
    {
        riding = value;
        if (riding) { SetSize(0); inWell = false; }
        Apply();
    }
    public void Apply()
    {
        VRCPlayerApi p = Networking.LocalPlayer;
        if (!ready || !Utilities.IsValid(p)) return;
        float s = sizeMode == 0 ? 1f : Mathf.Max(.05f, expectedEye / Mathf.Max(.1f, normalEye));
        float speed = Mathf.Pow(s, .75f);
        bool well = inWell && !riding;
        p.SetWalkSpeed(baseWalk * speed);
        p.SetRunSpeed(baseRun * speed);
        p.SetStrafeSpeed(baseStrafe * speed);
        p.SetGravityStrength(baseGravity * (well ? wellGravity : 1f));
        float jump = well ? Mathf.Max(baseJump, wellJump) : baseJump;
        p.SetJumpImpulse(jump * Mathf.Sqrt(s));
    }
    public void RefreshLabels()
    {
        if (labels == null) return;
        string size = sizeMode == 1 ? "TINY x0.1" : sizeMode == 2 ? "SMALL x0.5" : sizeMode == 3 ? "GIANT x4" : "NORMAL";
        string text = "SIZE LAB (LOCAL)\nNOW " + size + (inWell ? "\nLOW GRAVITY: hold JUMP to thrust" : "\nGIANT works on this deck only");
        for (int i = 0; i < labels.Length; i++) if (labels[i] != null) labels[i].text = text;
    }
    public override void InputJump(bool value, UdonInputEventArgs args) { jumpHeld = value; }
    void Update()
    {
        VRCPlayerApi p = Networking.LocalPlayer;
        if (!ready || !Utilities.IsValid(p)) return;
        if (inWell && !riding && jumpHeld && !p.IsPlayerGrounded())
        {
            Vector3 v = p.GetVelocity();
            if (v.y < thrustMaxRise) { v.y = Mathf.Min(thrustMaxRise, v.y + thrustAcceleration * Time.deltaTime); p.SetVelocity(v); }
        }
        if (Time.time < nextCheck) return;
        nextCheck = Time.time + .3f;
        if (sizeMode == 0) return;
        Vector3 pos = p.GetPosition();
        // CVS2 karts and drone fields expect normal-sized players; giants stay on the deck.
        if (pos.x < -15f || pos.x >= 100f || (sizeMode == 3 && !OnDeck())) SetSize(0);
    }
    public override void OnAvatarEyeHeightChanged(VRCPlayerApi player, float prevEyeHeightAsMeters)
    {
        if (!Utilities.IsValid(player) || !player.isLocal || !ready) return;
        float now = player.GetAvatarEyeHeightAsMeters();
        if (sizeMode == 0) { normalEye = now; expectedEye = now; return; }
        if (Mathf.Abs(now - expectedEye) > .05f)
        {
            // Manual scaling or an avatar swap overrides the lab; accept it as the new normal.
            sizeMode = 0; normalEye = now; expectedEye = now;
            if (viewJack != null) viewJack.SetHold(6, 0f, 1);
            Apply(); RefreshLabels();
        }
    }
    public override void OnAvatarChanged(VRCPlayerApi player)
    {
        if (!Utilities.IsValid(player) || !player.isLocal || !ready) return;
        sizeMode = 0;
        if (viewJack != null) viewJack.SetHold(6, 0f, 1);
        SendCustomEventDelayedSeconds("RecaptureEye", 1.5f);
    }
    public void RecaptureEye()
    {
        if (!Utilities.IsValid(Networking.LocalPlayer)) return;
        normalEye = Networking.LocalPlayer.GetAvatarEyeHeightAsMeters(); expectedEye = normalEye;
        Apply(); RefreshLabels();
    }
    public override void OnPlayerRespawn(VRCPlayerApi player)
    {
        if (!Utilities.IsValid(player) || !player.isLocal) return;
        inWell = false; SetSize(0); Apply(); RefreshLabels();
    }
}
