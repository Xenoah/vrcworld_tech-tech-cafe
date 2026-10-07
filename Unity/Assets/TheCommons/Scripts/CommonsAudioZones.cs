using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsAudioZones : UdonSharpBehaviour
{
    public CommonsWorldState state;
    public AudioSource ambience;
    public AudioSource music;
    public AudioSource dance;
    public AudioSource videoAudio;
    public bool voiceZoning = true;
    private VRCPlayerApi[] players = new VRCPlayerApi[80];
    private float nextVoicePoll;
    private float targetAmbience;
    private float targetMusic;
    private float targetVideo;
    private float targetDance;
    private bool quiet;
    private int area;
    void Start()
    {
        if(dance!=null && dance.clip!=null) dance.time=(float)(Networking.GetServerTimeInSeconds()%dance.clip.length);
        Refresh();
    }
    private bool Inside(Vector3 p)
    { return p.x > 20.1f && p.x < 27.5f && p.y > 4.65f && p.y < 8.5f && p.z > 1f && p.z < 7.8f; }
    public void Refresh()
    {
        int m = state == null ? 0 : state.mode;
        float k = quiet ? .12f : 1f;
        targetAmbience = .13f * k;
        targetMusic = (m == 1 ? .035f : m == 2 ? 0 : m == 3 ? .07f : .12f) * k;
        targetDance = m == 2 ? .32f*k : 0;
        if(state!=null && state.videoSync!=null && state.videoSync.playing){targetMusic=0;targetDance=0;}
        targetVideo = (quiet ? .10f : .7f);
        if (area != 0) {targetAmbience=.065f;targetMusic=0;targetDance=0;targetVideo=0;}
    }
    void Update()
    {
        if (!Utilities.IsValid(Networking.LocalPlayer)) return;
        int current=Area(Networking.LocalPlayer.GetPosition());
        if(current!=area){area=current;Refresh();}
        bool now = Inside(Networking.LocalPlayer.GetPosition());
        if (now != quiet) { quiet = now; Refresh(); }
        float k = Mathf.Min(1f, Time.deltaTime*3f);
        if (ambience != null) ambience.volume = Mathf.Lerp(ambience.volume,targetAmbience,k);
        if (music != null) music.volume = Mathf.Lerp(music.volume,targetMusic,k);
        if (dance != null) dance.volume = Mathf.Lerp(dance.volume,targetDance,k);
        if (videoAudio != null) videoAudio.volume = Mathf.Lerp(videoAudio.volume,targetVideo,k);
        if (Time.time < nextVoicePoll) return;
        nextVoicePoll = Time.time + 1f;
        Refresh();
        VRCPlayerApi.GetPlayers(players);
        for (int i=0; i<players.Length; i++)
        {
            VRCPlayerApi p = players[i];
            if (!Utilities.IsValid(p) || p.isLocal) continue;
            bool separated = voiceZoning && (quiet != Inside(p.GetPosition()) || area != Area(p.GetPosition()));
            p.SetVoiceGain(separated ? 5f : 15f);
            p.SetVoiceDistanceNear(0);
            p.SetVoiceDistanceFar(separated ? 8f : 18f);
        }
    }
    private int Area(Vector3 p) { return p.x>=100f?2:p.x < -15f?1:0; }
    public void ToggleVoiceZoning() { voiceZoning = !voiceZoning; }
}
