using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class UIManager : MonoBehaviour
{

    //public Text distanceLabel;
    //public float distanceTravelled;

    void Awake()
    {
        
    }

    void Start()
    {
   
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

