import QtQuick 1.1
import QtDesktop 0.1

KickElement {
    id: invalidControlRect
    height: txtWarningLabel.height + txtWarningLabel.anchors.topMargin
    width: 250

    property string warningText: ""
    // Actual text displaying control
    Label
    {
        id: txtWarningLabel
        anchors.top: parent.top
        anchors.topMargin: 30
        width: parent.width
        font.pointSize: 10
        text: warningText
    }
}
