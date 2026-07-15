import QtQuick 1.0
import QtDesktop 0.1

KickElement {

    id: bitFieldRect
    height: colContainer.height + colContainer.anchors.topMargin
    // use a bit more than the standard width to allow for meaningful checkbox texts
    width: 150

    // Used to make sure that no value change signals are emitted while initializing or setting value
    property bool initializing: false
    property bool setValueInProgress: false

    // Initialization of bitfield controls
    property string allOptionsStr        
    property int fieldSize: 0    

    // Single bit option
    Component
    {
        id: mySingleBit

        CheckBox {
            property int bitIndex: -1;

            signal wasClicked()
            onCheckedChanged: wasClicked();
        }
    }

    onUiFormatPropsChanged:
    {               
        var tmp = uiFormatProps["options"];
        if (tmp === undefined)
            tmp = "";
        allOptionsStr = tmp;

        tmp = uiFormatProps["fieldsize"];
        if (tmp === undefined || tmp < 0)
            tmp = "0";
        fieldSize = tmp

        // Create options' list by properties
        initOptions()
    }

    // Locate control's child index under the container, by the assigned bitIndex
    function getBitFieldChildId(bitIdx) {
        var foundIdx = -1;
        for (var i = 0; (foundIdx === -1 && i < colContainer.children.length); i++)
        {
            if (colContainer.children[i].bitIndex === bitIdx)
                foundIdx = i;
        }
        return foundIdx;
    }

    function initOptions()
    {
        initializing = true;

        // Note: if delimiter not found (like in "") returns same string
        var allOptions = allOptionsStr.split("|");

        var numOfRequiredBitFields = fieldSize;
        // If no field size given, work with the number of custom options
        if (fieldSize === 0 && allOptionsStr !== "") {
            numOfRequiredBitFields = allOptions.length;
        }

        // Find out how many bit options we need to iterate through (also to destroy unused ones)
        var numOfBitsToIterate = numOfRequiredBitFields;
        if (numOfBitsToIterate < colContainer.children.length)
            numOfBitsToIterate = colContainer.children.length;

        // Create/Delete option items
        for (var i = 0; i < numOfBitsToIterate; i++)
        {
            if (i < numOfRequiredBitFields) {
                // If child control doesn't exist yet - create it
                if (i >= colContainer.children.length) {                    
                    var currOption = mySingleBit.createObject(colContainer);
                }                                
                colContainer.children[i].wasClicked.connect(bitFieldRect.bitBoxChecked)                

                // IF field size is explicitly defined - use automatic naming and index by order of creation
                // (custom names are processed later
                if (fieldSize != 0) {
                    colContainer.children[i].bitIndex = i;
                    colContainer.children[i].text = dataObjectName + " " + i;
                }
            }
            else {
                // number of options has been reduced - destroy
                colContainer.children[i].destroy();
            }
        }        

        // Process the options attribute for custom definitions
        if (allOptionsStr !== "") {
            for (var q = 0; q < allOptions.length; q++)
            {
                var optionIdx = allOptions[q].split(",")[0];
                var optionText = allOptions[q].split(",")[1];

                // If fieldSize explicitly defined
                if (fieldSize != 0) {

                    // Adjust custom name if field present
                    var bitIdInContainer = getBitFieldChildId(optionIdx);
                    if (bitIdInContainer != -1) {
                        colContainer.children[bitIdInContainer].text = optionText;
                    }
                }
                // If fieldSize undefined - configure bits by options attribute
                else {
                    colContainer.children[q].bitIndex = optionIdx;
                    colContainer.children[q].text = optionText;
                }
            }
        }

        initializing = false;
    }

    onValueChanged: {

        //console.log("onValueChanged entered - changing value to " + value)

        // Iterate through field's bits to fill
        setValueInProgress = true;

        var valueWithoutPrefix = "";
        // any of the object editor value formats are supported
        if (value.indexOf("0b") === 0)
            // drop the "0b" prefix
            valueWithoutPrefix = value.substr(2)
        else if (value.indexOf("0x") === 0)
            // convert from "0x55" to "01010101"
            valueWithoutPrefix = parseInt(value.substr(2), 16).toString(2)
        else if (value.indexOf("h") === value.length - 1)
            // convert from "55h" to "01010101"
            valueWithoutPrefix = parseInt(value.substr(0, value.length - 1), 16).toString(2)
        else
            // convert from (decimal) 85 to "01010101".
            // NOTE: please ensure the object's data type is always unsigned.
            // Negative values will NOT result in the correct result.
            valueWithoutPrefix = parseInt(value).toString(2)


        // Go through all known fields
        for (var i = 0; i < colContainer.children.length; i++)
        {
            var currCharToSet = '0';
            var currBitIndex = colContainer.children[i].bitIndex;

            // If bit index is present in value - get char
            if (valueWithoutPrefix.length - 1 - currBitIndex > -1) {

                currCharToSet = valueWithoutPrefix.charAt(valueWithoutPrefix.length - 1 - currBitIndex);
            }
            colContainer.children[i].checked = (currCharToSet === '1')
        }
        setValueInProgress = false;
    }

    function bitBoxChecked()
    {
        // Ignore signals while initializing or setting value
        if (initializing || setValueInProgress)
            return;

        var currDisplayedBitFieldValue = "0b" + getCurrBitVal();
        // console.log("value changed to: " + currDisplayedBitFieldValue);
        bitFieldRect.notifyValueChanged(dataObjectId, currDisplayedBitFieldValue)
    }

    function getCurrBitVal()
    {
        var myConstructedVal = "";
        for (var i = 0; i < colContainer.children.length; i++) {

            var currFieldBitIndex = colContainer.children[i].bitIndex;

            // If bit index expands value, create '0' values to pad the difference
            if (currFieldBitIndex > myConstructedVal.length)
            {
                var missingBitsCount = (currFieldBitIndex + 1) - myConstructedVal.length;
                for (var q = 1; q <= missingBitsCount; q++)
                {
                    myConstructedVal = "0" + myConstructedVal;
                }
            }

            // Set current bit value
            var currBitVal = (colContainer.children[i].checked) ? "1" : "0";
            var charIdx = myConstructedVal.length - 1 - currFieldBitIndex;
            myConstructedVal = setCharAt(myConstructedVal, charIdx, currBitVal);
        }       
        return myConstructedVal;
    }

    function setCharAt(str,index,chr) {
        if(index > str.length - 1) return str;
        return str.substr(0, index) + chr + str.substr(index + 1);
    }

    ButtonColumn
    {
        id: colContainer
        enabled: !readOnly
        anchors.top: parent.top
        anchors.topMargin: 30
        width: parent.width
        exclusive: false        
    }
}
