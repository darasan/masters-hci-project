using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class Car_Movement : MonoBehaviour{

    [SerializeField] WheelCollider front_right;
    [SerializeField] WheelCollider front_left;
    [SerializeField] WheelCollider back_right;
    [SerializeField] WheelCollider back_left;

    [SerializeField] Transform front_right_tranform;
    [SerializeField] Transform front_left_tranform;
    [SerializeField] Transform back_right_tranform;
    [SerializeField] Transform back_left_tranform;

    public float acceleration = 500f;
    public float breakingForce = 300f;

    private float currentAcceleration= 0f;
    private float currentBreakForce = 0f; 
    public static float position_z=0;
    public static float position_x=0;

    public int maxVelocity;
    public float CurrentSpeed=0;

    private float LowestSteerSpeed = 47;
    private float lowSpeedSteerAngel = 37;
    private float heightSpeedSteeringel = 1;
    public bool entrou=true;

    [Header("UI")]
    public Text speedLabel; 
    public Text distanceLabel;

    public static float norm_pos_x = 0; //car pos + 500 adjusted for offset
    public static float percent_complete = 0;

    private void Start() {
        maxVelocity = Options_Menu.Car_speed; 
        
    }

    private void FixedUpdate() {
        controlar();
    }

     private void Update() {
        if(entrou){
            float x = Change_Road.lenght;
            float start_position =  GameObject.FindGameObjectWithTag("road").transform.position.x;
            start_position -= x;

            transform.position = new Vector3(start_position + 10, 1.5f , 500f);
            entrou =false;
        }

        rotate_wheels();

        if (speedLabel != null){
            speedLabel.text = ((int)CurrentSpeed) + " km/h";
        }

        distanceLabel.text = (norm_pos_x + " meters/3000");
     }
     
   
    private void controlar() {
        //limite de velocidade 
        CurrentSpeed = 2 * Mathf.PI * back_right.radius * back_right.rpm * 60 / 1000;
        CurrentSpeed= Mathf.Round(CurrentSpeed);

         // Get forward/reverse acceleration from the vertical axis (W and S keys)
         if(CurrentSpeed > (maxVelocity - 1 ) ){
            currentAcceleration= 1;
         }else{
            //currentAcceleration= acceleration * Input.GetAxis("Vertical");  
            currentAcceleration = 1000; //keep held 
         }
         
        //print("currentAcceleration: " + currentAcceleration);

        var speedFactor= GetComponent<Rigidbody>().linearVelocity.magnitude/LowestSteerSpeed;
        var currentSteerAngle =Mathf.Lerp(lowSpeedSteerAngel, heightSpeedSteeringel,speedFactor );
        
        //Kybd control
        currentSteerAngle *=Input.GetAxis("Horizontal");

        //Add wheel
        //currentSteerAngle *=Input.GetAxis("SteeringWheel");

        if(Input.GetKey(KeyCode.Space)){
            currentBreakForce = breakingForce;
        }
        else{
            currentBreakForce = 0f;
        }

        front_right.motorTorque = currentAcceleration;
        front_left.motorTorque = currentAcceleration;
        brake();
        
        front_left.steerAngle = currentSteerAngle;
        front_right.steerAngle = currentSteerAngle;

        position_z = transform.position.z;
        position_x=transform.position.x;

        //Debug.Log("Car pos x: " + position_x); //Starts at -500, finishes at 2500. So 3000 total -> Same val as Tocus x position. 
        //Offset added in SpawnImages, ln 79. Only Z axis though? Dunno why (dont care)
        norm_pos_x = Mathf.Round(position_x + 480);
        percent_complete =  Mathf.Round((norm_pos_x/2980) * 100); //subtract 20 offset from both
        //Debug.Log("Normalised car pos x: " + norm_pos_x + " % complete: " + percent_complete);
    }


    private void brake() {
         front_right.brakeTorque = currentBreakForce;
        front_left.brakeTorque = currentBreakForce;
        back_right.brakeTorque = currentBreakForce;
        back_left.brakeTorque = currentBreakForce;
     }

    private void rotate_wheels() {
        front_right_tranform.Rotate( front_right.rpm/60 * 360 * Time.deltaTime, 0 ,0);
        front_left_tranform.Rotate( front_left.rpm/60 * 360 * Time.deltaTime, 0 ,0);
        back_right_tranform.Rotate( back_right.rpm/60 * 360 * Time.deltaTime, 0 ,0);
        back_left_tranform.Rotate( back_left.rpm/60 * 360 * Time.deltaTime, 0 ,0);
     }


}