# turnTRACK A/B turntable

[`turntrack_a_b_turntable.py`](turntrack_a_b_turntable.py) is a compact MovingCap CODE
example that alternates a turntable between two absolute positions:

- **First IN1 rising edge:** moves to position B (`180°` by default).
- **Next IN1 rising edge:** moves back to position A (`0°` by default).
- **OUT1:** pulses after the commanded target is reached.

At startup, the application enables the drive and references the current position as
zero without moving. On its first run, it installs the example motor and application
parameters defined in the script.

## Quick start

From the repository root:

```bash
python testing/upload_mc_script.py app-scripts/turntrack_a_b_turntable.py --stop-first
```

After the startup delay, pulse physical IN1 or simulate it from host-side Python:

```python
from testing.mctk import RefgoClient, input_mask

with RefgoClient("192.168.2.150") as drive:
    drive.pulse_inputs(input_mask(1))  # move to B
    drive.pulse_inputs(input_mask(1))  # move back to A
```

For the complete functional check:

```bash
python testing/test_turntrack_a_b_turntable.py
```

> **Safety:** Uploading and running this application enables the drive and physically
> moves the axis. Ensure the turntable can rotate freely between both positions.
