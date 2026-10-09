using UdonSharp;
using UnityEngine;
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsComfort : UdonSharpBehaviour
{
    public CommonsWorldState state;
    public CommonsLightingModes lighting;
    public bool lasersEnabled = true;
    public Material[] luminousMaterials;
    public Material djMaterial;
    public GameObject mirrorRoot;
    public GameObject glowRoot;
    public bool glowEnabled = true;
    public TextMesh label;
    public bool reducedMotion = true;
    public bool lowEmission = false;
    public bool djVisuals = true;
    private bool mirrorOn;
    void Start() { if (mirrorRoot != null) mirrorRoot.SetActive(false); Refresh(); }
    public void ToggleLasers() { lasersEnabled = !lasersEnabled; Refresh(); }
    public void ToggleMotion() { reducedMotion = !reducedMotion; Refresh(); }
    public void ToggleEmission() { lowEmission = !lowEmission; Refresh(); }
    public void ToggleDJVisuals() { djVisuals = !djVisuals; Refresh(); }
    public void ToggleGlow() { glowEnabled = !glowEnabled; Refresh(); }
    public void ToggleMirror() { mirrorOn = !mirrorOn; if (mirrorRoot != null) mirrorRoot.SetActive(mirrorOn); }
    public void Refresh()
    {
        int mode = state == null ? 0 : state.mode;
        if (glowRoot != null) glowRoot.SetActive(glowEnabled && !lowEmission);
        float emission = (lowEmission ? .35f : 1f) * (mode == 3 ? .4f : 1f);
        if (luminousMaterials != null)
            for (int i=0; i<luminousMaterials.Length; i++)
                if (luminousMaterials[i] != null) luminousMaterials[i].SetFloat("_LocalEmission", emission);
        if (djMaterial != null)
        {
            djMaterial.SetFloat("_Motion", reducedMotion ? 0 : 1);
            djMaterial.SetFloat("_Intensity", djVisuals && mode == 2 ? (lowEmission ? .3f : .7f) : .12f);
        }
        if (lighting != null) lighting.Refresh();
        if (label != null) label.text = "LOCAL COMFORT\nMotion " + (reducedMotion ? "REDUCED" : "ON") + " / Emission " + (lowEmission ? "LOW" : "NORMAL") + "\nLasers " + (lasersEnabled ? "ON" : "OFF");
    }
}
