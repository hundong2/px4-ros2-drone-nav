# 05. 테스트와 디버깅

## 1. 검증 피라미드

### C++ unit test

```bash
./scripts/test.sh
```

컨테이너 안에서는 다음과 같습니다.

```bash
make test
```

`colcon` build 후 `ctest --test-dir build/drone_city_nav --output-on-failure`를 실행합니다. 알고리즘, contract, state machine에 직접 대응하는 test는 `drone_city_nav/tests/`에 있습니다.

### Python script/contract test

```bash
./scripts/dev_shell.sh
make test-scripts
```

orchestration, scenario, telemetry schema, launch wiring 같은 계약은 `scripts/tests/`가 검사합니다.

### Quality gate

```bash
./scripts/dev_shell.sh
make quality
```

dry-run format check, build, C++ tests와 사용 가능한 경우 scoped clang-tidy/cppcheck를 수행합니다. 변경한 C++만 format하려면 `make format`을 사용합니다.

### Integrated headless gate

```bash
./scripts/sim_headless.sh
```

simulation, mission result, controller dynamics, runtime artifacts를 함께 검사합니다. 적어도 120초 이상의 timeout으로 diagnostic run을 해야 합니다.

## 2. run 분석의 올바른 순서

1. mission outcome, destruction cause, disarm/hold settlement, final pose
2. manifest의 commit, dirty 상태, config/world/scenario hash, override
3. pose, heading, raw snapshot, ESDF freshness
4. active route, planner provenance, target source
5. MPPI selected tier, raw collision, post-update classification
6. measured progress, head progress, liveness
7. constrained span은 해당 route가 실제로 span을 지날 때만 분석
8. finite-path deadline, arrival profile, final hold
9. 마지막에 cost와 dynamics tuning

frame이나 stale input 문제를 weight 조정으로 가리면 재현성이 악화됩니다.

## 3. 주요 artifact

| Artifact | 역할 |
|---|---|
| `manifest.json` | commit, input hashes, mission, profile, effective override |
| `ros_drone_nav.log` | ROS node lifecycle과 event/summary |
| `gz_drone_nav.log` | Gazebo server와 orchestration |
| `mppi/mppi_track.jsonl` | 매 tick compact state, speed, limiter, planning/execution state |
| `mppi/mppi_ticks.jsonl` | throttled detailed cost, timing, route, world, validation |
| `mppi/mppi_error_context.jsonl` | diagnostics error episode 주변 bounded ring |
| `lidar_debug/` | synchronized lidar/grid/horizon snapshot |
| `resources.csv` | per-process CPU, RSS, thread, GPU/resource observation |
| `resources_host.json` | 결과를 측정한 host 환경 |
| `tracking.npz`, `gz_pose.csv` | setpoint/estimated/physical motion 비교 증거 |

artifact 경로는 wrapper가 출력한 run directory를 사용합니다.

## 4. manifest 먼저 보기

```bash
python3 -m json.tool log/runs/<run-id>/manifest.json | less
```

두 run이 정말 비교 가능한지 확인합니다.

```bash
python3 guide/examples/compare_run_manifests.py \
  log/runs/<run-a>/manifest.json \
  log/runs/<run-b>/manifest.json
```

commit, dirty flag, config/world/scenario hash, lidar/static profile, effective override가 다르면 그 차이를 결과 해석에 반영해야 합니다.

## 5. compact track 분석

```bash
python3 guide/examples/summarize_mppi_track.py \
  log/runs/<run-id>/mppi/mppi_track.jsonl
```

다음 질문을 빠르게 확인합니다.

- 전체 tick 중 planned/hold state 비율은 얼마인가?
- 어떤 limiter가 가장 자주 활성화되었는가?
- `no_executable_route`와 `no_executable_horizon` 중 무엇이 많은가?
- reference speed, head speed, clearance의 분포는 어떤가?
- JSON decode 오류나 field 누락이 있는가?

compact track은 모든 tick을 담지만 상세 원인은 제한적입니다. 이상 구간의 tick/stamp를 찾은 뒤 `mppi_ticks.jsonl`과 ROS log를 대조합니다.

## 6. 흔한 증상별 조사

### 이륙 후 hold

확인 순서:

1. CUDA와 `production_mppi_node` startup
2. PX4 pose/heading validity
3. raw occupancy/ESDF revision과 age
4. route planner state와 target source
5. `execution_reason`
6. offboard가 증가하는 horizon sequence를 받는지

### 장애물로 진행

1. raw obstacle evidence와 lidar projection
2. acquisition pose와 timestamp alignment
3. resident world lineage
4. route certificate와 swept footprint validation
5. post-update collision classification
6. offboard deadline/applied command

### 벽 앞 정체

- route generation과 endpoint
- D* Lite incumbent/search/repair state
- reserve available/required
- route head/terminal predicted progress
- 실제 displacement와 liveness action

예측 progress는 높은데 실제 route progress가 평평하면 route tracking/recovery 문제이지 단순 speed policy 문제가 아닐 수 있습니다.

### route 좌우 진동

route generation 자체가 바뀌는지부터 구분합니다. generation이 바뀌면 release reason, target identity, world lineage, suffix repair를 보고, route는 같은데 MPPI horizon만 바뀌면 warm start, first-control delta, cost hierarchy를 봅니다.

### RViz가 비어 있음

실제 topic과 QoS를 확인합니다.

```text
/drone_city_nav/raw_obstacle_grid
/drone_city_nav/mppi/path
/drone_city_nav/mppi/markers
/drone_city_nav/drone_marker
```

RViz 문제는 control failure 증거가 아닙니다. visualization path와 raw planner input을 분리해 조사합니다.

### Ctrl+C 이후 hang

```bash
./scripts/stop_sim.sh --dry-run
./scripts/stop_sim.sh
```

출력된 container, Gazebo, PX4, Micro XRCE-DDS, RViz, ROS process를 확인합니다.

## 7. acceptance 수치 읽기

현재 문서화된 no-static single-vehicle gate에는 다음이 포함됩니다.

- post-bootstrap route availability: 97% 초과
- ordinary post-bootstrap no-route hold: 3% 미만
- production tick wall time: p50 30 ms, p95 45 ms 이하
- raw snapshot hash/payload와 ownership gap 검사
- admitted successor reserve proof
- controller dynamics, localization, resource record 검사

이 값은 제품 결정에 따른 regression bound이며 tuning target의 전부가 아닙니다. availability는 stationary hold도 실행 owner로 셀 수 있으므로 `post_bootstrap_route_executable_ratio`와 실제 displacement도 같이 확인합니다.

## 8. 성능 문제 분리

`PRODUCTION_MPPI_SUMMARY`의 다음 값을 분리해서 읽습니다.

- `deadline_misses`: snapshot부터 publish/commit까지 whole tick overrun
- `controller_deadline_misses`: MPPI controller 자체 overrun
- `tick_total_*`: 전체 cycle 시간
- `gpu_*`, `total_ms`: controller 내부 GPU/host 시간
- ESDF build/upload age: async world path 시간
- dropped diagnostic/world snapshots

controller miss는 거의 없는데 whole tick miss가 많다면 rollout 수만 줄이기 전에 horizon assembly, revalidation, world update, publication을 조사합니다.

## 9. regression을 재현하는 기록법

이슈나 변경 설명에는 최소한 다음을 남깁니다.

```text
Repository commit:
Repository dirty:
Run ID / artifact directory:
Scenario and input hashes:
Static/lidar/localization profile:
Effective overrides:
Mission result:
First failing timestamp/tick:
Planning state / execution reason:
World and route revisions:
Expected behavior:
Observed behavior:
```

전체 private log를 공개하기 전에 secret, username, filesystem path, host detail을 검토합니다.

다음 단계: [성능·배포·확장·기여](06_advanced_and_contributing.md)
