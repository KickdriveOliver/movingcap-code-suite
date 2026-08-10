#!/usr/bin/env python3
"""Hardware E2E test for app-scripts/modbus_tcp_motion.py.

SAFETY: this test enables the drive and physically commands relative position
motion and profile velocity motion on the approved freely rotating axis.
"""

import os
import socket
import struct
import sys
import time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from mctk import RefgoClient, TestRunner, UdpMonitor, start_script, stop_script, upload_script

DEVICE_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.2.150"
SCRIPT_NAME = "modbus_tcp_motion.py"
SCRIPT_PATH = os.path.normpath(os.path.join(THIS_DIR, "..", "app-scripts", SCRIPT_NAME))
RESULTS_DIR = os.path.join(THIS_DIR, "results")
MODBUS_PORT = 502
SOCKET_TIMEOUT = 2.0
POSITION_TOLERANCE = 5
VELOCITY_STANDSTILL_TOLERANCE = 5
VELOCITY_MOTION_THRESHOLD = 10

U8 = "u8"
I8 = "i8"
U16 = "u16"
I16 = "i16"
U32 = "u32"
I32 = "i32"

FEEDBACK_MAP = (
    (5000, 0x6041, 0, U16, "statusword"),
    (5001, 0x6061, 0, I8, "mode display"),
    (5002, 0x6064, 0, I32, "actual position"),
    (5004, 0x606C, 0, I32, "actual velocity"),
)

WRITABLE_MAP = (
    (6000, 0x6040, 0, U16, "controlword"),
    (6001, 0x6060, 0, I8, "operation mode"),
    (6002, 0x607A, 0, I32, "target position"),
    (6004, 0x6081, 0, U32, "profile velocity"),
    (6006, 0x60FF, 0, I32, "target velocity"),
    (6008, 0x6083, 0, U32, "profile acceleration"),
    (6010, 0x6084, 0, U32, "profile deceleration"),
    (6012, 0x6067, 0, U32, "position window"),
    (6014, 0x6068, 0, U16, "position window time"),
    (6015, 0x607D, 1, I32, "software limit minimum"),
    (6017, 0x607D, 2, I32, "software limit maximum"),
    (6019, 0x60F2, 0, U16, "positioning option"),
    (6020, 0x6085, 0, U32, "quick-stop deceleration"),
    (6022, 0x605A, 0, I16, "quick-stop option"),
    (6023, 0x60A4, 0, U32, "profile jerk"),
)


class ModbusClient:
    def __init__(self, host):
        self.host = host
        self.sock = None
        self.transaction_id = 0
        self.buffer = b""

    def connect(self):
        self.sock = socket.create_connection((self.host, MODBUS_PORT), SOCKET_TIMEOUT)
        self.sock.settimeout(SOCKET_TIMEOUT)

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def abort(self):
        if self.sock is not None:
            try:
                # Force an immediate TCP reset so the peer observes disconnect now.
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                                     struct.pack("hh", 1, 0))
                self.sock.close()
            finally:
                self.sock = None

    def adu(self, pdu, unit=1, protocol=0, transaction_id=None):
        if transaction_id is None:
            self.transaction_id = (self.transaction_id + 1) & 0xFFFF
            transaction_id = self.transaction_id
        return struct.pack(">HHHB", transaction_id, protocol, len(pdu) + 1, unit) + pdu

    def send(self, pdu, unit=1):
        request = self.adu(pdu, unit)
        self.sock.sendall(request)
        return self.receive()

    def receive(self):
        while len(self.buffer) < 7:
            self.buffer += self.sock.recv(4096)
        transaction_id, protocol, length, unit = struct.unpack(">HHHB", self.buffer[:7])
        total = 6 + length
        while len(self.buffer) < total:
            self.buffer += self.sock.recv(4096)
        pdu = self.buffer[7:total]
        self.buffer = self.buffer[total:]
        return transaction_id, protocol, unit, pdu

    def read_registers(self, address, quantity, unit=1):
        response = self.send(struct.pack(">BHH", 3, address, quantity), unit)
        pdu = response[3]
        if pdu[0] & 0x80:
            raise AssertionError("Modbus exception " + str(pdu[1]))
        if pdu[0] != 3 or pdu[1] != quantity * 2:
            raise AssertionError("invalid FC03 response")
        return list(struct.unpack(">" + ("H" * quantity), pdu[2:]))

    def write_single(self, address, value, unit=1):
        pdu = struct.pack(">BHH", 6, address, value & 0xFFFF)
        response = self.send(pdu, unit)
        if response[3] != pdu:
            raise AssertionError("invalid FC06 response " + repr(response[3]))
        return response

    def write_multiple(self, address, values, unit=1):
        data = struct.pack(">" + ("H" * len(values)), *values)
        pdu = struct.pack(">BHHB", 16, address, len(values), len(data)) + data
        response = self.send(pdu, unit)
        expected = struct.pack(">BHH", 16, address, len(values))
        if response[3] != expected:
            raise AssertionError("invalid FC16 response " + repr(response[3]))
        return response


def words32(value):
    packed = struct.pack(">I", value & 0xFFFFFFFF)
    return struct.unpack(">HH", packed)


def signed32(high_word, low_word):
    return struct.unpack(">i", struct.pack(">HH", high_word, low_word))[0]


def type_width(type_code):
    return 2 if type_code in (U32, I32) else 1


def value_words(value, type_code):
    if type_width(type_code) == 2:
        return list(words32(value))
    if type_code in (U8, I8):
        return [value & 0xFF]
    return [value & 0xFFFF]


def words_value(words, type_code):
    if type_width(type_code) == 2:
        value = (words[0] << 16) | words[1]
        if type_code == I32 and value >= 0x80000000:
            value -= 0x100000000
        return value
    value = words[0]
    if type_code == I8:
        value &= 0xFF
        return value - 0x100 if value >= 0x80 else value
    if type_code == U8:
        return value & 0xFF
    if type_code == I16 and value >= 0x8000:
        return value - 0x10000
    return value


def raw_write_multiple(client, address, values):
    data = struct.pack(">" + ("H" * len(values)), *values)
    pdu = struct.pack(">BHHB", 16, address, len(values), len(data)) + data
    return client.send(pdu)


def connect_modbus(client, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            client.connect()
            return True
        except OSError:
            time.sleep(0.1)
    return False


def wait_position(client, target, timeout=5.0):
    deadline = time.monotonic() + timeout
    last_position = None
    last_status = None
    while time.monotonic() < deadline:
        registers = client.read_registers(5000, 4)
        last_status = registers[0]
        last_position = signed32(registers[2], registers[3])
        if last_status & 0x0008:
            return False, last_position, last_status
        if (last_status & 0x0400) and abs(last_position - target) <= POSITION_TOLERANCE:
            return True, last_position, last_status
        time.sleep(0.05)
    return False, last_position, last_status


def wait_standstill_refgo(drive, timeout=5.0):
    deadline = time.monotonic() + timeout
    velocity = None
    status = None
    while time.monotonic() < deadline:
        velocity = drive.read_object(0x606C, 0)
        status = drive.read_object(0x6041, 0)
        if status is not None and status & 0x0008:
            return False, velocity, status
        if velocity is not None and abs(velocity) <= VELOCITY_STANDSTILL_TOLERANCE:
            return True, velocity, status
        time.sleep(0.05)
    return False, velocity, status


def safe_refgo_cleanup(drive):
    results = {}
    results["quickstop_option_2"] = drive.write_object(0x605A, 0, 2)
    results["quickstop_controlword"] = drive.write_object(0x6040, 0, 0x0B)
    deadline = time.monotonic() + 5.0
    disabled = False
    while time.monotonic() < deadline:
        statusword = drive.read_object(0x6041, 0)
        if statusword is not None and (statusword & 0x006F) == 0x0040:
            disabled = True
            break
        if statusword is not None and statusword & 0x0008:
            break
        time.sleep(0.01)
    results["quickstop_reached_disabled"] = disabled
    if not disabled:
        results["fallback_controlword_0"] = drive.write_object(0x6040, 0, 0)
    results["target_velocity_zero"] = drive.write_object(0x60FF, 0, 0)
    results["mode_zero"] = drive.write_object(0x6060, 0, 0)
    return results


def verify_safe_refgo_state(drive, timeout=6.0):
    deadline = time.monotonic() + timeout
    target_velocity = None
    mode = None
    statusword = None
    actual_velocity = None
    while time.monotonic() < deadline:
        target_velocity = drive.read_object(0x60FF, 0)
        mode = drive.read_object(0x6060, 0)
        statusword = drive.read_object(0x6041, 0)
        actual_velocity = drive.read_object(0x606C, 0)
        if (target_velocity == 0 and mode == 0 and statusword is not None
                and (statusword & 0x006F) == 0x0040
                and actual_velocity is not None
                and abs(actual_velocity) <= VELOCITY_STANDSTILL_TOLERANCE):
            return True, target_velocity, mode, statusword, actual_velocity
        time.sleep(0.05)
    return False, target_velocity, mode, statusword, actual_velocity


def exception_code(response):
    pdu = response[3]
    return pdu[1] if len(pdu) == 2 and pdu[0] & 0x80 else None


def peer_closed(sock, timeout=1.0):
    old_timeout = sock.gettimeout()
    sock.settimeout(timeout)
    try:
        return sock.recv(1) == b""
    except (ConnectionResetError, ConnectionAbortedError):
        return True
    except socket.timeout:
        return False
    finally:
        sock.settimeout(old_timeout)


def main():
    runner = TestRunner("test_modbus_tcp_motion", device_ip=DEVICE_IP, script=SCRIPT_NAME)
    drive = None
    client = None
    monitor = None
    before = {}
    parameter_before = {}
    after_position = {}
    cleanup = {}

    try:
        runner.section("Setup and saved-parameter baseline")
        stop_script(DEVICE_IP)
        drive = RefgoClient(DEVICE_IP, verbose=True)
        drive.connect()
        safe_refgo_cleanup(drive)
        before = {
            "statusword": drive.read_object(0x6041, 0),
            "mode": drive.read_object(0x6060, 0),
            "position": drive.read_object(0x6064, 0),
            "actual_velocity": drive.read_object(0x606C, 0),
            "target_velocity": drive.read_object(0x60FF, 0),
            "profile_velocity": drive.read_object(0x6081, 0),
            "acceleration": drive.read_object(0x6083, 0),
            "deceleration": drive.read_object(0x6084, 0),
            "quickstop_deceleration": drive.read_object(0x6085, 0),
        }
        for entry in WRITABLE_MAP:
            address, index, subindex, type_code, name = entry
            value = drive.read_object(index, subindex)
            parameter_before[(index, subindex)] = value
            if index == 0x60A4:
                runner.check("MC349 profile jerk unsupported through REFGO", value is None,
                             "60A4h=" + str(value))
            else:
                runner.check("REFGO baseline " + name + " readable", value is not None,
                             hex(index) + ":" + str(subindex) + "=" + str(value))
        print("BEFORE " + repr(before))
        print("PARAMETER_BEFORE " + repr(parameter_before))
        runner.check("saved profile velocity baseline readable", before["profile_velocity"] is not None,
                     "6081h=" + str(before["profile_velocity"]))
        runner.check("saved acceleration baseline readable", before["acceleration"] is not None,
                     "6083h=" + str(before["acceleration"]))
        runner.check("saved deceleration baseline readable", before["deceleration"] is not None,
                     "6084h=" + str(before["deceleration"]))
        runner.check("saved quickstop baseline readable", before["quickstop_deceleration"] is not None,
                     "6085h=" + str(before["quickstop_deceleration"]))

        monitor = UdpMonitor(DEVICE_IP)
        monitor.start()
        uploaded = upload_script(DEVICE_IP, SCRIPT_PATH)
        runner.check("script upload", uploaded)
        if not uploaded:
            raise AssertionError("script upload failed")
        started = uploaded and start_script(DEVICE_IP)
        runner.check("script start", started)
        if not started:
            raise AssertionError("script start failed")
        client = ModbusClient(DEVICE_IP)
        connected = connect_modbus(client)
        runner.check("Modbus TCP port 502 connect", connected)
        if not connected:
            raise AssertionError("Modbus TCP connection failed")

        runner.section("Register map and REFGO cross-checks without enabling")
        unit = 0xA5
        transaction_id, protocol, echoed_unit, pdu = client.send(struct.pack(">BHH", 3, 5000, 6), unit)
        registers = list(struct.unpack(">6H", pdu[2:]))
        ref_status = drive.read_object(0x6041, 0)
        ref_mode_display = drive.read_object(0x6061, 0)
        ref_position = drive.read_object(0x6064, 0)
        ref_velocity = drive.read_object(0x606C, 0)
        runner.check("accept and echo arbitrary unit ID", echoed_unit == unit,
                     "unit=" + hex(echoed_unit))
        runner.check("MBAP protocol ID zero", protocol == 0, "transaction=" + str(transaction_id))
        runner.check("5000 statusword map", registers[0] == (ref_status & 0xFFFF))
        runner.check("5001 mode-display low byte map", registers[1] == (ref_mode_display & 0xFF))
        runner.check("5002-5003 position high-word-first",
                     signed32(registers[2], registers[3]) == ref_position)
        mapped_velocity = signed32(registers[4], registers[5])
        runner.check("5004-5005 velocity high-word-first",
                     abs(mapped_velocity) <= 10 and abs(ref_velocity) <= 10,
                     "Modbus 606Ch=" + str(mapped_velocity)
                     + " REFGO 606Ch=" + str(ref_velocity))

        runner.section("Expanded writable map readback and disabled round trips")
        safe_values = {
            (0x6040, 0): 0,
            (0x6060, 0): 0,
            (0x60FF, 0): 0,
        }
        for entry in WRITABLE_MAP:
            address, index, subindex, type_code, name = entry
            if index == 0x60A4:
                continue
            ref_value = drive.read_object(index, subindex)
            mapped_words = client.read_registers(address, type_width(type_code))
            mapped_value = words_value(mapped_words, type_code)
            expected_value = ref_value
            if type_code == U32:
                expected_value &= 0xFFFFFFFF
            runner.check("FC03 " + str(address) + " " + name + " REFGO cross-check",
                         mapped_value == expected_value,
                         "Modbus=" + str(mapped_value) + " REFGO=" + str(ref_value))

        all_writable_words = client.read_registers(6000, 25)
        runner.check("FC03 contiguous cross-entry read 6000-6024",
                     len(all_writable_words) == 25,
                     "registers=" + str(len(all_writable_words)))
        cross_words = client.read_registers(6007, 4)
        runner.check("FC03 cross-entry read starts in low word",
                     len(cross_words) == 4)

        roundtrip_evidence = {}
        for entry in WRITABLE_MAP:
            address, index, subindex, type_code, name = entry
            if index == 0x60A4:
                continue
            value = safe_values.get((index, subindex),
                                    parameter_before[(index, subindex)])
            words = value_words(value, type_code)
            if type_width(type_code) == 1:
                client.write_single(address, words[0])
            else:
                client.write_multiple(address, words)
            ref_after = drive.read_object(index, subindex)
            expected_after = value
            if type_code == U32 and ref_after is not None:
                ref_after &= 0xFFFFFFFF
                expected_after &= 0xFFFFFFFF
            roundtrip_evidence[name] = ref_after
            runner.check("write current " + name + " and REFGO verify",
                         ref_after == expected_after,
                         hex(index) + ":" + str(subindex) + "=" + str(ref_after))
        print("PARAMETER_ROUNDTRIPS " + repr(roundtrip_evidence))

        jerk_before_neighbors = (
            drive.read_object(0x605A, 0),
            drive.read_object(0x6085, 0),
        )
        jerk_response = raw_write_multiple(
            client, 6023, value_words(0, U32))
        jerk_after_neighbors = (
            drive.read_object(0x605A, 0),
            drive.read_object(0x6085, 0),
        )
        runner.check("unsupported 60A4 FC16 returns exception 04",
                     exception_code(jerk_response) == 4,
                     "exception=" + str(exception_code(jerk_response)))
        runner.check("unsupported jerk write does not disturb neighboring state",
                     jerk_after_neighbors == jerk_before_neighbors,
                     "before=" + repr(jerk_before_neighbors)
                     + " after=" + repr(jerk_after_neighbors))

        runner.section("Fragmented/coalesced framing and protocol exceptions")
        fragmented = client.adu(struct.pack(">BHH", 3, 5000, 1), unit=0x22)
        for octet in fragmented:
            client.sock.sendall(bytes((octet,)))
            time.sleep(0.005)
        fragmented_response = client.receive()
        runner.check("fragmented ADU response", fragmented_response[2] == 0x22
                     and fragmented_response[3][0] == 3)

        first = client.adu(struct.pack(">BHH", 3, 5000, 1), unit=3, transaction_id=0x7101)
        second = client.adu(struct.pack(">BHH", 3, 5002, 2), unit=4, transaction_id=0x7102)
        client.sock.sendall(first + second)
        response1 = client.receive()
        response2 = client.receive()
        runner.check("coalesced ADUs retain transaction order",
                     response1[0] == 0x7101 and response2[0] == 0x7102)
        runner.check("unsupported function exception 01",
                     exception_code(client.send(struct.pack(">BHH", 4, 5000, 1))) == 1)
        runner.check("unmapped address exception 02",
                     exception_code(client.send(struct.pack(">BHH", 3, 4999, 1))) == 2)
        runner.check("feedback/writable gap read exception 02",
                     exception_code(client.send(struct.pack(">BHH", 3, 5006, 1))) == 2)
        runner.check("past writable map read exception 02",
                     exception_code(client.send(struct.pack(">BHH", 3, 6025, 1))) == 2)
        runner.check("illegal quantity exception 03",
                     exception_code(client.send(struct.pack(">BHH", 3, 5000, 0))) == 3)
        runner.check("FC06 rejects partial 32-bit object",
                     exception_code(client.send(struct.pack(">BHH", 6, 6002, 1))) == 2)
        start_partial = struct.pack(">BHHBH", 16, 6002, 1, 2, 0)
        runner.check("FC16 rejects incomplete value from mapped start",
                     exception_code(client.send(start_partial)) == 3)
        partial = struct.pack(">BHHBH", 16, 6003, 1, 2, 1)
        runner.check("FC16 rejects partial 32-bit object",
                     exception_code(client.send(partial)) == 2)
        two_objects = struct.pack(">BHHBHH", 16, 6000, 2, 4, 0, 0)
        runner.check("FC16 rejects more than one complete value",
                     exception_code(client.send(two_objects)) == 3)
        runner.check("FC06 rejects unmapped gap",
                     exception_code(client.send(struct.pack(">BHH", 6, 5999, 0))) == 2)
        spanning = struct.pack(">BHHBHHH", 16, 6002, 3, 6, 0, 0, 0)
        runner.check("FC16 rejects complete object plus next-object word",
                     exception_code(client.send(spanning)) == 3)

        bad_protocol = client.adu(struct.pack(">BHH", 3, 5000, 1), protocol=1)
        client.sock.sendall(bad_protocol)
        runner.check("invalid MBAP protocol ID closes connection", peer_closed(client.sock))
        client.close()
        runner.check("reconnect after invalid protocol ID", connect_modbus(client))
        bad_length = struct.pack(">HHHB", 0x7202, 0, 1, 1)
        client.sock.sendall(bad_length)
        runner.check("invalid MBAP length closes connection", peer_closed(client.sock))
        client.close()
        runner.check("reconnect after invalid MBAP length", connect_modbus(client))

        runner.section("TCP disconnect safe-disable behavior")
        client.write_single(6001, 3)
        client.write_multiple(6006, words32(0))
        for controlword in (6, 7, 15):
            client.write_single(6000, controlword)
            time.sleep(0.05)
        client.abort()
        # mcnet transparently manages accepted clients on this firmware, so its
        # connection-state methods may mask FIN/RST. The request watchdog is the
        # bounded safety fallback and must make a disconnected client safe.
        disconnect_deadline = time.monotonic() + 6.0
        disconnect_target = None
        disconnect_mode = None
        disconnect_status = None
        while time.monotonic() < disconnect_deadline:
            disconnect_target = drive.read_object(0x60FF, 0)
            disconnect_mode = drive.read_object(0x6060, 0)
            disconnect_status = drive.read_object(0x6041, 0)
            if (disconnect_target == 0 and disconnect_mode == 0
                    and (disconnect_status & 0x006F) == 0x0040):
                break
            time.sleep(0.1)
        runner.check("disconnect clears target velocity", disconnect_target == 0)
        runner.check("disconnect clears mode", disconnect_mode == 0)
        runner.check("disconnect reaches switch-on-disabled",
                     (disconnect_status & 0x006F) == 0x0040,
                     "6041h=" + hex(disconnect_status or 0))
        runner.check("reconnect after safe disconnect", connect_modbus(client))

        runner.section("Approved profile-position motion +100 and return -100")
        position_start = drive.read_object(0x6064, 0)
        client.write_single(6001, 1)
        for controlword in (6, 7, 15):
            client.write_single(6000, controlword)
            time.sleep(0.05)
        client.write_multiple(6002, words32(100))
        client.write_single(6000, 95)
        time.sleep(0.02)
        client.write_single(6000, 15)
        reached, position_plus, status_plus = wait_position(client, position_start + 100)
        after_position["start"] = position_start
        after_position["plus_100"] = position_plus
        runner.check("+100 target reached without fault", reached,
                     "start=" + str(position_start) + " actual=" + str(position_plus)
                     + " status=" + hex(status_plus or 0))

        client.write_multiple(6002, words32(-100))
        client.write_single(6000, 95)
        time.sleep(0.02)
        client.write_single(6000, 15)
        returned, position_return, status_return = wait_position(client, position_start)
        after_position["return"] = position_return
        runner.check("-100 return reached without fault", returned,
                     "target=" + str(position_start) + " actual=" + str(position_return)
                     + " status=" + hex(status_return or 0))

        runner.section("Approved profile-velocity +100 and bounded stop")
        client.write_single(6001, 3)
        client.write_multiple(6006, words32(0))
        for controlword in (6, 7, 15):
            client.write_single(6000, controlword)
            time.sleep(0.05)
        client.write_multiple(6006, words32(100))
        time.sleep(1.0)
        velocity_registers = client.read_registers(5004, 2)
        modbus_velocity = signed32(velocity_registers[0], velocity_registers[1])
        refgo_velocity = drive.read_object(0x606C, 0)
        runner.check("profile velocity actual is nonzero",
                     abs(modbus_velocity) > VELOCITY_MOTION_THRESHOLD,
                     "Modbus 606Ch=" + str(modbus_velocity)
                     + " REFGO 606Ch=" + str(refgo_velocity))
        client.write_multiple(6006, words32(0))
        stopped, stop_velocity, stop_status = wait_standstill_refgo(drive)
        runner.check("profile velocity bounded standstill", stopped,
                     "606Ch=" + str(stop_velocity) + " status=" + hex(stop_status or 0))

        runner.section("Five-second valid-request inactivity watchdog")
        client.write_single(6001, 3)
        client.write_multiple(6006, words32(0))
        for controlword in (6, 7, 15):
            client.write_single(6000, controlword)
            time.sleep(0.05)
        client.write_multiple(6006, words32(100))
        time.sleep(1.0)
        watchdog_moving_velocity = drive.read_object(0x606C, 0)
        time.sleep(4.7)
        watchdog_target = drive.read_object(0x60FF, 0)
        watchdog_mode = drive.read_object(0x6060, 0)
        watchdog_status = drive.read_object(0x6041, 0)
        watchdog_quickstop_option = drive.read_object(0x605A, 0)
        watchdog_stopped, watchdog_velocity, _ = wait_standstill_refgo(drive, 2.0)
        runner.check("watchdog test began with motion",
                     abs(watchdog_moving_velocity) > VELOCITY_MOTION_THRESHOLD,
                     "606Ch=" + str(watchdog_moving_velocity))
        runner.check("watchdog clears target velocity", watchdog_target == 0,
                     "60FFh=" + str(watchdog_target))
        runner.check("watchdog clears mode", watchdog_mode == 0, "6060h=" + str(watchdog_mode))
        runner.check("watchdog reaches switch-on-disabled",
                     (watchdog_status & 0x006F) == 0x0040,
                     "6041h=" + hex(watchdog_status or 0))
        runner.check("watchdog uses quick stop option 2", watchdog_quickstop_option == 2,
                     "605Ah=" + str(watchdog_quickstop_option))
        runner.check("watchdog reaches standstill", watchdog_stopped,
                     "606Ch=" + str(watchdog_velocity))

    except (OSError, AssertionError, struct.error) as exc:
        runner.check("test completed without host/protocol exception", False, repr(exc))
    finally:
        runner.section("Unconditional safe cleanup")
        if client is not None:
            client.close()
        if monitor is not None:
            monitor.stop()
            print("UDP_DIAGNOSTICS " + repr(monitor.lines))
        if drive is None:
            try:
                drive = RefgoClient(DEVICE_IP, verbose=True)
                drive.connect()
            except OSError as exc:
                runner.check("cleanup REFGO connect", False, repr(exc))
                drive = None
        if drive is not None:
            try:
                cleanup = safe_refgo_cleanup(drive)
            except OSError as exc:
                runner.check("cleanup writes", False, repr(exc))
        cleanup_verified = False
        cleanup_state = (None, None, None, None)
        if drive is not None:
            try:
                cleanup_result = verify_safe_refgo_state(drive)
                cleanup_verified = cleanup_result[0]
                cleanup_state = cleanup_result[1:]
            except OSError as exc:
                runner.check("cleanup state verification", False, repr(exc))
        if not cleanup_verified:
            # Keep the application alive long enough for its disconnect watchdog.
            time.sleep(6.0)
            if drive is None:
                try:
                    drive = RefgoClient(DEVICE_IP, verbose=True)
                    drive.connect()
                except OSError as exc:
                    runner.check("watchdog cleanup REFGO connect", False, repr(exc))
            if drive is not None:
                try:
                    cleanup_result = verify_safe_refgo_state(drive, 1.0)
                    cleanup_verified = cleanup_result[0]
                    cleanup_state = cleanup_result[1:]
                except OSError as exc:
                    runner.check("watchdog cleanup verification", False, repr(exc))
        runner.check("safe state verified before stopping script", cleanup_verified,
                     "target=" + str(cleanup_state[0])
                     + " mode=" + str(cleanup_state[1])
                     + " status=" + hex(cleanup_state[2] or 0)
                     + " velocity=" + str(cleanup_state[3]))
        script_stopped = cleanup_verified and stop_script(DEVICE_IP)
        runner.check("uploaded script stopped", script_stopped)
        time.sleep(0.3)
        try:
            probe = socket.create_connection((DEVICE_IP, MODBUS_PORT), 0.5)
            probe.close()
            port_closed = False
        except OSError:
            port_closed = True
        runner.check("final Modbus TCP port 502 closed", port_closed)
        if drive is not None and script_stopped:
            restore_evidence = {}
            for entry in WRITABLE_MAP:
                address, index, subindex, type_code, name = entry
                baseline = parameter_before.get((index, subindex))
                if index == 0x60A4 or baseline is None:
                    continue
                restore_value = baseline
                if index == 0x6040:
                    restore_value = 0
                elif index == 0x6060 or index == 0x60FF:
                    restore_value = 0
                restored = drive.write_object(index, subindex, restore_value)
                readback = drive.read_object(index, subindex)
                if type_code == U32 and readback is not None:
                    readback &= 0xFFFFFFFF
                    restore_value &= 0xFFFFFFFF
                restore_evidence[name] = readback
                runner.check("final restore " + name,
                             restored and readback == restore_value,
                             "expected=" + str(restore_value)
                             + " actual=" + str(readback))
            print("PARAMETER_RESTORE " + repr(restore_evidence))
            safe_refgo_cleanup(drive)
            final_status = drive.read_object(0x6041, 0)
            final_mode = drive.read_object(0x6060, 0)
            final_target_velocity = drive.read_object(0x60FF, 0)
            final_actual_velocity = drive.read_object(0x606C, 0)
            final_position = drive.read_object(0x6064, 0)
            final_profile_velocity = drive.read_object(0x6081, 0)
            final_acceleration = drive.read_object(0x6083, 0)
            final_deceleration = drive.read_object(0x6084, 0)
            final_quickstop = drive.read_object(0x6085, 0)
            print("POSITION_VALUES " + repr(after_position))
            print("CLEANUP_WRITES " + repr(cleanup))
            print("FINAL status=" + hex(final_status or 0)
                  + " mode=" + str(final_mode)
                  + " target_velocity=" + str(final_target_velocity)
                  + " actual_velocity=" + str(final_actual_velocity)
                  + " position=" + str(final_position))
            runner.check("final target velocity zero", final_target_velocity == 0)
            runner.check("final mode zero", final_mode == 0)
            runner.check("final switch-on-disabled", (final_status & 0x006F) == 0x0040,
                         "6041h=" + hex(final_status or 0))
            runner.check("final standstill", abs(final_actual_velocity) <= VELOCITY_STANDSTILL_TOLERANCE,
                         "606Ch=" + str(final_actual_velocity))
            runner.check("saved profile velocity preserved", final_profile_velocity == before.get("profile_velocity"),
                         "before=" + str(before.get("profile_velocity"))
                         + " after=" + str(final_profile_velocity))
            runner.check("saved acceleration preserved", final_acceleration == before.get("acceleration"))
            runner.check("saved deceleration preserved", final_deceleration == before.get("deceleration"))
            runner.check("saved quickstop preserved", final_quickstop == before.get("quickstop_deceleration"))
            drive.close()

    return runner.finish(RESULTS_DIR)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
