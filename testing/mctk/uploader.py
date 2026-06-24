"""HTTP upload / start / stop helpers for MovingCap CODE scripts.

This is **host-side desktop Python** (CPython 3). It talks to the drive's web
interface (``program.html``) to upload a MicroPython application script and to
start/stop its execution.

The drive exposes three relevant HTTP endpoints on port 80:

* ``POST /program.html``                  - upload a ``.py`` script (multipart form)
* ``GET  /program.html?codeAct=3``        - start (run) the uploaded script
* ``GET  /program.html?codeAct=4``        - stop the running script

Typical use::

    from mctk import upload_script, start_script, stop_script
    upload_script("192.168.2.150", "app-scripts/driveTurntablePositioning.py")
    start_script("192.168.2.150")
    ...
    stop_script("192.168.2.150")
"""

import os

import requests

DEFAULT_HTTP_TIMEOUT = 10.0

# The form field name the MovingCap web interface expects for the script upload.
_UPLOAD_FIELD = "Python script file for MovingCap CODE"


def upload_script(device_ip, script_path, start_after_upload=False,
                  timeout=DEFAULT_HTTP_TIMEOUT):
    """Upload a MicroPython script to the drive via HTTP POST.

    Args:
        device_ip: IP address of the MovingCap drive, e.g. ``"192.168.2.150"``.
        script_path: Path to the ``.py`` application script to upload.
        start_after_upload: If True, also start the script after a successful
            upload.
        timeout: HTTP timeout in seconds.

    Returns:
        True on success, False otherwise.
    """
    if not os.path.exists(script_path):
        print("[uploader] Script not found: " + script_path)
        return False

    print("[uploader] Uploading " + script_path + " to " + device_ip + " ...")
    with open(script_path, "rb") as handle:
        content = handle.read()

    files = {
        _UPLOAD_FIELD: (os.path.basename(script_path), content, "text/x-python"),
    }
    url = "http://" + device_ip + "/program.html"
    try:
        response = requests.post(url, files=files, timeout=timeout)
    except requests.RequestException as exc:
        print("[uploader] Upload error: " + repr(exc))
        return False

    if response.status_code != 200:
        print("[uploader] Upload failed: HTTP " + str(response.status_code))
        return False

    print("[uploader] Upload OK")
    if start_after_upload:
        return start_script(device_ip, timeout=timeout)
    return True


def start_script(device_ip, timeout=DEFAULT_HTTP_TIMEOUT):
    """Start / restart the uploaded script (``codeAct=3``).

    Returns True if the drive accepted the request (HTTP 200).
    """
    url = "http://" + device_ip + "/program.html?codeAct=3"
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        print("[uploader] Start error: " + repr(exc))
        return False
    ok = response.status_code == 200
    print("[uploader] Start " + ("OK" if ok else "FAILED"))
    return ok


def stop_script(device_ip, timeout=DEFAULT_HTTP_TIMEOUT):
    """Stop the running script (``codeAct=4``).

    Returns True if the drive accepted the request (HTTP 200). Never raises.
    """
    url = "http://" + device_ip + "/program.html?codeAct=4"
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        print("[uploader] Stop error: " + repr(exc))
        return False
    return response.status_code == 200
