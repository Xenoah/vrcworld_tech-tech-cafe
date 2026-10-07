using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsAreaVisibility : UdonSharpBehaviour
{
    public Renderer[] cafe;
    public Renderer[] fpv;
    public Renderer[] kart;
    public CommonsTimeOfDay timeOfDay;
    private float nextTick;
    private int area = -1;
    void Update()
    {
        if (Time.time<nextTick || !Utilities.IsValid(Networking.LocalPlayer)) return;
        nextTick=Time.time+.25f;
        float x=Networking.LocalPlayer.GetPosition().x;
        int value=x>=100f?2:x < -15f?1:0;
        if(value==area)return;
        area=value;
        // Colliders and Udon stay alive. External CVS2 vehicles are never toggled here.
        if(cafe!=null)for(int i=0;i<cafe.Length;i++)if(cafe[i]!=null)cafe[i].enabled=area==0;
        if(fpv!=null)for(int i=0;i<fpv.Length;i++)if(fpv[i]!=null)fpv[i].enabled=area==1;
        if(kart!=null)for(int i=0;i<kart.Length;i++)if(kart[i]!=null)kart[i].enabled=area==2;
        if(timeOfDay!=null)timeOfDay.Refresh();
    }
}
