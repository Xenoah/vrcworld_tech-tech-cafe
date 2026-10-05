using UdonSharp;
using UnityEngine;
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsButton : UdonSharpBehaviour
{
    public UdonSharpBehaviour target;
    public string eventName;
    public override void Interact() { if (target != null) target.SendCustomEvent(eventName); }
}
