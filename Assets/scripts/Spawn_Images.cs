
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Spawn_Images : MonoBehaviour
{
   public float distanciaMin = 60f;
   public static float real_curve=0.0f; // passa -1 se tiver na direita , passa 0 se tiver no centro , passa 1 se tiver na esquerda
   public static float real_position=0.0f;
   
   private GameObject player;

   public GameObject passar_prefab;
   public GameObject Nao_passar_prefab;

   public Quaternion Z_90 =new Quaternion( 0.0f, 0.0f, 1.0f, 1.0f);
   
   private float distancia;
   private float offset= 500.01f;
   private float car_position=0;
   public bool enterd=false;

   public float layer_2 = -4.166666667f; //These are the lane Z positions: layer 3 is left lane, layer 2 is right line. 0 is center
   public float layer_3 = 4.166666667f;

   public enum LanePosition{
      Left,
      Center,
      Right
   }

   //Current lane of car
   public static LanePosition currentLane = LanePosition.Center;
   
   public static  int right_left=3;
   public static int right_center=3;

   public static int left_right=3;
   public static int left_center=3;

   public static int center_left=3;
   public static int center_right=3;

   public static List <float> curves_array= new List <float>();
   private bool changed_scene;

   //public GameObject shapePanelScript; can just ref class directly? => Yes, if func is public static. Gives global storage class, no need to create instance

  // [SerializeField] private ShapePanel shapepanel;// "no point doing this cos spawning multiple inst so mult panels. will have to manage many. want panel as single instance, like UI. find way to get signal from this code, when sign display is triggered"

   void Start()
   {
      player = GameObject.FindGameObjectWithTag ("Player");
       if(Options_Menu.ViewField!=0){
            distanciaMin = Options_Menu.ViewField;
        }
      real_position=0.0f;

      //shapepanel.DisablePanel();
      //UnityEngine.Debug.Log("Start");
   }

   void FixedUpdate ()
   {
      changed_scene = Reset_Level.sceneChanging_in_between;
      verify_variables();
      Spawn_signal();
      UpdateCurrentLane();      
     
   }

   
   void UpdateCurrentLane(){

      car_position = Car_Movement.position_z - offset; //NB same as SpawnSignal - duplicate calc

      if(car_position > layer_3 ){
         currentLane = LanePosition.Left;
      }

      else if( layer_3 >= car_position && car_position > layer_2){
         currentLane = LanePosition.Center;
      }

      else if(layer_2 >= car_position){
         currentLane = LanePosition.Right;
      }
   }

  //centro =0
  // direita =-1
  //esquerda = 1


  //center = 0
  //right = -1
  //left = 1

   void Spawn_signal(){
      distancia = Vector3.Distance(transform.position, player.transform.position);  //distancia is dist from car to the sign? transform is the next sign, spawn new and calc dist each time
     // "debug player pos, relation to road sign distance param. Then update dist % label"

      //Debug.Log("player.transform.position X: " + player.transform.position.x); //starts at -500, same as Tocus
     
      if (distancia <= distanciaMin) { //"60m before sign, then turns on? test"

         //UnityEngine.Debug.Log("spawn signal"); //but does all the time after first one. yes, called in fixed update above
 
         car_position = Car_Movement.position_z - offset; //Horizontal car pos - used for lane detection

         if(!enterd){ //enterd set true when signals set (at end of all below)
            int aleatorio =0;

            Vector3 right_side__center = new Vector3 ( transform.position.x - 0.1f, transform.position.y, transform.position.z + 20);
            Vector3 left_side__center= new Vector3 ( transform.position.x - 0.1f, transform.position.y, transform.position.z - 20);

            Vector3 right_side__left = new Vector3 ( transform.position.x - 0.1f, transform.position.y, transform.position.z + 20 +3);
            Vector3 left_side__left= new Vector3 ( transform.position.x - 0.1f, transform.position.y, transform.position.z - 20 +3 );

            Vector3 right_side__right = new Vector3 ( transform.position.x - 0.1f, transform.position.y, transform.position.z + 20 -3 );
            Vector3 left_side__right= new Vector3 ( transform.position.x - 0.1f, transform.position.y, transform.position.z - 20 -3);

            //Debug.Log("distancia: " + distancia + "distanciaMin: " + distanciaMin + "car_position: " + car_position);
            
            //Car on the left side - layer 3 (4.16) is min pos for left lane
            if(car_position > layer_3 ){
               Instat_NaoPassar(right_side__left, left_side__left); //signal_nao_passar(Clone) in Inspector is an X (no pass). Passar is the arrow to pass in this lane. Each separate clone for each sign (seems dumb). Add keeps spawning in loop
              // "whatever, dont try to fix everything. just want to trigger prompts to driver for pin pad etc, get this working, commit and then clean rest."

               aleatorio= Random.Range(1,5); //"randomly set lane?" aleatorio means random. Thinks its next lange to change to, chooses one of below randomly

              if(aleatorio<3 && (center_left>0 || center_right>0 )&& left_center>0)
               {
                  real_position=0.0f;
                  left_center--;

                  //signal_positioning(Vector3 inst_side1, Vector3 inst_side2, Vector3 Ninst_side1, Vector3 Ninst_side2, int Numb_curves , float RP){
                  // So (right side On, left side On, right side Off, left side Off)
                //  Debug.Log("car on left, set sign to X Y X ");
                  signal_positioning(right_side__center, left_side__center, right_side__right, left_side__right, 1, real_position );
                   
               }
               else if((right_left>0 || right_center>0) && left_right>0) // carro vai do lado esquerdo para o direita -> car goes from left to right
               {
                  real_position=-1.0f;
                  left_right--;
                //  Debug.Log("car on left, set sign to X X Y ");
                  signal_positioning(right_side__right, left_side__right, right_side__center, left_side__center, 2, real_position );  
               }
                
               else  { //Duplicate of first case! this code...
                  real_position=0.0f;
                  left_center--;
                 // Debug.Log("car on left, set sign to X Y X again? ");
                  signal_positioning(right_side__center, left_side__center, right_side__right, left_side__right, 1, real_position );
               }
            }

            //carro ta no no centro -> car in the centre
            if( layer_3 >= car_position && car_position > layer_2){

               Instat_NaoPassar(right_side__center, left_side__center);
               aleatorio = Random.Range(1,5);

               if(aleatorio<3 && (right_left>0 || right_center>0) && center_right>0 ){
                  center_right--;
                  real_position=-1.0f;
                  signal_positioning(right_side__right, left_side__right, left_side__left, right_side__left, 1, real_position );
                  
               }
               else if((left_right>0 || left_center>0) && center_left>0){
                  center_left--;
                  real_position=1.0f;
                  signal_positioning(right_side__left, left_side__left, right_side__right, left_side__right, 1, real_position );
                 
               }
               else{
                  real_position=-1.0f;
                  center_right--;
                  signal_positioning(right_side__right, left_side__right, right_side__left, left_side__left, 1, real_position );
               }
            }

            //carro ta no no lado direito -> The car is on the right side
            if(layer_2 >= car_position){
               
               Instat_NaoPassar(right_side__right, left_side__right);
               aleatorio= Random.Range(1,5);

               if(aleatorio<3 && (center_left>0 || center_right>0)&& right_center>0  ) {
                  real_position=0.0f;
                  right_center--;
                  signal_positioning(right_side__center, left_side__center, left_side__left, right_side__left, 1, real_position );
                 
               }
                else if((left_center>0 || left_right>0) && right_left>0){
                  real_position=1.0f;
                  right_left--;
                  signal_positioning(right_side__left, left_side__left, left_side__center, right_side__center, 2, real_position );
            
               }
               else {
                  real_position=0.0f;
                  right_center--;
                  signal_positioning(right_side__center, left_side__center, left_side__left, right_side__left, 1, real_position );
               }
            }
            enterd=true;

            //trigger panel on
            //shapepanel.EnablePanel();
            //StartCoroutine(Wait(3.0f));

         } //end enterd (lane selected?)
      }
   }

    IEnumerator Wait(float delay)
    {
      yield return new WaitForSeconds(delay);
      //shapepanel.DisablePanel();
    }

   private void signal_positioning(Vector3 inst_side1, Vector3 inst_side2, Vector3 Ninst_side1, Vector3 Ninst_side2, int Numb_curves , float RP){
      Instat_Passar(inst_side1, inst_side2);
      Instat_NaoPassar(Ninst_side1, Ninst_side2);
      perfectCurve(RP,Numb_curves);
   }

   void Instat_NaoPassar( Vector3 Side1, Vector3 Side2){
      Instantiate(Nao_passar_prefab, Side1, Z_90);
      Instantiate(Nao_passar_prefab, Side2, Z_90);
   }

   void Instat_Passar( Vector3 Side1, Vector3 Side2){
      Instantiate(passar_prefab, Side2, Z_90);
      Instantiate(passar_prefab, Side1, Z_90);
   }


    void verify_variables ()
   {
      if( changed_scene== true){
         right_left=3;
         right_center=3;
         left_center=3;
         left_right=3;
         center_left=3; 
         center_right=3;
         changed_scene= false;
      }

   }
  
   void perfectCurve(float real_position, float nmb_lane){
      if(real_position > real_curve){
         while(nmb_lane>0){
           
            nmb_lane-= 0.50f;
            real_curve += 0.5f * 1;

            if(real_curve<=1 ){
               if(real_curve>=-1) {
                  curves_array.Add(real_curve);

               }
            }
            //StartCoroutine(Wait(1));
         } 

      }else{

        while(nmb_lane>0){

            nmb_lane -= 0.50f;
                  real_curve += 0.5f * -1;

            if(real_curve<=1 ){
               if(real_curve>=-1) {
                  curves_array.Add(real_curve);

               }
            }
           // StartCoroutine(Wait(-1));
         }
      }
   }
/*
   IEnumerator Wait( int add_sub)
    {
      real_curve += 0.5f * add_sub;

      if(real_curve<=1 ){
         if(real_curve>=-1) {
            curves_array.Add(real_curve);

         }
      }
      yield return new WaitForSeconds(0.5f);
    }*/
}
