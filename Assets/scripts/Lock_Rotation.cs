using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Lock_Rotation : MonoBehaviour
{
   public Transform r;
   private bool change_view= true;
   private bool cliked= false;
    
    void FixedUpdate () {
        
        r.eulerAngles = new Vector3 (r.eulerAngles.x, r.eulerAngles.y, 0);

        cliked = Input.GetKeyDown("c") ? true : cliked;

        if(cliked){
            
            if(change_view){
                transform.position = transform.position + new Vector3(-12, 2.5f,0 );
                change_view= false;
            }
            else{
                transform.position = transform.position + new Vector3(12, -2.5f,0 );
                change_view= true;
            }
           
            cliked=false;
        }

        
    }
}
