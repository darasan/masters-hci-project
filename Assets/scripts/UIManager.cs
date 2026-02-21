using UnityEngine;
using UnityEngine.SceneManagement;

public class UIManager : MonoBehaviour
{

    void Awake()
    {
        
    }

    void Start()
    {
   
    }
    void Update()
    {
       
    }

    public void QuitButtonPressed()
    {
        UnityEngine.Debug.Log("Quit");
        SceneManager.LoadScene("Menu");
    }

}

