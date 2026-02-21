using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Strat_Line : MonoBehaviour
{
    public float position=0;
    private float cube_lenght=0;
    
    void Update()
    {
        position =  GameObject.FindGameObjectWithTag("road").transform.position.x;
        cube_lenght= Change_Road.lenght;

        transform.position = new Vector3 (position - cube_lenght  + 30 , 8 , 500);

    }
}
