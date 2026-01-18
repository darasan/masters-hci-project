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
    }

    void OnTriggerExit()
    {
        Object.SetActive(false);
    }
}
