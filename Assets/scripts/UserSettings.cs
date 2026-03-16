using UnityEngine;

public class UserSettings : MonoBehaviour
{
    public static UserSettings Instance { get; private set; }

    //User settings
    public string userID = "Default";
    public string userNotes = " ";
    public bool autoShowShapePanel = false;
    public int shapePanelSeconds = 5;

    public enum ShapeType{
      Flat = 0,
      Square01mm,
      Square02mm,
      Square03mm,
      Square04mm,
      Square05mm,
      Square06mm,
      Square07mm
   }

    public ShapeType currentShape =  ShapeType.Flat;
    public int numShapes = System.Enum.GetValues(typeof(ShapeType)).Length;

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
        autoShowShapePanel = false;
    }

    void Update()
    {

    }

    public void SetUserID(string ID)
    {
        userID = ID;
        Debug.Log("SetUserID: " + userID);
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("Username:", userID, " ");
    }

    public void SetUserNotes(string notes)
    {
        LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("User notes:", notes, " ");
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
            LoggingSystem.Instance.writeAOTMessageWithTimestampToLog("SetShapePanelSeconds:", shapePanelSeconds.ToString(), " ");
        }
        else{
            Debug.Log("Invalid number");
        }
    }
}
