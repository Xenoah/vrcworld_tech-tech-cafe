using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.Manual)]
public class CommonsWorldState : UdonSharpBehaviour
{
    [UdonSynced] public int mode = 0; // Lounge, Academic, DJ, Quiet Night
    [UdonSynced] public int slideIndex;
    [UdonSynced] public bool timerRunning;
    [UdonSynced] public double timerEnd;
    [UdonSynced] public bool questionTime;
    [UdonSynced] public bool pointerVisible;
    [UdonSynced] public float pointerX = 0.5f;
    [UdonSynced] public float pointerY = 0.5f;
    public bool hostLocked = true;
    public GameObject loungeRoot;
    public GameObject academicRoot;
    public GameObject hologramRoot;
    public GameObject pointerRoot;
    public Transform pointerTransform;
    public Material presentationMaterial;
    public Texture[] slides;
    public TextMesh modeLabel;
    public TextMesh timerLabel;
    public TextMesh qaLabel;
    public CommonsComfort comfort;
    public CommonsAudioZones audioZones;
    public CommonsVideoSync videoSync;
    private float nextTick;

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
    private void Commit() { ApplyState(); RequestSerialization(); }
    public void Lounge() { SetMode(0); }
    public void Academic() { SetMode(1); }
    public void DJ() { SetMode(2); }
    public void QuietNight() { SetMode(3); }
    private void SetMode(int value)
    {
        if (!BeginChange()) return;
        mode = value;
        if (mode != 1) { timerRunning = false; questionTime = false; pointerVisible = false; }
        Commit();
    }
    public void NextSlide() { ChangeSlide(1); }
    public void PreviousSlide() { ChangeSlide(-1); }
    private void ChangeSlide(int step)
    {
        if (!BeginChange() || slides == null || slides.Length == 0) return;
        if (videoSync != null && videoSync.playing) videoSync.StopPlayback();
        slideIndex = (slideIndex + step + slides.Length) % slides.Length;
        Commit();
    }
    public void StartTalk() { StartTimer(900); }
    public void StartQA() { StartTimer(300); }
    private void StartTimer(int seconds)
    {
        if (!BeginChange()) return;
        mode = 1; timerRunning = true;
        questionTime = seconds == 300;
        timerEnd = Networking.GetServerTimeInSeconds() + seconds;
        Commit();
    }
    public void StopTimer() { if (!BeginChange()) return; timerRunning = false; Commit(); }
    public void ToggleQA() { if (!BeginChange()) return; questionTime = !questionTime; Commit(); }
    public void TogglePointer() { if (!BeginChange()) return; pointerVisible = !pointerVisible; Commit(); }
    public void PointerLeft() { MovePointer(-0.05f, 0); }
    public void PointerRight() { MovePointer(0.05f, 0); }
    public void PointerUp() { MovePointer(0, 0.05f); }
    public void PointerDown() { MovePointer(0, -0.05f); }
    private void MovePointer(float x, float y)
    {
        if (!BeginChange()) return;
        pointerVisible = true; pointerX = Mathf.Clamp01(pointerX+x); pointerY = Mathf.Clamp01(pointerY+y); Commit();
    }
    public void ApplyState()
    {
        mode = Mathf.Clamp(mode, 0, 3);
        if (loungeRoot != null) loungeRoot.SetActive(mode == 0 || mode == 3);
        if (academicRoot != null) academicRoot.SetActive(mode == 1);
        if (hologramRoot != null) hologramRoot.SetActive(mode != 1);
        if (presentationMaterial != null && slides != null && slides.Length > 0 && (videoSync == null || !videoSync.playing))
            presentationMaterial.mainTexture = slides[Mathf.Clamp(slideIndex,0,slides.Length-1)];
        if (pointerRoot != null) pointerRoot.SetActive(mode == 1 && pointerVisible);
        if (pointerTransform != null) pointerTransform.position = new Vector3(10.45f + 7.1f*pointerX, .4f + 4f*pointerY, 16.735f);
        if (modeLabel != null) modeLabel.text = mode == 0 ? "LOUNGE" : mode == 1 ? "ACADEMIC" : mode == 2 ? "DJ / LIVE" : "QUIET NIGHT";
        if (qaLabel != null) qaLabel.text = questionTime ? "Q & A" : "";
        if (comfort != null) comfort.Refresh();
        if (audioZones != null) audioZones.Refresh();
        RefreshTimer();
    }
    void Update()
    {
        if (Time.time < nextTick) return;
        nextTick = Time.time + .25f; RefreshTimer();
    }
    private void RefreshTimer()
    {
        if (timerLabel == null) return;
        if (!timerRunning) { timerLabel.text = "15 MIN TALK / 5 MIN Q&A"; return; }
        int seconds = Mathf.Max(0, (int)(timerEnd - Networking.GetServerTimeInSeconds()));
        timerLabel.text = (seconds / 60).ToString("00") + ":" + (seconds % 60).ToString("00");
        if (seconds == 0 && Networking.IsOwner(gameObject))
        {
            timerRunning = false;
            // End-of-session emphasis returns to the conversation area.
            mode = 0; questionTime = false; pointerVisible = false; Commit();
        }
    }
    public override bool OnOwnershipRequest(VRCPlayerApi requestingPlayer, VRCPlayerApi newOwner)
    { return !hostLocked || (Utilities.IsValid(requestingPlayer) && (requestingPlayer.isMaster || requestingPlayer.isInstanceOwner)); }
}
