using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Signal_Position : MonoBehaviour
{
    
    public GameObject plane_prefab_;
    public GameObject empty_prefab_script;

    public Quaternion Z_90 =new Quaternion( 0.0f, 0.0f, 1.0f, 1.0f);

    public float road_tickness = 100f;

    private bool enterd= true;
    public float dist_betwen_sig=200;
    private float start_position = 0;
    private float cube_lenght=0;

     void Start()
    {
        if(Options_Menu.SignaDistance!=0){
            dist_betwen_sig = Options_Menu.SignaDistance;
        }
           
    }

    void Update()
    {
        if(enterd){

            float number_of_signal = calc_numb_signals();

            for(int i=0; i< number_of_signal -1; i++){

             create_signals(i);

            }  
            enterd=false;
        }
    }


    void create_signals(int i){
        int aleatorio = Random.Range(30, 60);

        Vector3 vector = new Vector3 (start_position+ i * dist_betwen_sig + aleatorio, 6f, 501 + road_tickness/2);
        Instantiate(plane_prefab_, vector, Z_90);

        vector = new Vector3 (start_position + i * dist_betwen_sig + aleatorio, 6f, 501 - road_tickness/2);
        Instantiate(plane_prefab_, vector, Z_90);

        vector = new Vector3 (start_position + i * dist_betwen_sig + aleatorio, 6f, 501);
        Instantiate(empty_prefab_script, vector, Z_90);
    }


    float calc_numb_signals(){
        cube_lenght=Change_Road.lenght;
        start_position = GameObject.FindGameObjectWithTag("road").transform.position.x;
        start_position -= cube_lenght -200;
        cube_lenght = cube_lenght * 2;

        float number_of_signal= (cube_lenght + start_position)/ dist_betwen_sig;
        return number_of_signal;
    }
}
