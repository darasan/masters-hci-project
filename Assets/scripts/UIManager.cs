using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
public class UIManager : MonoBehaviour
{

    //public Text distanceLabel;
    //public float distanceTravelled;

    int val = 150;

    void Awake()
    {
        
    }

    void Start()
    {
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("StartTest", " " , " ");
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Username: ", "Daire", " ");
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Test value: ", val.ToString(), " ");
    }
    void Update()
    {
        //Update distance travelled UI
       // distanceLabel.text = (distanceTravelled + " kms");
       
    }

    public void QuitButtonPressed()
    {
        UnityEngine.Debug.Log("Quit");
        SceneManager.LoadScene("Menu");
    }

}

