using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Mov_Cam : MonoBehaviour
{
    // Start is called before the first frame update
   /* [SerializeField] 
    private Vector3 offset;
    public GameObject car;
    public Vector3 offset_word;

    [Range(0,1)]
    public float suavidade= 0.3f;
    public Transform player;

    // Update is called once per frame
    void FixedUpdate()
    {
        transform.position = Vector3.Lerp(transform.position, player.position + offset, suavidade) ;

        transform.rotation = Quaternion.Euler(car.transform.localRotation.eulerAngles.x, car.transform.localRotation.eulerAngles.y, 0f);

        transform.RotateAround(offset, Vector3.zero, player.eulerAngles.x );

    }*/
//-471.9999  1.433669    500.0002
/*
    public Transform car;
    public float distance;
    public float height;
    public float rotationDamping;
    public float heightDamping;
    public float zoomRatio;
    public float defaultFOV;
    private float rotation_vector;

    void FixedUpdate(){
        Vector3 local_velocity= car.InverseTransformDirection(car.GetComponent<Rigidbody>().velocity);
        
        if(local_velocity.z< -0.5f){
            rotation_vector = car.eulerAngles.y + 100;
        }
        else{
            rotation_vector = car.eulerAngles.y ;
        }

        float accelaration = car.GetComponent<Rigidbody> ().velocity.magnitude;
        Camera.main.fieldOfView = defaultFOV+ accelaration * zoomRatio * Time.deltaTime;

    }


    void LateUpdate (){
        float wantedAngle = rotation_vector;
        float wantedHeight = car.position.y + height;
        float myAngle = transform.eulerAngles. y;
        float myHeight = transform.position.y;
       

       myAngle = Mathf.LerpAngle (myAngle, wantedAngle, rotationDamping * Time.deltaTime);

        myHeight = Mathf.LerpAngle (myHeight, wantedHeight, heightDamping * Time.deltaTime);

        Quaternion currentRotation = Quaternion.Euler (0,myAngle, 0);
        transform.position = car.position;
        transform.position -= currentRotation * Vector3.forward * distance;

        Vector3 temp = transform.position;
        temp.y = myHeight;

        transform.position= temp;
        transform.LookAt (car);

    }

*/
    
}
