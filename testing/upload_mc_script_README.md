# upload_mc_script.py

Small CLI utility to upload and start a **MovingCap CODE** (MicroPython) application
script on a MovingCap Ethernet ETH servo drive, over the drive's HTTP web interface.

It is a thin wrapper around [`mctk.uploader`](mctk/uploader.py) and can be called
from **any current working directory** — the script resolves the `mctk` package
relative to its own file location, not relative to the caller's cwd.

---

## Requirements

* Desktop Python 3 (CPython).
* The [`requests`](https://pypi.org/project/requests/) package.

Install with:

```bash
python -m pip install -r requirements.txt
```

Run that command from the repository root. The root `requirements.txt` covers the
whole `mctk` toolkit and is the only third-party dependency used across its modules
and test scripts.

Your computer also needs an IP address reachable by the target drive (typically
the `192.168.2.x` subnet, e.g. `192.168.2.100`).

---

## Usage

```bash
python upload_mc_script.py SCRIPT_PATH [DEVICE_IP] [options]
```

### Examples

Upload and start a script on the default drive IP (`192.168.2.150`):
```bash
python upload_mc_script.py app-scripts/turntrack_a_b_turntable.py
```

Upload and start on a specific drive IP (positional shortcut):
```bash
python upload_mc_script.py my_script.py 192.168.2.50
```

Upload and start on a specific drive IP (explicit flag):
```bash
python upload_mc_script.py my_script.py --device-ip 192.168.2.50
```

Stop whatever script is currently running before uploading the new one:
```bash
python upload_mc_script.py my_script.py --stop-first
```

Upload only, without starting the script:
```bash
python upload_mc_script.py my_script.py --no-start
```

Call from any directory using an absolute path to the script:
```bash
python C:\repos\movingcap-code-suite\testing\upload_mc_script.py C:\scripts\my_script.py
```

---

## Arguments

| Argument | Description |
| :--- | :--- |
| `SCRIPT_PATH` | Path to the local `.py` MovingCap CODE script to upload (relative paths are resolved against the current working directory). Required. |
| `DEVICE_IP` | Optional positional shortcut for `--device-ip`. |

## Options

| Option | Description |
| :--- | :--- |
| `--device-ip`, `-i IP` | IP address of the target MovingCap drive. Default: `192.168.2.150` |
| `--stop-first` | Stop any currently running script on the drive before uploading the new one. |
| `--no-start` | Upload only; do not start the script afterwards. |
| `--timeout SECONDS` | HTTP request timeout in seconds. Default: `10` |

---

## Exit codes

* `0` — script uploaded (and started, unless `--no-start` was given) successfully.
* `1` — script path not found, or the upload/start HTTP request failed.

---

## Using it as a library

`upload_and_run()` can also be imported directly instead of invoking the CLI:

```python
from upload_mc_script import upload_and_run

ok = upload_and_run("my_script.py", device_ip="192.168.2.50", stop_first=True)
```

Or use the lower-level `mctk.uploader` functions directly (`upload_script`,
`start_script`, `stop_script`) for finer control — see [mctk/uploader.py](mctk/uploader.py).
