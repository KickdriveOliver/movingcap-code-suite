import QtQuick 1.1
import QtDesktop 0.1

KickElement {
    id: labelRect
    height: txtLabel.height + txtLabel.anchors.topMargin
    // Actual text displaying control
    Label
    {
        id: txtLabel
        anchors.top: parent.top
        anchors.topMargin: 30
        width: parent.width
        font.pointSize: 10
        text: value
    }
}
