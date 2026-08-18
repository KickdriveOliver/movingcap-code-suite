#!/usr/bin/env python3
"""Verify basic Modbus TCP communication with modbus_tcp_motion.py using modpoll.

This script uploads app-scripts/modbus_tcp_motion.py to the target MovingCap
drive and uses the free 'modpoll' CLI utility (by ProconX) to run basic Modbus
TCP read/write verification commands.

Usage:
    python verify_modbus_tcp_modpoll.py [DEVICE_IP]
    python verify_modbus_tcp_modpoll.py 192.168.2.54
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from upload_mc_script import upload_and_run

DEFAULT_DEVICE_IP = "192.168.2.150"
SCRIPT_PATH = os.path.normpath(os.path.join(THIS_DIR, "..", "app-scripts", "modbus_tcp_motion.py"))


def find_modpoll_executable():
    """Locate modpoll executable in common locations or system PATH."""
    candidates = [
        os.path.join(THIS_DIR, "modpoll.exe"),
        os.path.join(THIS_DIR, "modpoll"),
        os.path.join(THIS_DIR, "tools", "modpoll.exe"),
        os.path.join(THIS_DIR, "tools", "modpoll"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    system_modpoll = shutil.which("modpoll")
    if system_modpoll:
        return system_modpoll

    # Check Windows-specific .exe search if on Windows
    if sys.platform == "win32":
        system_modpoll_exe = shutil.which("modpoll.exe")
        if system_modpoll_exe:
            return system_modpoll_exe

    return None


def run_my_command(cmd_args):
    print(f"Running: {' '.join(cmd_args)}")
    result = subprocess.run(cmd_args, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return (result.returncode == 0)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify modbus_tcp_motion.py with modpoll CLI."
    )
    parser.add_argument(
        "device_ip",
        nargs="?",
        default=DEFAULT_DEVICE_IP,
        help=f"IP address of the target MovingCap drive (default: {DEFAULT_DEVICE_IP}).",
    )
    args = parser.parse_args(argv)
    device_ip = args.device_ip

    print("=" * 75)
    print(" MovingCap Modbus TCP Verification with modpoll")
    print(f" Target Drive IP: {device_ip}")
    print("=" * 75)

    # 1. Upload and start the MicroPython drive script
    print(f"\n[1/6] Uploading and starting modbus_tcp_motion.py on drive ({device_ip})...")
    if not upload_and_run(SCRIPT_PATH, device_ip=device_ip, stop_first=True):
        print(f"[ERROR] Failed to upload/start modbus_tcp_motion.py on drive {device_ip}.", file=sys.stderr)
        return 1

    # 2. Locate modpoll
    modpoll_path = find_modpoll_executable()
    if not modpoll_path:
        print("\n[WARNING] modpoll executable was not found on your system!")
        print("\nTo run automatic Modbus TCP polling verification:")
        print("  1. Download modpoll from: https://www.modbusdriver.com/modpoll.html")
        print("     Direct Link: https://www.modbusdriver.com/downloads/modpoll.zip")
        print("  2. Extract modpoll.exe (from win32 / x86_64 folder) to:")
        print(f"     {os.path.join(THIS_DIR, 'modpoll.exe')}")
        print("     or add modpoll to your system PATH.")
        print("  3. Re-run this script.")
        print(f"\nScript modbus_tcp_motion.py is now running on drive {device_ip}:502.")
        return 0

    print(f"[INFO] Found modpoll at: {modpoll_path}")
    print("[2/6] Waiting 2 seconds for server startup...")
    time.sleep(2.0)

    # 3. Read Status & Feedback Block (PDU 5000-5005 -> modpoll 5001, count 6)
    print("\n[3/6] Reading Status & Feedback Block (PDU 5000-5005, modpoll reference 5001, count 6)...")
    cmd_read = [modpoll_path, "-m", "tcp", "-p", "502", "-1", "-r", "5001", "-c", "6", device_ip]
    if not run_my_command(cmd_read):
        print("[ERROR] Failed to read feedback registers.", file=sys.stderr)
        return 1

    # 4. Write Operation Mode = 1 (Profile Position Mode, PDU 6001 -> modpoll reference 6002)
    print("\n[4/6] Writing Operation Mode = 1 (Profile Position) to PDU 6001 (modpoll reference 6002)...")
    cmd_mode = [modpoll_path, "-m", "tcp", "-p", "502", "-1", "-r", "6002", device_ip, "1"]
    if not run_my_command(cmd_mode):
        print("[ERROR] Failed to write operation mode.", file=sys.stderr)
        return 1

    # 5. Write Target Position = 1000 (32-bit int, PDU 6002-6003 -> modpoll reference 6003)
    print("\n[5/6] Writing Target Position = 1000 to PDU 6002-6003 (modpoll reference 6003, 32-bit int)...")
    cmd_target = [modpoll_path, "-m", "tcp", "-p", "502", "-1", "-t", "4:int", "-r", "6003", device_ip, "1000"]
    if not run_my_command(cmd_target):
        print("[ERROR] Failed to write target position.", file=sys.stderr)
        return 1

    # 6. Write Controlword = 6 (Shutdown, PDU 6000 -> modpoll reference 6001)
    print("\n[6/6] Writing Controlword = 6 (Shutdown) to PDU 6000 (modpoll reference 6001)...")
    cmd_control = [modpoll_path, "-m", "tcp", "-p", "502", "-1", "-r", "6001", device_ip, "6"]
    if not run_my_command(cmd_control):
        print("[ERROR] Failed to write controlword.", file=sys.stderr)
        return 1

    print("\n" + "=" * 75)
    print(" [SUCCESS] Basic Modbus TCP Verification Passed!")
    print("=" * 75)
    print("\nOptional: To continuously poll and verify Watchdog timeout (WATCHDOG_MS = 5000ms),")
    print("run modpoll with loop option:")
    print(f'  "{modpoll_path}" -m tcp -p 502 -r 5001 -c 6 -l 1000 {device_ip}')
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
