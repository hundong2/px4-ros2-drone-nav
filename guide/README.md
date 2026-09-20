# PX4 ROS 2 Drone Navigation 한국어 학습 가이드

이 가이드는 이 저장소를 처음 보는 학습자가 PX4 SITL, ROS 2, Gazebo의 역할을 이해하는 단계부터 실제 비행 증거를 해석하고 안전 계약을 확장하는 단계까지 순서대로 학습하도록 구성했습니다. 설명은 한국어로 작성했지만 코드 식별자, 명령, 로그 필드 이름은 원문 그대로 유지합니다.

> **안전 경고**
>
> 이 프로젝트는 시뮬레이션 중심 연구용 스택이며 실제 항공기에 대해 인증되거나 검증되지 않았습니다. 아래 실습도 PX4 SITL과 Gazebo만을 대상으로 합니다. 실제 기체에 적용하려면 별도의 위험 분석, 하드웨어별 failsafe, 통제된 시험 절차, 법규 검토가 필요합니다.

## 학습 목표

전체 과정을 마치면 다음을 할 수 있습니다.

- PX4, ROS 2, Gazebo, Micro XRCE-DDS가 맡는 역할을 구분한다.
- 정적 지도와 3D lidar 기반 no-static 실행의 차이를 설명한다.
- 컨테이너 기반 공식 워크플로로 빌드, 테스트, headless/GUI 시뮬레이션을 실행한다.
- point-to-point scenario와 환경 변수로 임무를 구성한다.
- raw occupancy, persistent D* Lite, GPU MPPI, execution horizon의 데이터 흐름을 추적한다.
- hold, braking, horizon expiry, raw collision validation 등 안전 경계를 설명한다.
- run manifest와 JSONL 진단을 이용해 재현 가능한 장애 분석을 수행한다.
- 기존 ownership과 compile-time 경계를 보존하며 노드, 파라미터, topic, planning stage를 확장한다.

## 사전 요구 사항

- Linux 호스트와 POSIX shell
- Git과 Docker를 실행할 권한
- NVIDIA GPU 및 NVIDIA Container Toolkit
- GUI 실행 시 X11 또는 XWayland 접근
- 첫 bootstrap에서 여러 GiB를 내려받고 빌드할 시간과 디스크 공간

ROS 2, Gazebo, PX4를 호스트에 따로 설치하는 방식은 지원 경로가 아닙니다. 프로젝트 컨테이너가 고정된 도구와 의존성을 제공합니다.

## 학습 순서

| 단계 | 문서 | 결과 |
|---|---|---|
| 1 | [기초 개념](01_foundations.md) | 시스템 구성 요소, 좌표계, 핵심 용어를 설명한다. |
| 2 | [설치와 첫 비행](02_setup_and_first_flight.md) | 공식 컨테이너 경로로 준비, 빌드, 테스트, 최소 비행을 수행한다. |
| 3 | [임무와 내비게이션 파이프라인](03_mission_and_navigation.md) | scenario에서 PX4 setpoint까지의 흐름을 추적한다. |
| 4 | [안전과 운영](04_safety_and_operations.md) | fail-closed 동작과 여러 임무 모드의 운영 경계를 이해한다. |
| 5 | [테스트와 디버깅](05_testing_and_debugging.md) | 테스트 계층, 로그, manifest, JSONL을 이용해 문제를 좁힌다. |
| 6 | [성능·배포·확장·기여](06_advanced_and_contributing.md) | 성능을 계측하고 아키텍처 계약을 지키며 확장한다. |

처음 실행만 필요하면 1단계의 용어와 2단계를 먼저 읽고, 실제 코드 변경 전에는 반드시 3~6단계까지 읽으세요.

## 시스템을 한 장으로 보기

```text
Gazebo physics + GPU lidar                         PX4 SITL state
              |                                         |
              +---------- ROS 2 / bridge ---------------+
                                   |
                       obstacle_memory_3d_node
                                   |
                  revisioned raw Occupancy3D evidence
                                   |
                         production_mppi_node
                +------------------+------------------+
                |                                     |
       persistent D* Lite route               CUDA MPPI horizon
                |                                     |
                +---- raw swept-footprint validation--+
                                   |
                       atomic ExecutionPlan3D commit
                                   |
                    timestamped MppiTrajectoryHorizon
                                   |
                         mppi_offboard_node
                                   |
                           PX4 setpoints
```

핵심 원칙은 디버그 시각화나 soft risk가 물리적 충돌 판정을 대신하지 않는다는 점입니다. raw occupied evidence와 비행 영역이 hard reject의 근거이고, 실행 가능한 새 경로가 없으면 기존 경로를 무기한 연장하지 않고 검증된 정지 또는 position hold로 전환합니다.

## 공식 명령 빠른 참조

저장소 루트에서 실행합니다.

```bash
# Fresh checkout preparation and first urban flight
./scripts/bootstrap.sh

# Preparation only or headless first run
./scripts/bootstrap.sh --no-run
./scripts/bootstrap.sh --headless

# Common development workflow
./scripts/build.sh
./scripts/test.sh
./scripts/sim_headless.sh
./scripts/sim_gui.sh

# Inspect cleanup targets, then stop only this repository's simulation stack
./scripts/stop_sim.sh --dry-run
./scripts/stop_sim.sh
```

대화형 컨테이너가 필요할 때만 `./scripts/dev_shell.sh`를 시작하고, 그 안에서 `make build`, `make test`, `make test-scripts`, `make quality`, `make sim-headless` 같은 저장소 대상만 사용합니다. 호스트에서 ad-hoc top-level CMake를 실행하지 않습니다.

## 격리된 실습 도구

[`examples/README.md`](examples/README.md)의 도구는 Python 표준 라이브러리만 사용하고 비행 제어 또는 빌드 산출물을 수정하지 않습니다.

| 실습 | 도구 | 학습 포인트 |
|---|---|---|
| Scenario preflight | `examples/inspect_scenario.py` | 목표점, 비행 고도, 경로 길이를 실행 전에 확인한다. |
| Tick diagnostics | `examples/summarize_mppi_track.py` | limiter, planning state, hold 비율, 속도를 집계한다. |
| Run comparison | `examples/compare_run_manifests.py` | 두 실행의 commit, 입력 hash, profile, override 차이를 찾는다. |

이 도구들은 학습용 read-only 보조 도구입니다. 프로젝트의 공식 scenario 검사, headless mission check, acceptance gate를 대체하지 않습니다.

## 검증 수준 구분

| 수준 | 증거 | 답할 수 있는 질문 |
|---|---|---|
| 정적 점검 | scenario, 설정, source contract | 입력 형식과 선언된 계약이 맞는가? |
| 단위·스크립트 테스트 | `make test`, `make test-scripts` | 작은 알고리즘과 orchestration 계약이 유지되는가? |
| headless mission check | `./scripts/sim_headless.sh` | 통합 스택이 제한 시간 내 임무와 안전 gate를 통과하는가? |
| 반복 비행 증거 | 서로 다른 run ID의 manifest와 metrics | 결과가 재현되며 성능 분포가 허용 범위인가? |
| 실제 기체 검증 | 이 저장소 범위 밖 | 하드웨어와 현실 환경에서 안전한가? 현재 답할 수 없음. |

## 원문 자료

- [프로젝트 README](../README.md)
- [코드 아키텍처 분석과 대화형 도식](../docs/archify/README.md)
- [프로젝트 개요](../docs/overview.md)
- [설치 요구 사항](../docs/installation.md)
- [아키텍처](../docs/architecture.md)
- [내비게이션 파이프라인](../docs/navigation_pipeline.md)
- [테스트와 acceptance gate](../docs/testing.md)
- [보안 정책](../SECURITY.md)

저장소는 활발히 변할 수 있으므로 구체적인 기본값과 지원되는 override는 항상 현재 checkout의 `README.md`, `Makefile`, `scripts/run_drone_nav_sim.sh`, `drone_city_nav/config/urban_mvp.yaml`을 최종 근거로 사용하세요.
