using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.Manual)]
public class CommonsTimeOfDay : UdonSharpBehaviour
{
    [UdonSynced] public float hour = 20f;
    [UdonSynced] public bool cycling;
    [UdonSynced] public double epoch;
    public float secondsPerDay = 1440f;
    public CommonsWorldState state;
    public Material[] surfaces;
    public Material sky;
    public Material[] glows;
    public Light sun;
    public TextMesh[] labels;
    private float nextTick;

    void Start() { ApplyHour(CurrentHour()); }
    public override void OnDeserialization() { ApplyHour(CurrentHour()); }
    public float CurrentHour()
    {
        return Mathf.Repeat(hour + (cycling ? (float)(Networking.GetServerTimeInSeconds() - epoch) * 24f / Mathf.Max(120f, secondsPerDay) : 0f), 24f);
    }
    private bool BeginChange()
    {
        if (state == null || !state.CanControl()) return false;
        if (!Networking.IsOwner(gameObject)) Networking.SetOwner(Networking.LocalPlayer, gameObject);
        return Networking.IsOwner(gameObject);
    }
    private void SetHour(float value)
    {
        if (!BeginChange()) return;
        hour = Mathf.Repeat(value, 24f); cycling = false;
        epoch = Networking.GetServerTimeInSeconds();
        ApplyHour(hour); RequestSerialization();
    }
    public void Dawn() { SetHour(6f); }
    public void Day() { SetHour(12f); }
    public void Dusk() { SetHour(18f); }
    public void Night() { SetHour(0f); }
    public void Earlier() { SetHour(CurrentHour() - 1f); }
    public void Later() { SetHour(CurrentHour() + 1f); }
    public void ToggleCycle()
    {
        if (!BeginChange()) return;
        hour = CurrentHour(); epoch = Networking.GetServerTimeInSeconds(); cycling = !cycling;
        ApplyHour(hour); RequestSerialization();
    }
    void Update()
    {
        if (!cycling || Time.time < nextTick) return;
        nextTick = Time.time + .25f; ApplyHour(CurrentHour());
    }
    public void Refresh() { ApplyHour(CurrentHour()); }
    public void ApplyHour(float value)
    {
        float a = (value - 6f) * Mathf.PI / 12f;
        float elevation = Mathf.Sin(a);
        float day = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(-.12f, .5f, elevation));
        float twilight = Mathf.Clamp01(1f - Mathf.Abs(elevation) / .38f);
        Color top = Color.Lerp(new Color(.009f,.016f,.044f), new Color(.12f,.32f,.61f), day);
        Color horizon = Color.Lerp(new Color(.045f,.065f,.11f), new Color(.57f,.72f,.86f), day);
        horizon = Color.Lerp(horizon, new Color(.62f,.27f,.12f), twilight * .65f);
        Color sunlight = Color.Lerp(new Color(1f,.42f,.17f), new Color(1f,.96f,.86f), Mathf.Clamp01(elevation * 2f));
        Vector3 direction = new Vector3(Mathf.Cos(a)*.85f, elevation, Mathf.Cos(a)*.53f).normalized;
        if (sky != null)
        {
            sky.SetColor("_Top",top); sky.SetColor("_Horizon",horizon);
            sky.SetColor("_Ground",Color.Lerp(new Color(.018f,.023f,.035f),new Color(.18f,.21f,.24f),day));
            sky.SetVector("_SunDirection",direction); sky.SetColor("_SunColor",sunlight * day * 1.8f);
        }
        RenderSettings.ambientSkyColor = Color.Lerp(new Color(.10f,.14f,.22f),new Color(.45f,.56f,.7f),day);
        RenderSettings.ambientEquatorColor = Color.Lerp(new Color(.075f,.085f,.11f),new Color(.27f,.30f,.34f),day);
        RenderSettings.ambientGroundColor = Color.Lerp(new Color(.045f,.042f,.04f),new Color(.13f,.12f,.10f),day);
        RenderSettings.fogColor = Color.Lerp(new Color(.026f,.036f,.06f),horizon*.72f,day);
        bool atKart=Utilities.IsValid(Networking.LocalPlayer) && Networking.LocalPlayer.GetPosition().x>=100f;
        RenderSettings.fogDensity = atKart?Mathf.Lerp(.0022f,.001f,day):Mathf.Lerp(.007f,.0035f,day);
        if (sun != null) { sun.transform.rotation=Quaternion.LookRotation(-direction); sun.color=sunlight; sun.intensity=day*.85f; }
        Color tint = Color.Lerp(new Color(.78f,.84f,.94f),Color.white,day);
        Color fill = Color.Lerp(new Color(.008f,.012f,.025f),new Color(.16f,.20f,.25f),day);
        if (surfaces != null) for (int i=0;i<surfaces.Length;i++)
        {
            Material m=surfaces[i]; if (m==null) continue;
            m.SetColor("_TimeTint",tint); m.SetColor("_DayFill",fill);
            if (m.HasProperty("_TimeEmission")) m.SetFloat("_TimeEmission",Mathf.Lerp(1f,.45f,day));
            if (m.HasProperty("_SunDirection")) m.SetVector("_SunDirection",direction);
            if (m.HasProperty("_SunColor")) m.SetColor("_SunColor",sunlight*day);
        }
        if (glows != null) for (int i=0;i<glows.Length;i++)
            if (glows[i]!=null) glows[i].SetFloat("_TimeGlow",Mathf.Lerp(1f,.4f,day));
        int minutes = Mathf.FloorToInt(Mathf.Repeat(value,24f)*60f);
        if (labels != null) for (int i=0;i<labels.Length;i++)
            if (labels[i]!=null) labels[i].text="TIME / "+(minutes/60).ToString("00")+":"+(minutes%60).ToString("00")+(cycling?" / CYCLE":" / HOLD");
    }
    public override bool OnOwnershipRequest(VRCPlayerApi requestingPlayer,VRCPlayerApi newOwner)
    {
        return state!=null && (!state.hostLocked || (Utilities.IsValid(requestingPlayer) && (requestingPlayer.isMaster || requestingPlayer.isInstanceOwner)));
    }
}
