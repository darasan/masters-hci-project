using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

using System;
using System.Linq;
using System.Collections;
using System.Collections.Generic;

public class Main_Menu : MonoBehaviour
{
    [SerializeField] private Dropdown currentShapeDropdown;

    void PopulateCurrentShapeDropdown()
    {
        currentShapeDropdown.ClearOptions();

        List<string> shapes = Enum.GetNames(typeof(UserSettings.ShapeType)).ToList();
        currentShapeDropdown.AddOptions(shapes);
    }

    void OnShapeSelected(int index)
    {
        UserSettings.Instance.currentShape = (UserSettings.ShapeType)index;
        Debug.Log("Selected shape: " + UserSettings.Instance.currentShape);
    }

    void Start()
    {
        PopulateCurrentShapeDropdown();
        currentShapeDropdown.onValueChanged.AddListener(OnShapeSelected);

        //Set initial value
        currentShapeDropdown.value = (int) UserSettings.Instance.currentShape;
        currentShapeDropdown.RefreshShownValue();
    }

    public void StartTest()
    {
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Start Test", " " , " ");
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Current shape:", UserSettings.Instance.currentShape.ToString(), " ");
        Debug.Log("Current shape:" + UserSettings.Instance.currentShape.ToString());

        //Set column names for driving data
        LoggingSystem.Instance.writeMultipleValuesWithTimestamp("Meters", "currentLane", "targetLane");

        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex + 1);
    }

    public void QuitApplication ()
    {
        Debug.Log("Quit Application");
        Application.Quit();
    }
}

