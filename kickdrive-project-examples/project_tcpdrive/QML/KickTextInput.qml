import QtQuick 1.1
import QtDesktop 0.1

KickElement {
    id: labelInput
    height: txtInput.height + txtInput.anchors.topMargin

    // Actual text displaying control
    onValueChanged: {        
        txtInput.text = value
    }

    // Decide whether to emit changed signal
    function valueChangeNotification()
    {
        var myTextValue = txtInput.text
        //! If value changed because of outside change, no need to notify
        if (myTextValue !== value)
        {            
            labelInput.notifyValueChanged(dataObjectId, myTextValue)
        }
    }

    // Actual text input control
    TextField
    {
        id: txtInput
        anchors.top: parent.top
        anchors.topMargin: 30
        width: parent.width
        readOnly: labelInput.readOnly
        onTextChanged: valueChangeNotification()
        font.pointSize: 10
    }
}
