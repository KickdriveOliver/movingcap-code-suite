import QtQuick 1.1
import QtDesktop 0.1

KickElement {
    id: dialRect

    // Range properties
    // TODO: implement for non decimal steps
    property real step
    property real valueBottom
    property real valueTop
    property real numOfSteps
    property int calculatedDialPosition
    property bool dialUpdateAllowed: !myDial.inDrag

    onUiFormatPropsChanged:
    {
        valueBottom = uiFormatProps["range"].split(",")[0];
        valueTop = uiFormatProps["range"].split(",")[1];
        var tmp = uiFormatProps["step"];
        if (tmp === undefined)
            tmp = 1;
        step = tmp;
        numOfSteps = (valueTop - valueBottom) / step;
    }

    onValueChanged: {
        calculatedDialPosition = Math.round(numOfSteps - ((value - valueBottom) / step))
        if (dialUpdateAllowed && calculatedDialPosition != Math.round(myDial.value))
        {
           myDial.value = calculatedDialPosition;
        }
        txtCurrVal.text = value;
    }

    // Decide whether to emit changed signal
    function valueChangeNotification()
    {
        //! If value changed because of outside change, no need to notify
        if (Math.round(myDial.value) != calculatedDialPosition)
        {
            calculatedDialPosition = Math.round(myDial.value)
            var valueFromDial = Math.round((numOfSteps - calculatedDialPosition) * step + valueBottom)
            // make sure this is in range
            if (valueFromDial < valueBottom) valueFromDial = valueBottom
            if (valueFromDial > valueTop) valueFromDial = valueTop
            txtCurrVal.text = valueFromDial
            logMessage("value change from inside (dial moved): to " + valueFromDial)
            dialRect.notifyValueChanged(dataObjectId, valueFromDial)
        }
    }

    // Dial container
    Rectangle
    {
        id: dialFrame
        enabled: !readOnly
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 10
        width: parent.width
        height: parent.height
        color: "transparent"

        Dial
        {
            id: myDial
            height: parent.width
            width: parent.width
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            minimumValue: 0
            maximumValue: numOfSteps
            onValueChanged: valueChangeNotification()
            scale: containsMouse || inDrag ? 1.1 : 1
            Behavior on scale { NumberAnimation { easing.type: Easing.OutCubic ; duration: 120} }
        }
        Text
        {
            id: txtMaxVal
            text: valueTop
            anchors.bottom: myDial.bottom
            anchors.right: parent.right
        }
        Text
        {
            id: txtMinVal
            text: valueBottom
            anchors.bottom: myDial.bottom
            anchors.left: parent.left
        }
        Text
        {
            z: 1
            id: txtCurrVal
            font.pointSize: 10
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
        }      
    }
}
