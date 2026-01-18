using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using System;

public class Form_Menu : MonoBehaviour
{
    public static string Person_ID = "Daire";
    public static int rep;

    void Start()
    {
        print("Start Form Menu");
        print("Person_ID: " + Person_ID);
        print("Application.dataPath: " + Application.dataPath);
    }

    public void PlayGame()
    {
       if( Person_ID !=null){
         
            SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex + 1);
       }
    }

    public void String_reader_1(string ID){
        Person_ID = ID;
       
    }

    public void String_reader_2(string repetition){

        rep = 1;

        try{
             rep = int.Parse(repetition);

            rep = rep > 30 ? 30 : rep;
            rep = rep < 1  ? 1  : rep;  
        }
        catch(Exception e)
        {
            print("Error: " +e);
        }
    }

    public void QuitGame()
    {
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex - 1);
    }
}
