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
| Configuration | `DeviceConfig`, `DeviceConfigSet`, `DeviceConfigSetMember` — recipe and configuration definitions modelled along ISA-88 / IEC 61512 (batch control and recipe management) lines |
| Rules | `DeviceRuleSet`, `DeviceRule` — apply, assert, and validate configurations; supports hierarchical rule sets and priority ordering, consistent with the ISA-88 / IEC 61512 separation of recipe logic from equipment control |
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
| `moqui.device.DeviceGatewayServices.run#GatewayDeviceRequest` | Dispatches requests via the `moqui-device-gateway` REST API (MQTT / OPC UA) |
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
- **Generate device requests automatically**: iterate over
  `ApproximatedFunctionSample` records ordered by `sequenceNum`, read the
  corresponding `VectorComponent` values, and create `DeviceRequest` /
  `DeviceRequestItem` rows targeting the bound device — a repeatable, audited
  motion command sequence derived entirely from the data model.
- **Close the feedback loop**: bind the velocity and acceleration derivatives
  (computed from consecutive waypoints and `TrajectoryPoint.pointTimeOffsetMillis`)
  to feed-forward parameters of the drive, reducing tracking error without
  requiring explicit PID tuning changes.

The `TrajectoryAxisBinding` entity uses `use="configuration"` with
`enable-audit-log="true"`, so every change to axis assignments is audited and
effective-dated — essential when certifying motion programs for safety-critical
machinery.

## Related components

- **[moqui-math](https://github.com/moqui/moqui-math)** — the dual math model (models, runs, lineage, trajectories).
- **[moqui-plc](https://github.com/moqui/moqui-plc)** — generates IEC 61131-3 PLC code from this device model and its status flows.
- **[moqui-device-gateway](https://github.com/moqui/moqui-device-gateway)** — executes this model at the edge as Apache Camel routes.

## Dependencies

- **moqui-math** `1.0.0`

## Install

    ./gradlew getComponent -Pcomponent=moqui-device
