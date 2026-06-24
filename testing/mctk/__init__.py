"""MovingCap Test Kit (mctk) - host-side helpers for testing MovingCap CODE.

This package is **desktop CPython 3** tooling that runs on a PC to develop and
test MovingCap CODE (MicroPython) applications on a MovingCap Ethernet ETH servo
drive. It is *not* drive-side code and is not subject to the MovingCap CODE
constraints (f-strings, stdlib, etc. are all fine here).

Modules:

* :mod:`mctk.uploader` - upload / start / stop scripts over HTTP.
* :mod:`mctk.refgo`    - REFGO ASCII client (object read/write, status, inputs).
* :mod:`mctk.udp`      - UDP diagnostics monitor for ``print()`` output.
* :mod:`mctk.runner`   - small pass/fail test runner with JSON reports.

Only the ``requests`` third-party package is required (see ``requirements.txt``).
"""

from .uploader import upload_script, start_script, stop_script
from .refgo import RefgoClient, input_mask, parse_int
from .udp import UdpMonitor, listen
from .runner import TestRunner, PASS, FAIL

__all__ = [
    "upload_script",
    "start_script",
    "stop_script",
    "RefgoClient",
    "input_mask",
    "parse_int",
    "UdpMonitor",
    "listen",
    "TestRunner",
    "PASS",
    "FAIL",
]

__version__ = "1.0.0"
