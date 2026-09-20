# 04. 안전과 운영

## 1. 안전 모델의 범위

이 프로젝트의 안전 계약은 시뮬레이션 안에서 입력 freshness, raw geometry, trajectory validity, execution ownership을 일관되게 다루기 위한 것입니다. 항공 인증, 센서 고장률 분석, 전원·통신 redundancy, 실제 비행 termination system을 제공하지 않습니다.

따라서 다음 두 문장을 분리해야 합니다.

- **저장소 안에서 증명하는 것:** 이 run에서 어떤 raw evidence와 contract를 바탕으로 어떤 horizon을 publish했는가.
- **저장소가 증명하지 못하는 것:** 현실의 모든 sensor fault와 환경에서 물리적 기체가 안전한가.

## 2. hard constraint와 soft preference

### Hard constraint

- raw occupied cell과 swept oriented body의 교차
- `1.0 <= z < 32.0 m` flight envelope 위반
- stale/invalid pose 또는 required world evidence
- invalid horizon sequence, frame, timestamp, finite point
- producer/revision/owner contract 불일치

### Soft preference

- ESDF/known-obstacle distance 기반 clearance ranking
- risk band exposure
- progress, speed tracking, acceleration, jerk, yaw cost
- cooperative maneuver preference

soft cost를 무한히 크게 만들어 hard constraint처럼 사용하는 대신, 실제 물리적 금지 조건은 raw validation 계약에 명시해야 합니다.

## 3. 실행할 수 없을 때의 상태

| 상황 | 기대 동작 |
|---|---|
| route가 아직 없음, 기체 정지 | typed stationary hold |
| 진행 중 route가 여전히 raw-safe | deadline과 증거 범위 안에서 resident owner continuation 가능 |
| 움직이는 중 path가 무효화됨 | 가능한 경우 current state에서 certified braking trajectory |
| fresh horizon이 만료됨 | old horizon extrapolation 금지, 감속 후 hold |
| mission goal capture | terminal rest를 포함한 horizon 뒤 동일 위치 hold |
| pose/world evidence stale | fail closed; 새 planned execution 금지 |
| physical destruction event | bounded force-disarm retry, PX4 disarm 확인 |

`no_executable_route`와 `no_executable_horizon`은 서로 다릅니다. 전자는 전략 경로를 제공할 수 없는 상태이고, 후자는 route가 있어도 지금 실행 가능한 finite horizon을 commit할 수 없는 상태일 수 있습니다.

## 4. sensor-limited motion

No-static flight는 확인된 occupied voxel만 hard obstacle로 사용하지만 속도는 다음을 포함하는 braking contract에 묶입니다.

- lidar가 보장하는 detection range
- scan과 world evidence age
- reaction/processing latency
- jerk-limited stopping distance
- body margin과 진행 방향

따라서 `unknown`을 전략적으로 traversable로 두더라도, 관측되지 않은 공간 앞에서 멈출 수 없는 속도를 허용해서는 안 됩니다. `sensor_braking`과 `unobserved_frontier` limiter, lidar freshness, stopping reserve를 함께 확인합니다.

## 5. 임무 모드별 운영

### Point-to-point

```bash
./scripts/sim_headless.sh
./scripts/sim_gui.sh
```

순서가 있는 waypoint를 terminal goal로 방문합니다. 마지막 목표에서 settle해야 성공입니다.

### Intercept

```bash
./scripts/sim_intercept_headless.sh
./scripts/sim_intercept_gui.sh
```

세 interceptor와 한 evader를 사용하는 finite mission입니다. interceptor는 evader coordinates를 직접 받지 않고 simulated radar range/azimuth/elevation/radial velocity를 바탕으로 track을 만듭니다. proximity result는 typed physical evidence와 disarm/hold settlement를 요구합니다.

### Multi-intercept

```bash
./scripts/sim_multi_intercept_headless.sh
./scripts/sim_multi_intercept_gui.sh
```

2v2 scenario와 spectator reselection을 사용합니다. `INTERCEPT_SPECTATOR_RESELECTION_POLICY`는 `first_living` 또는 `next_living`입니다.

### Cooperative traffic

```bash
./scripts/sim_cooperative_traffic_headless.sh
./scripts/sim_cooperative_traffic_gui.sh
```

각 agent가 bounded-validity intent를 공유하고 continuous closest approach를 평가합니다. peer preference는 soft planning input이며 raw physical obstacle을 대체하지 않습니다.

### Urban asset workflow

```bash
./scripts/sim_urban_point_to_point_headless.sh
./scripts/sim_cooperative_traffic_urban_headless.sh
```

versioned environment artifact를 준비하고 정해진 scenario를 사용합니다. acceptance 실행에서는 default를 무작정 바꾸지 말고 target에 선언된 override와 bounds를 기록합니다.

## 6. 안전한 실험 설계

1. **가설을 한 문장으로 쓴다.** 예: route endpoint limiter 변경이 no-route hold를 줄이는가?
2. **baseline commit과 입력을 고정한다.** manifest hash가 다른 run을 같은 조건이라고 부르지 않는다.
3. **한 번에 한 축만 바꾼다.** speed, sensor profile, map mode를 동시에 바꾸지 않는다.
4. **고유 run ID를 쓴다.** 로그 overwrite와 잘못된 비교를 막는다.
5. **최소 1회의 성공만으로 결론 내리지 않는다.** 동일 commit의 반복 run으로 분포를 본다.
6. **성공뿐 아니라 hold, deadline, memory growth, crash를 본다.** mission success 하나로 safety regression을 숨기지 않는다.
7. **검증을 약화해 성능을 얻지 않는다.** bottleneck을 먼저 계측한다.

예시:

```bash
DRONE_GAZEBO_RUN_ID=baseline-01 \
DRONE_GAZEBO_LOG_DIR=log/baseline-01 \
./scripts/sim_urban_point_to_point_headless.sh

CRUISE_SPEED_MPS=5.5 \
DRONE_GAZEBO_RUN_ID=cruise-5_5-01 \
DRONE_GAZEBO_LOG_DIR=log/cruise-5_5-01 \
./scripts/sim_urban_point_to_point_headless.sh
```

위 예시는 실험 방법을 보여줄 뿐, `5.5`가 더 안전하거나 빠르다는 결론을 미리 뜻하지 않습니다.

## 7. 정지와 cleanup

simulation interrupt가 hang하면 새 run을 겹쳐 시작하지 않습니다.

```bash
./scripts/stop_sim.sh --dry-run
./scripts/stop_sim.sh
```

GUI wrapper는 충돌하는 stale Gazebo process를 정리하도록 설계되어 있지만, `--dry-run` 결과를 통해 종료 대상 범위를 먼저 확인할 수 있습니다.

## 8. 데이터·보안 주의 사항

- log, bag, host resource inventory에는 환경 경로와 운용 정보가 들어갈 수 있습니다.
- 공개 issue나 commit에 secret, private log, 민감한 environment detail을 넣지 않습니다.
- 외부 environment asset과 PX4 checkout은 setup script의 pin/version 흐름을 따릅니다.
- 임의의 container image, ROS setup, binary artifact를 production-equivalent 결과로 간주하지 않습니다.
- ROS 2 graph에 외부 network participant가 들어오는 배포는 authentication, DDS security, network isolation을 별도로 설계해야 합니다. 현재 simulation 문서가 이를 제공한다고 가정하지 않습니다.
- 실제 기체로 연결되는 offboard topic과 force-disarm 경로는 독립적 safety review 없이 노출하지 않습니다.

보안 문제는 [`SECURITY.md`](../SECURITY.md)의 비공개 보고 지침을 따릅니다.

## 9. 실제 기체로 옮기기 전에 필요한 별도 작업

현재 저장소의 범위를 넘어서는 최소 검토 항목입니다.

- sensor calibration, timing, packet loss, degraded mode 분석
- hardware watchdog, communication loss, RC/manual takeover
- geofence, altitude, battery, return/land behavior
- real-time compute와 thermal throttling 검증
- arm64/target GPU build와 reproducible artifact supply chain
- HIL, tethered test, indoor cage, 점진적 flight envelope 확대
- 지역 항공법, 주파수, 개인정보·촬영 규정
- 독립 안전 검토와 hazard log

`docs/resource_budget.md`가 Jetson Orin 계열을 배제하지 않는다고 설명하는 것은 해당 device에서 검증했다는 뜻이 아닙니다. 현재 수치는 workstation simulation 측정치입니다.

다음 단계: [테스트와 디버깅](05_testing_and_debugging.md)
