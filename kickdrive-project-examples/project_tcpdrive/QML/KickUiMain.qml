// KickUiMain.qml - main qml file for UI Panel scene

import QtQuick 1.1
import QtDesktop 0.1
import "KickUiMain.js" as DynamicObjCreation

Rectangle {
    z: -20
    id: mainContainer
    width: 600
    height: 400
    property bool disallowDesignMode: false
    property bool designMode: false

    onDesignModeChanged: {
        // Set all child controls' design mode property
        for (var i = 0; i < mainContainer.children.length; i++)
        {
            if (mainContainer.children[i].dataObjectId !== undefined && mainContainer.children[i].dataObjectId !== "")
            {
                mainContainer.children[i].designMode = mainContainer.designMode;
            }
        }
    }

    signal valueChanged(string dataObjectId, string newValue)
    signal instanceClosed(string dataObjectId, string instanceId)
    signal messageStrOut(string msgStrOut)
    signal instancePositionChanged(string dataObjectId, string instanceId, int newX, int newY)

    function childValueChanged(dataObjectId, newValue)
    {
       mainContainer.valueChanged(dataObjectId, newValue);
    }

    function childClosed(dataObjectId, instanceId)
    {
       mainContainer.instanceClosed(dataObjectId, instanceId);
    }

    // Notify C++ that an instance changed position because of inner drag-drop
    function childPositionChanged(dataObjectId, instanceId, newX, newY)
    {
       mainContainer.instancePositionChanged(dataObjectId, instanceId, newX, newY);
    }

    // Emit a KickMessage from QML to C++
    function childKickMessageOut(msgStrOut)
    {
        // console.log("QML msgOut:" + msgStrOut)
        mainContainer.messageStrOut(msgStrOut);
    }

    // This function is called from C++ to update the model with the UI data
    function collectChildControlData()
    {
        var collectedData = "";
        for (var i = 0; i < mainContainer.children.length; i++)
        {
            // Only for the registered data objects
            if (mainContainer.children[i].dataObjectId !== undefined && mainContainer.children[i].dataObjectId !== "")
            {
                // Append data
                collectedData += mainContainer.children[i].dataObjectId + "," + mainContainer.children[i].staticUiInstanceData + "," + mainContainer.children[i].x + "," + mainContainer.children[i].y + ";";
            }
        }
        return collectedData;
    }

    function updateDataObjectValue(dataObjectId, newValue)
    {
        for (var i = 0; i < mainContainer.children.length; i++)
        {
            // Only for the controls of this data object
            if (mainContainer.children[i].dataObjectId !== undefined && mainContainer.children[i].dataObjectId === dataObjectId)
            {
                mainContainer.children[i].value = newValue
                // notify, even if newValue is same as old.
                mainContainer.children[i].valueUpdateToggle = !mainContainer.children[i].valueUpdateToggle
            }
        }
    }
	
    // Distributes a message to all children of control
    function broadcastMessageStrIn(msgStrIn)
    {
        // console.log("QML msgIn:" + msgStrIn)
        for (var i = 0; i < mainContainer.children.length; i++)
        {
            if (mainContainer.children[i].dataObjectId !== undefined && mainContainer.children[i].dataObjectId !== "")
            {
                mainContainer.children[i].kickMessageIn = msgStrIn;
            }
        }
    }

    // Signals emitted from C++ are caught here
    Connections {
            target: KickUi
            // Creation of a new control
            onDynamicUiCreateRequested: {
                DynamicObjCreation.createDynamicUiElement(mainContainer, uiInstance, createdDataObjectId, uiFormatPropsMap, dataObjectName, initialValue, designMode);                
            }
            // Value change that needs to be reflected in the UI controls
            onModelValueChanged: {
                // console.log("QML onModelValueChanged:" + dataObjectId + " value: " + newValue)
                updateDataObjectValue(dataObjectId, newValue);
            }            
            onDesignModeToggled: {
                designMode = designModeChecked;
            }
            onMessageStrIn: {
                broadcastMessageStrIn(msgStrIn);
            }
    }

    Image  {
        id: background
        source: "background.png"
        anchors.fill: parent
    }
    Image  {
        id: backgroundLogo
        source: "backgroundLogo.png"
        anchors.centerIn: parent
    }
}
