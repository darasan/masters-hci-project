using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using System;

/*
public class Form_Menu : MonoBehaviour
{
    public static string Person_ID = "Daire";
    public static bool autoShowShapePanel = true;
    public static int shapePanelSeconds = 5;
    public static int rep;

    public static Form_Menu Instance { get; private set; }

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        DontDestroyOnLoad(gameObject); //Will persist between scenes. Create a new GO in top level menu and attach this script as component
    }

    void Start()
    {
        Debug.Log("Start Form Menu");
        Debug.Log("Person_ID: " + Person_ID);
        Debug.Log("Application.dataPath: " + Application.dataPath);
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
            Debug.Log("Error: " +e);
        }
    }

    public void SetShapePanelAutoShow(bool show)
    {
        autoShowShapePanel = show;
        Debug.Log("SetShapePanelAutoShow: " + autoShowShapePanel);
    }

    public void SetShapePanelTimeout(string seconds)
    {
        if(int.TryParse(seconds, out int shapePanelSeconds)){
            Debug.Log("SetShapePanelTimeout: " + shapePanelSeconds);

            //write to user settings for test
            UserSettings.Instance.shapePanelTimeoutSeconds = shapePanelSeconds;
        }
        else{
            Debug.Log("Invalid number");
        }
    }

    public void QuitGame()
    {
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex - 1);
    }
}
*/
