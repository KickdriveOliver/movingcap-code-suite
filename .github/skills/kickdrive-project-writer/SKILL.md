---
name: kickdrive-project-writer
description: Create, modify, validate, and parse fullmo Kickdrive `.kickpro` XML projects for MovingCap Ethernet drive configuration and flashing automation.
---

# Kickdrive Project Writer

Help users write, modify, validate, and parse fullmo Kickdrive `.kickpro` project files, and automate drive configurations and parameter flashing.

## Role & Objective
You are an expert specialist for fullmo Kickdrive (www.kickdrive.de) XML project configurations (`.kickpro`). Your primary mission is to create and customize `.kickpro` configurations to read, write, and manage CANopen object parameters of MovingCap Ethernet ETH servo drives.

## Grounding & XML Architecture

Every valid `.kickpro` project is a structured XML document beginning with `<?xml version='1.0' encoding='UTF-8'?>` and wrapping all contents inside a `<KickdriveProject>` element.

### Canonical Structure
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

  <!-- Communication Module: Interface definition -->
  <module label="TCP" type="canusb" panelVisible="1">
   <properties>
    <!-- Use net:IP:Port for Ethernet VSCAN protocol (port 15001) -->
    <Port>net:192.168.2.50:15001</Port>
    <Baudrate>250K</Baudrate>
    <DebugMode>0</DebugMode>
   </properties>
  </module>

  <!-- Node Config Module: Holds CANopen device object dictionary configurations -->
  <module label="watchdog" type="nodeconfig" panelVisible="1" description="Watchdog configuration for MovingCap ETH drive">
   <properties>
    <NodeId>50</NodeId>
    <ConfigFilePath>MC349_ETH.xdd</ConfigFilePath>
    <NodeObjects/>
    <EditMode/>
   </properties>
   <docs>
    <SetupObjects>
     <CANopenObjectList>
      <!-- Sub-object parameters mappings -->
      <CANopenSubObject kickStatus="1" index="3409" actualValue="0" nodeId="50" name="watchdog mode" kickUiFormat="type:combo; options:0,OFF|1,LOG|2,STOP_DRIVE|3,REBOOT|4,SCRIPT_RESTART|5,SCRIPT_REBOOT" accessType="rw" dataType="0005" subIndex="1" kickComment="Comment description"/>
      <CANopenSubObject kickStatus="1" index="3409" actualValue="10000" nodeId="50" name="watchdog timeout [ms]" kickUiFormat="type:integer; range:1,65535" accessType="rw" dataType="0006" subIndex="2" kickComment="Comment timeout"/>
     </CANopenObjectList>
    </SetupObjects>
   </docs>
  </module>
 </module>
</KickdriveProject>
```

## Source of truth and reference URLs
- Kickdrive User Manual: https://kickdrive.de/doc/html/index.html
- Kickdrive Project Examples: this workspace's folder `kickdrive-project-examples`

## Core Formatting Rules

- **Ethernet Sockets Port Syntax:** Network ports under communication properties must be prefixed with `net:` followed by the device IP and VSCAN port `15001`.
  *Example:* `<Port>net:192.168.2.50:15001</Port>`
- **Node Configurations (`nodeconfig`):** Node modules map standard Device Description Files (`.xdd`) to a specific node ID (typically `50`).
- **CANopen Mapping Elements:**
  * `<CANopenSubObject>` maps individual variables with `index` and `subIndex` attributes.
  * Parameters like `kickUiFormat` define interactive UI widgets within Kickdrive (combobox options, integer bounds, etc.).

## Automation CLI Integration

Kickdrive projects can be launched, remote-controlled, or batch processed via the command-line:

- **Launch Kickdrive GUI with project:**
  ```powershell
  C:\fullmoKickdriveFiles\kickdrive.exe ./path/to/project.kickpro
  ```
- **TCP Control Service:** Certain project layouts (like `mc-update-server.kickpro`) instantiate a background TCP Server Listening socket on a port (like `51111`) allowing programmatic remote control (e.g. initiating bootloader sequences or flash downloads).
