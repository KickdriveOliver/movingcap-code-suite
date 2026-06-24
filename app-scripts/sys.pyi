"""sys module stub/interface for fullmo MovingCap servo drives / CODE / Micropython

The `sys` module provides system-specific parameters and functions for MovingCap MicroPython.

This module includes:
- Standard MicroPython/CPython sys module functions (subset of v1.9.4)
- MovingCap-specific extensions for real-time control applications
- Compatibility functions for legacy MovingCap CANopen drives with pymite/Python-On-A-Chip

Standard Functions:
    - version - Python version string
    - version_info - Python version tuple (major, minor, patch)
    - implementation - Implementation details (name, version, platform, platver)
    - platform - Platform identifier string
    - byteorder - Native byte order ('little' or 'big')
    - exit([retval]) - Exit the program
    - print_exception(exc, [file]) - Print exception traceback
    - exc_info() - Get current exception info tuple

MovingCap Extensions:
    - cycle_time_ms(period) - Fixed-cycle-time loop helper
    - time() - Compatibility: Get millisecond timer (use time.ticks_ms() in new code)
    - wait(ms) - Compatibility: Delay milliseconds (use time.sleep_ms() in new code)

For complete MicroPython sys module documentation, see:
https://docs.micropython.org/en/v1.9.4/pyboard/library/sys.html

Example Usage:
  import sys
  import time

  def do_control_task():
      dummy = 2000
      for runs in range((time.ticks_ms() % 100) + 10):
          dummy = dummy - 20
          dummy2 = dummy + 10

  # Check Python version
  print("sys.version (python) = %s" % sys.version)
  # Check implementation details
  print("sys.implementation = %s" % repr(sys.implementation))

  # Fixed-cycle-time control loop
  sys.cycle_time_ms(0)  # Reset cycle timer
  for cycle in range(20):
      # Perform control operations
      do_control_task()
      remaining = sys.cycle_time_ms(10)  # Ensure 10ms cycle time
      print ("10 msec cycle, round = %d, remaining time = %d" % (cycle, remaining)) 

  # Exception handling
  try:
      risky_operation()
  except Exception as e:
      sys.print_exception(e)
      sys.exit(1)
"""
__author__ =  "Oliver Heggelbacher"
__email__ = "oliver.heggelbacher@fullmo.de"
__version__ = "50.00.10.xx"
__date__ = "2026-01-19"

# Module attributes
version: str
"""Python language version string (e.g., "3.4.0")."""

version_info: tuple
"""Python language version as tuple (major, minor, patch)."""

class _Implementation:
    """Implementation information object."""
    name: str
    """Implementation name ("micropython")."""
    version: tuple
    """MicroPython version tuple (major, minor, micro)."""
    platform: str
    """Platform name ("movingcap")."""
    platver: tuple
    """MovingCap version tuple (dev_type, major, minor, revision)."""

implementation: _Implementation
"""Implementation details including MicroPython and MovingCap versions."""

platform: str
"""Platform identifier string."""

byteorder: str
"""Native byte order: 'little' or 'big'."""

stdin: object
"""Standard input stream."""

stdout: object
"""Standard output stream."""

stderr: object
"""Standard error stream."""

def exit(retval: int = 0):
    """Exit the program by raising SystemExit exception.
    
    :param retval: Exit code (0 for success, non-zero for error). Default is 0.
    :type retval: int
    :raises SystemExit: Always raised to terminate the program.
    
    Example:
        if error_condition:
            sys.exit(1)  # Exit with error code 1
    """
    pass

def print_exception(exc, file=None):
    """Print exception traceback to a file or stdout.
    
    Prints the exception type, message, and traceback in a readable format.
    If no file is specified, prints to stdout.
    
    :param exc: Exception object to print.
    :type exc: Exception
    :param file: Optional file stream to write to. If None, uses stdout.
    :type file: file-like object or None
    
    Example:
        try:
            risky_operation()
        except Exception as e:
            sys.print_exception(e)
            # or write to file:
            # with open('error.log', 'w') as f:
            #     sys.print_exception(e, f)
    """
    pass

def exc_info() -> tuple:
    """Get information about the current exception.
    
    Returns a tuple containing (type, value, traceback) of the current exception.
    If no exception is being handled, returns (None, None, None).
    
    :return: Tuple of (exception_type, exception_value, traceback).
    :rtype: tuple
    
    Example:
        try:
            1 / 0
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(exc_type)  # <class 'ZeroDivisionError'>
    """
    pass


def cycle_time_ms(period: int) -> int:
    """Fixed-cycle-time loop helper for real-time control applications.
    
    This function ensures that a control loop runs with a precise, fixed cycle time,
    compensating for varying execution times of the loop body. It maintains timing
    by delaying as needed to reach the target period.
    
    Usage pattern:
    1. Call with negative value (e.g., -1) to reset/initialize the cycle timer
    2. Call with desired period (ms) at the end of each loop iteration
    
    The function calculates remaining time until the next cycle should start and delays
    accordingly. If the loop body takes longer than the period, the function returns
    immediately (no delay) and the return value will be negative or zero.
    
    :param period: Target cycle time in milliseconds. Use negative value to reset timer.
    :type period: int
    :return: Remaining time in milliseconds before cycle completes. Negative if overrun.
    :rtype: int
    
    Example:
        import sys
        
        # Initialize cycle timer
        sys.cycle_time_ms(-1)
        
        while True:
            # Perform control tasks (variable execution time)
            read_sensors()
            calculate_control()
            update_outputs()
            
            # Ensure fixed 10ms cycle time
            remaining = sys.cycle_time_ms(10)
            if remaining < 0:
                print("Warning: Cycle overrun by", -remaining, "ms")
    
    Note:
        For high-precision real-time control loops where consistent timing is critical.
        The actual cycle time may have small variations due to system scheduling.
    """
    pass

def time() -> int:
    """Get current system time in milliseconds.
    
    Returns the millisecond counter value. This is a compatibility function for
    legacy MovingCap CANopen drives with pymite/Python-On-A-Chip.
    
    **Deprecated:** Use `time.ticks_ms()` from the `time` module for new applications.
    
    :return: Current time in milliseconds since system start as a micropython small int (signed 30-bit integer in the current implementation).
    :rtype: int
    
    Example:
        start = sys.time()
        # ... do something ...
        elapsed = sys.time() - start
        print(f"Operation took {elapsed} ms")
    
    See also:
        time.ticks_ms() - Preferred function for new code
    """
    pass

def wait(ms: int):
    """Wait for specified milliseconds.
    
    Delays execution for the given number of milliseconds. This is a compatibility
    function for legacy MovingCap CANopen drives with pymite/Python-On-A-Chip.
    
    **Deprecated:** Use `time.sleep_ms()` from the `time` module for new applications.
    
    :param ms: Number of milliseconds to wait.
    :type ms: int
    
    Example:
        sys.wait(100)  # Wait 100 milliseconds
    
    See also:
        time.sleep_ms() - Preferred function for new code
    """
    pass
