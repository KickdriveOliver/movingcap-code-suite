"""drive library stub/interface for fullmo MovingCap servo drives

The drive library allows access to the MovingCap DS402/CiA402 object dictionary for
micropython scripts that can be loaded and executed on MovingCap Ethernet drives 
(MC349 ETH or MCN23 ETH).

* WriteObject and ReadObject provide general access to all available objects of the 
MovingCap's drive dictionary. If you are familar with DS402/CiA402 standard objects 
and the manufacturer-specific objects as documented in the MovingCap user manual, this
is all you need for writing a full drive master application. 

* Additional functions are provided as a shortcut and faster way to write your applications.
They essentially perform several write/read operations on the DS402/CiA402 objects for
the desired funtionality. Please refer to our examples to see how to get your drive
moving with a few lines of code only.
"""
__author__ =  "Oliver Heggelbacher"
__email__ = "oliver.heggelbacher@fullmo.de"
__version__ = "50.00.02.016"
__date__ = "2022-07-07"

def WriteObject(index : int, subindex : int, value : int) -> int:
    """Write CANopen object value (numeric only)

    :param index: CANopen index [unsigned16], e.g. 0x607A for "target position"
    :type index: int
    :param subindex: CANopen subindex [unsigned8], e.g. 0
    :type subindex: int
    :param value: new value for this object [integer32]
    :type value: int
    :return: 0 if successful, or the the internal error code from the CANopen stack.
        You can usually ignore this value. Check only when you are not sure 
        if the index/subindex is a valid object for write access at all. 
    :rtype: int
    """
    ret =  0
    return ret

def ReadObject(index : int, subindex : int) -> int:
    """Read CANopen object value (numeric only)

    :param index: CANopen index [unsigned16], e.g. 0x6064 for "position actual value"
    :type index: int
    :param subindex: CANopen subindex [unsigned8], e.g. 0
    :type subindex: int
    :return: current object value [integer32]. If the object is not a valid object for read access,
        an internal CANopen stack error value is returned. Note the return value is always integer32,
        even if the object dictionary entry has a different CANopen data type. 
    :rtype: int
    """
    value = 0
    return value

def WriteControl(control : int):
    """Write DS402 control word (CANoypen object 6040h.0h)

    :param control: new value [unsigned8]
    :type control: int
    """
    pass


def EnableDrive():
    """Prepare for operation. 
    
    This function switches through the required states of the DS402 state machine,
    until "operation enabled" is reached. 
    
    This is equivalent to checking the drive statusword
    via `ReadStatusword` and commanding the required state changes using 
    `WriteControl`. The sequence is:

    * If drive in error state: WriteControl(0x80) fault reset -> new state "switch on disabled"
    * WriteControl(0x6) shutdown -> new state "ready to switch on"
    * WriteControl(0x7) switch on -> new state "switched on"
    * WriteControl(0xf) enable operation -> new state "operation enabled"
    
    Only the required transitions are performed. If the drive is already in "operation enabled"
    state (ReadStatusword is 0x27), the function returns immediately.

    See also `PowerQuit`
    """
    pass

def StopMotion():
    """Command a quickstop ("slow down on quick stop option ramp"). 
    Uses object 6085h.0h quickstop deceleration value. 
    """
    pass

def PowerQuit():
    """Resets operation mode to zero (see `SetOpMode`), 
    then switches the DS402 state machine to "switch on disabled". 

    See also `EnableDrive`
    """
    pass

def GoPosAbs(targetPos : int):
    """Start new movement to an absolute position.

    * If required, switch to operation mode 1 - profile positioning mode (SetOpMode(1))
    * Set the new target (see `SetTargetPos`)
    * Start positioning using DS402 "single setpoint" mode: the new target position is processed immediately.

    The positioning control uses "6083h.0h profile acceleration" (`SetAcc`) and 
    "6084h.0h profile deceleration" (`SetDec`) for the movement. 

    Use `ChkReady` and `ChkError` to wait for end of the positioning and detect errors during the run. 

    See also 'GoPosRel'

    :param targetPos: new absolute target position [integer32]
    :type targetPos: int
    """
    pass

def GoPosRel(relativePos : int):
    """Start new movement to relative position.

    Same as `GoPosAbs`, but specify a relative position. 

    By default "relative" means "relative to the preceeding target position used", 
    but the object "60F2h.0h positioning option code" can specify a different 
    meaning, e.g. "relative to the current actual position".

    :param relativePos: new relative target position [integer32]
    :type relativePos: int
    """
    pass

def GoVel(targetVelocity : int):
    """Start new constant velocity operation.

    * If required, switch to operation mode 3 - profile velocity mode (SetOpMode(3))
    * Set new target velocity and 
    
    Velocity changes are applied using object  "6083h.0h profile acceleration" (see `SetAcc`). 
    If the direction is changed (e.g. from positive to negative velocity), the object 
    "6085h.0h quickstop deceleration" is used until the velocity is zero, 
    then 6083h.0h is applied to accelerate in the opposite direction. 
    
    The deceleration parameter has no influence. 

    :param targetVelocity: new target velocity [integer32]
    :type targetVelocity: int
    """
    pass

def SetTargetPos(targetPos : int):
    """Shortcut to write object "607Ah.0h target position"

    :param targetPos: new target position [integer32]
    :type targetPos: int
    """
    pass

def SetPosVel(profileVelocity : int):
    """Shortcut to write object "6081h.0h profile velocity"

    :param profileVelocity: new profile velocity [unsigned32]
    :type profileVelocity: int
    """
    pass

def SetAcc(profileAcceleration : int):
    """Shortcut to write object "6083h.0h profile acceleration"

    :param profileAcceleration: new profile acceleration [unsigned32]
    :type profileAcceleration: int
    """
    pass

def SetDec(profileDeceleration : int):
    """Shortcut to write object "6084h.0h profile deceleration"

    :param profileDeceleration: new profile deceleration [unsigned32]
    :type profileDeceleration: int
    """
    pass

def GoHome(method : int, velocity : int, acceleration : int, offset : int):
    """Start DS402 referencing/homing run

    * Switch to operation mode 6 - profile velocity mode (SetOpMode(3))
    * Set objects 6098h.0h homing method, 6099h.1h homing speed, 609Ah.0h homing acceleration and 607Ch.0h homing offset
    * Start movement 
    
    Comming `method` values for MovingCap are: 
    * 35 = don't move. Set current actual position as new zero position. 
    * -18 = block reference run in positive direction
    * -19 = block reference run in negative direction
    
    Use `ChkReady` and `ChkError` to wait for end of the homing run and detect errors during the run. 

    :param method: DS402 homing method [unsigned8]
    :type method: int
    :param velocity: Homing velocity [unsigned32]
    :type velocity: int
    :param acceleration: Homing acceleration [unsigned32]
    :type acceleration: int
    :param offset: Homing offet position [integer32]. After successful homing operation, make this position 
        value the new actual position. 
    :type offset: int
    """
    pass

def SetOpMode(opMode: int):
    """Shortcut to write object "6060h.0h modes of operation"

    :param opMode: new operation mode [unsigned8]: 0 - no mode. 1 - profile position mode. 3 - profile velocity mode. 6 - homing mode.
    :type opMode: int
    """
    pass

def GetOpMode() -> int:
    """Shortcut to read object "6060h.0h modes of operation"

    :return: operation mode [unsigned8], see `SetOpMode`
    :rtype: int
    """
    opMode = 0
    return opMode

def SetTorque(torque : int):
    """Shortcut to write object "6073h.0h max current"

    :param torque: new max. current value [unsigned16], which is directly in relation to the maximum torque during operation. 
        Value unit is 0.1%, i.e. torque = 100 means "10% torque" and torque = 1000 means "100% torque" (default).
    :type torque: int
    """
    pass

def ChkIn(inNo : int) -> int:
    """Check digital input

    :param inNo: Input no. from 1..8 (depending on MovingCap model)
    :type inNo: int
    :return: 0 if low. 1 if high (active)
    :rtype: int
    """
    pass

def SetOut(outNo : int):
    """Set/Activate digital output

    :param outNo: Output no. from 1..4 (depending on MovingCap model)
    :type outNo: int
    """
    pass

def ClearOut(outNo : int):
    """Reset/deactivate digital output

    :param outNo: Output no. from 1..4 (depending on MovingCap model)
    :type outNo: int
    """
    pass

def GetActualPos() -> int:
    """Shortcut to read object "6064h.0h position actual value"

    :return: actual position [integer32]
    :rtype: int
    """
    actualPos = 0
    return actualPos

def ReadStatusword() -> int:
    """Shortcut to read object "6041h.0h statusword"

    :return: DS402 statusword value [unsigned16]
    :rtype: int
    """
    statusWord = 0
    return statusWord


def ChkReady() -> int:
    """Check if drive has finished the current movement (statusword "target reached" bit is set), 
    or an error occured ("error" bit is set).

    Use this after a new `GoPosAbs`, `GoPosRel` or `GoHome` call. 

    :return: 1 if ready. 0 if not ready (yet).
    :rtype: int
    """
    isReady = 0
    return isReady

def ChkError() -> int:
    """Check if the Statusword "error" bit is set.

    :return: 1 if error. 0 if no error.
    :rtype: int
    """   
    isError = 0
    return isError

def ChkMfrStatus(bitIndex : int) -> int:
    """Check a specific bit from object 1002h.0h manufacturer status register.

    MovingCap Ethernet error bits available:
    0 Error over volt (Uzk)
    1 Error under volt (Uzk)
    2 Error Ack
    3 Error over temp
    4 Error I2T / Derating
    5 Abort connection
    6 Error stroke
    7 Error communication
    8 Error Sensor
    9 Error Hardware Enable
    11 Error Over Current
    12 Error External Force / Torque

    :param bitIndex: the bit number from 0..15
    :type bitIndex: int
    :return: 1 if error. 0 if no error.
    :rtype: int
    """
    isError = 0
    return isError
