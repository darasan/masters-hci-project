using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Store_Values : MonoBehaviour
{
    private float offset_z= 500.01f;
    private float offset_x= 37.1f;
    public static List <float> positions_x= new List <float>();
    public static List <float> positions_z= new List <float>();
    public static List <float> real_positions= new List <float>();

  
    private float position_x=0f; 
    private float position_z=0f;
    private float Real_position=0;

    public bool store_continues ;
    // Update is called once per frame

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
        Real_position= Spawn_Images.real_position;

        store_continues = Reset_Level.stop_storage;
       
    }

    IEnumerator take_values()
    {
        while( !store_continues){
           
            positions_z.Add(position_z);
            positions_x.Add(position_x);
            real_positions.Add(Real_position);
            yield return new WaitForSeconds(0.5f);

        }
    }

}
