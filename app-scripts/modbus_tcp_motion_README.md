# Minimal Modbus TCP motion API

[`modbus_tcp_motion.py`](modbus_tcp_motion.py) is a general-purpose MovingCap CODE
application for exposing a minimal Modbus TCP interface. It maps
selected CiA-402 objects to holding registers and supports profile position mode and
profile velocity mode. It does not use PDOs.

The server listens on TCP port `502` and accepts one Modbus TCP client at a time.
Register addresses below are literal PDU addresses, not `4xxxx` display notation.
All 32-bit values use high-word-first register order.

## Register map

### Read holding registers

| Register(s) | CANopen object | Exact type | Description / unit |
| --- | --- | --- | --- |
| `5000` | `6041h:00h` | `u16` | Statusword |
| `5001` | `6061h:00h` | `i8` low byte | Mode display |
| `5002-5003` | `6064h:00h` | `i32` | Actual position, configured position units |
| `5004-5005` | `606Ch:00h` | `i32` | Actual velocity: rotary rev/min; linear configured position units/s |

### Writable holding registers

Function 03 reads these registers as well as the feedback block.

| Register(s) | CANopen object | Exact type | Description / unit |
| --- | --- | --- | --- |
| `6000` | `6040h:00h` | `u16` | Controlword |
| `6001` | `6060h:00h` | `i8` low byte | Operation mode |
| `6002-6003` | `607Ah:00h` | `i32` | Target position, configured position units |
| `6004-6005` | `6081h:00h` | `u32` | Profile velocity: rotary rev/min; linear configured position units/s |
| `6006-6007` | `60FFh:00h` | `i32` | Target velocity: rotary rev/min; linear configured position units/s |
| `6008-6009` | `6083h:00h` | `u32` | Profile acceleration: rotary 100 rev/min²; linear 1000 × configured position units/s² |
| `6010-6011` | `6084h:00h` | `u32` | Profile deceleration, same units as `6083h` |
| `6012-6013` | `6067h:00h` | `u32` | Position window, configured position units |
| `6014` | `6068h:00h` | `u16` | Position-window time, ms |
| `6015-6016` | `607Dh:01h` | `i32` | Software minimum position limit, configured position units |
| `6017-6018` | `607Dh:02h` | `i32` | Software maximum position limit, configured position units |
| `6019` | `60F2h:00h` | `u16` | Positioning option code (bit-coded) |
| `6020-6021` | `6085h:00h` | `u32` | Quick-stop deceleration, same units as `6083h` |
| `6022` | `605Ah:00h` | `i16` | Quick-stop option code |
| `6023-6024` | `60A4h:00h` | `u32` | Profile jerk: linear 1000 × configured position units/s³; model support required |

On RABBIT-controller products, writing profile acceleration `6083h` also sets profile
deceleration `6084h`. RABBIT profile positioning uses `60A4h` jerk; support is
model/firmware dependent. In particular, the tested MC349 reports `60A4h` unsupported,
so a write returns Modbus exception `04` rather than implying positive jerk support.

## Supported Modbus functions

- Function `03`: Read holding registers from either the `5000` feedback block or the
  contiguous `6000-6024` writable/readback block. Reads may cross mapped entries.
- Function `06`: Write one complete one-register writable entry.
- Function `16` (`10h`): Write one complete mapped value. 32-bit values must be written
  as both words in one request. Partial and multi-object writes are rejected.

The server echoes the transaction and unit identifiers. Unsupported functions, unmapped
addresses, invalid quantities, and failed object writes return standard Modbus exception
codes.

## Safety behavior

Writing the controlword, operation mode, target position, profile velocity, or target
velocity can enable the drive or move the axis.

The application applies a fail-safe shutdown:

- At startup, it configures CiA-402 quick-stop option `605Ah = 2`.
- On TCP disconnect or five seconds without a valid request, it issues controlword
  `0Bh`, which ramps down using the quick-stop deceleration and transitions to
  switch-on-disabled.
- It waits up to five seconds for switch-on-disabled, then uses controlword `0` as a
  bounded fallback if necessary.
- It clears target velocity and operation mode after the stop sequence.

Ensure the rotary axis can move freely before enabling the drive.

## Quick start

1. Confirm the turnTRACK 349 is connected at `192.168.2.150` and the axis is safe to
   rotate.
2. Upload and start the script from the repository root:

```text
   python testing/upload_mc_script.py app-scripts/modbus_tcp_motion.py --stop-first
```

3. Connect a Modbus TCP client to `192.168.2.150:502`.
4. Use the register map above to perform the CiA-402 startup sequence:
    - Profile position: write mode `1`, controlwords `6`, `7`, `15`, then target position
     and controlword `95` for a relative setpoint.
    - Profile velocity: write mode `3`, target velocity `0`, controlwords `6`, `7`, `15`,
     then write the signed target velocity to `6006-6007`.
5. Before stopping the script, perform and verify a safe shutdown:
    - Write quick-stop option `2` to `6022`.
    - Write controlword `0Bh` to `6000`.
    - Poll statusword `5000` until `(statusword & 006Fh) == 0040h`
      (switch-on-disabled).
    - Write target velocity `0` to `6006-6007` and operation mode `0` to `6001`.
6. Stop the script only after switch-on-disabled and standstill are confirmed. Closing the
   client or leaving it inactive also starts the five-second application watchdog, but
   stopping the script itself does not execute the shutdown sequence.

## Verification

The hardware integration test exercises the register map, fragmented and coalesced TCP
frames, Modbus exceptions, connection interruption, the inactivity watchdog, profile
position motion, and profile velocity motion:

```text
python testing/test_modbus_tcp_motion.py 192.168.2.150
```

This test enables the drive and physically rotates the approved freely rotating axis.
It always attempts to clear target velocity, quick-stop/disable the drive, clear the
operation mode, stop the uploaded script, and verify the final state through REFGO.

## References

- [MovingCap CODE](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html)
- [MovingCap `mcdrive` documentation](https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/mcdrive_pyi.txt)
- [Positioning mode parameters](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/positionierbetrieb.html)
- [Velocity mode parameters](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/drehzahlbetrieb.html)
- [MovingCap RABBIT mode and profile jerk](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcap-rabbit---betriebsart.html)
