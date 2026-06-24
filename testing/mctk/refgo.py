"""REFGO ASCII protocol client for MovingCap ETH drives (host-side CPython).

REFGO is MovingCap's text command protocol, served on **TCP port 10001**. It
lets a host PC read/write the drive's CANopen object dictionary and query status
without uploading any script. This client wraps the handful of commands needed
for functional testing:

* ``OR<index>h,<sub>h``               - object read  -> numeric value
* ``OW<index>h,<sub>h,<value>``       - object write
* ``TS``                              - tell status (statusword)
* ``TP``                              - tell position (actual position)

Convenience methods cover the most common testing tasks: reading the actual
position (object 6064h), simulating digital inputs (object 3510h.01h), and
clearing drive faults (object 6040h.0h = 128).

Example::

    from mctk import RefgoClient
    with RefgoClient("192.168.2.150") as drive:
        print(drive.tell_position())
        magic = drive.read_object(0x3410, 0x0A)
        drive.write_object(0x6073, 0x00, 1000)   # max torque 100%
        drive.simulate_inputs(0x10000)           # IN1 high (bit 16)
"""

import socket
import time

DEFAULT_REFGO_PORT = 10001
DEFAULT_TIMEOUT = 3.0
DEFAULT_SETTLE = 0.15

# Digital-input simulation object: 3510h.01h. Inputs are mapped to the high
# 16 bits, i.e. IN1 = bit 16 (0x10000), IN2 = bit 17 (0x20000), ...
INPUT_SIM_INDEX = 0x3510
INPUT_SIM_SUBINDEX = 0x01


def input_mask(*input_numbers):
    """Build a 3510h.01h simulation mask from 1-based input numbers.

    ``input_mask(1, 4)`` -> 0x90000 (IN1 and IN4 high).
    """
    mask = 0
    for number in input_numbers:
        mask |= 1 << (15 + int(number))
    return mask


def parse_int(token):
    """Parse a REFGO numeric token (decimal, ``0x..`` or trailing ``h`` hex).

    Returns an int, or None if the token is not numeric.
    """
    token = token.strip()
    if not token:
        return None
    negative = token.startswith("-")
    if negative:
        token = token[1:]
    try:
        if token[-1:] in ("h", "H"):
            value = int(token[:-1], 16)
        elif token[:2].lower() == "0x":
            value = int(token, 16)
        else:
            value = int(token, 10)
    except ValueError:
        try:
            value = int(token, 16)
        except ValueError:
            return None
    return -value if negative else value


def _hex(value):
    return format(int(value), "X")


class RefgoClient:
    """A persistent TCP connection to the drive's REFGO interpreter."""

    def __init__(self, device_ip, port=DEFAULT_REFGO_PORT, timeout=DEFAULT_TIMEOUT,
                 settle=DEFAULT_SETTLE, verbose=False):
        self.device_ip = device_ip
        self.port = port
        self.timeout = timeout
        self.settle = settle
        self.verbose = verbose
        self._sock = None

    # -- connection management ------------------------------------------------
    def connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.device_ip, self.port))
        return self

    def close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # -- low-level command ----------------------------------------------------
    def cmd(self, command):
        """Send a raw REFGO command and return the response as a string.

        Stale bytes left in the socket from a previous response are drained
        first so reads don't get contaminated.
        """
        if self._sock is None:
            self.connect()

        # Drain any pending/stale data.
        self._sock.settimeout(0.05)
        try:
            while self._sock.recv(4096):
                pass
        except (socket.timeout, OSError):
            pass

        self._sock.settimeout(self.timeout)
        self._sock.sendall((command + "\r").encode("utf-8"))
        time.sleep(self.settle)
        try:
            raw = self._sock.recv(4096).decode("utf-8", errors="ignore")
        except socket.timeout:
            raw = ""
        if self.verbose:
            print("> " + command + " -> " + raw.replace("\r", " ").replace("\n", " ").strip())
        return raw

    # -- object access --------------------------------------------------------
    def read_object(self, index, subindex):
        """Read object ``index.subindex`` via ``OR``; return int or None.

        ``index``/``subindex`` are integers, e.g. ``read_object(0x6064, 0)``.
        """
        command = "OR" + _hex(index) + "h," + _hex(subindex) + "h"
        response = self.cmd(command)
        return self._parse_object_value(response)

    def write_object(self, index, subindex, value):
        """Write ``value`` to object ``index.subindex`` via ``OW``.

        Returns True if the drive did not report an error in its reply.
        """
        command = "OW" + _hex(index) + "h," + _hex(subindex) + "h," + str(int(value))
        response = self.cmd(command)
        lowered = response.lower()
        return "error" not in lowered and "?" not in response

    @staticmethod
    def _parse_object_value(response):
        """Extract the numeric value from an ``OR`` (object read) response.

        The drive replies by echoing the command and then answering with the
        full ``OR<index>,<sub>,<value>`` triple, e.g.::

            OR3410h,1h            <- command echo
            OR3410H,1H,4242       <- answer (value in the 3rd field)
            >                     <- prompt

        The value field is decimal or hex (``0x..`` or trailing ``h``). Returns
        the parsed int, or None if no well-formed answer line is found.
        """
        for line in response.splitlines():
            line = line.strip()
            if not line.upper().startswith("OR"):
                continue
            parts = line.split(",")
            if len(parts) >= 3:
                value = parse_int(parts[2])
                if value is not None:
                    return value
        return None

    # -- status / position ----------------------------------------------------
    def _tell(self, command):
        response = self.cmd(command)
        for line in response.splitlines():
            line = line.strip()
            if line in ("", ">", command):
                continue
            value = parse_int(line)
            if value is not None:
                return value
        return None

    def tell_status(self):
        """``TS`` - return the drive statusword as int (or None)."""
        return self._tell("TS")

    def tell_position(self):
        """``TP`` - return the actual position as int (or None)."""
        return self._tell("TP")

    def actual_position(self):
        """Read the actual position from object 6064h.00h."""
        return self.read_object(0x6064, 0x00)

    # -- digital input simulation --------------------------------------------
    def simulate_inputs(self, mask):
        """Set the input-simulation mask (object 3510h.01h)."""
        return self.write_object(INPUT_SIM_INDEX, INPUT_SIM_SUBINDEX, mask)

    def clear_inputs(self):
        """Clear input simulation (return control to physical inputs)."""
        return self.write_object(INPUT_SIM_INDEX, INPUT_SIM_SUBINDEX, 0)

    def pulse_inputs(self, mask, hold_seconds=0.25):
        """Set a simulation mask, hold it, then clear it."""
        self.simulate_inputs(mask)
        time.sleep(hold_seconds)
        return self.clear_inputs()

    # -- misc -----------------------------------------------------------------
    def reset_fault(self):
        """Issue a CiA-402 fault reset (controlword 6040h.0h = 128)."""
        return self.write_object(0x6040, 0x00, 128)
