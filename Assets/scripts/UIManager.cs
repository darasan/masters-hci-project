using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;


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
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("StartTest", " " , " ");
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Username: ", "Daire", " ");
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
        if (Input.GetKeyDown(KeyCode.Space))
        {
            Debug.Log("Spacebar pressed!");
            detectShapePanel.SetActive(!detectShapePanel.activeSelf);
            LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Detect shape prompt: ", detectShapePanel.activeSelf.ToString(), " ");
        }
    }

    public void QuitButtonPressed()
    {
        UnityEngine.Debug.Log("Quit");
        SceneManager.LoadScene("Menu");
    }

}

