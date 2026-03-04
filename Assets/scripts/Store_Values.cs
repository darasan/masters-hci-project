using System.Collections;
using System.Collections.Generic;
//using System.Diagnostics;
using UnityEngine;

public class Store_Values : MonoBehaviour
{
    private float offset_z= 500.01f;
    private float offset_x= 37.1f;
  
    private float position_x=0f; 
    private float position_z=0f;

    public bool store_continues ;
    // Update is called once per frame

    private string currentLane;
    private string targetLane;

    void Start()
    {
        StartCoroutine(take_values());
        float cube_lenght=Change_Road.lenght;
        float start_position =  GameObject.FindGameObjectWithTag("road").transform.position.x;
        offset_x=start_position - cube_lenght;
    }


    void FixedUpdate()
    {
        position_x = Car_Movement.position_x - offset_x;
        position_z = Car_Movement.position_z - offset_z;
        //targetLane = Spawn_Images.real_position; real_position already captured in fixed update in SpawnImages, no need to copy here. Just write to data below
        //Guess this is called every frame, eg at 30 fps so 30 times/second-> around 30ms. If want faster writes than this maybe update it but prob fine

        store_continues = Reset_Level.stop_storage;
        //Debug.Log("pos X: " + position_x + "pos Z: " + position_z + "real pos: " + Real_position);       
    }

    IEnumerator take_values()
    {
        while( !store_continues){
            currentLane = Spawn_Images.currentLane.ToString();
            targetLane  = ((Spawn_Images.LanePosition)Spawn_Images.real_position).ToString();

            //try own logger and compare
            //LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("pos_x", position_x.ToString() , " ");

            //For mult values per timestamp like orig file, just use simple message, not AOT. Separate with semicolons by self:
            LoggingSystem.Instance.writeMessageWithTimestampToLog("meters: " + Car_Movement.norm_pos_x + "; currentLane: " + currentLane + "; targetLane: " + targetLane + "; currentShape: " + UserSettings.Instance.currentShape.ToString());

            yield return new WaitForSeconds(0.20f); //was 0.5, slow down for testing
        }
    }

}
