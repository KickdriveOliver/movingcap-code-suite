# Modbus TCP Verification with modpoll

This guide describes how to verify the [`modbus_tcp_motion.py`](../app-scripts/modbus_tcp_motion.py)
MovingCap CODE script using **`modpoll`**, a free, standalone Modbus CLI master utility provided by ProconX.

---

## 1. Downloading `modpoll`

`modpoll` is a free, lightweight command-line tool for Windows (no installer required).

* **Download Page**: [https://www.modbusdriver.com/modpoll.html](https://www.modbusdriver.com/modpoll.html)
* **Direct Zip Download**: [https://www.modbusdriver.com/downloads/modpoll.zip](https://www.modbusdriver.com/downloads/modpoll.zip)

### Setup
1. Download `modpoll.zip` from the link above.
2. Extract `modpoll.exe` (found inside the `win32` or `x86_64` directory of the zip).
3. Place `modpoll.exe` into the `testing/` directory of this workspace, or add its location to your Windows `%PATH%`.

---

## 2. Automated Verification Script

An automated Python script is provided in `testing/verify_modbus_tcp_modpoll.py`.

### How to Run

From a terminal inside the `testing/` directory:

```bash
python verify_modbus_tcp_modpoll.py [DEVICE_IP]
```

Or from the repository root:

```bash
python testing/verify_modbus_tcp_modpoll.py 192.168.2.150
```

### What the script does

1. **Uploads and starts drive script**: Calls `upload_mc_script.py` to stop any currently running script and start `app-scripts/modbus_tcp_motion.py` on the target drive (`192.168.2.150:502`).
2. **Checks for `modpoll.exe`**: Confirms `modpoll.exe` is available locally or in PATH.
3. **Reads Feedback Block**: Polling PDU registers `5000–5005` (Statusword, Mode display, Actual position, Actual velocity).
4. **Writes Operation Mode**: Sets operation mode (`6060h`) to `1` (Profile Position Mode).
5. **Writes 32-bit Target Position**: Writes target position `1000` (`607Ah`) as a 32-bit integer across two registers.
6. **Writes Controlword**: Sends CiA-402 Shutdown command (`0x0006` -> `6040h`).

Each `modpoll -1` invocation creates a separate one-request TCP connection. The verifier
does not delay successful calls. It retries an idempotent command up to three times with a
short backoff if `modpoll` reports a transient connection failure while Windows and the
utility recycle consecutive sockets.

---

## 3. Register Addressing Note (`modpoll` vs. PDU)

`modbus_tcp_motion.py` uses **0-based PDU addresses** as defined in the Modbus protocol specification.  
`modpoll` uses **1-based Modbus reference notation** (`40001` format / offset 1).

| PDU Address (`modbus_tcp_motion.py`) | `modpoll` Reference Address (`-r`) | Description | Type |
| :--- | :--- | :--- | :--- |
| `5000` | `5001` | Statusword (`6041h`) | `u16` |
| `5001` | `5002` | Mode display (`6061h`) | `i8` |
| `5002–5003` | `5003` | Actual position (`6064h`) | `i32` (`-t 4:int`) |
| `5004–5005` | `5005` | Actual velocity (`606Ch`) | `i32` (`-t 4:int`) |
| `6000` | `6001` | Controlword (`6040h`) | `u16` |
| `6001` | `6002` | Operation mode (`6060h`) | `i8` |
| `6002–6003` | `6003` | Target position (`607Ah`) | `i32` (`-t 4:int`) |
| `6006–6007` | `6007` | Target velocity (`60FFh`) | `i32` (`-t 4:int`) |

---

## 4. Manual `modpoll` CLI Commands

If you want to run `modpoll` commands manually:

### Read Status & Feedback (Registers 5000–5005)
```cmd
modpoll -m tcp -p 502 -1 -r 5001 -c 6 192.168.2.150
```

### Write Operation Mode = 1 (Profile Position)
```cmd
modpoll -m tcp -p 502 -1 -r 6002 192.168.2.150 1
```

### Write 32-bit Target Position = 1000
```cmd
modpoll -m tcp -p 502 -1 -t 4:int -r 6003 192.168.2.150 1000
```

### Write Controlword = 6 (Shutdown)
```cmd
modpoll -m tcp -p 502 -1 -r 6001 192.168.2.150 6
```

### Continuous Polling Loop (Watchdog Keep-Alive)
`modbus_tcp_motion.py` has a 5-second watchdog (`WATCHDOG_MS = 5000`). To keep the connection alive and continuously monitor feedback every 1000 ms:
```cmd
modpoll -m tcp -p 502 -r 5001 -c 6 -l 1000 192.168.2.150
```
