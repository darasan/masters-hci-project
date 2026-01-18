using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;
using System.IO;
using System;


public class Scene_Changing : MonoBehaviour
{
    public static float repetition;
    public float number_of_reps;
    private bool values_stored = false;
    
    void Start()
    {
        number_of_reps=Form_Menu.rep;
    }

    void Update()
    {
        if(!values_stored){
            writeCSV();
            values_stored=true;
        }
       
        if(Input.GetKeyDown("r")){
            repetition = Reset_Level.repetition;

            if(repetition!= number_of_reps)
            {
                SceneManager.LoadScene("Lane_chance_tes");
            }
            else
            {
                SceneManager.LoadScene("Menu");
            }    
         }
    }


    public void writeCSV()
    {
        List <float> positions_of_z= Store_Values.positions_z;
        List <float> positions_of_x= Store_Values.positions_x;

        List <float> Real_position= Store_Values.real_positions;

       // List <float> curves =  Spawn_Images.curves_array;
        List <float> curves_V2 =  Spawn_Images.curves_array;
        
        Spawn_Images.real_curve=0;

        string filePath = Application.dataPath + "/test.csv";

        float value=0;
        float previous_values=0;

        //loop novo o antigo vai aqui!!!!!!!
       for( int i = 0; i < Real_position.Count; i++ ){
            value=Real_position[i];

            if(value!=previous_values){
                print(" previus value: "+ previous_values+ " || valor atual: "+ value+"|| valor anterior-2"+Real_position[i-2] );

                float nmb_lane= (Math.Abs(value) + Math.Abs(previous_values));
                float lanes = nmb_lane;
            
                while(lanes>0){
                    lanes-= 0.5f;
                    curves_V2.Add(lanes);
                } 
                lanes=0;
                
                if(previous_values==-1 || (previous_values == 0 && value==1 )){
                    print("E  ");

                    for( int j = 0; (j < (nmb_lane*2) ) && ((i + j) < Real_position.Count); j++ )
                    {

                        if ((i + j) < Real_position.Count && curves_V2.Count>0){
                            Real_position[i+j]=curves_V2[0];
                            curves_V2.RemoveAt(0);

                        } 
                    }

                    i+=(int)(nmb_lane*2);

                }

                if(previous_values==1 || (previous_values == 0 && value == -1 )){
                    print("D  ");

                    /*for (int j = 0; j < curves_V2.Count; j++)
                    {
                        curves_V2[j] = -curves_V2[j];
                    }*/


                    for( int j = 0; (j < (nmb_lane*2)) && ((i + j) < Real_position.Count); j++ )
                    {

                        if ((i + j) < Real_position.Count && curves_V2.Count>0){
                            Real_position[i+j]=curves_V2[0];// fazer uma funçao que retorna uma lista de realposition e separar esta secçao toda da parte de escrever no ficheiro
                            curves_V2.RemoveAt(0);

                        }
                        
                    }

                    i+=(int)(nmb_lane*2);
                }
               
            }


            previous_values=value;
        }//////////////////////////////////

        if(IsFileLocked(filePath)){
            Debug.LogError("O arquivo CSV está sendo usado por outro processo. Não é possível escrever nele.");
            return;
        }

        TextWriter tw= new StreamWriter(filePath, true);
        tw.WriteLine("Position X; Position Z; Signals Position");


       for( int i = 0; i < positions_of_x.Count; i++ )
        {
            double sig_pos = Math.Round( Real_position[i]*2*3.85f, 3);
            double Pos_z = Math.Round( positions_of_z[i], 3);
            double Pos_x = Math.Round( positions_of_x[i], 3);
        
            tw.WriteLine(Pos_x+";"+Pos_z+";"+sig_pos);
        }


        tw.Close(); 
        Real_position.Clear();
        positions_of_z.Clear();
        positions_of_x.Clear();
    }


        
    private bool IsFileLocked(string filePath)
    {   
        try
        {
            using (FileStream fs = File.Open(filePath, FileMode.Open, FileAccess.ReadWrite, FileShare.None))
            {
                fs.Close();
            }
        }
        catch (IOException ex)
        {
            var errorCode = System.Runtime.InteropServices.Marshal.GetHRForException(ex) & ((1 << 16) - 1);
            return errorCode == 32 || errorCode == 33;
        }

        return false;
    }
}




/*loop que estava antes
        for( int i = 0; i < Real_position.Count; i++ ){
      
            value=Real_position[i];

            if(value!=previous_values){

                float add= ( Math.Abs(value) + Math.Abs(previous_values))*2;// valeu entre 1 e -1 a multiplicar por 2
                

                for( int j = 0; (j < add ) && ((i + j) < Real_position.Count); j++ )
                {

                    if ((i + j) < Real_position.Count && curves.Count>0){
                        Real_position[i+j]=curves[0];
                        curves.RemoveAt(0);

                    }

                }

                i+=(int)add;
            }

            previous_values=value;
        }*/
        