using UdonSharp;
using UnityEngine;
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class CommonsTopicCard : UdonSharpBehaviour
{
    public TextMesh card;
    public string[] topics;
    private int index;
    public override void Interact()
    {
        if (card == null || topics == null || topics.Length == 0) return;
        index = (index + 1) % topics.Length; card.text = topics[index];
    }
}
