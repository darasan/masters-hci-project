using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using UnityEngine.UI;
using System;

public class Options_Menu : MonoBehaviour
{

    public static int Car_speed = 60;
    public static int SignaDistance =150;
    public static int RoadLenght = 1000;
    public static float ViewField= 60;

    public void Car_velocity(string Car_velocity){
        try{
            Car_speed = int.Parse(Car_velocity);

            Car_speed = Car_speed > 400 ? 400 : Car_speed;
            Car_speed = Car_speed < 10 ? 10 : Car_speed;  
        }
        catch(Exception e)
        {
            print("Error "+e);
        }
    }

    public void Signal_Distancing(string SignaDistanceing){
        try{
            SignaDistance = int.Parse(SignaDistanceing);

            SignaDistance = SignaDistance > 500 ? 500 : SignaDistance;
            SignaDistance = SignaDistance < 100  ? 100  : SignaDistance;  
        }
        catch(Exception e)
        {
            print("Error "+e);
        }
    }


    public void Road_Lenght(string Lenght){
        try{
            RoadLenght = int.Parse(Lenght);

            RoadLenght = RoadLenght > 10000 ? 10000 : RoadLenght;
            RoadLenght = RoadLenght < 750 ? 750 : RoadLenght;  
        }
        catch(Exception e)
        {
            print("Error "+e);
        }

        print("RoadLenght: " + RoadLenght);
    }

     public void Field_of_view(string View){
        try{
            ViewField = int.Parse(View);

            ViewField = ViewField > 900 ? 900 : ViewField;
            ViewField = ViewField < 100 ? 100 : ViewField; 
        }
        catch(Exception e)
        {
            print("Error "+e);
        }
    }
}
