using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using System.Collections;


public class UIManager : MonoBehaviour
{
    Color32 greenColour =  new Color32(32, 125, 47, 255);
    Color32 redColour   =  new Color32(221, 28, 0, 255);

    public Text currentLaneText;
    public Text targetLaneText;
    public Text currentShapeText;
    public Text currentReversalText;

    private string currentLane;
    private string targetLane;
    private bool inCorrectLane = true;

    [SerializeField] private GameObject detectShapePanel;

    public void SelectNextShapeInList(){
        int numShapes = UserSettings.Instance.numShapes;
        UserSettings.Instance.currentShape = (UserSettings.ShapeType) ((((int) UserSettings.Instance.currentShape) + 1) % numShapes);
        currentShapeText.text =  UserSettings.Instance.currentShape.ToString();
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Change current shape to: ",  currentShapeText.text, " ");
        //Debug.Log("Current shape: " + UserSettings.Instance.currentShape);
    }

    public void SelectPreviousShapeInList(){
        int numShapes = UserSettings.Instance.numShapes;
        UserSettings.Instance.currentShape = (UserSettings.ShapeType) ((((int) UserSettings.Instance.currentShape) - 1 + numShapes) % numShapes);
        currentShapeText.text =  UserSettings.Instance.currentShape.ToString();
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Change current shape to: ",  currentShapeText.text, " ");
        //Debug.Log("Current shape: " + UserSettings.Instance.currentShape);
    }

    public void SelectNextReversal(){
        int numReversals = UserSettings.Instance.numReversals;
        UserSettings.Instance.currentReversal = (UserSettings.ReversalType) ((((int) UserSettings.Instance.currentReversal) + 1) % numReversals);
        currentReversalText.text =  UserSettings.Instance.currentReversal.ToString();
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Change current reversal to: ",  currentReversalText.text, " ");
        Debug.Log("Current reversal: " + UserSettings.Instance.currentReversal);
    }

    public void SelectPreviousReversal(){
        int numReversals = UserSettings.Instance.numReversals;
        UserSettings.Instance.currentReversal = (UserSettings.ReversalType) ((((int) UserSettings.Instance.currentReversal) - 1 + numReversals) % numReversals);
        currentReversalText.text =  UserSettings.Instance.currentReversal.ToString();
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Change current reversal to: ",  currentReversalText.text, " ");
        Debug.Log("Current reversal: " + UserSettings.Instance.currentReversal);
    }


    void Awake()
    {

    }

    void Start()
    {
        currentShapeText.text =  UserSettings.Instance.currentShape.ToString();
    }

    void Update()
    {
        currentLane = Spawn_Images.currentLane.ToString();
        targetLane  = ((Spawn_Images.LanePosition)Spawn_Images.real_position).ToString();

        //Update UI text
        currentLaneText.text = "Current Lane: " + currentLane;
        targetLaneText.text  = " Target  Lane: " + targetLane;

        //Set colour
        if(currentLane == targetLane){
            currentLaneText.color = greenColour;
            inCorrectLane = true;
        }

        else{
            currentLaneText.color = redColour;
            inCorrectLane = false;
        }

        //Keyboard input
        if(Input.GetKeyDown(KeyCode.Space)){
            detectShapePanel.SetActive(!detectShapePanel.activeSelf);
            LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Detect shape prompt by spacebar: ", detectShapePanel.activeSelf.ToString(), "Current shape: " + UserSettings.Instance.currentShape.ToString());
        }

        else if (Input.GetKeyDown(KeyCode.UpArrow)){
            SelectNextShapeInList();
        }

        else if (Input.GetKeyDown(KeyCode.DownArrow)){
            SelectPreviousShapeInList();
        }

        else if (Input.GetKeyDown(KeyCode.LeftArrow)){
            SelectPreviousReversal();
        }

        else if (Input.GetKeyDown(KeyCode.RightArrow)){
            SelectNextReversal();
        }

        else if (Input.GetKeyDown(KeyCode.Return)){
            Debug.Log("Confirmed that detected shape");
            LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Confirmed that detected shape: ", UserSettings.Instance.currentShape.ToString(), " ");
        }

         else if (Input.GetKeyDown(KeyCode.Backspace)){
            Debug.Log("Could not detect shape");
            LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Could not detect shape: ", UserSettings.Instance.currentShape.ToString(), " ");
        }
    }

    public void QuitButtonPressed()
    {
        Debug.Log("Quit");
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Quit button pressed, load main menu", " ", " ");
        SceneManager.LoadScene("MainMenu");
    }

    IEnumerator DisplayShapePanelForTime(float seconds)
    {
        Debug.Log("Display shape panel for " + seconds + " seconds");
        detectShapePanel.SetActive(true);
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Detect shape panel active:", detectShapePanel.activeSelf.ToString(), " ");
        yield return new WaitForSeconds((float)seconds);

        detectShapePanel.SetActive(false);
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Detect shape panel active:", detectShapePanel.activeSelf.ToString(), " ");
    }

    private void signalZoneEntered()
    {
        //Debug.Log("UIMgr: signalZoneEnteredEvent");
        if(UserSettings.Instance.autoShowShapePanel){
            StartCoroutine(DisplayShapePanelForTime(UserSettings.Instance.shapePanelSeconds));   
        }
    }

    void OnEnable()
    {
        Spawn_Images.signalZoneEnteredEvent += signalZoneEntered;
    }

    void OnDisable()
    {
        Spawn_Images.signalZoneEnteredEvent -= signalZoneEntered;
    }

}

