# PX4 ROS 2 Drone Navigation 코드 아키텍처 분석

분석일: 2026-09-20

- 저장소: <https://github.com/hundong2/px4-ros2-drone-nav.git>
- 분석 revision: `ba9dd45c1807c5f85eb7ff8495c7950ca3843b23`
- 분석 범위: 단일 차량, no-static 3D lidar 기반 point-to-point 실행 경로
- 대화형 문서: [architecture.html](architecture.html)
- 원본 명세: [architecture.json](architecture.json)
- 자동 브라우저 증거: [visual-check receipt](architecture.visual-check.json) · [contact sheet](architecture.visual-check.html)

## 분석 범위와 읽는 방법

이 문서는 README의 설명만 다시 그린 것이 아니라 launch 파일, ROS 2 실행 진입점, 구독·발행 코드, world·route·MPPI runtime, 실행 권한 facade, PX4 command 경계와 빌드 manifest를 직접 대조해 만든 대표 아키텍처입니다. 도식의 각 구성요소에서 `SRC`를 열면 `architecture.json`에 기록한 상대 경로와 줄 번호를 확인할 수 있습니다.

저장소에는 intercept, multi-intercept, cooperative traffic, radar tracking, RViz와 다수의 진단 경로도 있습니다. 한 화면에서 핵심 실행 권한을 읽을 수 있도록 이 도식은 다음 주 경로에 집중합니다.

```text
Gazebo/PX4 SITL/ROS bridge
  → lidar·vehicle-state 인지와 위치추정
  → revisioned raw occupancy
  → RawWorldIngressRos3D / WorldPipeline3D
  → persistent D* Lite route
  → PlanningCycleCoordinator / CUDA MPPI
  → ExecutionSupervisor3D atomic commit
  → mppi_offboard_node
  → PX4 setpoint와 vehicle command
```

## 구성요소별 코드 근거

| 구성요소 | 책임 | 대표 근거 |
|---|---|---|
| 컨테이너·런치 | NVIDIA runtime을 확인하고 simulation 및 ROS graph를 시작 | [`scripts/container_run.sh`](../../scripts/container_run.sh), [`city_nav.launch.py`](../../drone_city_nav/launch/city_nav.launch.py) |
| Gazebo·PX4 SITL·브리지 | 물리·3D lidar·PX4 state를 시뮬레이션하고 ROS 2 topic으로 연결 | [`run_drone_nav_sim.sh`](../../scripts/run_drone_nav_sim.sh), [`px4_autopilot_adapter.cpp`](../../drone_city_nav/src/px4_autopilot_adapter.cpp) |
| 인지·위치추정 | LIO pose와 `VehicleOdometry`를 만들고 lidar hit/miss를 `ObstacleMemory3D`에 통합 | [`lidar_inertial_odometry_node.cpp`](../../drone_city_nav/src/lidar_inertial_odometry_node.cpp), [`obstacle_memory_3d_node.cpp`](../../drone_city_nav/src/obstacle_memory_3d_node.cpp) |
| `WorldPipeline3D` | producer epoch·revision·freshness를 검증하고 비영속 immutable resident world를 게시 | [`raw_world_ingress_ros_3d.cpp`](../../drone_city_nav/src/runtime/ros/raw_world_ingress_ros_3d.cpp), [`world_pipeline_3d.cpp`](../../drone_city_nav/src/world/world_pipeline_3d.cpp) |
| Route lifecycle·D* Lite | coherent world를 대상으로 persistent full-3D route를 탐색·구체화·활성화 | [`route_lifecycle_coordinator_3d.cpp`](../../drone_city_nav/src/route_application/route_lifecycle_coordinator_3d.cpp), [`route_planner_3d.cpp`](../../drone_city_nav/src/route_application/route_planner_3d.cpp) |
| PlanningCycle·CUDA MPPI | world·route·vehicle state의 일관된 snapshot으로 짧은 local horizon을 최적화 | [`production_mppi_node_planning_tick.cpp`](../../drone_city_nav/src/runtime/ros/production_mppi_node_planning_tick.cpp), [`mppi_controller_3d.cpp`](../../drone_city_nav/src/runtime/mppi_controller_3d.cpp) |
| `ExecutionSupervisor3D` | pending/active execution의 단일 facade로 최신 증거를 재검증하고 horizon을 원자적으로 commit | [`execution_supervisor_3d.hpp`](../../drone_city_nav/include/drone_city_nav/execution_supervisor_3d.hpp), [`production_mppi_node_execution_publication.cpp`](../../drone_city_nav/src/runtime/ros/production_mppi_node_execution_publication.cpp) |
| Offboard → PX4 | horizon의 producer·session·payload·freshness를 admission하고 50 Hz PX4 setpoint로 변환 | [`mppi_offboard_node.cpp`](../../drone_city_nav/src/mppi_offboard_node.cpp) |
| 독립 충돌 안전 경로 | Gazebo contact를 `VehicleDestroyed`로 만들고 별도 force-disarm lifecycle을 작동 | [`drone_contact_system.cpp`](../../drone_city_nav/src/drone_contact_system.cpp), [`collision_crash_node.cpp`](../../drone_city_nav/src/collision_crash_node.cpp) |

정확한 시작·끝 줄 번호는 [architecture.json](architecture.json)의 각 `sources` 항목에 최대 세 개씩 고정했습니다. `WorldPipeline3D`는 영속 데이터베이스가 아니라 메모리 내 immutable snapshot 소유자입니다. 도식의 database 색상은 상태 소유를 강조할 뿐 영속 저장을 뜻하지 않습니다.

## 실행 흐름과 상태 소유

1. `ros_gz_bridge`와 PX4 adapter가 lidar 및 vehicle state를 ROS 2 message로 전달합니다.
2. `ObstacleMemory3D`는 organized scan을 pose와 맞추고, 최신 즉시 안전 scan과 누적 snapshot/delta를 서로 다른 계약으로 내보냅니다.
3. `RawWorldIngressRos3D`는 producer identity, revision, frame과 currentness를 검사한 뒤 `WorldPipeline3D`에 최신 raw world를 commit합니다.
4. route lifecycle은 하나의 coherent full-3D world와 vehicle state를 고정해 persistent D* Lite를 갱신합니다.
5. planning cycle은 route reference와 resident world를 CUDA MPPI에 넘겨 finite candidate horizon을 만듭니다.
6. `ExecutionSupervisor3D`가 raw occupancy, flight envelope, 최신 state와 execution ownership을 다시 검사해 atomic commit한 뒤에만 `MppiTrajectoryHorizon`이 발행됩니다.
7. `mppi_offboard_node`는 horizon을 다시 admission하고 PX4 `OffboardControlMode`, `TrajectorySetpoint`, `VehicleCommand`로 변환합니다. 적용된 control feedback은 다음 planning tick의 증거로 돌아갑니다.

## 신뢰와 안전 경계

- 이 저장소는 Gazebo와 PX4 SITL을 위한 연구·개발 스택입니다. 실제 기체에 대한 인증, hardware failsafe 또는 비행 안전 검증을 제공하지 않습니다.
- raw occupied geometry와 flight envelope가 hard collision authority입니다. RViz, debug topic, JSONL과 soft risk field는 실행 권한이 아닙니다.
- `RawWorldIngressRos3D`, `ExecutionSupervisor3D`, offboard horizon admission은 각각 sensor evidence, execution ownership, PX4 command 직전의 fail-closed 경계입니다.
- Gazebo contact 기반 파괴 경로는 planner와 독립적으로 유지됩니다. mission 실패 자체는 disarm 권한이 아니며 typed physical destruction evidence가 force-disarm을 시작합니다.
- 개발 컨테이너는 GPU, `--privileged`, host network와 read-write workspace mount를 사용하므로 강한 host 격리 경계로 해석하면 안 됩니다.

## 제외와 불확실성

- intercept·cooperative traffic·multi-vehicle assignment와 diagnostics composition은 대표 도식에서 제외했습니다.
- ROS 2 RMW/DDS vendor, DDS Security 설정, 네트워크 인증·권한 모델은 저장소 근거로 확정할 수 없습니다.
- 대표 제어 경로는 `px4_msgs`와 Micro XRCE-DDS로 확인했습니다. MAVLink 호출 근거는 확인하지 못했으므로 도식에 넣지 않았습니다.
- 실제 하드웨어 배포, flight-controller failsafe, 센서 calibration과 법규 준수는 이 분석의 범위 밖입니다.
- 분석 revision 이후 코드가 바뀌면 `sources` 줄 번호와 관계를 다시 검증해야 합니다.

## Archify 검증 영수증

한국어는 현재 Archify Viewer locale로 지원되지 않아 `meta.locale`을 생략했습니다. 따라서 문서 내용은 한국어지만 고정 Viewer UI와 생성된 `<html lang>`은 영어 fallback을 사용합니다.

```text
diagram_type: architecture
output: D:\workspace\laboratory\px4-ros2-drone-nav\docs\archify\architecture.html
specification_sha256: 579c0fc42ed4cf19417c890ac4d589515db1e3ddee8fc8a8664d8cd36e69d773
artifact_sha256: 86938a4c62cd994f008f9dfd486cc818f9dc071e903e80e434ce5f4e7e7efe1b
validation: 9/9 showcase, 0 errors, 0 warnings
browser_evidence: passed
visual_review: passed
correction_rounds: 1
```

- **Deterministic delivery**: frozen JSON과 전달 HTML의 SHA-256 및 byte identity가 `deliver` receipt에서 확인됐습니다.
- **Automated browser evidence**: Chrome의 light theme 1440×900, 1600×1000, 1920×1080, 2048×1320에서 수평·수직 overflow 없이 통과했고, 1440×900과 2048×1320의 light/dark screenshot이 생성됐습니다.
- **Perceptual visual review**: 생성된 light/dark 네 장을 이미지 도구로 직접 확인했습니다. node·card 잘림, 관계선 교차, label 충돌, theme 대비 문제는 발견되지 않았습니다.
- **Correction round 1**: 첫 browser evidence에서 세로 overflow가 발견되어 viewBox와 구성요소 간격을 압축하고 불필요한 범례를 숨긴 뒤 validate·deliver·visual-check를 다시 실행했습니다.
