"""UDP diagnostics monitor for MovingCap CODE scripts (host-side CPython).

While a MovingCap CODE script runs, its ``print(...)`` output and the drive's
own status messages are broadcast as UDP datagrams on **port 14999**. To start
receiving them the host must first send a single carriage return (``\\r``) to the
drive on that port to register as a listener.

``UdpMonitor`` runs a background thread that collects every line received from a
given drive IP, so a test can later assert on what the script printed. A one-shot
``listen()`` helper is provided for quick interactive captures.

Example::

    from mctk import UdpMonitor
    monitor = UdpMonitor("192.168.2.150")
    monitor.start()
    ...                              # run the script
    assert monitor.has_line("homing OK")
    pos = monitor.last_value("POS1", "pos=")
    monitor.stop()
"""

import socket
import threading
import time
from datetime import datetime

DEFAULT_UDP_PORT = 14999


class UdpMonitor:
    """Background collector for UDP diagnostic lines from one drive."""

    def __init__(self, device_ip, port=DEFAULT_UDP_PORT, echo=True):
        self.device_ip = device_ip
        self.port = port
        self.echo = echo
        self.lines = []
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        time.sleep(0.5)
        return self

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)
        try:
            sock.bind(("", self.port))
        except OSError as exc:
            print("[udp] Cannot bind to port " + str(self.port) + ": " + repr(exc))
            return
        print("[udp] Listening on port " + str(self.port))
        # Register as a listener with the drive.
        try:
            sock.sendto(b"\r", (self.device_ip, self.port))
        except OSError as exc:
            print("[udp] Registration ping failed: " + repr(exc))

        while self._running:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError as exc:
                print("[udp] Error: " + repr(exc))
                break
            if addr[0] != self.device_ip:
                continue
            message = data.decode("utf-8", errors="ignore")
            self.lines.append(message)
            if self.echo:
                print("[udp] " + message, end="" if message.endswith("\n") else "\n")
        sock.close()

    # -- queries --------------------------------------------------------------
    def has_line(self, keyword):
        """Return True if any received line contains ``keyword``."""
        return any(keyword in line for line in self.lines)

    def last_value(self, keyword, prefix):
        """Return the int after ``prefix`` on the most recent line containing
        ``keyword`` (e.g. ``last_value("POS1", "pos=")`` -> 180). None if absent.
        """
        for line in reversed(self.lines):
            if keyword in line and prefix in line:
                tail = line.split(prefix, 1)[1].strip()
                token = tail.split()[0] if tail else ""
                token = token.strip().rstrip(",;")
                try:
                    return int(token)
                except ValueError:
                    continue
        return None

    def clear(self):
        """Forget all collected lines."""
        self.lines = []


def listen(device_ip, port=DEFAULT_UDP_PORT, duration=30):
    """One-shot blocking capture: print UDP lines from ``device_ip`` for
    ``duration`` seconds. Returns the list of captured messages.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1.0)
    sock.bind(("", port))
    print("[udp] Listening on port " + str(port) + " for " + str(duration) + "s ...")
    sock.sendto(b"\r", (device_ip, port))
    captured = []
    start = time.time()
    while (time.time() - start) < duration:
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        if addr[0] != device_ip:
            continue
        stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        message = data.decode("utf-8", errors="ignore")
        captured.append(message)
        print("[" + stamp + "] " + message, end="" if message.endswith("\n") else "\n")
    sock.close()
    return captured


if __name__ == "__main__":
    import sys

    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.2.150"
    secs = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    listen(ip, duration=secs)
