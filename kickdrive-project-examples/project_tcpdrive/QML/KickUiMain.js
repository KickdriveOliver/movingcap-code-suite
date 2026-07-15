// Dynamic object creation, used by Main.qml

var component;
var myControl;

function createDynamicUiElement(parentElement, uiInstance, dataObjectId, uiFormatPropsMap, dataObjectName, initialValue, designMode)
{
	var sourceQmlFileName;
    var defaultQmlFile = "KickInvalidControl.qml";

	var uiInstanceParams = uiInstance.split(",");

	// Get QML file from instance data
    if (uiInstanceParams[0].indexOf(".qml") !== -1) {
		sourceQmlFileName = uiInstanceParams[0];
	}
	// if this is not a qml file, it's a type. Determine QML file according to it. 
	else {        
        if (uiInstanceParams[0] === "slider")
                sourceQmlFileName = "KickSlider.qml"
        else if (uiInstanceParams[0] === "text")
                sourceQmlFileName = "KickTextInput.qml"
        else if (uiInstanceParams[0] === "label")
                sourceQmlFileName = "KickLabel.qml"
        else if (uiInstanceParams[0] === "radio")
                sourceQmlFileName = "KickOptions.qml"
        else if (uiInstanceParams[0] === "dial")
                sourceQmlFileName = "KickDial.qml"
        else if (uiInstanceParams[0] === "bitfield")
                sourceQmlFileName = "KickBitField.qml"
        else
            sourceQmlFileName = defaultQmlFile;
	}

	// Get location
	var instanceX = (uiInstanceParams[1] === "") ? 0 : uiInstanceParams[1];
	var instanceY = (uiInstanceParams[2] === "") ? 0 : uiInstanceParams[2];

	// Create actual object
    console.log("Instance type: " + uiInstanceParams[0] + " initializing: " + sourceQmlFileName)
	component = Qt.createComponent(sourceQmlFileName);
	myControl = component.createObject(parentElement);

    if (myControl !== null && sourceQmlFileName === defaultQmlFile) {
        myControl.warningText = "Error: Unknown instance type " + uiInstanceParams[0];
    }

    // If creation failed
    if (myControl === null)
    {
        // If failed even the default control - give up
        if (sourceQmlFileName === defaultQmlFile)
            return;
        // If failed creating a known/identified control - go to default
        else {
            component = Qt.createComponent(defaultQmlFile);
            myControl = component.createObject(parentElement);

            // Again, if failed default, give up
            if (myControl === null)
                return;
            else
                myControl.warningText = "Error creating " + sourceQmlFileName + ".\nPlease check your QML file."
        }
    }

    // Identify
    myControl.dataObjectId = dataObjectId
    myControl.dataObjectName = dataObjectName;

    console.log("Created: " + myControl.dataObjectId + " " + myControl.dataObjectName);

    // Set uiFormat
    myControl.uiFormatProps = uiFormatPropsMap;

    // Set STATIC ui instance data
    myControl.staticUiInstanceData = uiInstanceParams[0];

    // If no write permission, set readOnly
    var updatesPolicy = uiFormatPropsMap["updates"];
    if (updatesPolicy === null || updatesPolicy === undefined)
    {
        console.log("Error - no updates attribute found")
        myControl.readOnly = true;
    }
    else
    {
        myControl.readOnly = (updatesPolicy.indexOf("w") === -1);
    }
    myControl.designMode = designMode;

    // Set location
    myControl.x = instanceX;
    myControl.y = instanceY;

    // Assign initial value to the control
    myControl.value = initialValue;

    // This is how to connect signals from the dynamic controls to the main container
    myControl.notifyValueChanged.connect(parentElement.childValueChanged);
    myControl.kickMessageOut.connect(parentElement.childKickMessageOut);
    myControl.closed.connect(parentElement.childClosed);
    myControl.positionChanged.connect(parentElement.childPositionChanged);
}
