import QtQuick 1.1

Rectangle {
    id: baseElement
    z: 5
    width: 120
    height: 140
    property int pixelStep: 10
    border.width: designMode ? 1 : 0
    border.color: "lightgrey"
    color: "transparent"

    scale: (!designMode && scaleOnHover && dragMouseArea.containsMouse) ? 1.2 : 1
    Behavior on scale { NumberAnimation { easing.type: Easing.OutCubic ; duration: 120} }

    // Identifiers
    property string dataObjectId    
    property string instanceId
    property string dataObjectName
    property variant uiFormatProps
    property string staticUiInstanceData
    property bool readOnly: false
    property bool designMode: false
    property bool debugMode: false
    property bool scaleOnHover: false
    property string value
    // this is used to notify about incoming new "value" data, even if it is
    // the same than the previous "value"
    property bool valueUpdateToggle

    property string kickMessageIn

    signal kickMessageOut(string msgStr)
    signal notifyValueChanged(string myDataObjectId, string myValue)
    signal closed(string myDataObjectId, string instanceId)
    signal positionChanged(string myDataObjectId, string instanceId, int newX, int newY)
	
    function logMessage(message)
    {
        if (debugMode)
            console.log(message);
    }

    MouseArea
    {
        id: dragMouseArea
        anchors.fill: parent

        // OH 2012-03-19 extension for KickDriveTile
        hoverEnabled: true

        drag.target: (designMode) ? baseElement : null // Cancels drag when not in design mode
        drag.minimumX: 0
        drag.minimumY: 0
        drag.maximumX: baseElement.parent.width - titleBar.width - (border.width * 2)
        drag.maximumY: baseElement.parent.height - baseElement.height - (border.width * 2)
        drag.onActiveChanged:
        {
            if (!drag.active)
            {
                var currX = parent.x;
                var xInSetUnits = currX / pixelStep
                var xRoundedToSetUnits = Math.round(xInSetUnits);
                var setXTo = xRoundedToSetUnits * pixelStep
                if (setXTo + parent.width > parent.parent.width)
                    setXTo -= pixelStep;
                parent.x = setXTo;

                var currY = parent.y;
                var yInSetUnits = currY / pixelStep
                var yRoundedToSetUnits = Math.round(yInSetUnits);
                var setYTo = yRoundedToSetUnits * pixelStep
                if (setYTo + parent.height > parent.parent.height)
                    setYTo -= pixelStep;
                // Fix added to never lose the draggable title bar
                if (setYTo < 0)
                    setYTo = 0;
                parent.y = setYTo;

                // !Emit signal notifying change
                baseElement.positionChanged(dataObjectId, instanceId, parent.x, parent.y);
            }
        }
    }

    // Title bar - currently used to display Data Object Id and the close button
    Rectangle {
        id: titleBar
        anchors.top: parent.top
        anchors.left: parent.left
        width: parent.width
        Text {
            id: txtTitle
            anchors.top: parent.top
            anchors.left: parent.left
            width: parent.width
            text: dataObjectName + ((designMode) ? "\n(" + dataObjectId + ")" : "")
            wrapMode: Text.Wrap
            font.pointSize: 9
        }
    }

    Image  {
        z: 10
        id: btnClose
        visible: designMode
        anchors.top: parent.top
        anchors.right: parent.right
        source: "KickElementClose.png"

        MouseArea {
            anchors.fill: parent
            onClicked: {
                // Notify closed
                 baseElement.closed(dataObjectId, instanceId)
                baseElement.destroy()
            }
        }
    }
}
