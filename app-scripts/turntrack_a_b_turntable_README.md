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

1. Open the drive's **MovingCap CODE** page in a web browser.
2. Select `turntrack_a_b_turntable.py`, upload it, and start the application.
3. Wait until startup and referencing are complete.
4. Open **Setup > IO In** (for the default address:
   [`http://192.168.2.150/io_in.html`](http://192.168.2.150/io_in.html)).
5. Use the **IN Simulator** to set IN1 high, then low again. Each new rising edge
   alternates the target between B and A.

The application can also be controlled with a physical signal connected to IN1.

## Documentation

- [MovingCap CODE](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html)
- [Uploading and running a test program](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/ein-einfaches-testprogramm.html)
- [Input functions and IN Simulator](https://movingcap.de/webmanuals/mc-eth-sw-manual-en/inputfct.html)

> **Safety:** Uploading and running this application enables the drive and physically
> moves the axis. Ensure the turntable can rotate freely between both positions.
