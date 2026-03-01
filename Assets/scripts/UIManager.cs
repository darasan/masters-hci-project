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

    private string currentLane;
    private string targetLane;
    private bool inCorrectLane = true;

    [SerializeField] private GameObject detectShapePanel;


    void Awake()
    {

    }

    void Start()
    {
      
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
            //Debug.Log("Spacebar pressed!");
            detectShapePanel.SetActive(!detectShapePanel.activeSelf);
            LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Detect shape prompt by spacebar: ", detectShapePanel.activeSelf.ToString(), " ");
        }
    }

    public void StartTest()
    {
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex + 1);
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Start Test", " " , " ");
    }

    public void QuitApplication()
    {
        Debug.Log("Quit Application");
        Application.Quit ();
    }

    public void QuitButtonPressed()
    {
        Debug.Log("Quit");
        SceneManager.LoadScene("MainMenu");
    }

    IEnumerator DisplayShapePanelForTime(float seconds)
    {
        Debug.Log("Display shape panel for " + seconds + " seconds");
        detectShapePanel.SetActive(true);
        yield return new WaitForSeconds((float)seconds);
        detectShapePanel.SetActive(false);
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
        Debug.Log("OnEnable, subscribe events");
        Spawn_Images.signalZoneEnteredEvent += signalZoneEntered;
    }

    void OnDisable()
    {
        Debug.Log("OnDisable, unsubscribe events");
        Spawn_Images.signalZoneEnteredEvent -= signalZoneEntered;
    }

}

