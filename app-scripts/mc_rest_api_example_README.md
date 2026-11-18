# MovingCap CODE mc_rest_api_example

[mc_rest_api_example.py](mc_rest_api_example.py) demonstrates a lightweight HTTP/JSON
REST interface running directly on a MovingCap drive on port **8080**.

It is an accessible example showing how to serve status, motor data, and drive commands
over a local network connection using standard MicroPython on MovingCap Ethernet drives.

## Endpoints

Base URL: `http://<device-ip>:8080`.

| Method | Path | Description |
|---|---|---|
| GET | `/api` | API discovery: name, version, and endpoints list |
| GET | `/api/status` | Position, velocity, statusword, mode, motion state, and error flags |
| GET | `/api/motor` | Actual current, velocity, temperature, and calculated power |
| GET | `/api/config` | Configured profile velocity, ramps, soft limits, and timeout |
| GET | `/api/objects/<index>/<subindex>` | Read any numeric object dictionary entry |
| PUT | `/api/objects/<index>/<subindex>` | Write an object dictionary entry (`{"value": 100}`) |
| POST | `/api/refgo` | Execute a raw REFGO command string (`{"command": "TS"}`) |
| POST | `/api/enable` | Enable the drive power stage |
| POST | `/api/disable` | Disable drive power (safe standstill required) |
| POST | `/api/move` | Move to an absolute position (`{"position": 1000, "velocity": 400}`) |
| POST | `/api/velocity` | Start profile velocity mode (`{"velocity": 400}`) |
| POST | `/api/stop` | Quick stop the current motion |
| POST | `/api/continue` | Resume a stopped move |

### Object Addressing
Numeric objects accept decimal, hex with `0x`, or trailing `h`:
- `/api/objects/0x6041/0`
- `/api/objects/6041h/0`
- `/api/objects/24641/0`

## How It Works

- **MicroPython Networking:** Listens on port 8080 using `mcnet.McNet`.
- **DS402 Drive Control:** Uses standard `mcdrive` APIs (`EnableDrive`, `GoPosAbs`, `GoVel`, `StopMotion`, `ContinueMotion`, `PowerQuit`).
- **Object Access:** Directly reads and writes CANopen Object Dictionary entries via `mc.ReadObject()` / `mc.WriteObject()`.
- **HTTP / JSON:** Implements a self-contained, lightweight HTTP parser and flat JSON encoder/decoder without external dependencies.
- **Keep-Alive:** Supports HTTP/1.1 persistent connections (`keep-alive`) for efficient status polling.

## Upload and Testing

From the repository root:

```powershell
# Upload and start the script on the drive:
python testing/upload_mc_script.py app-scripts/mc_rest_api_example.py --device-ip <device-ip> --stop-first

# Run offline unit tests:
python testing/test_mc_rest_api_example.py --offline

# Run live hardware tests:
python testing/test_mc_rest_api_example.py <device-ip>

# Run hardware tests including motion (rotates the free shaft):
python testing/test_mc_rest_api_example.py <device-ip> --motion
```

## Safety Notice
- `move`, `velocity`, `continue`, and generic object writes or REFGO commands can **physically actuate the motor** or energize the power stage.
- Always ensure the axis is clear before issuing motion commands.
- Designed for trusted local automation networks; no TLS or authentication is included.


References: [profile position and scaling](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/positionierbetrieb.html),
[actual values](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/istwerte.html),
[statusword](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/cia402-statusword.html),
and the local [mcdrive](mcdrive.pyi), [mcnet](mcnet.pyi), [REFGO](refgo.pyi) stubs.