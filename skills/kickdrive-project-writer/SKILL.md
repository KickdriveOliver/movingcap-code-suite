---
name: kickdrive-project-writer
description: Create, modify, validate, and parse fullmo Kickdrive `.kickpro` XML projects for MovingCap Ethernet ETH servo drive configuration and parameter flashing. Companion to the MovingCap CODE (MicroPython) skill — this covers drive configuration, not on-drive scripts.
---

# Kickdrive Project Writer

Help users write, modify, validate, and parse fullmo Kickdrive `.kickpro` project files, and
automate MovingCap Ethernet ETH drive configuration and CANopen parameter flashing.

## Scope — how this relates to MovingCap CODE
This is a **companion** skill, distinct from
[`movingcap-code-python-writer`](../movingcap-code-python-writer/SKILL.md):
- **Kickdrive `.kickpro`** (this skill) = host-side **drive configuration** — reading, writing,
  and flashing CANopen object-dictionary parameters over Ethernet, driven from the fullmo
  Kickdrive tool. It does **not** run on the drive.
- **MovingCap CODE** (the other skill) = **MicroPython application logic that runs on the drive**.

Use this skill when the user asks about `.kickpro` files, Kickdrive, CANopen object/parameter
configuration, node configs, `.xdd` device descriptions, or automated flashing.

## Role & objective
You are a specialist for fullmo Kickdrive (https://www.kickdrive.de) XML project configurations
(`.kickpro`). Your primary mission is to create and customize `.kickpro` configurations that
read, write, and manage the CANopen object parameters of MovingCap Ethernet ETH servo drives.

---

## 1. Grounding & XML architecture

Every valid `.kickpro` project is a structured XML document beginning with
`<?xml version='1.0' encoding='UTF-8'?>` and wrapping all contents inside a
`<KickdriveProject>` element.

### Canonical structure
```xml
<?xml version='1.0' encoding='UTF-8'?>
<KickdriveProject>
 <module label="MovingCap Support" type="project" panelVisible="0" description="Description">
  <docs>
   <default>
    <html>
     <head><title>Title</title></head>
     <body>
      <h1>Header</h1>
      <p>Prose documentation notes go here.</p>
     </body>
    </html>
   </default>
  </docs>

  <!-- Communication module: interface definition -->
  <module label="TCP" type="canusb" panelVisible="1">
   <properties>
    <!-- Use net:IP:Port for Ethernet VSCAN protocol (port 15001) -->
    <Port>net:192.168.2.50:15001</Port>
    <Baudrate>250K</Baudrate>
    <DebugMode>0</DebugMode>
   </properties>
  </module>

  <!-- Node config module: holds CANopen device object-dictionary configurations -->
  <module label="watchdog" type="nodeconfig" panelVisible="1" description="Description">
   <properties>
    <NodeId>50</NodeId>
    <ConfigFilePath>mcslave_multi_turn.xdd</ConfigFilePath>
    <NodeObjects/>
    <EditMode/>
   </properties>
   <docs>
    <SetupObjects>
     <CANopenObjectList>
      <!-- Sub-object parameter mappings -->
      <CANopenSubObject kickStatus="1" index="3409" actualValue="0" nodeId="50" name="watchdog mode" kickUiFormat="type:combo; options:0,OFF|1,LOG|2,STOP_DRIVE|3,REBOOT|4,SCRIPT_RESTART|5,SCRIPT_REBOOT" accessType="rw" dataType="0005" subIndex="1" kickComment="Comment description"/>
      <CANopenSubObject kickStatus="1" index="3409" actualValue="10000" nodeId="50" name="watchdog timeout [ms]" kickUiFormat="type:integer; range:1,65535" accessType="rw" dataType="0006" subIndex="2" kickComment="Comment timeout"/>
     </CANopenObjectList>
    </SetupObjects>
   </docs>
  </module>
 </module>
</KickdriveProject>
```

---

## 2. Core formatting rules

- **Ethernet socket port syntax:** network ports under communication properties must be prefixed
  with `net:` followed by the device IP and the VSCAN port `15001`.
  *Example:* `<Port>net:192.168.2.50:15001</Port>`. Replace the IP with your drive's address
  (examples in this suite use `192.168.2.150`; use whatever address the drive is configured for).
- **Node configurations (`nodeconfig`):** node modules map a standard device description file
  (`.xdd`) to a specific node ID (typically `50`).
- **CANopen mapping elements:**
  - `<CANopenSubObject>` maps individual variables via `index` and `subIndex` attributes.
  - `kickUiFormat` defines the interactive UI widget shown in Kickdrive (combobox options,
    integer bounds, etc.).
- **Data types:** the `dataType` attribute uses CANopen type codes (e.g. `0005` = UNSIGNED8,
  `0006` = UNSIGNED16). Match `dataType` to the object's real type; never guess.

---

## 3. Automation / CLI integration

Kickdrive projects can be launched, remote-controlled, or batch processed from the command line:

- **Launch Kickdrive GUI with a project:**
  ```powershell
  C:\fullmoKickdriveFiles\kickdrive.exe ./path/to/project.kickpro
  ```
- **TCP control service:** certain project layouts (e.g. `mc-update-server.kickpro`) start a
  background TCP server socket on a port (such as `51111`), allowing programmatic remote control
  — for example initiating bootloader sequences or flash downloads.

---

## 4. Constraints

- Only use element names, attributes, and value formats you can confirm from an existing
  `.kickpro` example, the device's `.xdd`, or the Kickdrive documentation — do not invent
  attributes or object indices.
- Match `index`/`subIndex`/`dataType`/`accessType` to the target device's object dictionary.
  Never guess object numbers, ranges, or units.
- Flashing parameters changes drive behavior. Flag any action that writes to or reboots a drive.

## Reference resources
- fullmo Kickdrive: https://www.kickdrive.de
- MovingCap product & company (Fullmo Drives GmbH): https://movingcap.de
- MovingCap CODE manual (for the on-drive MicroPython side): https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html
- Example & demo collection: https://github.com/KickdriveOliver/movingcap
