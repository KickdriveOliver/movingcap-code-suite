# turnTRACK six-slot turntable

[`turntrack_6_slot_turntable.py`](turntrack_6_slot_turntable.py) is a MovingCap CODE
application for a forward-only rotary table with six equally spaced slots:
`0°, 60°, 120°, 180°, 240°, 300°`.

- **IN1 rising edge:** moves forward to the next `0°` position.
- **IN2 rising edge:** finds the slot nearest the current position and moves forward to
  the following slot.
- **OUT1/OUT2:** default to positioning feedback and drive-status feedback.

On its first run, the application installs example defaults for a turnTRACK 349 with a
35:1 gear and 360° coordinates. Review the parameter lists in the script before using
different hardware.

## Quick start

From the repository root:

```bash
python testing/upload_mc_script.py app-scripts/turntrack_6_slot_turntable.py --stop-first
```

The default drive address is `192.168.2.150`. After startup, pulse physical IN1 or IN2,
or simulate an input from host-side Python:

```python
from testing.mctk import RefgoClient, input_mask

with RefgoClient("192.168.2.150") as drive:
    drive.pulse_inputs(input_mask(2))  # IN2: advance one slot
    drive.pulse_inputs(input_mask(1))  # IN1: move forward to 0°
```

For an automated basic check:

```bash
python testing/test_turntrack_6_slot_turntable.py
```

> **Safety:** Uploading and running this application enables the drive and physically
> moves the axis. Ensure the turntable can rotate freely.
