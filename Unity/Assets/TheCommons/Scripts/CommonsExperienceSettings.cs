using UdonSharp;
using UnityEngine;

// Per-player settings for the experience layer. Nothing here is synced: every
// visitor chooses how much of their own view, music and companion chatter
// they want. Defaults are deliberately gentle.
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsExperienceSettings : UdonSharpBehaviour
{
    public CommonsComfort comfort;
    public CommonsAdaptiveMusic music;
    public CommonsKomo komo;
    public TextMesh[] labels;
    public int viewFxLevel = 1;          // 0 OFF / 1 SOFT / 2 FULL
    public bool fxTransitions = true;    // portal and lift warps
    public bool fxAttractions = true;    // ride, sky deck, size lab
    public bool fxAmbient = false;       // lighting-mode overlays in the cafe
    public bool fxBeatPulse = false;     // DISCO edge pulse (never a strobe)
    public bool comfortVignette = true;  // tunnel vignette on the ride; independent of VIEW FX
    public int musicStep = 4;            // 0..5 local music volume
    public bool komoBubbles = true;
    public int komoLanguage = 0;         // 0 EN / 1 JP

    void Start() { Refresh(); }
    public void CycleViewFx() { viewFxLevel = (viewFxLevel + 1) % 3; Refresh(); }
    public void ToggleTransitions() { fxTransitions = !fxTransitions; Refresh(); }
    public void ToggleAttractions() { fxAttractions = !fxAttractions; Refresh(); }
    public void ToggleAmbient() { fxAmbient = !fxAmbient; Refresh(); }
    public void ToggleBeatPulse() { fxBeatPulse = !fxBeatPulse; Refresh(); }
    public void ToggleComfortVignette() { comfortVignette = !comfortVignette; Refresh(); }
    public void MusicUp() { musicStep = Mathf.Min(5, musicStep + 1); Refresh(); }
    public void MusicDown() { musicStep = Mathf.Max(0, musicStep - 1); Refresh(); }
    public void ToggleKomoBubbles() { komoBubbles = !komoBubbles; Refresh(); }
    public void ToggleKomoLanguage() { komoLanguage = 1 - komoLanguage; Refresh(); }

    public float ViewFxGain() { return viewFxLevel == 0 ? 0f : viewFxLevel == 1 ? .55f : 1f; }
    public float MusicGain() { return musicStep / 5f; }
    public bool ReducedMotion() { return comfort != null && comfort.reducedMotion; }
    public bool CategoryAllowed(int category)
    {
        // 0 transition, 1 attraction, 2 ambient, 3 comfort
        if (category == 3) return comfortVignette;
        if (viewFxLevel == 0) return false;
        if (category == 0) return fxTransitions;
        if (category == 1) return fxAttractions;
        return fxAmbient;
    }
    public void Refresh()
    {
        if (music != null) music.Refresh();
        if (komo != null) komo.RefreshSettings();
        if (labels == null) return;
        string level = viewFxLevel == 0 ? "OFF" : viewFxLevel == 1 ? "SOFT" : "FULL";
        string text = "EXPERIENCE (LOCAL)\nVIEW FX " + level
            + " / WARP " + (fxTransitions ? "ON" : "OFF")
            + " / RIDE " + (fxAttractions ? "ON" : "OFF")
            + "\nAMBIENT " + (fxAmbient ? "ON" : "OFF")
            + " / PULSE " + (fxBeatPulse ? "ON" : "OFF")
            + " / VIGNETTE " + (comfortVignette ? "ON" : "OFF")
            + "\nMUSIC " + musicStep + "/5 / KOMO " + (komoBubbles ? (komoLanguage == 0 ? "EN" : "JP") : "QUIET")
            + (ReducedMotion() ? "\nREDUCED MOTION: effects stay still" : "");
        for (int i = 0; i < labels.Length; i++) if (labels[i] != null) labels[i].text = text;
    }
}
