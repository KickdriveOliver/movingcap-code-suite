import QtQuick 1.0

KickElement {

    id: buttonRect

    width: 300

    property string messageToEmit
    property alias text: buttonTxt.text

    // Actual button area
    Rectangle
    {
        id: btnArea
        color: 'lightGrey'
        anchors.top: parent.top
        anchors.topMargin: designMode ? 30 : 0
        width: parent.width
        height: 40

        Text
        {
            id: buttonTxt
            anchors.centerIn: parent
        }
        MouseArea
        {
            id: activeArea
            anchors.fill: parent
            onEntered: btnArea.color = 'darkGrey'
            onExited: btnArea.color = 'lightGrey'
            hoverEnabled: true
            onClicked:
            {
                //buttonRect.designMode = true
                buttonRect.kickMessageOut(messageToEmit)
            }
        }
    }
}
