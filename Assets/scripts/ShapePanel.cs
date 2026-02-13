using UnityEngine;

public class ShapePanel : MonoBehaviour
{
   // [SerializeField] private GameObject spawnscript;
    [SerializeField] private GameObject shapepanel;

    void Awake()
    {
        
    }

    void Start()
    {
       // panel = GameObject.FindGameObjectWithTag("DetectShapePanel");
     /*  if(spawnscript.enterd == true) "or query state from here"
        {
            UnityEngine.Debug.Log("trigger road sign prefab spawn");
        }
        */
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            //Debug.Log("Spacebar pressed!");
            shapepanel.SetActive(!shapepanel.activeSelf);
        }
    }

    public void EnablePanel()
    {
        UnityEngine.Debug.Log("enable panel");
        //panel.SetActive(true);
    }

    public void DisablePanel()
    {
        UnityEngine.Debug.Log("disable panel");
        //panel.SetActive(false);
    }
}

/*
 //Get prompt panel reference
      if(shapePanel==null){
         shapePanel = GameObject.FindGameObjectWithTag("DetectShapePanel");
         shapePanel.SetActive(true); //hide at start
      }



 //Test - show panel when next signal displayed
            if(!shapePanel.activeSelf){
               shapePanel = GameObject.FindGameObjectWithTag("DetectShapePanel"); //find it again
               UnityEngine.Debug.Log("show panel");
               shapePanel.SetActive(true);
               StartCoroutine(Wait(3.0f));
            }


 IEnumerator Wait(float delay)
    {
      yield return new WaitForSeconds(delay);
      UnityEngine.Debug.Log("hide panel");
      shapePanel.SetActive(false);
    }

*/