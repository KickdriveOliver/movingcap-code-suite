import QtQuick 1.1
import QtDesktop 0.1

KickElement {
    id: optionsRect
    height: colContainer.height + colContainer.anchors.topMargin
    // use a bit more than the standard width to allow for meaningful checkbox texts
    width: 150

    // Used to make sure that no value change signals are emitted while initializing
    property bool initializing: false;
    // Initialization of radio button controls
    property string allOptionsStr

    // Encapsulation of a single RadioButton
    Component
    {
        id: mySingleOption
        RadioButton {
            property string optionValue
        }
    }

    onUiFormatPropsChanged:
    {
        allOptionsStr = uiFormatProps["options"];
    }

    onAllOptionsStrChanged: initOptions()

    onValueChanged: {
        // Select the correct radio button by value
        for (var i = 0; i < colContainer.children.length; i++)
        {
            if (colContainer.children[i].optionValue === value) {
                colContainer.children[i].checked = true;
            }
        }
        initializing = false;
    }

    function initOptions()
    {
        initializing = true;
        var allOptions = allOptionsStr.split("|");
        var childUBound = colContainer.children.length;
        if (childUBound < allOptions.length) childUBound = allOptions.length;
        for (var i = 0; i < childUBound; i++)
        {
            if (i < allOptions.length) {
                var valueTextPair = allOptions[i].split(",");
                if (i >= colContainer.children.length) {
                    // need additional radio button
                    var currOption = mySingleOption.createObject(colContainer);
                }
                colContainer.children[i].text = valueTextPair[1];
                colContainer.children[i].optionValue = valueTextPair[0];
            }
            else {
                // number of options has been reduced.
                colContainer.children[i].destroy();
            }
        }
        initializing = false;
    }

    // Function called as slot to the "selected" signal coming from each single option when selected
    function optionSelected()
    {
        //! If value changed because of outside change, no need to notify
        if (!initializing)
        {
            var selectedValue = colContainer.checkedButton.optionValue;
            if (selectedValue !== value)
            {
                optionsRect.notifyValueChanged(dataObjectId, selectedValue)
            }
        }
    }

    ButtonColumn
    {
        id: colContainer
        enabled: !readOnly
        anchors.top: parent.top
        anchors.topMargin: 30
        width: parent.width
        onCheckedButtonChanged: optionSelected();
    }
}
