# 02. 설치와 첫 비행

## 1. 지원 환경 확인

공식 경로는 NVIDIA GPU가 연결된 Linux 호스트의 Docker 컨테이너입니다. Windows나 macOS에서 소스 파일을 열 수는 있지만, 문서의 simulation workflow가 그대로 지원된다는 뜻은 아닙니다.

호스트에서 다음을 확인합니다.

```bash
git --version
docker --version
docker ps
nvidia-smi
docker info | grep -i runtime
```

`docker ps`가 permission error를 내면 Docker group/daemon 설정을 먼저 고칩니다. NVIDIA runtime 검사를 건너뛰고 ROS 노드 단계에서 CUDA 오류를 해결하려 하지 마세요. repository wrapper가 컨테이너 시작 전에 이를 검사합니다.

## 2. 빠른 준비 방법

새 clone에서 가장 간단한 경로입니다.

```bash
git clone https://github.com/formiat/px4-ros2-drone-nav.git
cd px4-ros2-drone-nav
./scripts/bootstrap.sh --no-run
```

`bootstrap.sh`는 다음을 준비합니다.

1. host tool과 NVIDIA runtime 확인
2. development image 준비
3. `external/PX4-Autopilot`에 PX4 v1.17.0 준비
4. 컨테이너 안에서 PX4 SITL build
5. ROS 2 workspace build
6. versioned urban environment assets 준비

GUI까지 즉시 실행하려면 option을 빼고, headless로 실행하려면 다음을 사용합니다.

```bash
./scripts/bootstrap.sh
./scripts/bootstrap.sh --headless
```

첫 실행은 여러 GiB 다운로드와 수십 분의 build가 필요할 수 있습니다. 각 단계는 결과가 이미 있으면 건너뛰므로 실패 원인을 해결한 뒤 같은 명령을 재실행할 수 있습니다.

## 3. 단계별 준비 방법

문제를 한 단계씩 분리할 때 공식 script를 사용합니다.

```bash
./scripts/build_dev_image.sh
./scripts/setup_px4_autopilot.sh
./scripts/dev_shell.sh make -C external/PX4-Autopilot px4_sitl
./scripts/build.sh
./scripts/test.sh
```

정상 workflow에서는 ROS setup 파일을 수동으로 source하지 않습니다. shared container entrypoint가 `/opt/ros/${ROS_DISTRO}/setup.bash`와 `/opt/px4_msgs_ws/install/setup.bash`를 처리합니다. 커스텀 image를 의도적으로 시험하는 경우에만 `ROS_SETUP_FILE`과 `PX4_MSGS_SETUP_FILE`을 override합니다.

## 4. build와 test

호스트 wrapper:

```bash
./scripts/build.sh
./scripts/test.sh
```

대화형 컨테이너 안:

```bash
./scripts/dev_shell.sh
make build
make test
make test-scripts
make quality
```

`make build`는 `colcon build --packages-select drone_city_nav`를 실행하고 `build/`, `install/`, `log/`를 사용합니다. ad-hoc `cmake ..` build tree를 만들지 않습니다.

## 5. 최소 headless 실행

```bash
./scripts/sim_headless.sh
```

이 wrapper는 build 후 headless simulation과 mission check를 실행합니다. single-vehicle 기본 localization profile은 `lidar_inertial`, map mode는 no-static, lidar profile은 `3d`입니다. 실행 전에 stale simulation을 정리하고, 끝날 때도 같은 repository scope의 simulation process/container를 정리합니다.

개별 실행을 구분하려면 고유한 ID와 directory를 지정합니다.

```bash
DRONE_GAZEBO_RUN_ID=learning-run-001 \
DRONE_GAZEBO_LOG_DIR=log/learning-run-001 \
./scripts/sim_headless.sh
```

반복 acceptance run은 동시에 실행하지 말고 서로 다른 ID와 directory로 순차 실행합니다.

## 6. 한 개 목표점 실습

`MISSION_GOALS_XYZ_M`은 `x,y,z;x,y,z;...` 형식입니다. 하나의 triple이면 single-destination mission입니다.

```bash
MISSION_GOALS_XYZ_M='216,378,18' \
DRONE_GAZEBO_RUN_ID=one-goal-001 \
DRONE_GAZEBO_LOG_DIR=log/one-goal-001 \
./scripts/sim_headless.sh
```

목표점은 현재 flight envelope인 `1.0 <= z < 32.0 m` 안에 있어야 합니다. 새로운 경로는 낮은 위험의 빈 도시에서 먼저 검증하고, 복잡한 환경으로 바로 확대하지 않습니다.

## 7. versioned urban scenario 실행

환경 asset까지 포함된 공식 urban point-to-point workflow입니다.

```bash
./scripts/sim_urban_point_to_point_headless.sh
```

GUI:

```bash
./scripts/sim_urban_point_to_point_gui.sh
```

이 target은 `scripts/prepare_environment_simulation.py`로 versioned asset을 준비하고, `drone_city_nav/config/urban_circuit_practice_01_point_to_point_scenario.json`을 사용해 no-static 3D lidar run을 구성합니다.

## 8. GUI와 정리

```bash
./scripts/sim_gui.sh
```

GUI 실행이 끝나거나 중단된 뒤 다른 Gazebo instance를 시작하기 전에 cleanup 대상을 확인합니다.

```bash
./scripts/stop_sim.sh --dry-run
./scripts/stop_sim.sh
```

`stop_sim.sh`는 이 저장소의 simulation target을 실행하는 container와 관련 Gazebo/PX4/ROS process를 대상으로 합니다. `--dry-run`은 종료하지 않고 후보만 출력합니다.

## 9. 결과 확인

wrapper가 출력한 run directory를 기준으로 다음을 확인합니다.

```text
manifest.json
ros_drone_nav.log
gz_drone_nav.log
mppi/mppi_ticks.jsonl
mppi/mppi_track.jsonl
resources.csv
resources_host.json
```

고정된 `log/latest`가 방금 실행한 run이라고 가정하지 마세요. `manifest.json`의 commit, input hash, runtime profile, effective override를 먼저 확인한 뒤 로그를 읽습니다.

## 10. 첫 실행 체크리스트

- [ ] Docker와 NVIDIA runtime preflight를 통과했다.
- [ ] source tree와 generated file이 일반 사용자 소유다.
- [ ] `./scripts/build.sh`가 성공했다.
- [ ] `./scripts/test.sh`가 성공했다.
- [ ] headless wrapper가 run directory를 출력했다.
- [ ] mission result와 physical crash 여부를 확인했다.
- [ ] manifest의 commit과 `dirty` 값을 확인했다.
- [ ] cleanup 후 stale Gazebo/PX4 process가 남지 않았다.

## 11. 자주 하는 실수

| 실수 | 올바른 접근 |
|---|---|
| 호스트에 ROS/Gazebo/PX4를 따로 설치해 섞음 | container workflow만 사용 |
| root로 build해 workspace ownership이 깨짐 | wrapper의 UID/GID 전달 사용 |
| `cmake`를 직접 실행 | `./scripts/build.sh` 또는 `make build` |
| no-static인데 `LIDAR_PROFILE=none` | `LIDAR_PROFILE=3d` 유지 |
| 실패 후 새 GUI를 바로 시작 | `stop_sim.sh --dry-run`, 그 다음 `stop_sim.sh` |
| log 하나만 보고 tuning 시작 | manifest와 진단 순서부터 확인 |

다음 단계: [임무와 내비게이션 파이프라인](03_mission_and_navigation.md)
