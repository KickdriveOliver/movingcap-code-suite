"""refgo module stub/interface for fullmo MovingCap servo drives / CODE / Micropython

The refgo Python module/library provides access to the ASCII protocol interpreter on TCP port 10001.

REFGO is MovingCap's ASCII command protocol for drive control and status monitoring. It provides
a simple, text-based interface for common drive operations without requiring knowledge of the
CiA402 object dictionary.

This module supports two areas of applications: 

1. Direct RefGo command execution via `cmd()`
   - Send REFGO commands and receive responses directly
   - Automatic parsing and return value conversion
   
2. Access to the MovingCap TCP port 10001 server data, using `open()`, `read()`, `write()`, `close()`:
   - reading/tapping into REFGO data that is sent to the MovingCap server port 10001
   - writing own answers to the client request. 
   - Allows custom protocol implementations, e.g. for protocol compatibility layers to master applications using the
     JennyScience XENAX® ASCII protocol. 

Note: The 'TS' and 'TP' commands return integer values directly for improved performance,
while other commands return string responses.
"""
__author__ =  "Oliver Heggelbacher"
__email__ = "oliver.heggelbacher@fullmo.de"
__version__ = "50.00.10.xx"
__date__ = "2025-11-04"

def cmd(command: str):
    """Execute RefGo command and return answer.

    This is how you can access the full REFGO command set from your MovingCap CODE Python script.
    
    Special optimization: The 'TS' (tell status), 'TPSR' (tell process status register) and 'TP' (tell position)
    commands return integer values instead of strings for better performance and 
    avoiding unnecessary conversion on the script side. 

    :param command: The RefGo command string, without CR/LF line ending. 
        Example: 'TS', 'TP', 'G5000'
    :type command: str
    :return: RefGo answer string, or int for TS/TP commands. 
        Returns None if no response or error.
    :rtype: str or int or None

    Examples:
        refgo.cmd("TS")  # Get current position (returns int)
        refgo.cmd("G5000")  # Go to position 5000
    """
    pass

def open(redirect_mode: int) -> int:
    """Open the RefGo communication channel.
    
    Opens access to the RefGo protocol TCP port (10001) to augment or replace
    the built-in REFGO command interpreter.

    :param redirect_mode: The redirect mode:
        1 - Forward all incoming REFGO data to this Python script.
        2 - Forward only data that has not been processed by the built-in REFGO 
            command interpreter
        3 - Disable the built-in REFGO command interpreter and forward everything 
            to this Python script.
    :return: 0 if successful, non-zero on error.
    :rtype: int
    """
    returnCode = 0
    return returnCode

def read() -> str:
    """Read incoming command
    
    Reads the next text command which has been received on the 10001 REFGO TCP server port.

    :return: The command as string, without the CR terminator. None if no command available.
    :rtype: str or None
    """
    pass

def write(msg: str) -> int:
    """Write data to the specified RefGo channel.
    
    Sends your REFGO command answer to the connected client. 

    :param msg: The answer to send.
    :type msg: str   
    :return: 0 if successful, non-zero on error.
    :rtype: int
    
    Example:
        refgo.write('OK')  # Send 'OK' response
        refgo.write('100')  # Send numeric response
    """
    returnCode = 0
    return returnCode

def close(index: int):
    """Close a RefGo communication channel.
    
    Closes the channel opened with open() and releases associated resources.

    :param index: The channel index as specified when calling open().
    :type index: int
    
    Example:
        refgo.close(0)  # Close channel 0
    """
    pass