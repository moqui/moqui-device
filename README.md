# Moqui Device

[![license](http://img.shields.io/badge/license-CC0%201.0%20Universal-blue.svg)](https://github.com/moqui/moqui-device/blob/master/LICENSE.md)

Moqui Device is a Moqui Framework component that provides a **complete, universal
data model for physical devices (PLC, Drive/Inverter, remote IO, IoT devices, etc.)** — the dual of [moqui-math](https://github.com/moqui/moqui-math).
It models devices as digital twins, defines how to communicate with them
(fieldbus protocols, message brokers, REST gateways), and governs their behaviour
over time through a rule and configuration engine.

A math model cannot run without a device; a device cannot be meaningfully
described without modelling what it computes. `moqui-device` is the device half
of that pairing — the single, auditable source of truth for what a device *is*,
what it *runs*, and what it *did*.

## Trajectories and discrete-event systems

A device's behaviour over time falls into one of two forms, and the model covers
both. Either it is a **trajectory** — a continuous path through a state space — or
it is a **discrete-event system (DES)**, a sequence of state transitions fired by
events. A robot arm moving through space and a thermodynamic process following a
temperature profile are trajectories; a batch advancing through its phases or an
industrial bioprocess stepping between operating states is a DES.

The math/device duality captures the continuous case directly:
`moqui.math.Trajectory` describes the path, and `TrajectoryAxisBinding` maps its
axes (position, velocity, acceleration, jerk, snap) onto the concrete parameters
of the device that executes it — a servo axis or a temperature ramp alike. The
discrete case is captured by the device status flows (below), where state and
transition are the modelling primitives. The same component therefore lets you
model, command, log, and audit both how a device *moves* and how it *switches*.

## Contents

| Domain | Entities |
|---|---|
| Digital Twin | `Device`, `PhysicalDevice`, `DeviceGroup`, `DeviceGroupMember`, `DeviceContent`, `DeviceStats`, `DeviceLog` |
| Math Binding | `DeviceMathModel` — binds a `Device` to a `moqui.math.MathModel` for training, inference, simulation, or monitoring |
| Connectivity | `DeviceConnection` — Modbus TCP, OPC UA, EtherNet/IP, CANopen, PROFINET, BACnet/IP, KNXnet/IP, MTConnect, Logix CIP/EIP |
| Requests | `DeviceRequest`, `DeviceRequestItem` — Read, Write, ConfigWrite, Subscribe (Event / StateChange / Cyclic), Unsubscribe, ContentTransfer, Browse, Discovery |
| Configuration | `DeviceConfig`, `DeviceConfigSet`, `DeviceConfigSetMember` — reusable recipes, drive macros, and static configuration packages. `DeviceConfigSet` is reserved for device groups and system/subsystem configuration baselines, modelled along ISA-88 / IEC 61512 lines |
| Rules | `DeviceRuleSet`, `DeviceRule` — apply, assert, validate, and orchestrate `DeviceConfig` over devices or compatible groups, and `DeviceConfigSet` over device groups, subsystems, production cells, or plants; priority models the logical system-engineering phase |
| FSM definition (moqui-framework `BasicEntities.xml`) | `StatusType`, `StatusItem`, `StatusFlow`, `StatusFlowItem`, `StatusFlowTransition` — data-driven definition of the finite state machines that govern device behaviour |
| Trajectory Binding | `TrajectoryAxisBinding` — maps `moqui.math.Trajectory` axes to device parameters (position, velocity, acceleration, jerk, snap) |
| Dashboards | `DeviceDashboard` |

### Device status flows, and why automation reduces to FSMs

Two built-in status flows are provided as seed data:

- **DeviceBasicStatusFlow** — `Disabled → Standstill → Homing / Run / SynchronizedRun → Stopping → ErrorStop`
- **DeviceAdvancedStatusFlow** — adds `OperationInhibited` and `EmergencyStop`

Both follow the IEC 61131-3 / PLCopen Motion Control state-machine conventions.
These status flows are not only documentation: combined with the device model
they are the source from which [moqui-plc](https://github.com/moqui/moqui-plc)
generates the FSM logic that runs on the controller, defined data-driven through
the `StatusType`, `StatusItem`, `StatusFlow`, `StatusFlowItem`, and
`StatusFlowTransition` entities of moqui-framework's `BasicEntities.xml`.

The architectural reason this works is worth stating, because it is the central
design choice of the whole stack. The reusable components — `Actuator`,
`ActuatorGroup`, `Axis`, `AxisGroup`, `SignalMgmt` — form a **Hardware
Abstraction Layer**. Once the messy device-level detail (handshakes, motion
function blocks, signal conditioning) is hidden behind that HAL, the *behaviour*
of a machine or process can be expressed as a **finite state machine**: a small
set of states, a set of input and output symbols, and the transition and output
functions between them.

This is not a loose analogy. An FSM is a precise mathematical object — the
ordered quintuple (input alphabet, output alphabet, set of states, next-state
function, output function) familiar from logic-network and automata theory.
Expressing automation problems in this form gives them a **solid mathematical
basis**: the model is finite, enumerable, and analysable. Bringing this
hardware-design discipline — the methods of synchronous logic networks — into the
software layer is what makes the approach valuable beyond convenience. Because the
state space and transitions are explicit and finite, the generated code can be
**tested and validated as a mathematical object**: every state reachable, every
transition exercised, every output checked against the specification. The model
that defines the FSM is the same model against which its test suite is built.

The two flows above are the built-in starting points; real machines extend and
compose them, and the HAL keeps even complex coordinated systems expressible as
FSMs over abstracted components rather than as ad hoc procedural code.

### Device type taxonomy

`DeviceData.xml` contains an extensive taxonomy of device types aligned with
MTConnect, ISO 9787, and ISO 8373: controllers (PLC, PAC, CNC, motion, robot),
drives, sensors, actuators, RFID, network devices, IoT gateways, computing
servers (GPU, HPC, twin servers), and device group types for clusters,
manufacturing cells, HVAC, and conveyor systems.

## Recipes, batch management, and system engineering

Industrial configuration is not only a list of parameters on one device. In a
real plant, the same recipe or drive macro may be loaded into many compatible
controllers, drives, instruments, or machine modules. A commissioning procedure
may apply different configuration packages to different subsystems in a precise
logical order. After commissioning, operators or service technicians may still
change some values manually. The model therefore separates **declared recipes**
from the **live state** of each device, and separates **static configuration
packages** from **operational/system-engineering rule sets**.

The key entities are:

| Entity | Plain meaning | Typical industrial analogy |
|---|---|---|
| `ParameterDef` | Definition of one parameter: name, type, unit, bounds, meaning | One field in a PLC recipe definition or drive parameter list |
| `DeviceConfig` + `Parameter` | Reusable atomic recipe/configuration/macro | One Codesys recipe, one ABB drive macro, one tuning profile |
| `DeviceConfigSet` + `DeviceConfigSetMember` | Static package made of multiple `DeviceConfig` rows and applied only to a device group/system node | HVAC package combining compressor, condenser, and AHU fan configurations |
| `Device` + `Parameter` | Live/materialized values on one device or system node | PLC global variables after recipe load; actual drive parameters after tuning |
| `DeviceRule` | One operation against a target: apply, check, assert, suggest, or validate | Load recipe, compare expected values, detect configuration drift |
| `DeviceRuleSet` | Ordered system-engineering plan made of rules | Commissioning sequence, plant startup plan, batch configuration procedure |

### `DeviceConfig` is the recipe; `Device + Parameter` is the live state

A `DeviceConfig` is a reusable configuration artifact. It may contain parameter
values through `Parameter.deviceConfigId`, and it may also refer to a control
method or a trajectory. It is therefore more general than a scalar PLC recipe: it
can describe values to load, the control method to use, and the trajectory or
profile to execute.

A `Device` has its own `Parameter` rows through `Parameter.deviceId`. Those rows
represent the values that are actually present, loaded, measured, materialized,
or maintained for that specific device or system node. A device may initially
receive its values from a `DeviceConfig`, but the two are not the same thing.
After the load operation, the device values may diverge because of manual HMI
changes, service tuning, emergency intervention, automatic adaptation, or local
maintenance.

For example, an ABB ACH580 drive macro may declare:

```text
DeviceConfig: ACH580_COMPRESSOR_MACRO_V1
  maxSpeed = 50 Hz
  accelTime = 30 s
  decelTime = 30 s
```

When this macro is loaded into `COMP_17_DRIVE`, the drive receives live values:

```text
Device: COMP_17_DRIVE
  maxSpeed = 50 Hz
  accelTime = 30 s
  decelTime = 30 s
```

Later a technician may reduce the maximum speed directly on the drive or HMI:

```text
Device: COMP_17_DRIVE
  maxSpeed = 45 Hz
```

The original `DeviceConfig` still says `50 Hz`; the live `Device` state now says
`45 Hz`. This difference is intentional and useful: a later `DeviceRule` can
check compliance, report drift, or suggest restoring the expected value.

### Applying the same recipe to many compatible devices

A recipe is normally reusable. For example, a plant may have 30 compressors, each
with an ABB ACH580 drive configured in the same way. The standard macro is stored
once as a `DeviceConfig`, not copied manually as 30 separate recipe definitions:

```text
DeviceConfig: ACH580_COMPRESSOR_MACRO_V1
  compatible with: ABB_ACH580 compressor drives
```

The 30 physical drives are represented as `Device` rows, often under a device
group or subsystem node:

```text
Device: COMPRESSOR_DRIVES_GROUP
  Device: COMP_01_DRIVE
  Device: COMP_02_DRIVE
  ...
  Device: COMP_30_DRIVE
```

A `DeviceRule` can then apply the same `DeviceConfig` to the whole group. At
execution time the implementation expands the target group and applies the
configuration to the compatible member devices. The resulting live values are
stored or compared on each individual `Device`.

### `DeviceConfigSet`: static composition for device groups

A `DeviceConfigSet` is a static configuration package for a device group or
system node. It answers the question: **which configurations belong together as
one declared package for this subsystem, machine module, production cell, or
plant area?**

A `DeviceConfigSet` is intentionally not the normal way to configure one single
leaf device. For a single PLC, drive, instrument, or actuator use `DeviceConfig`
directly. Use `DeviceConfigSet` when the target is a `DeviceGroup` or another
group/system node represented in the `Device` hierarchy.

For example, an HVAC refrigeration subsystem may need a coordinated
configuration for a compressor drive, a condenser, and an AHU fan. Each machine
part has its own atomic `DeviceConfig`, but the system baseline is the set of
those configurations together:

```text
DeviceConfig: ACH580_COMPRESSOR_DRIVE_MACRO_V1
DeviceConfig: CONDENSER_FAN_STAGE_PROFILE_V1
DeviceConfig: AHU_FAN_AIRFLOW_PROFILE_V1

DeviceConfigSet: HVAC_REFRIGERATION_SYSTEM_BASELINE_V1
  sequence 10 -> ACH580_COMPRESSOR_DRIVE_MACRO_V1
  sequence 20 -> CONDENSER_FAN_STAGE_PROFILE_V1
  sequence 30 -> AHU_FAN_AIRFLOW_PROFILE_V1
```

This package is applied to an HVAC device group or subsystem, not to a single
leaf device:

```text
DeviceGroup/System node: HVAC_REFRIGERATION_SYSTEM
  COMPRESSOR_DRIVES_GROUP
  CONDENSER_GROUP
  AHU_FANS_GROUP
```

At execution time, the implementation expands the target group and maps each
member `DeviceConfig` to the compatible child device or child group using device
type compatibility, group purpose, hierarchy, or explicit mapping rules.

`DeviceConfigSetMember.sequenceNum` defines the deterministic order inside that
static package. It is the order of composition of the configuration package
itself. This is different from `DeviceRule.priority`, which orders operations
over the plant or system hierarchy.

### `DeviceRule` and `DeviceRuleSet`: operational and system-engineering layer

A `DeviceRule` performs one operation against a target `Device`. The target may
be a physical drive, a PLC, a logical device, a device group, a subsystem, a
machine module, a production cell, a line, or a plant node represented in the
`Device` hierarchy. When the rule references `deviceConfigSetId`, the target must
be a device group or a higher-level group/system node; this is enforced by model
validation, not only by convention.

A rule can operate on exactly one configuration reference:

```text
deviceConfigId     -> operate on one atomic DeviceConfig
deviceConfigSetId  -> operate on one composed DeviceConfigSet; target must be a DeviceGroup/system node
```

The two fields are mutually exclusive: one and only one must be present.

When `deviceConfigSetId` is present, the target `deviceId` must identify a group
or system node. A typical validation checks the target device type and accepts it
only if its `deviceTypeEnumId` is the device-group type or inherits from that
parent type. This prevents using a composed configuration package where a single
atomic `DeviceConfig` should be used instead.

A `DeviceRuleSet` is the operational plan. It answers the question: **which
configuration operations must be performed on which system targets, and in which
logical phase?**

For example, a commissioning plan for an HVAC refrigeration plant may look like
this:

```text
DeviceRuleSet: COMMISSIONING_HVAC_REFRIGERATION_PLANT_A

priority 10:
  target = SAFETY_SYSTEM
  apply  = SAFETY_BASELINE_SET

priority 20:
  target = HVAC_REFRIGERATION_SYSTEM
  apply  = HVAC_REFRIGERATION_SYSTEM_BASELINE_V1

priority 30:
  target = COMPRESSOR_DRIVES_GROUP
  apply  = ACH580_COMPRESSOR_DRIVE_MACRO_V1

priority 30:
  target = AHU_FANS_GROUP
  apply  = AHU_FAN_AIRFLOW_PROFILE_V1

priority 40:
  target = HVAC_REFRIGERATION_SYSTEM
  check  = HVAC_REFRIGERATION_EXPECTED_STATE_SET
```

In this example `HVAC_REFRIGERATION_SYSTEM_BASELINE_V1` is a `DeviceConfigSet`
because it is applied to the HVAC subsystem group. `ACH580_COMPRESSOR_DRIVE_MACRO_V1`
and `AHU_FAN_AIRFLOW_PROFILE_V1` are individual `DeviceConfig` records and may be
applied directly to compatible device groups or leaf devices.

Rules with the same priority belong to the same logical phase. Increasing
priority values represent progression through commissioning, startup, subsystem
configuration, plant-level coordination, validation, compliance checking, or
recovery procedures.

This is the system-engineering distinction:

```text
DeviceConfigSetMember.sequenceNum
  = order inside a static recipe/configuration package

DeviceRule.priority
  = logical phase of an operation over devices, groups, subsystems, or plants
```

The model therefore supports both ways of composing industrial configuration:

1. **Static composition for groups** with `DeviceConfigSet`: define a reusable
   package of recipes/macros/configurations for a device group, subsystem, cell,
   or plant area.
2. **Operational composition** with `DeviceRuleSet` and `DeviceRule.priority`:
   apply, check, or validate those configurations across a system hierarchy.

This is useful for batch management because recipe logic remains separate from
equipment control, while still making the execution plan explicit and auditable.
It is also useful for system engineering because the same model can represent a
single device, a group of devices, a subsystem made of groups, or a complete
plant-level configuration and validation procedure.

## Math–Device duality

`moqui.device` and `moqui.math` are two complementary faces of one problem. The
binding entity `DeviceMathModel` connects them so the *same* governance machinery
— config history, rule evaluation, audit log, effective dating — serves a PLC
moving a servo and a GPU cluster training a transformer, unchanged. The only knob
that differs is the device type. This is the part general MLOps tooling lacks:
those tools come from the software side and treat the device as a deployment
detail; here it is co-primary.

## Services

| Service | Description |
|---|---|
| `moqui.device.DeviceServices.run#DeviceRequest` | Dispatches a single `DeviceRequest` to its configured implementation service |
| `moqui.device.DeviceServices.run#DeviceRequestGroup` | Runs all requests in a named group; designed to be called as a scheduled service |
| `moqui.device.DeviceServices.run#DeviceRequestInternal` | Interface that driver components (e.g. `moqui-plc4j`) must implement |
| `moqui.device.DeviceServices.send#DeviceNotification` | Sends a Moqui notification for a device event |
| `moqui.device.DeviceGatewayServices.run#GatewayDeviceRequest` | Dispatches scalar parameter write/read/subscribe requests via the `moqui-device-gateway` REST API (MQTT / OPC UA) |
| `moqui.device.DeviceGatewayServices.export#DeviceConfig` | Exports a device configuration recipe (Codesys txt format, persistent data) via the gateway |
| `moqui.device.DeviceGatewayServices.export#Trajectory` | Exports a computed trajectory as a structured JSON payload to the gateway for MQTT publishing (ephemeral bulk data) |
| `moqui.device.DeviceGatewayServices.transfer#DeviceContent` | Streams a file (G-Code, firmware, recipe) to a device via the gateway SFTP/file endpoint |

## Service layer — Python ecosystem via moqui-jep

`moqui.device` follows the same philosophy as `moqui.math`: it defines entities,
seed data, and the service interfaces only. Driver implementations that
communicate with physical devices over fieldbus protocols (Modbus, OPC UA,
EtherNet/IP, CANopen, etc.) are provided by separate components such as
**moqui-plc4j** (Apache PLC4X, JVM) or Python libraries (python-opcua, pymodbus,
python-snap7, etc.) embedded via **moqui-jep**. Control algorithms and ML
inference services likewise run through moqui-jep using NumPy, SciPy, JAX, or
python-control.

## Example service: 6-DOF robot arm trajectory planning

`moqui-device` ships an end-to-end example that shows how math modelling,
ML inference, and device binding work together. The service
`moqui.device.TrajectoryPlannerServices.run#RobotArmTrajectoryPlanner`
computes a collision-free joint-space trajectory for a 6-DOF robot arm using a
small feedforward neural network and persists the full output chain into the
moqui-math entity model.

### Neural network

A three-layer MLP (12 → 128 → 256 → 60) is trained offline on 50 000 synthetic
quintic-spline trajectories with the script
`script/train_robot_arm_trajectory_planner.py`. The quintic (degree-5) basis
enforces zero velocity and acceleration at both endpoints, giving smooth,
jerk-limited motion. Inference runs at runtime via
[DJL](https://djl.ai/) 0.31.0 + ONNX Runtime 1.19.0, which are declared as
Gradle dependencies and placed in `lib/` by the `copyDependencies` task.

Input shape: `float32[1, 12]` — `[q_start(6) ‖ q_goal(6)]` joint angles in
radians. Output shape: `float32[1, 60]` — 10 waypoints × 6 joints, flat
row-major.

### Data modelling

The service writes to the following entity chain on every successful call:

```
MathModelDef ──► MathModel ──► MathModelRun ──► MathModelPerf
                                   │
                                   └──► MathModelData (3 rows)
                                            │
                         ┌──────────────────┼──────────────────────┐
                         ▼                  ▼                      ▼
               ApproximatedFunction     Vector (q_start)    Vector (q_goal)
                     │
          ┌──────────┼──────────────┐
          ▼          ▼              ▼
    ParametricPath  Trajectory  ApproximatedFunctionSample (×10)
                                        │
                          ┌─────────────┴──────────────┐
                          ▼                             ▼
                  ParametricPathPoint            TrajectoryPoint
                  (path geometry)             (time offset ms)
                          │
                          ▼
                    Vector + VectorComponent (×6, joint angles)
```

| Entity | Role |
|---|---|
| `MathModelDef` (`TrjPlannerMlp6Dof`) | Blueprint: model type, service name, version |
| `MathModel` (`TrjPlannerMlp6DofV1`) | Versioned production instance; governed by `MathModelStatusFlow` |
| `MathModelDefContent` | Points to the ONNX file via `component://moqui-device/data/ml/trajectory_planner.onnx` |
| `MathModelRun` | Nontransactional execution record; survives TX rollback; stores input parameters as JSON and output summary |
| `MathModelPerf` | Performance counters: `totalDurationSec` (end-to-end), `inferenceLatencyMs` (DJL `predict()` only), `throughputSamplesSec` |
| `MathModelData` | Three rows per run: output `ApproximatedFunction` + input `Vector` for q_start and q_goal |
| `ApproximatedFunction` | The trajectory container; `vectorSpaceEnumId = EngJointSpace6Dof` (6-DOF revolute joint space) |
| `ParametricPath` | Path-level metadata; `profileEnumId = PppfTrajectoryProfile` |
| `Trajectory` | Time-tagged motion; `controlMethodEnumId = PtcmNNControl` |
| `ApproximatedFunctionSample` (×10) | One per waypoint (WP0000–WP0009); start, waypoint, end type |
| `ParametricPathPoint` (×10) | Path geometry for each sample |
| `TrajectoryPoint` (×10) | Absolute time offset in milliseconds (uniform 1 s total) |
| `Vector` + `VectorComponent` | Per-waypoint 6-DOF joint angle vector; plus separate vectors for q_start and q_goal |

### Model lifecycle tracking

The `MathModel` lifecycle is governed by `MathModelStatusFlow`
(`Draft → Validation → Production → Archived`). Every inference call creates a
`MathModelRun` record (nontransactional, `use="nontransactional"`) that captures:

- `startTime` / `endDate` — wall-clock span
- `parameters` — JSON snapshot of `startConfig` and `goalConfig`
- `results` — JSON summary (`approximatedFunctionId`, `waypointCount`)
- `hasError` / `errors` — fault isolation without rolling back the parent transaction
- `approximatedFunctionId` — direct FK to the output trajectory

`MathModelPerf` records two timing levels: `totalDurationSec` covers the full
service call including entity persistence; `inferenceLatencyMs` covers only the
DJL `predictor.predict()` call, which is the figure relevant to real-time control
cycle budgets.

The `MathModelData` snowflake table links the run to all mathematical objects it
produced or consumed, enabling complete data lineage: given a `MathModelRun` it
is possible to reconstruct exactly which model version, which inputs, and which
output trajectory were involved.

### Extending to real servo drives with TrajectoryAxisBinding

The `moqui.math.Trajectory` computed above is a **mathematical object** — a
sequence of 6-DOF joint-angle waypoints. To **execute** it on a physical robot
arm the waypoints must be mapped to the parameters of real servo drives or a
motion controller. That bridge is `TrajectoryAxisBinding`:

```
ApproximatedFunction ──► TrajectoryAxisBinding
                              │   (per axis / per device)
                              ├── approximatedFunctionId  (FK → Trajectory)
                              ├── axisName                (e.g. "J1" … "J6")
                              ├── deviceId                (FK → Device / servo drive)
                              ├── pointParameterDefId     (position setpoint parameter)
                              ├── velocityParameterDefId  (velocity feed-forward)
                              ├── accelerationParameterDefId
                              ├── jerkParameterDefId
                              └── snapParameterDefId
```

Each row binds one axis of the mathematical trajectory to one device parameter
definition. Once the binding is in place it becomes possible to:

- **Validate kinematic limits before execution**: retrieve the `ParameterDef`
  records identified by `pointParameterDefId` / `velocityParameterDefId` /
  `accelerationParameterDefId` and compare each `VectorComponent` value against
  the drive's configured min/max bounds. Any waypoint that violates a limit can be
  flagged before a single motion command is issued.
- **Dispatch the trajectory to the drive**: call `export#Trajectory` (ephemeral
  bulk path) or `export#DeviceConfig` (persistent recipe path). `export#Trajectory`
  reads the `ApproximatedFunctionSample` / `VectorComponent` chain directly and
  publishes a structured per-axis JSON payload via `moqui-device-gateway` → MQTT →
  `MqttParameterSub` on the controller. `export#DeviceConfig` serialises parameters
  as a Codesys txt recipe that the PLC recipe FB loads from the filesystem.
- **Close the feedback loop**: bind the velocity and acceleration derivatives
  (computed from consecutive waypoints and `TrajectoryPoint.pointTimeOffsetMillis`)
  to feed-forward parameters of the drive, reducing tracking error without
  requiring explicit PID tuning changes.

The `TrajectoryAxisBinding` entity uses `use="configuration"` with
`enable-audit-log="true"`, so every change to axis assignments is audited and
effective-dated — essential when certifying motion programs for safety-critical
machinery.

### Dispatching the computed trajectory — export#Trajectory

`TrajectoryPlannerData.xml` ships minimal seed data to test the ephemeral dispatch
path end-to-end:

| Record | Key |
|---|---|
| `Device` | `deviceId = moqui-device-gateway1` |
| `DeviceRequest` | `requestName = ROBOT_ARM_TRAJECTORY_EXPORT` |

The `DeviceRequest` points to a local gateway instance (`brokerUri = http://localhost:8081`)
and carries the MQTT topic in its `query` field (`moqui/robot/arm1/trajectory`).

To dispatch after planning:

```
moqui.device.DeviceGatewayServices.export#Trajectory
    approximatedFunctionId = <output of run#RobotArmTrajectoryPlanner>
    requestName            = ROBOT_ARM_TRAJECTORY_EXPORT
```

The service reads the `ApproximatedFunctionSample` / `VectorComponent` chain directly
(no `DeviceRequestItem` or `Parameter` records required) and POSTs the following
JSON to the gateway endpoint `POST /api/trajectory/export`:

```json
{
  "approximatedFunctionId": "100000",
  "waypointCount": 10,
  "mqttTopic": "moqui/robot/arm1/trajectory",
  "axes": {
    "J1": [0.10, 0.18, …],
    "J2": [0.00, 0.05, …],
    "J3": […], "J4": […], "J5": […], "J6": […]
  }
}
```

The gateway publishes this payload to the MQTT topic; `MqttParameterSub` on the
PLC receives it and passes each key/value pair to `JsonToParametersMapper`, which
maps `"J1"`…`"J6"` array values to the controller's trajectory buffer.

For the **persistent recipe path** use `export#DeviceConfig` instead: store
waypoints as `DeviceConfig/Parameter` entries under a `DeviceRuleSet`, then call
`export#DeviceConfig` to serialise them as a Codesys txt recipe that the PLC
recipe FB loads autonomously from the filesystem.

## Related components

- **[moqui-math](https://github.com/moqui/moqui-math)** — the dual math model (models, runs, lineage, trajectories).
- **[moqui-plc](https://github.com/moqui/moqui-plc)** — generates IEC 61131-3 PLC code from this device model and its status flows.
- **[moqui-device-gateway](https://github.com/moqui/moqui-device-gateway)** — executes this model at the edge as Apache Camel routes.

## Dependencies

- **moqui-math** `1.0.0`

## Install

    ./gradlew getComponent -Pcomponent=moqui-device
