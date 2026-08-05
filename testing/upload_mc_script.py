#!/usr/bin/env python3
"""Upload and start a MovingCap CODE (MicroPython) script on a drive.

Thin CLI wrapper around :mod:`mctk.uploader` that can be invoked from *any*
current working directory (the ``functional_testing`` folder containing the
``mctk`` package is located relative to this file, not relative to the
caller's cwd).

Usage:
    python upload_mc_script.py SCRIPT_PATH [DEVICE_IP] [options]
    python upload_mc_script.py app-scripts/turntrack_a_b_turntable.py
    python upload_mc_script.py my_script.py 192.168.2.50
    python upload_mc_script.py my_script.py --device-ip 192.168.2.50 --no-start
    python upload_mc_script.py my_script.py --stop-first

Arguments:
    SCRIPT_PATH             Path to the local ``.py`` MovingCap CODE script to
                            upload (relative paths are resolved against the
                            current working directory). Required.
    DEVICE_IP               Optional positional shortcut for --device-ip.

Options:
    --device-ip, -i IP      IP address of the target MovingCap drive.
                            Default: 192.168.2.150
    --stop-first            Stop any currently running script on the drive
                            before uploading the new one.
    --no-start               Upload only; do not start the script afterwards.
    --timeout SECONDS       HTTP request timeout in seconds. Default: 10
"""

import os
import sys
import argparse

# Add this script's own directory to sys.path so `import mctk` resolves
# regardless of the caller's current working directory.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from mctk import upload_script, start_script, stop_script

DEFAULT_DEVICE_IP = "192.168.2.150"
DEFAULT_HTTP_TIMEOUT = 10.0


def upload_and_run(script_path, device_ip=DEFAULT_DEVICE_IP, start=True,
                    stop_first=False, timeout=DEFAULT_HTTP_TIMEOUT):
    """Upload a MovingCap CODE script to a drive and optionally start it.

    Args:
        script_path: Path to the local ``.py`` script to upload.
        device_ip: IP address of the target MovingCap drive.
        start: If True, start the script after a successful upload.
        stop_first: If True, stop any currently running script before
            uploading the new one.
        timeout: HTTP timeout in seconds.

    Returns:
        True on success, False otherwise.
    """
    script_path = os.path.abspath(script_path)

    if stop_first:
        print(f"[upload_mc_script] Stopping any running script on {device_ip} ...")
        stop_script(device_ip, timeout=timeout)

    uploaded = upload_script(device_ip, script_path, start_after_upload=False,
                              timeout=timeout)
    if not uploaded:
        return False

    if not start:
        return True

    return start_script(device_ip, timeout=timeout)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Upload and start a MovingCap CODE (MicroPython) script on a drive.")
    parser.add_argument("script_path",
                         help="Path to the local .py MovingCap CODE script to upload")
    parser.add_argument("device_ip_positional", nargs="?", default=None,
                         help="Optional positional shortcut for --device-ip")
    parser.add_argument("--device-ip", "-i", dest="device_ip", default=None,
                         help=f"IP address of the target MovingCap drive (default: {DEFAULT_DEVICE_IP})")
    parser.add_argument("--stop-first", action="store_true",
                         help="Stop any currently running script on the drive before uploading")
    parser.add_argument("--no-start", action="store_true",
                         help="Upload only; do not start the script afterwards")
    parser.add_argument("--timeout", type=float, default=DEFAULT_HTTP_TIMEOUT,
                         help=f"HTTP request timeout in seconds (default: {DEFAULT_HTTP_TIMEOUT})")
    args = parser.parse_args(argv)

    device_ip = args.device_ip or args.device_ip_positional or DEFAULT_DEVICE_IP

    if not os.path.exists(args.script_path):
        print(f"[upload_mc_script] [ERROR] Script not found: {args.script_path}")
        return 1

    success = upload_and_run(
        args.script_path,
        device_ip=device_ip,
        start=not args.no_start,
        stop_first=args.stop_first,
        timeout=args.timeout,
    )

    if success:
        action = "uploaded and started" if not args.no_start else "uploaded"
        print(f"[upload_mc_script] Script {action} successfully on {device_ip}.")
        return 0

    print(f"[upload_mc_script] [ERROR] Failed to upload/start script on {device_ip}.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
