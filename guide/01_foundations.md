# 01. 기초 개념

## 1. 이 프로젝트가 해결하는 문제

이 저장소는 도시형 3차원 환경에서 드론이 목표점까지 이동하도록 만드는 연구용 내비게이션 스택입니다. PX4 SITL이 비행체 상태와 저수준 제어를 담당하고, ROS 2 노드가 인지·경로·궤적·offboard 명령을 구성하며, Gazebo Harmonic이 물리 환경과 lidar를 시뮬레이션합니다.

현재 주력 경로는 다음과 같습니다.

- 3D lidar의 hit/miss beam을 누적해 revision이 있는 raw `Occupancy3D`를 만든다.
- persistent sparse D* Lite가 전체 3D 전략 경로를 계산하고 world update에 맞춰 수선한다.
- CUDA MPPI가 짧은 receding horizon에서 동역학적으로 실행할 local trajectory를 고른다.
- raw occupied geometry에 대해 드론의 swept oriented 3D footprint를 검증한다.
- 검증된 timestamped horizon만 `mppi_offboard_node`가 PX4 setpoint로 실행한다.

이것은 범용 autopilot이나 실제 기체 제품이 아닙니다. 지도 없는 인지, 경로 수선, local trajectory optimization, 실행 안전 계약을 SITL 환경에서 연구하고 검증하는 testbed입니다.

## 2. 구성 요소의 역할

### PX4 SITL

PX4의 Software-In-The-Loop 실행입니다. 실제 flight controller 대신 프로세스로 실행되며 arming, offboard mode, local position, attitude, trajectory setpoint 처리를 담당합니다. ROS 2 측은 `/fmu/in/*`, `/fmu/out/*` message로 연결됩니다.

### Gazebo Harmonic

드론과 도시 환경의 물리, 충돌, lidar를 시뮬레이션합니다. Gazebo ground truth는 mission readiness와 물리적 결과 판정에만 사용되고 production navigation estimator나 planner 입력으로 되먹임되지 않습니다.

### ROS 2와 `drone_city_nav`

단일 ament CMake package가 sensing adapter, raw world, planning, MPPI, execution contract, offboard node, diagnostics를 제공합니다. `colcon`이 공식 build entry point이며 direct top-level CMake는 지원되지 않습니다.

### Micro XRCE-DDS Agent

PX4 uXRCE-DDS client와 ROS 2 DDS graph 사이의 통신을 중계합니다. 장애 분석에서는 planner와 offboard만 보지 말고 이 프로세스와 transport age도 함께 확인해야 합니다.

## 3. 주요 runtime owner

| 구성 요소 | 소유하는 상태와 책임 |
|---|---|
| `obstacle_memory_3d_node` | lidar 수집, pose 보정, hit/miss ray 통합, revisioned snapshot/delta |
| `WorldPipeline3D` | raw reconstruction, static/observed world build, coherent resident world publication |
| `RoutePlanningCoordinator3D` | persistent D* Lite request, worker lifecycle, route result 전달 |
| `RouteMaterializer3D` | 경로 형상화와 candidate validation |
| `production_mppi_node` | ROS composition root, world/route/controller/execution service 연결 |
| `ExecutionSupervisor3D` | pending/active owner, revalidation, atomic horizon commit |
| `mppi_offboard_node` | fresh horizon 실행, PX4 setpoint, expired horizon의 감속/hold |
| `mission_monitor_node` | mission success와 simulated crash 관찰 |
| `lidar_debug_node` | lidar와 navigation snapshot 기록 |

소유권이 중요한 이유는 진단 정보가 실행 권한이 되거나 한 subsystem이 다른 subsystem의 상태를 몰래 바꾸는 것을 막기 위해서입니다.

## 4. 좌표계와 시간

- `map`: planner와 mission이 사용하는 좌표계입니다.
- PX4 local position은 NED 관례를 따릅니다.
- Gazebo world는 보통 ENU/SDF 관례를 사용합니다.
- scenario의 시작 pose와 canonical world's `map_to_sdf`가 변환을 정의합니다.
- `gazebo_map`과 `drone_follow`는 주로 시각화를 위한 frame입니다.

좌표 오차는 soft MPPI weight로 고칠 문제가 아닙니다. 장애가 보이면 먼저 scenario 시작 pose, `map_to_sdf`, PX4 NED-to-map 변환, lidar acquisition pose와 timestamp를 확인해야 합니다.

시간도 safety contract의 일부입니다. world revision, pose age, lidar evidence age, horizon `valid_from`과 deadline이 맞지 않으면 오래된 경로를 계속 실행하지 않고 fail-closed 동작으로 전환합니다.

## 5. world representation

### Raw occupancy

센서나 canonical map에서 직접 얻은 `unknown/free/occupied` 증거입니다. raw occupied voxel과 swept footprint의 교차는 hard collision reject입니다.

### Occupied-distance evidence

occupied source와의 거리를 계산해 candidate의 clearance를 순위화하는 soft evidence입니다. 경로 선호도와 속도에 영향을 줄 수 있지만 자체적으로 새로운 hard obstacle을 만들지는 않습니다.

### 정적 지도와 no-static

| 구분 | Static | No-static 3D |
|---|---|---|
| 활성화 | `ENABLE_STATIC_MAP=true` | 기본값 `ENABLE_STATIC_MAP=false` |
| 주 world | canonical `Occupancy3D`와 precomputed `ESDF3D` | lidar가 만든 revisioned observed `Occupancy3D` |
| lidar | 정적 실험에서 선택적으로 비활성 가능 | `LIDAR_PROFILE=3d` 필수 |
| unknown 공간 | canonical map이 기준 | free와 같은 전략적 traversability/base cost; raw occupied만 hard reject |
| 제한 | static map은 runtime lidar를 collision map에 합치지 않음 | static topology metadata에 의존하지 않음 |

No-static에서 unknown을 통과 가능하게 보는 것이 곧 blind flight를 의미하지는 않습니다. 최신 lidar, evidence age, braking range, raw path validation이 실행 가능 속도와 horizon을 제한합니다.

## 6. 전략 경로와 local horizon

### Persistent D* Lite route

목표까지 이어지는 장거리 geometry입니다. world revision이 변하면 가능한 상태를 재사용하면서 영향받은 구간을 수선합니다. 단순한 매 tick full replanning이나 2D branch가 아닙니다.

### GPU MPPI

현재 상태, route reference, dynamics, risk/cost를 이용해 여러 control rollout을 평가하고 짧은 local horizon을 선택합니다. soft cost가 낮더라도 raw validation과 altitude envelope를 통과하지 못하면 실행할 수 없습니다.

### Execution plan과 horizon

- `ExecutionPlan3D`: route geometry, tracking tube, nominal horizon, braking fallback, 증거 revision을 묶은 atomic artifact입니다.
- `MppiTrajectoryHorizon`: offboard로 보낼 timestamped local trajectory입니다.
- accepted horizon은 sequence, frame, finite points, 시간 창, altitude envelope, hold target 계약을 만족해야 합니다.
- offboard는 50 Hz로 horizon을 보간해 PX4 setpoint를 보냅니다.

## 7. 안전을 이해하는 다섯 문장

1. raw physical occupancy와 flight envelope가 hard authority다.
2. RViz, debug topic, JSONL, soft risk field는 제어 입력이 아니다.
3. 새 route나 horizon이 실패해도 검증되지 않은 candidate가 기존 owner를 지우지 못한다.
4. 실행할 경로가 없으면 움직이는 기체는 가능한 경우 검증된 braking path로 정지하고, 정지한 기체는 hold한다.
5. mission 실패만으로 disarm하지 않으며 typed physical destruction event만 bounded force-disarm lifecycle을 시작한다.

## 8. 용어 정리

| 용어 | 의미 |
|---|---|
| SITL | 실제 hardware 없이 autopilot firmware를 프로세스로 실행하는 방식 |
| Offboard control | 외부 computer가 PX4에 position/velocity/acceleration setpoint를 주는 모드 |
| Occupancy3D | 3차원 voxel의 unknown/free/occupied 상태 |
| ESDF | 장애물까지의 signed/unsigned distance 질의를 위한 거리 표현; 이 저장소에서는 hard occupancy authority가 아님 |
| D* Lite | 환경 변화에 따라 이전 탐색 결과를 재사용하는 incremental graph search |
| MPPI | sampled controls의 cost로 receding-horizon control sequence를 갱신하는 model predictive path integral 방식 |
| Swept footprint | 기체가 한 segment를 이동할 때 점유하는 전체 부피 |
| Receding horizon | 짧은 미래 계획을 반복 계산하고 앞부분만 실행하는 방식 |
| Fail closed | 증거가 stale/불충분하면 계속 진행하지 않고 안전 상태로 제한하는 정책 |
| Provenance | world, route, execution evidence가 어떤 producer/revision에서 왔는지 나타내는 계보 |

## 9. 코드 읽기 순서

1. [`docs/overview.md`](../docs/overview.md)
2. [`docs/architecture.md`](../docs/architecture.md)
3. [`docs/navigation_pipeline.md`](../docs/navigation_pipeline.md)
4. [`drone_city_nav/src/runtime/ros/production_mppi_node.cpp`](../drone_city_nav/src/runtime/ros/production_mppi_node.cpp)
5. [`drone_city_nav/src/mppi_offboard_node.cpp`](../drone_city_nav/src/mppi_offboard_node.cpp)
6. 관련 contract header와 같은 이름의 `drone_city_nav/tests/*_test.cpp`

다음 단계: [설치와 첫 비행](02_setup_and_first_flight.md)
