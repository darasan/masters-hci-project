using UnityEngine;

public class UserSettings : MonoBehaviour
{
    public static UserSettings Instance { get; private set; }

    //User settings
    public string userID = "Daire";
    public bool autoShowShapePanel = true;
    public int shapePanelSeconds = 5;

    private void Awake()
    {
        // If an instance already exists and it's not this one, destroy this one
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;

        //Persist between scene loads
        DontDestroyOnLoad(gameObject);
    }

    void Start()
    {

    }

    void Update()
    {

    }

    public void SetUserID(string ID)
    {
        userID = ID;
        Debug.Log("SetUserID: " + userID);
    }

    public void SetShapePanelAutoShow(bool show)
    {
        autoShowShapePanel = show;
        Debug.Log("SetShapePanelAutoShow: " + autoShowShapePanel);
    }

    public void SetShapePanelSeconds(string seconds)
    {
        if(int.TryParse(seconds, out int secs)){
            shapePanelSeconds = secs; //Needed to add intermediary variable, or class instance not updated (eg when access from UI manager)
            Debug.Log("SetShapePanelSeconds: " + shapePanelSeconds);
        }
        else{
            Debug.Log("Invalid number");
        }
    }
}
