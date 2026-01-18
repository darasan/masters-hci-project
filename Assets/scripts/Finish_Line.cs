using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Finish_Line : MonoBehaviour
{
    private float position=0;
    private float cube_lenght=0;
    
    void Update()
    {
        position =  GameObject.FindGameObjectWithTag("road").transform.position.x;
        cube_lenght= Change_Road.lenght;

        transform.position = new Vector3 (position + cube_lenght -20 , 8 , 501);
    }
}
