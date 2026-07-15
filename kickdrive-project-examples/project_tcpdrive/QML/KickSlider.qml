import QtQuick 1.1
import QtDesktop 0.1

KickElement {
    id: dialRect
    height: width * 1.5

    // a slider is just a dial on a linear curve. Reuse code from CustomDial.qml

    // Range properties
    // TODO: implement for non decimal steps
    property real step
    property real valueBottom
    property real valueTop
    property int numOfSteps
    property int calculatedDialPosition

    onUiFormatPropsChanged:
    {
        valueBottom = uiFormatProps["range"].split(",")[0];
        valueTop = uiFormatProps["range"].split(",")[1];
        var tmp = uiFormatProps["step"];
        if (tmp === undefined)
            tmp = 1;
        step = tmp;
        numOfSteps = Math.round((valueTop - valueBottom) / step);
    }

    onValueChanged: {
        calculatedDialPosition = Math.round((value - valueBottom) / step);
        if (calculatedDialPosition != myDial.value)
        {
            myDial.value = calculatedDialPosition;
        }
        txtCurrVal.text = value;
    }

    // Decide whether to emit changed signal
    function valueChangeNotification()
    {
        //! If value changed because of outside change, no need to notify
        if (myDial.value != calculatedDialPosition)
        {
            calculatedDialPosition = myDial.value;
            var valueFromDial = Math.round(myDial.value * step + valueBottom);
            // make sure this is in range
            if (valueFromDial < valueBottom) valueFromDial = valueBottom;
            if (valueFromDial > valueTop) valueFromDial = valueTop;
            txtCurrVal.text = valueFromDial;
            dialRect.notifyValueChanged(dataObjectId, valueFromDial);
        }
    }

    // slider container
    Rectangle
    {
        enabled: !readOnly
        anchors.centerIn: parent
        anchors.verticalCenterOffset: height * 0.05
        width: parent.width * 0.6
        height: parent.height * 0.95
        color: "transparent"

        Text {
            id: txtTopValue
            text: valueTop
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.right: parent.right
        }
        Text {
            id: txtBottomValue
            text: valueBottom
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            anchors.right: parent.right
        }
        Text {
            id: txtCurrVal
            anchors.right: parent.right
            anchors.verticalCenter: myDial.verticalCenter
            font.pointSize: 10
        }
        Slider {
            id: myDial
            enabled: !readOnly
            tickmarksEnabled: true
            minimumValue: 0
            maximumValue: numOfSteps
            stepSize: 1
            orientation: Qt.Vertical
            onValueChanged: valueChangeNotification()
            anchors.right: txtTopValue.left
            anchors.rightMargin: 10
            anchors.top: parent.top
            anchors.topMargin: parent.height * 0.05
            anchors.bottom: parent.bottom
            anchors.bottomMargin: parent.height * 0.05
            scale: (containsMouse && enabled) ? 1.15 : 1
            Behavior on scale { NumberAnimation { easing.type: Easing.OutCubic ; duration: 120} }
        }
    }
}
