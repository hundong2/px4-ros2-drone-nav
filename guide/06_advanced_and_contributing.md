# 06. 성능·배포·확장·기여

## 1. 성능 최적화 원칙

최적화 순서는 다음과 같습니다.

1. mission과 safety contract를 고정한다.
2. 같은 commit과 입력으로 baseline run을 여러 번 측정한다.
3. whole tick, world update, planner, controller, publication을 분리한다.
4. p50뿐 아니라 p95, p99, maximum, deadline miss를 본다.
5. 변경 후 mission, route availability, hold, raw validation, resource growth를 함께 비교한다.

물리적 validation을 약화하거나 diagnostic field를 지워서 속도를 얻지 않습니다.

## 2. CUDA MPPI benchmark

컨테이너 안에서 isolated benchmark를 실행합니다.

```bash
make mppi-benchmark \
  MPPI_BENCHMARK_ARGS="--scenario urban_blocks --rollouts 8192 --steps 80"
```

이 benchmark는 dynamics integration, ESDF texture query, clearance cost, weighted update, warm start를 포함하지만 ROS, Gazebo, live ESDF contention은 포함하지 않습니다. 따라서 production tick과 같은 수치라고 해석하면 안 됩니다.

## 3. production profiling 순서

1. sensor/raw snapshot cadence
2. ESDF build/upload latency와 evidence age
3. planner search slice와 request-to-route lead time
4. MPPI GPU/host p50, p95, maximum
5. horizon assembly, revalidation, commit, wire time
6. deadline misses와 dropped snapshot
7. offboard receive age와 applied-control feedback
8. liveness/hold 빈도
9. process CPU, RSS growth, GPU memory, simulation real-time factor

`resources.csv`는 simulator와 onboard 후보 process를 구분해 해석해야 합니다. Gazebo GPU lidar의 cost를 실제 onboard perception cost로 그대로 옮기지 않습니다.

## 4. 배포 현실성 평가

현재 문서의 workstation 측정에서는 navigation/mapping/offboard/Micro XRCE Agent가 여러 CPU core와 수백 MiB 메모리, NVIDIA GPU memory를 사용합니다. 이는 Jetson Orin 계열이 용량상 배제되지 않는다는 근거일 뿐입니다.

배포 전 별도 검증 항목:

- arm64 container/image와 모든 dependency build
- target GPU에서 rollout latency와 thermal steady state
- real sensor rate/pattern과 mount calibration
- PX4 hardware link latency와 packet loss
- process restart, watchdog, degraded behavior
- power budget와 memory pressure
- real-time scheduling과 CPU affinity
- safety monitor, manual takeover, geofence
- signed/reproducible artifacts와 dependency provenance

온보드 컴퓨터에서 recorded flight를 성공시키기 전에는 “배포 지원”이라고 표현하지 않습니다.

## 5. compile-time 아키텍처 경계

production dependency 방향은 다음과 같습니다.

```text
ROS component
  -> MPPI runtime
  -> route application/runtime
  -> world runtime
```

- `src/world/`: raw world와 coherent publication
- `src/route_application/`: planning, materialization, activation, execution publication use case
- `src/runtime/`: ROS-free MPPI application service/config
- `src/runtime/ros/`: ROS adapter와 composition root

private source include root를 package 전체에 다시 열거나 ROS-free target에서 ROS header를 참조하지 않습니다. CMake target과 header-graph test가 이 방향을 검사합니다.

## 6. 새 ROS node 추가

1. node의 owner와 input/output contract를 문서로 먼저 정의한다.
2. source는 `drone_city_nav/src`, 필요한 public interface만 `include/drone_city_nav`에 둔다.
3. `drone_city_nav/CMakeLists.txt`의 가장 좁은 target에 등록한다.
4. C++ default와 YAML default를 함께 추가한다.
5. main graph 구성 요소면 launch wiring을 추가한다.
6. topic, QoS, frame, timestamp, raw/executable/debug classification을 문서화한다.
7. unit test와 launch/contract test를 추가한다.
8. container에서 format, targeted tests, quality gate를 실행한다.

## 7. 새 parameter 추가

다음을 한 change에서 처리합니다.

- C++ default
- `urban_mvp.yaml` default
- range/sanitization
- 관련 fingerprint 또는 runtime manifest override
- unit/config test
- `docs/configuration.md`
- 동작 변화에 맞는 architecture/diagnostics/troubleshooting 문서

YAML이 load되었을 때와 그렇지 않을 때 의미가 달라지는 hidden default를 만들지 않습니다.

## 8. 새 topic 추가

설계 표를 먼저 작성합니다.

| 항목 | 결정할 내용 |
|---|---|
| Publisher/Subscriber | 어느 node가 소유하는가? |
| Message | 기존 typed contract로 충분한가? |
| QoS | reliability, durability, depth가 의미와 맞는가? |
| Frame | `map`, NED, sensor frame 중 무엇인가? |
| Time | source stamp와 receive stamp를 어떻게 보존하는가? |
| Classification | raw input, executable output, debug-only 중 무엇인가? |
| Failure | stale, out-of-order, producer restart 때 어떻게 되는가? |
| Evidence | 어떤 log/test가 올바른 전달을 증명하는가? |

debug topic을 planner의 authoritative input으로 연결하지 않습니다.

## 9. planning stage 추가

코드 전에 다음 contract를 정합니다.

- input artifact와 owner
- output artifact와 owner
- raw/world revision binding
- hard validation rule
- failure 시 기존 owner에 미치는 영향
- timing field와 diagnostic reason
- unit/state-machine test
- integration acceptance scenario

geometry를 바꾸는 stage와 단순 진단 stage를 구분합니다. 진단용 stage가 몰래 executable geometry를 수정해서는 안 됩니다.

## 10. 테스트 작성 위치

| 변경 | 권장 테스트 |
|---|---|
| 순수 C++ 알고리즘/contract/state machine | `drone_city_nav/tests/` direct unit test |
| launch, topic, QoS, script, telemetry schema | `scripts/tests/` Python contract test |
| 실제 component transaction/concurrency | C++ API/state-machine test; source text 순서 분석으로 대체 금지 |
| mission behavior | headless scenario와 retained run evidence |
| timing/resource | 반복 run 분포와 explicit threshold |

## 11. 기여 workflow

```bash
# Inside the supported dev container
make format
make test
make test-scripts
make quality

# On the host, review only intended changes
git status --short
git diff --check
```

주의 사항:

- broad whole-repository formatter를 실행하지 않는다.
- `build/`, `install/`, `log/`, bag, generated runtime artifact를 commit하지 않는다.
- behavior가 바뀌면 config/architecture/diagnostics/troubleshooting 문서를 함께 갱신한다.
- accepted old trajectory가 새 candidate 실패로 사라지지 않는지 확인한다.
- offboard continuity와 rejection reason을 진단할 수 있어야 한다.
- contribution 전 [`CPP_BEST_PRACTICES.md`](../CPP_BEST_PRACTICES.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md), [`AGENTS.md`](../AGENTS.md)를 다시 확인한다.

## 12. 고급 학습 과제

### 과제 A: run pair audit

두 headless run을 고유 ID로 실행한 뒤 `compare_run_manifests.py`로 입력 차이가 없는지 확인하고, `summarize_mppi_track.py` 출력에서 limiter와 hold 비율을 비교합니다. 결과 차이를 “GPU가 느렸다”처럼 한 변수로 단정하지 말고 tick timing, world age, planner lead time을 함께 설명합니다.

### 과제 B: contract 추적

`MppiTrajectoryHorizon` message 정의에서 시작해 production publisher, execution commit, offboard subscriber, feedback publication, 관련 tests까지 `rg`로 추적합니다. 각 단계의 owner, sequence/revision, failure behavior를 표로 작성합니다.

### 과제 C: 안전한 parameter proposal

새 parameter 하나를 실제로 구현하지 말고 설계안만 작성합니다. default, range, owner, fingerprint, manifest, diagnostic, unit test, headless acceptance 영향을 모두 채우면 구현 준비가 된 것입니다.

### 과제 D: performance hypothesis

`mppi_ticks.jsonl`에서 whole tick의 p95 contributor를 식별하고 한 가지 최적화 가설을 제안합니다. raw validation을 줄이는 대신 중복 계산, allocation, stale work coalescing, diagnostic backpressure 중 어디를 개선할지 근거를 제시합니다.

## 13. 다음 학습 경로

- PX4 offboard와 message: `docs/drone_control.md`, `px4_msgs`
- 3D mapping: `docs/obstacle_mapping.md`, `docs/world3d.md`
- Incremental planning: `docs/replanning.md`, D* Lite 원 논문
- Sampling-based control: `docs/trajectory_optimization.md`, MPPI 이론
- Localization: `docs/localization.md`, lidar-inertial odometry와 observability
- Runtime evidence: `docs/diagnostics.md`, `docs/testing.md`, `docs/performance.md`
- Multi-agent coordination: architecture의 mission layer와 cooperative space-time contract

[가이드 시작으로 돌아가기](README.md)
