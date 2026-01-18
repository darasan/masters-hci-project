using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Change_Road : MonoBehaviour
{
    public float X_axis = 1000f;
    private float Y_axis = 0.8f;
    private float Z_axis = 25f;

    public static float lenght = 0;

    void Start()
    {
     
      float sum=0f;
        if(Options_Menu.RoadLenght!=0){
           sum=Options_Menu.RoadLenght; 
         
        }
      sum = X_axis;
      
      transform.localScale = new Vector3(sum ,Y_axis, Z_axis);
   
      lenght= sum/2;

      print("Road length: " + lenght);

    }

}
