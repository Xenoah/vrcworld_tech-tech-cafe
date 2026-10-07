using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsAreaVisibility : UdonSharpBehaviour
{
    public Renderer[] cafe;
    public Renderer[] fpv;
    private float nextTick;
    private bool initialized;
    private bool inField;
    void Update()
    {
        if (Time.time<nextTick || !Utilities.IsValid(Networking.LocalPlayer)) return;
        nextTick=Time.time+.25f;
        bool value=Networking.LocalPlayer.GetPosition().x < -15f;
        if (initialized && value==inField) return;
        initialized=true; inField=value;
        // Keep objects, colliders and Udon alive so teleport arrival is always supported.
        if (cafe!=null) for(int i=0;i<cafe.Length;i++) if(cafe[i]!=null) cafe[i].enabled=!inField;
        if (fpv!=null) for(int i=0;i<fpv.Length;i++) if(fpv[i]!=null) fpv[i].enabled=inField;
    }
}
