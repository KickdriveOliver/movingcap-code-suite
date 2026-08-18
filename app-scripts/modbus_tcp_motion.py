#id modbus_tcp_motion.py oh 2026-08-10
# Modbus TCP motion/object gateway for MovingCap CODE.
#
# This example exposes a small Modbus TCP API for basic CiA 402 Profile
# Positioning Mode and Profile Velocity Mode objects. Function 03 reads the
# mapped status/feedback and motion objects; functions 06 and 16 write the
# mapped control and motion objects. The maps use literal Modbus addresses
# and high-word-first order for 32-bit values.
#
# A client connection or request timeout is treated as inactive after
# WATCHDOG_MS. Closing the connection or exceeding that timeout clears the
# target velocity and mode, performs a CiA 402 quick stop, and leaves the
# drive in switch-on-disabled. The same shutdown is used for protocol errors
# and application exit.

import mcnet
import mcdrive as mc
import ustruct
import time

PORT_SETTINGS = "SERVER:502"
MAX_ADU_LENGTH = 260
MAX_BUFFER_LENGTH = 1024
WATCHDOG_MS = 5000
QUICKSTOP_TIMEOUT_MS = 5000

U8 = 0
I8 = 1
U16 = 2
I16 = 3
U32 = 4
I32 = 5

SAFE_DISABLE_IDLE = 0
SAFE_DISABLE_ACTIVE = 1

# The immutable maps contain (Modbus address, object index, subindex, type).
# All 32-bit values use high-word-first Modbus register order.

READ_MAP = (
    (5000, 0x6041, 0, U16),
    (5001, 0x6061, 0, I8),
    (5002, 0x6064, 0, I32),
    (5004, 0x606C, 0, I32),
)

WRITE_MAP = (
    (6000, 0x6040, 0, U16),
    (6001, 0x6060, 0, I8),
    (6002, 0x607A, 0, I32),
    (6004, 0x6081, 0, U32),
    (6006, 0x60FF, 0, I32),
    (6008, 0x6083, 0, U32),
    (6010, 0x6084, 0, U32),
    (6012, 0x6067, 0, U32),
    (6014, 0x6068, 0, U16),
    (6015, 0x607D, 1, I32),
    (6017, 0x607D, 2, I32),
    (6019, 0x60F2, 0, U16),
    (6020, 0x6085, 0, U32),
    (6022, 0x605A, 0, I16),
    (6023, 0x60A4, 0, U32),
)


def start_safe_disable():
    # Quick stop option 2 ramps to standstill, then enters switch-on-disabled.
    mc.WriteObject(0x605A, 0, 2)
    # This can decelerate/stop the axis and remove drive power.
    mc.WriteControl(0x0B)
    return SAFE_DISABLE_ACTIVE, time.ticks_ms()


def step_safe_disable(state, start_time):
    if state != SAFE_DISABLE_ACTIVE:
        return state
    statusword = mc.ReadStatusword()
    if (statusword & 0x006F) == 0x0040:
        mc.WriteObject(0x60FF, 0, 0)
        # Clearing the mode prevents a stale motion mode being reused.
        mc.WriteObject(0x6060, 0, 0)
        return SAFE_DISABLE_IDLE
    if (statusword & 0x0008
            or time.ticks_diff(time.ticks_ms(), start_time) >= QUICKSTOP_TIMEOUT_MS):
        # Fall back to immediate voltage disable if quick stop cannot complete.
        mc.WriteControl(0)
        mc.WriteObject(0x60FF, 0, 0)
        # Clearing the mode prevents a stale motion mode being reused.
        mc.WriteObject(0x6060, 0, 0)
        return SAFE_DISABLE_IDLE
    return state


def type_width(type_code):
    if type_code == U32 or type_code == I32:
        return 2
    return 1


def find_entry_start(entries, address):
    for entry in entries:
        if entry[0] == address:
            return entry
    return None


def find_entry_register(entries, address):
    for entry in entries:
        offset = address - entry[0]
        if offset >= 0 and offset < type_width(entry[3]):
            return entry, offset
    return None


def cached_object_value(entry, snapshots):
    for snapshot in snapshots:
        if snapshot[0] is entry:
            return snapshot[1]
    value = mc.ReadObject(entry[1], entry[2])
    snapshots.append((entry, value))
    return value


def register_value(address, snapshots):
    found = find_entry_register(READ_MAP, address)
    if found is None:
        found = find_entry_register(WRITE_MAP, address)
    if found is None:
        return None
    entry, offset = found
    value = cached_object_value(entry, snapshots)
    type_code = entry[3]
    if type_code == U8 or type_code == I8:
        return value & 0xFF
    if type_width(type_code) == 1:
        return value & 0xFFFF
    if offset == 0:
        return (value >> 16) & 0xFFFF
    return value & 0xFFFF


def signed8(value):
    value = value & 0xFF
    if value >= 0x80:
        return value - 0x100
    return value


def signed16(value):
    value = value & 0xFFFF
    if value >= 0x8000:
        return value - 0x10000
    return value


def words_value(type_code, data):
    if type_width(type_code) == 2:
        high_word, low_word = ustruct.unpack(">HH", data)
        value = ((high_word & 0xFFFF) << 16) | (low_word & 0xFFFF)
        # WriteObject accepts integer32, so preserve unsigned32 bits as signed.
        if value >= 0x80000000:
            value = value - 0x100000000
        return value
    value = ustruct.unpack(">H", data)[0]
    if type_code == I8:
        return signed8(value)
    if type_code == I16:
        return signed16(value)
    if type_code == U8:
        return value & 0xFF
    return value


def write_entry(entry, data):
    # Mapped writes can alter power, motion commands, limits, or motion profiles.
    value = words_value(entry[3], data)
    return mc.WriteObject(entry[1], entry[2], value) == 0


def exception_pdu(function, code):
    return ustruct.pack(">BB", function | 0x80, code)


def process_pdu(pdu):
    if len(pdu) < 1:
        return exception_pdu(0, 3), False

    function = pdu[0]
    if function == 3:
        if len(pdu) != 5:
            return exception_pdu(function, 3), False
        address, quantity = ustruct.unpack(">HH", pdu[1:5])
        if quantity < 1 or quantity > 125:
            return exception_pdu(function, 3), False
        values = b""
        snapshots = []
        for register_address in range(address, address + quantity):
            value = register_value(register_address, snapshots)
            if value is None:
                return exception_pdu(function, 2), False
            values = values + ustruct.pack(">H", value)
        return ustruct.pack(">BB", function, len(values)) + values, True

    if function == 6:
        if len(pdu) != 5:
            return exception_pdu(function, 3), False
        address, value = ustruct.unpack(">HH", pdu[1:5])
        entry = find_entry_start(WRITE_MAP, address)
        if entry is None or type_width(entry[3]) != 1:
            return exception_pdu(function, 2), False
        result = write_entry(entry, ustruct.pack(">H", value))
        if result:
            return pdu, True
        return exception_pdu(function, 4), False

    if function == 16:
        if len(pdu) < 6:
            return exception_pdu(function, 3), False
        address, quantity, byte_count = ustruct.unpack(">HHB", pdu[1:6])
        if quantity < 1 or byte_count != quantity * 2 or len(pdu) != 6 + byte_count:
            return exception_pdu(function, 3), False
        entry = find_entry_start(WRITE_MAP, address)
        if entry is None:
            return exception_pdu(function, 2), False
        if quantity != type_width(entry[3]):
            return exception_pdu(function, 3), False
        result = write_entry(entry, pdu[6:])
        if result:
            return ustruct.pack(">BHH", function, address, quantity), True
        return exception_pdu(function, 4), False

    return exception_pdu(function, 1), False


def make_adu(transaction_id, unit_id, pdu):
    return (ustruct.pack(">HHH", transaction_id, 0, len(pdu) + 1)
            + ustruct.pack(">B", unit_id) + pdu)


def send_all(server, data):
    sent = 0
    while sent < len(data):
        count = server.write(data[sent:])
        if count is None or count <= 0:
            return False
        sent = sent + count
    return True


server = mcnet.McNet(PORT_SETTINGS)
buffer = b""
was_connected = False
empty_read_seen = False
last_valid_request = time.ticks_ms()
watchdog_done = True
safe_disable_state, safe_disable_start_time = start_safe_disable()

while True:
    connected = server.is_connected()
    if was_connected and not connected:
        safe_disable_state, safe_disable_start_time = start_safe_disable()
        buffer = b""
        empty_read_seen = True
        watchdog_done = True
    was_connected = connected

    if connected:
        waiting = server.in_waiting()
        if waiting < 0:
            safe_disable_state, safe_disable_start_time = start_safe_disable()
            server.close()
            time.sleep_ms(20)
            server = mcnet.McNet(PORT_SETTINGS)
            buffer = b""
            was_connected = False
            empty_read_seen = False
            watchdog_done = True
        else:
            chunk = server.read(256)
            if chunk is not None and len(chunk) == 0:
                if not empty_read_seen:
                    safe_disable_state, safe_disable_start_time = start_safe_disable()
                buffer = b""
                empty_read_seen = True
                watchdog_done = True
            elif chunk:
                empty_read_seen = False
                buffer = buffer + chunk
                if len(buffer) > MAX_BUFFER_LENGTH:
                    safe_disable_state, safe_disable_start_time = start_safe_disable()
                    server.close()
                    time.sleep_ms(20)
                    server = mcnet.McNet(PORT_SETTINGS)
                    buffer = b""
                    was_connected = False
                    empty_read_seen = False
                    watchdog_done = True

        while len(buffer) >= 7 and server.is_connected():
            transaction_id, protocol_id, length = ustruct.unpack(">HHH", buffer[0:6])
            if protocol_id != 0 or length < 2 or length > (MAX_ADU_LENGTH - 6):
                safe_disable_state, safe_disable_start_time = start_safe_disable()
                server.close()
                time.sleep_ms(20)
                server = mcnet.McNet(PORT_SETTINGS)
                buffer = b""
                was_connected = False
                empty_read_seen = False
                watchdog_done = True
                break
            adu_length = 6 + length
            if len(buffer) < adu_length:
                break
            unit_id = buffer[6]
            pdu = buffer[7:adu_length]
            buffer = buffer[adu_length:]
            response_pdu, valid = process_pdu(pdu)
            if not send_all(server, make_adu(transaction_id, unit_id, response_pdu)):
                break
            if valid:
                last_valid_request = time.ticks_ms()
                watchdog_done = False
                # A valid master request resumes control immediately. Any
                # commands already issued by the quick stop remain effective
                # until the master changes them via mapped objects.
                safe_disable_state = SAFE_DISABLE_IDLE

        if not watchdog_done and time.ticks_diff(time.ticks_ms(), last_valid_request) >= WATCHDOG_MS:
            safe_disable_state, safe_disable_start_time = start_safe_disable()
            watchdog_done = True

    safe_disable_state = step_safe_disable(safe_disable_state,
                                           safe_disable_start_time)

    time.sleep_ms(2)
