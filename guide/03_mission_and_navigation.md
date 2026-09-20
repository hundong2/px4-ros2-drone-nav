# 03. 임무와 내비게이션 파이프라인

## 1. point-to-point scenario 읽기

예제 scenario는 [`drone_city_nav/config/manhattan_low_altitude_point_to_point_scenario.json`](../drone_city_nav/config/manhattan_low_altitude_point_to_point_scenario.json)입니다.

```json
{
  "schema": "drone_city_nav_point_to_point_scenario_v2",
  "canonical_world": "../worlds/canonical_city.world3d.json",
  "navigation": {
    "initial_altitude_m": 5.0,
    "minimum_target_z_m": 1.0,
    "maximum_target_z_m": 32.0
  },
  "vehicle": {
    "px4_model_target": "gz_x500_lidar_2d",
    "gazebo_model_name": "x500_lidar_2d_0",
    "map_start_m": [54.0, 54.0, 0.3],
    "yaw_rad": 0.0
  },
  "mission_goal_sequence_m": [[54.0, 378.0, 5.0]]
}
```

주요 필드:

- `schema`: parser와 contract test가 구분하는 형식 버전
- `canonical_world`: scenario 파일 기준 상대 경로
- `navigation`: 이 scenario가 요구하는 takeoff/target altitude 범위
- `vehicle.map_start_m`: map 좌표의 spawn 위치
- `vehicle.yaw_rad`: 초기 heading
- `mission_goal_sequence_m`: 차례로 capture해야 하는 terminal waypoint

spawn의 Z는 지면 근처일 수 있지만 mission goal은 flight envelope 안에 있어야 합니다. takeoff 단계가 먼저 안전한 초기 고도로 이동한 뒤 route execution이 시작됩니다.

## 2. 입력을 바꾸는 두 방법

### 빠른 waypoint override

```bash
MISSION_GOALS_XYZ_M='216,378,18;216,54,18' ./scripts/sim_headless.sh
```

간단한 경로 시험에 적합합니다. 숫자가 아닌 값, 비어 있는 waypoint, 세 좌표가 아닌 값은 runner가 거부합니다.

### versioned scenario

```bash
POINT_TO_POINT_SCENARIO_PATH=drone_city_nav/config/manhattan_low_altitude_point_to_point_scenario.json \
./scripts/sim_headless.sh
```

world, spawn, 목표를 함께 고정해야 하는 재현 실험에 적합합니다. 외부 environment asset을 쓰는 경우에는 수동으로 path만 바꾸지 말고 해당 `sim_*` target이 수행하는 `prepare_environment_simulation.py` 단계도 따라야 합니다.

## 3. mission lifecycle

```text
scenario parse
  -> Gazebo model spawn
  -> PX4/Micro XRCE-DDS/ROS graph startup
  -> pose, heading, world evidence readiness
  -> takeoff and hover capture
  -> waypoint request
  -> route certification and activation
  -> repeated MPPI horizon execution
  -> waypoint capture
  -> next waypoint or terminal position hold
  -> mission check and evidence collection
```

목표 도착은 단순히 한 번 반경 안에 들어오는 사건이 아닙니다. capture contract와 terminal state가 충족되어야 하며, 마지막 horizon은 자체적으로 zero translational velocity와 yaw rate에 도달한 뒤 offboard가 그 terminal point를 hold합니다.

## 4. raw world 생성

No-static 3D pipeline에서 `obstacle_memory_3d_node`는 organized scan의 hit와 miss beam을 모두 처리합니다.

1. scan timestamp와 PX4 pose history를 맞춘다.
2. lidar mount extrinsic과 full 6DoF pose로 beam을 map frame에 투영한다.
3. self hit와 예상 surface 정책을 적용한다.
4. ray를 `unknown/free/occupied` voxel로 통합한다.
5. base snapshot과 cumulative dirty chunks를 revision과 provenance와 함께 발행한다.
6. 최신 raw lidar hit도 별도 안전 입력으로 발행한다.

planner가 소비하는 raw snapshot/delta와 RViz용 `/drone_city_nav/raw_obstacle_grid`를 혼동하면 안 됩니다. visualization grid를 planner input에 되돌려 연결하는 것은 금지된 구조입니다.

정적 mode에서는 canonical `Occupancy3D`와 fingerprint-bound `ESDF3D`를 load합니다. static topology는 passage metadata와 진단에 쓰일 수 있지만 경쟁하는 route producer나 hard obstacle source가 아닙니다.

## 5. world에서 route까지

`WorldPipeline3D`가 immutable resident world를 만들면 `RoutePlanningCoordinator3D`가 persistent D* Lite session을 진행합니다.

- minimum-resolution 26-connected lattice가 reachability baseline입니다.
- open volume에서는 adaptive edge가 긴 이동을 줄일 수 있습니다.
- occupied change와 관련된 cached edge만 invalidate합니다.
- deadline 안에서 search를 이어가며 이전 label과 incumbent route를 재사용합니다.
- candidate는 raw swept body validation을 통과해야 합니다.
- accepted route는 generation, mission target identity, world lineage, certificate를 가집니다.

route를 볼 때 단순히 `path length`만 확인하지 말고 다음을 함께 봅니다.

- planner status와 incumbent 존재 여부
- raw world revision과 producer identity
- route generation과 release reason
- certified reserve와 required reserve
- remaining distance와 measured progress
- constrained span과 route endpoint semantics

## 6. route에서 MPPI horizon까지

MPPI는 route의 일부를 reference로 받아 control sequence를 반복 최적화합니다.

1. current state와 fresh world snapshot을 capture한다.
2. route target, speed policy, risk/clearance input을 준비한다.
3. CUDA에서 noise rollout을 simulation한다.
4. progress, speed, clearance, acceleration, jerk, terminal cost 등을 계산한다.
5. weighted control update를 수행한다.
6. post-update raw validation과 altitude envelope를 적용한다.
7. finite arrival profile을 포함한 execution horizon을 조립한다.
8. 최신 evidence에 대해 commit 시점 revalidation을 거친다.

`selected_costs`는 어떤 candidate가 선택됐는지 설명하지만 안전 증명 자체는 아닙니다. `post_update_executable`, raw collision flags, route certificate, execution commit을 함께 확인해야 합니다.

## 7. speed limiter 해석

`active_speed_limiter` 또는 compact track의 `limiter`는 그 tick의 reference speed를 가장 강하게 제한한 원인을 나타냅니다.

| 값 | 해석 |
|---|---|
| `cruise` | 기본 cruise limit |
| `curvature` | route curvature에 따른 감속 |
| `sensor_braking` | detection range와 evidence age에서 계산한 정지 가능 속도 |
| `goal` | 목표 접근 감속 |
| `route_endpoint` | 현재 certified route 끝에서 정지할 수 있도록 제한 |
| `route_constraint` | passage envelope의 속도 제약 |
| `blocked_route` | 진행 가능한 route evidence 부족 |
| `clearance` | tracking-error tube가 허용하는 속도 |
| `unobserved_frontier` | horizon/route 앞쪽에서 아직 관측되지 않은 공간까지의 거리 |

limiter가 계속 바뀌면 먼저 input age, route generation, world revision, constrained span을 확인합니다. 곧바로 weight를 바꾸면 근본 원인을 숨길 수 있습니다.

## 8. localization profile

| Profile | 용도 | 핵심 계약 |
|---|---|---|
| `lidar_inertial` | single-vehicle 기본 | lidar-inertial odometry를 PX4 external vision으로 fusion, simulated GNSS/magnetometer 비활성 |
| `gnss` | multi-vehicle와 비교 실행 | simulated GNSS와 simulation heading source 사용 |
| `gnss_shadow` | estimator 비교 | control은 GNSS, lidar-inertial estimate는 diagnostic only |

`lidar_inertial`의 estimator가 unhealthy하거나 odometry가 stale해 PX4 local position이 invalid가 되면 controller는 execution을 revoke하고 offboard가 hold합니다. truth pose는 평가에 쓰일 뿐 estimator의 복구 입력이 아닙니다.

## 9. 단계별 관찰 실습

### 실습 A: scenario 정적 검사

```bash
python3 guide/examples/inspect_scenario.py \
  drone_city_nav/config/manhattan_low_altitude_point_to_point_scenario.json
```

목표 고도, 직선 leg 거리, 전체 최소 경로 길이를 확인합니다. 실제 obstacle-aware route 길이는 이보다 길 수 있습니다.

### 실습 B: run manifest 확인

```bash
python3 -m json.tool log/runs/<run-id>/manifest.json | less
```

먼저 `repository`, `configuration`, `world`, `mission`, `runtime_profile`, `effective_overrides`를 확인합니다.

### 실습 C: compact tick 분석

```bash
python3 guide/examples/summarize_mppi_track.py \
  log/runs/<run-id>/mppi/mppi_track.jsonl
```

planning state와 execution reason의 비율을 확인한 후 full `mppi_ticks.jsonl`과 ROS log로 상세 원인을 추적합니다.

## 10. 코드 탐색 지도

| 관심사 | 시작 파일 |
|---|---|
| Simulation orchestration | [`scripts/run_drone_nav_sim.sh`](../scripts/run_drone_nav_sim.sh) |
| Scenario/launch | `drone_city_nav/launch/city_nav.launch.py` |
| Raw lidar world | `drone_city_nav/src/obstacle_memory_3d_node.cpp` |
| World service | `drone_city_nav/src/world/world_pipeline_3d.cpp` |
| Route service | `drone_city_nav/src/route_application/route_planning_coordinator_3d.cpp` |
| ROS composition | `drone_city_nav/src/runtime/ros/production_mppi_node.cpp` |
| Offboard execution | [`drone_city_nav/src/mppi_offboard_node.cpp`](../drone_city_nav/src/mppi_offboard_node.cpp) |
| Runtime config | [`drone_city_nav/config/urban_mvp.yaml`](../drone_city_nav/config/urban_mvp.yaml) |

정확한 파일명은 refactor로 바뀔 수 있으므로 `rg --files drone_city_nav/src`와 CMake target source list를 함께 확인하세요.

다음 단계: [안전과 운영](04_safety_and_operations.md)
