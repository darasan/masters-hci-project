using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Show_Warning : MonoBehaviour
{
   public GameObject Object;

    void Start()
    {
        Object. SetActive (false);
    }

    void OnTriggerEnter (){
        Object.SetActive(true);
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Warning: user off track!", " ", " ");
    }

    void OnTriggerExit()
    {
        Object.SetActive(false);
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("User back on track", " ", " ");
    }
}
