using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
using VRC.SDK3.Components;
using VRC.SDK3.Components.Video;
using VRC.SDK3.Video.Components.Base;

[UdonBehaviourSyncMode(BehaviourSyncMode.Manual)]
public class CommonsVideoSync : UdonSharpBehaviour
{
    public CommonsWorldState state;
    public BaseVRCVideoPlayer player;
    public VRCUrlInputField urlInput;
    public RenderTexture output;
    public Material screen;
    public TextMesh status;
    [UdonSynced] public VRCUrl sharedUrl = VRCUrl.Empty;
    [UdonSynced] public bool playing;
    [UdonSynced] public int revision;
    [UdonSynced] public double startedAt;
    private int loadedRevision = -1;
    private bool ready;
    private float nextCheck;
    private float nextAllowedLoad;

    public void LoadFromField()
    {
        if (state == null || !state.CanControl() || urlInput == null || Time.time < nextAllowedLoad) return;
        VRCUrl value = urlInput.GetUrl();
        if (value == null || string.IsNullOrEmpty(value.Get())) return;
        Networking.SetOwner(Networking.LocalPlayer,gameObject);
        sharedUrl=value;revision++;playing=true;startedAt=0;nextAllowedLoad=Time.time+6f;
        RequestSerialization(); Apply();
    }
    public void StopPlayback()
    {
        if(state == null || !state.CanControl())return;
        Networking.SetOwner(Networking.LocalPlayer,gameObject);playing=false;RequestSerialization();Apply();
    }
    public override void OnDeserialization(){Apply();}
    private void Apply()
    {
        if(player==null)return;
        if(!playing)
        {
            ready=false;player.Stop();if(state!=null)state.ApplyState();
            if(status!=null)status.text="VIDEO STOPPED";return;
        }
        if(loadedRevision!=revision)
        {
            loadedRevision=revision;ready=false;player.LoadURL(sharedUrl);
            if(status!=null)status.text="LOADING VIDEO";
        }
    }
    public override void OnVideoReady(){ready=true;if(playing)player.Play();}
    public override void OnVideoStart()
    {
        if(!playing){player.Stop();return;}
        if(Networking.IsOwner(gameObject) && startedAt==0)
        {startedAt=Networking.GetServerTimeInSeconds();RequestSerialization();}
        if(screen!=null)screen.mainTexture=output;
        if(status!=null)status.text="VIDEO / SYNC";
        CorrectTime();
    }
    void Update()
    {
        if(Time.time<nextCheck)return;
        nextCheck=Time.time+5;CorrectTime();
    }
    private void CorrectTime()
    {
        if(!playing || !ready || startedAt<=0 || player==null)return;
        float duration=player.GetDuration();
        if(duration<=0 || float.IsInfinity(duration))return; // Live streams: no seek.
        float expected=Mathf.Clamp((float)(Networking.GetServerTimeInSeconds()-startedAt),0,duration);
        if(Mathf.Abs(player.GetTime()-expected)>1.5f)player.SetTime(expected);
    }
    public override void OnVideoEnd()
    {
        if(!Networking.IsOwner(gameObject))return;
        playing=false;RequestSerialization();Apply();
    }
    public override void OnVideoError(VideoError error)
    {
        ready=false;if(status!=null)status.text="VIDEO ERROR: "+error.ToString();
        if(Networking.IsOwner(gameObject)){playing=false;RequestSerialization();}
        if(state!=null && screen!=null && state.slides!=null && state.slides.Length>0)
            screen.mainTexture=state.slides[Mathf.Clamp(state.slideIndex,0,state.slides.Length-1)];
    }
    public override bool OnOwnershipRequest(VRCPlayerApi requestingPlayer,VRCPlayerApi newOwner)
    {return state==null || !state.hostLocked || (Utilities.IsValid(requestingPlayer) && (requestingPlayer.isMaster || requestingPlayer.isInstanceOwner));}
}
