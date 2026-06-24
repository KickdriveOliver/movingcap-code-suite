"""time/utime module stub/interface for fullmo MovingCap servo drives / CODE / Micropython

The `utime` module (alternatively: `time`) provides a subset of the MicroPython or CPython `time` module.

This is a limited implementation for the MovingCap platform that provides timing and delay functions.
Full date/time functionality (localtime, mktime, time) is not supported on MovingCap.

For complete documentation on the standard MicroPython time module, see:
https://docs.micropython.org/en/latest/library/time.html

Available Functions:
    - sleep(seconds) - Sleep for the specified number of seconds
    - sleep_ms(ms) - Sleep for the specified number of milliseconds
    - sleep_us(us) - Sleep for the specified number of microseconds
    - ticks_ms() - Get millisecond counter value
    - ticks_us() - Get microsecond counter value
    - ticks_add(ticks, delta) - Add delta to a ticks value
    - ticks_diff(ticks1, ticks2) - Calculate difference between ticks values

Not Available on MovingCap:
    - localtime() - Not supported (no RTC)
    - mktime() - Not supported (no RTC)
    - time() - Not supported (no RTC)
    - ticks_cpu() - Not supported

Ticks Functions - Important Notes:
    The ticks_ms() and ticks_us() functions return values in an implementation-defined
    range. On the current MovingCap CODE platform, values wrap around within a positive range
    smaller than the full 32-bit integer range.
    
    DO NOT make assumptions about the specific value range or perform direct
    arithmetic operations on ticks values. The range may change in future implementations.
    
    ALWAYS use these helper functions for ticks arithmetic:
        - ticks_diff(ticks1, ticks2) - Calculate difference between two ticks values
        - ticks_add(ticks, delta) - Add/subtract an offset to a ticks value
    
    These functions correctly handle wraparound regardless of the underlying value range.

Usage Notes:
    - Use this module for delays, timing measurements, and timeout implementations
    - For precise timing, prefer ticks_us() over ticks_ms()

Example Usage:
    import time  # or: import utime
    
    # Simple delays
    time.sleep(1)  # Sleep 1 second
    time.sleep_ms(100)  # Sleep 100 milliseconds
    time.sleep_us(50)  # Sleep 50 microseconds
    
    # Timing measurement
    start = time.ticks_ms()
    # ... do something ...
    elapsed = time.ticks_diff(time.ticks_ms(), start)
    print("Elapsed:", elapsed, "ms")
    
    # Timeout implementation
    timeout = 5000  # 5 second timeout
    start = time.ticks_ms()
    condition = True
    while condition:
        if time.ticks_diff(time.ticks_ms(), start) > timeout:
            print("Timeout!")
            break
        # ... do work ...
"""
__author__ =  "Oliver Heggelbacher"
__email__ = "oliver.heggelbacher@fullmo.de"
__version__ = "50.00.10.xx"
__date__ = "2026-01-19"

def sleep(seconds: int):
    """Sleep for the specified number of seconds.
    
    Suspends execution for at least the given number of seconds.
    The actual sleep time may be longer due to system scheduling.

    NOTE: MovingCap MicroPython currently does not support floats. "seconds" cannot be a fractional number.
    
    :param seconds: Number of seconds to sleep.
    :type seconds: int
    
    Example:
        time.sleep(2)  # Sleep for 2 seconds
        time.sleep(1)  # Sleep for 1 second
    """
    pass

def sleep_ms(ms: int):
    """Sleep for the specified number of milliseconds.
    
    Suspends execution for at least the given number of milliseconds.
    More precise than sleep() for short delays.
    
    :param ms: Number of milliseconds to sleep.
    :type ms: int
    
    Example:
        time.sleep_ms(500)  # Sleep for 500 milliseconds
        time.sleep_ms(10)   # Sleep for 10 milliseconds
    """
    pass

def sleep_us(us: int):
    """Sleep for the specified number of microseconds.
    
    Suspends execution for at least the given number of microseconds.
    Most precise delay function available. For very short delays, use with caution
    as system overhead may affect accuracy.
    
    :param us: Number of microseconds to sleep.
    :type us: int
    
    Example:
        time.sleep_us(1000)  # Sleep for 1000 microseconds (1 ms)
        time.sleep_us(50)    # Sleep for 50 microseconds
    """
    pass

def ticks_ms() -> int:
    """Get the current millisecond counter value.
    
    Returns a monotonically increasing millisecond counter with arbitrary reference point.
    The counter wraps around after reaching an implementation-defined maximum value.
    
    The specific value range is implementation-dependent and may change in future versions.
    NEVER rely on any particular range or perform direct arithmetic on ticks values.
    
    ALWAYS use ticks_diff() to calculate time differences and ticks_add() to offset
    ticks values - these functions handle wraparound correctly.
    
    :return: Current millisecond tick count (implementation-defined range).
    :rtype: int
    
    Example:
        start = time.ticks_ms()
        # ... do something ...
        duration = time.ticks_diff(time.ticks_ms(), start)  # CORRECT
        # duration = time.ticks_ms() - start  # WRONG - do not use!
    """
    pass

def ticks_us() -> int:
    """Get the current microsecond counter value.
    
    Returns a monotonically increasing microsecond counter with arbitrary reference point.
    The counter wraps around after reaching an implementation-defined maximum value.
    Provides higher resolution than ticks_ms() for precise timing.
    
    The specific value range is implementation-dependent and may change in future versions.
    NEVER rely on any particular range or perform direct arithmetic on ticks values.
    
    ALWAYS use ticks_diff() to calculate time differences and ticks_add() to offset
    ticks values - these functions handle wraparound correctly.
    
    :return: Current microsecond tick count (implementation-defined range).
    :rtype: int
    
    Example:
        start = time.ticks_us()
        # ... precise operation ...
        duration_us = time.ticks_diff(time.ticks_us(), start)  # CORRECT
    """
    pass

def ticks_add(ticks: int, delta: int) -> int:
    """Add a delta to a ticks value with proper wraparound handling.
    
    This is the correct way to add or subtract from a ticks value.
    Performs addition while correctly handling counter wraparound.
    
    :param ticks: Base ticks value (from ticks_ms() or ticks_us()).
    :type ticks: int
    :param delta: Value to add (positive) or subtract (negative).
    :type delta: int
    :return: New ticks value with proper wraparound handling.
    :rtype: int
    
    Example:
        # Calculate a deadline 5 seconds from now
        deadline = time.ticks_add(time.ticks_ms(), 5000)
        
        # Check if deadline has passed
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            # Still before deadline
            pass
    """
    pass

def ticks_diff(ticks1: int, ticks2: int) -> int:
    """Calculate the signed difference between two ticks values.
    
    This is the correct way to compare or find the difference between ticks values.
    Computes (ticks1 - ticks2) with proper handling of counter wraparound.
    
    The result is a signed integer:
        - Positive if ticks1 is "after" ticks2
        - Negative if ticks1 is "before" ticks2
        - Zero if they are equal
    
    The result is valid as long as the actual time difference does not exceed half
    the ticks period (approximately 149 hours for ticks_ms on current implementation).
    
    :param ticks1: First ticks value, typically the "later" or "end" time.
    :type ticks1: int
    :param ticks2: Second ticks value, typically the "earlier" or "start" time.
    :type ticks2: int
    :return: Signed difference (ticks1 - ticks2).
    :rtype: int
    
    Example:
        # Measure elapsed time
        start = time.ticks_ms()
        # ... operation ...
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        
        # Deadline-based timeout
        deadline = time.ticks_add(time.ticks_ms(), 1000)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            pass  # Wait until deadline
        
        # Check if timeout exceeded
        if time.ticks_diff(time.ticks_ms(), start) > 1000:
            print("More than 1 second elapsed")
    """
    pass