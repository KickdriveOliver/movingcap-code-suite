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

1. Open the drive's **MovingCap CODE** page in a web browser.
2. Select `turntrack_6_slot_turntable.py`, upload it, and start the application.
3. Open **Setup > IO In** (for the default address:
   [`http://192.168.2.150/io_in.html`](http://192.168.2.150/io_in.html)).
4. Use the **IN Simulator** to set IN1 or IN2 high, then low again to create a new
   rising edge:
   - IN2 advances to the next 60° slot.
   - IN1 moves forward to the next 0° position.

The application can also be controlled with physical signals connected to IN1 and IN2.

## Documentation

- [MovingCap CODE](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html)
- [Uploading and running a test program](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/ein-einfaches-testprogramm.html)
- [Input functions and IN Simulator](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/inputfct.html)

> **Safety:** Uploading and running this application enables the drive and physically
> moves the axis. Ensure the turntable can rotate freely.
