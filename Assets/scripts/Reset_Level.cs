using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class Reset_Level : MonoBehaviour
{
    private GameObject player;

    public static float num_Of_Reps=0;
    public static float repetition=0;

    public static bool stop_storage = false;
    private bool Enterd=false;
    public static bool sceneChanging_in_between= false;
  
    void Start()
    {
      sceneChanging_in_between=false;
      num_Of_Reps=Form_Menu.rep;
      repetition=Scene_Changing.repetition;
      stop_storage=false;
        
      player = GameObject.FindGameObjectWithTag("Player");
       
    }


  void Update()
  {
    if (Enterd) {//stops car
      
      player.GetComponent<Rigidbody>().linearVelocity = Vector3.zero;
      player.GetComponent<Rigidbody>().angularVelocity = Vector3.zero;

      if (Input.GetKeyDown("r")){ 
        stop_storage=false;
        repetition++;

        SceneManager.LoadScene("in_between");
        
      }
    }
  }


  void OnCollisionEnter(Collision collision)
  {
    if (collision.gameObject.tag == "Player"){
      sceneChanging_in_between=true;
      Enterd=true;
      stop_storage=true;
    }
  }
}
