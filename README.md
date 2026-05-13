# Moqui Device

[![license](http://img.shields.io/badge/license-CC0%201.0%20Universal-blue.svg)](https://github.com/moqui/moqui-device/blob/master/LICENSE.md)

Moqui Device is a Moqui Framework component that provides a data model for physical device management, industrial connectivity, and AI/ML compute orchestration. It models devices as digital twins, defines how to communicate with them (fieldbus protocols, message brokers, REST gateways), and provides a rule/configuration engine for governing device behavior over time.

## Contents

| Domain | Entities |
|---|---|
| Digital Twin | `Device`, `PhysicalDevice`, `DeviceGroup`, `DeviceGroupMember`, `DeviceContent`, `DeviceStats`, `DeviceLog` |
| Math Binding | `DeviceMathModel` — binds a `Device` to a `moqui.math.MathModel` for training, inference, simulation, or monitoring |
| Connectivity | `DeviceConnection` — Modbus TCP, OPC UA, EtherNet/IP, CANopen, PROFINET, BACnet/IP, KNXnet/IP, MTConnect, Logix CIP/EIP |
| Requests | `DeviceRequest`, `DeviceRequestItem` — Read, Write, ConfigWrite, Subscribe (Event / StateChange / Cyclic), Unsubscribe, ContentTransfer, Browse, Discovery |
| Configuration | `DeviceConfig`, `DeviceConfigSet`, `DeviceConfigSetMember` |
| Rules | `DeviceRuleSet`, `DeviceRule` — apply, assert, and validate configurations; supports hierarchical rule sets and priority ordering |
| Trajectory Binding | `TrajectoryAxisBinding` — maps `moqui.math.Trajectory` axes to device parameters (position, velocity, acceleration, jerk, snap) |
| Dashboards | `DeviceDashboard` |

### Device status flows

Two built-in status flows are provided as seed data:

- **DeviceBasicStatusFlow** — `Disabled → Standstill → Homing / Run / SynchronizedRun → Stopping → ErrorStop`
- **DeviceAdvancedStatusFlow** — adds `OperationInhibited` and `EmergencyStop`

Both follow the IEC 61131-3 / PLCopen Motion Control state machine conventions.

### Device type taxonomy

`DeviceData.xml` contains an extensive taxonomy of device types aligned with MTConnect, ISO 9787, and ISO 8373: controllers (PLC, PAC, CNC, motion, robot), drives, sensors, actuators, RFID, network devices, IoT gateways, computing servers (GPU, HPC, twin servers), and device group types for clusters, manufacturing cells, HVAC, and conveyor systems.

## Services

| Service | Description |
|---|---|
| `moqui.device.DeviceServices.run#DeviceRequest` | Dispatches a single `DeviceRequest` to its configured implementation service |
| `moqui.device.DeviceServices.run#DeviceRequestGroup` | Runs all requests in a named group; designed to be called as a scheduled service |
| `moqui.device.DeviceServices.run#DeviceRequestInternal` | Interface that driver components (e.g. `moqui-plc4j`) must implement |
| `moqui.device.DeviceServices.send#DeviceNotification` | Sends a Moqui notification for a device event |
| `moqui.device.DeviceGatewayServices.run#GatewayDeviceRequest` | Dispatches requests via the `moqui-device-gateway` REST API (MQTT / OPC UA) |
| `moqui.device.DeviceGatewayServices.transfer#DeviceContent` | Streams a file (G-Code, firmware, recipe) to a device via the gateway SFTP/file endpoint |

## Service layer — Python ecosystem via moqui-jep

`moqui.device` follows the same philosophy as `moqui.math`: it defines entities, seed data, and the service interfaces only. Driver implementations that communicate with physical devices over fieldbus protocols (Modbus, OPC UA, EtherNet/IP, CANopen, etc.) are provided by separate components such as **moqui-plc4j** (Apache PLC4X, JVM) or Python libraries (python-opcua, pymodbus, python-snap7, etc.) embedded via **moqui-jep**. Control algorithms and ML inference services likewise run through moqui-jep using NumPy, SciPy, JAX, or python-control.

## Dependencies

- **moqui-math** `1.0.0`

## Install

    ./gradlew getComponent -Pcomponent=moqui-device
