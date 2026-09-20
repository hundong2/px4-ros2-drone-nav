# PX4 ROS 2 드론 내비게이션

[English README](README.md) | [한국어 학습 가이드](guide/README.md) |
[한국어 아키텍처 분석](docs/archify/README.md)

이 저장소는 PX4/Gazebo 드론 내비게이션 스택을 위한 ROS 2 워크스페이스입니다.
주요 패키지는 `colcon`으로 빌드하는 ament CMake 패키지인
`drone_city_nav`입니다.

## 데모 영상

[![도시 환경에서 지도 없이 수행하는 자율 3D 내비게이션](https://img.youtube.com/vi/rKXcERqb9Ho/maxresdefault.jpg)](https://www.youtube.com/watch?v=rKXcERqb9Ho)

[YouTube에서 보기](https://www.youtube.com/watch?v=rKXcERqb9Ho): v0.2.1(2026년 9월)에
공개된 데모로, 정적 지도 없이 3D 라이다 증거만 사용해 Urban Circuit Practice 01
환경을 지점 간 비행합니다.

## 빠른 시작

Docker, git, NVIDIA 컨테이너 런타임이 설치된 Linux 호스트에서 다음 스크립트 하나로
새 저장소 복제본을 준비하고 도시 지점 간 시뮬레이션을 시작할 수 있습니다.

```bash
git clone https://github.com/formiat/px4-ros2-drone-nav.git
cd px4-ros2-drone-nav
./scripts/bootstrap.sh
```

이 스크립트는 개발 이미지를 빌드하고, PX4 Autopilot을 `external/`에 복제하며,
컨테이너 안에서 PX4 SITL과 워크스페이스를 빌드합니다. 이어서 버전이 지정된 도시
환경 애셋을 가져오고 Gazebo GUI 비행을 시작합니다. `--headless`는 같은 비행을
GUI 없이 미션 검사와 함께 실행하며, `--no-run`은 준비만 수행합니다. 이미 결과가
있는 단계는 모두 건너뛰므로 스크립트를 다시 실행해도 됩니다. 첫 실행에서는 수 GB를
다운로드하며 빌드에 수십 분이 걸립니다.

## 로드맵

프로젝트 로드맵은 [`docs/roadmap.md`](docs/roadmap.md)에서 관리합니다. 요격 미션,
레이더 기반 표적 추적, 예측 유도, 다중 드론 시나리오, 협력 항공 교통, 일반화된 정적
3D 통로, 정적 지도 없는 3D 라이다 인지, 라이다-관성 위치 추정, 라이다나 정적 지도
없는 비전 전용 3D 인지를 다룹니다.

## 릴리스

코드 릴리스는 `main`에서 `vMAJOR.MINOR.PATCH` 태그를 사용하며
[`CHANGELOG.md`](CHANGELOG.md)에 설명합니다. 환경 애셋 번들은 별도의
`environment-assets-*` 태그를 사용합니다. 현재 릴리스는 `v0.3.0`으로, GNSS나
자력계 없이 복잡한 3D 도시 환경에서 정적 지도 없이 지점 간 내비게이션을 수행합니다.
각 비행의 런타임 매니페스트에는 패키지 버전과 `git describe` 결과가 기록됩니다.

## 상태 및 안전

이 프로젝트는 시뮬레이션 중심의 연구·개발 스택입니다. Gazebo의 PX4 SITL로
테스트했으며 실제 항공기 운용에 대한 인증이나 검증을 받지 않았습니다.

계획, 시뮬레이션, 오프보드 제어 테스트베드로 사용하십시오. 별도의 안전 검토,
하드웨어별 안전장치 설계, 통제된 시험 환경, 현지 규정 준수 없이 실제 드론에
사용하지 마십시오. 온보드 컴퓨터에서 실행한 적이 없으며, 자원 수치는 워크스테이션에서
측정했습니다([docs/resource_budget.md](docs/resource_budget.md)). 단일 기체 비행은
기본적으로 GNSS 없이 수행됩니다. 라이다-관성 추정기가 시뮬레이션 GNSS, 자력계,
시뮬레이션 헤딩 소스를 대체합니다
(`LOCALIZATION_PROFILE=lidar_inertial`, [docs/localization.md](docs/localization.md)).
`LOCALIZATION_PROFILE=gnss`를 지정하면 GNSS 프로필로 돌아가며, 다중 기체 미션은
아직 이 프로필로 비행합니다.

## 승인된 명령

저장소 루트에서 개발 컨테이너를 통해 명령을 실행하십시오. 이 저장소에서 지원하는
빌드, 테스트, 품질 검사, 시뮬레이션 방법은 컨테이너 워크플로뿐입니다.

일반적인 워크플로에는 최상위 래퍼 스크립트를 사용합니다.

```bash
./scripts/bootstrap.sh
./scripts/build.sh
./scripts/test.sh
./scripts/sim_gui.sh
./scripts/sim_headless.sh
./scripts/sim_intercept_gui.sh
./scripts/sim_intercept_headless.sh
./scripts/sim_multi_intercept_gui.sh
./scripts/sim_multi_intercept_headless.sh
./scripts/sim_cooperative_traffic_gui.sh
./scripts/sim_cooperative_traffic_headless.sh
./scripts/sim_cooperative_traffic_urban_gui.sh
./scripts/sim_cooperative_traffic_urban_headless.sh
./scripts/sim_urban_point_to_point_gui.sh
./scripts/sim_urban_point_to_point_headless.sh
ENVIRONMENT_DEMO_ID=urban_circuit_practice_01 ./scripts/sim_environment_demo.sh
./scripts/stop_sim.sh
```

이 래퍼들은 현재 UID/GID로 개발 컨테이너를 시작하므로 생성되거나 포맷된 파일의
소유권이 실행 사용자에게 유지됩니다. 모든 `sim_*.sh` 래퍼는 실행 전과 종료 시점에
종료 방식과 관계없이 `./scripts/stop_sim.sh`와 같은 정리를 수행합니다.
`stop_sim.sh`는 시뮬레이션 대상을 실행 중인 이 저장소의 모든 컨테이너와 호스트의
모든 시뮬레이션 프로세스를 중지하며, 그 밖의 항목은 건드리지 않습니다. 래퍼들은
매 실행 전 일주일이 지난 시뮬레이션 로그도 삭제합니다
(`./scripts/prune_sim_logs.sh`: `log/` 항목, 실행 디렉터리, PX4 비행 로그가
대상이며 `log/tools`와 `.keep` 파일을 보유한 항목은 유지됩니다. `--dry-run`은
대상을 미리 보여 주며 `DRONE_GAZEBO_PRUNE_LOGS=false`는 삭제를 비활성화합니다).
대화형 컨테이너 셸이 필요하면 `./scripts/dev_shell.sh`를 사용할 수 있습니다.
그 셸 안에서는 다음 대상을 사용하십시오.

모든 개발 컨테이너에는 NVIDIA 런타임이 필요하며 자동으로 제공됩니다. 호스트에서
NVIDIA 런타임을 사용할 수 없으면 컨테이너 래퍼가 시작 전에 실패하므로 CUDA 런타임
오류가 ROS 노드나 테스트 단계까지 지연되지 않습니다.

```bash
make build
make test
make test-scripts
make quality
make format
make sim-gui
make sim-headless
make sim-intercept-gui
make sim-intercept-headless
make sim-multi-intercept-gui
make sim-multi-intercept-headless
make sim-cooperative-traffic-gui
make sim-cooperative-traffic-headless
make sim-cooperative-traffic-urban-gui
make sim-cooperative-traffic-urban-headless
make sim-urban-point-to-point-gui
make sim-urban-point-to-point-headless
ENVIRONMENT_DEMO_ID=urban_circuit_practice_01 make sim-environment-demo
```

기본 `sim` 미션은 순차적으로 지점 간 웨이포인트를 방문합니다. 기본 경로는 도시의
네 모서리를 따릅니다. `x,y,z;x,y,z;...` 문법을 사용하는
`MISSION_GOALS_XYZ_M`으로 경로를 재정의할 수 있습니다. 각 웨이포인트는 종단점이며,
기체가 마지막 웨이포인트에서 안정된 뒤에만 미션이 성공합니다.

단일 목적지 미션은 같은 매개변수에 `x,y,z` 삼중항 하나를 사용합니다.

```bash
MISSION_GOALS_XYZ_M='216,378,18;216,54,18;54,378,18;54,54,18' \
  ./scripts/sim_headless.sh
```

격리된 CUDA MPPI 벤치마크를 빌드하고 실행합니다.

```bash
make mppi-benchmark \
  MPPI_BENCHMARK_ARGS="--scenario urban_blocks --rollouts 8192 --steps 80"
```

벤치마크 대상은 명시적으로 선택해야 하며 일반 ROS 런타임 대상에 CUDA를 추가하지
않습니다. NVIDIA 컨테이너 런타임이 필요하고, 해당 런타임을 사용할 수 있으면
`scripts/container_run.sh`가 호스트 GPU를 자동으로 전달합니다.

공유 컨테이너 엔트리포인트는 명령을 실행하기 전에 지원되는 ROS 2 및 PX4 메시지
워크스페이스를 자동으로 source합니다. 일반 워크플로에서는 ROS나 `px4_msgs` setup
파일을 수동으로 source하지 마십시오. 사용자 지정 이미지나 외부 의존성 체크아웃을
사용하려면 스크립트를 편집하는 대신 `ROS_SETUP_FILE` 또는
`PX4_MSGS_SETUP_FILE`을 재정의하십시오.

ROS 패키지를 빌드합니다.

```bash
./scripts/build.sh
```

단위 테스트를 실행합니다.

```bash
./scripts/test.sh
```

대화형 컨테이너 셸 안에서 스크립트 수준 테스트를 실행합니다.

```bash
make test-scripts
```

대화형 컨테이너 셸 안에서 파일을 변경하지 않는 C++ 품질 검사를 실행합니다.

```bash
make quality
```

대화형 컨테이너 셸 안에서 변경된 C++ 파일만 포맷합니다.

```bash
make format
```

GUI 시뮬레이션을 실행합니다.

```bash
./scripts/sim_gui.sh
```

시뮬레이션 실행은 기본적으로 정적 지도를 사용하지 않습니다. 정적 지도 실행이
필요할 때는 `ENABLE_STATIC_MAP=true`를 명시적으로 설정하십시오.

## 환경 관람자 데모

PX4, ROS, RViz, 라이다, 미션 없이 다운로드한 환경을 실행합니다.

```bash
ENVIRONMENT_DEMO_ID=urban_circuit_practice_01 ./scripts/sim_environment_demo.sh
```

Gazebo의 자유 카메라가 관람자 역할을 합니다. 일반적인 마우스 및 키보드 카메라
조작으로 월드를 살펴볼 수 있습니다. 데모는 로컬 시각 리소스를 구체화하며, 관련
환경 애셋을 가져온 뒤에는 네트워크 연결이 필요하지 않습니다.

카메라 위치, 방향, 월드 공간의 전방 방향은 기본적으로 1초에 한 번
`log/environment_demo/<environment-id>/gz_gui_free_camera.jsonl`에 기록됩니다.
`GZ_GUI_CAMERA_LOG_INTERVAL_S`와 `GZ_GUI_CAMERA_LOG_FILE`로 기록 주기나
대상을 재정의할 수 있습니다.

사용 가능한 ID는 다음과 같습니다.

```text
finals_prize_round_world_07
cave_circuit_practice_01
urban_circuit_practice_01
tunnel_circuit_practice_01
cave_world
industrial_warehouse
aws_robomaker_small_warehouse
aws_robomaker_hospital
```

처음 세 ID는 버전이 지정된 릴리스 아티팩트를 사용합니다. 나머지 ID는 로컬 평가
후보이며 캐시된 원본 애셋이 없으면 명확한 오류를 보고합니다.

`LIDAR_PROFILE=none|3d`는 프로덕션 인지 프로필을 선택합니다. 모든 시뮬레이션
엔트리포인트는 기본적으로 3D 라이다를 사용합니다. 정적 지도 실행에서는 라이다를
완전히 비활성화할 수 있습니다.

```bash
ENABLE_STATIC_MAP=true LIDAR_PROFILE=none ./scripts/sim_gui.sh
```

정적 지도 없는 내비게이션에는 `LIDAR_PROFILE=3d`가 필요하며 시작 전에 `none`을
거부합니다. 미확인 공간과 자유 공간은 통과 가능성과 기본 비용이 같고, 확인된 점유
형상만 강체 공간 장애물입니다.

로드맵 8 인수 검사는 Manhattan, 정적 지도 없음, 3D 프로필만 사용합니다.

```bash
POINT_TO_POINT_SCENARIO_PATH=drone_city_nav/config/manhattan_low_altitude_point_to_point_scenario.json \
ENABLE_STATIC_MAP=false \
LIDAR_PROFILE=3d \
REQUIRE_OBSERVED_3D_ROUTE_VOLUME_CROSSING=true \
OBSERVED_3D_ROUTE_VOLUME_BOUNDS_M='42,147,1.5,66,177,8.5' \
./scripts/sim_headless.sh
```

모든 실행은 `log/runs/<run-id>/manifest.json`을 작성합니다. 매니페스트는 정확한 Git
커밋, 내비게이션 구성, 생성된 월드, 미션 시나리오, 런타임 프로필을 SHA-256으로
결속합니다. 제한 부피 검증을 활성화하면 transient-local 구독자가 해당 부피의 정확한
관찰/점유 비트 워드도 리비전이 기록된
`raw_snapshot_3d_revision_<revision>.json` 아티팩트로 보존합니다. 헤드리스 인수
게이트는 아티팩트 해시와 페이로드, 소유권 공백 0건, 부트스트랩 이후 97%를 초과하는
경로 가용성, 일반적인 경로 없음 홀드 상태가 부트스트랩 이후 틱의 3% 미만인지,
측정된 플래너 p95 목표, 승인된 모든 후속 예약 증명을 검증합니다. 임계값과 근거는
`docs/testing.md`의 "Headless Acceptance Gate"를 참조하십시오. 여러 인수 실행을
각각 검색할 수 있게 유지해야 한다면 `DRONE_GAZEBO_RUN_ID`와
`DRONE_GAZEBO_LOG_DIR`을 설정하십시오.

정적 지도 없는 단일 기체 헤드리스 실행은 영속 3D 인수 게이트를 자동으로 활성화합니다.
반복 인수 실행은 순차적으로 수행하고, 각각 다른 `DRONE_GAZEBO_RUN_ID`와
`DRONE_GAZEBO_LOG_DIR` 값을 사용해야 매니페스트, 메트릭, 원시 부피 스냅숏을
독립적으로 감사할 수 있습니다. 선택적 경로 부피 경계는 헤드리스 평가기만 소비하며
매핑이나 계획에는 절대 제공되지 않습니다.

`POINT_TO_POINT_SCENARIO_PATH`를 설정하면 `MISSION_GOALS_XYZ_M`도 명시적으로
제공하지 않는 한 시나리오가 웨이포인트 순서를 소유합니다.

## 비행 속도 프로필

내비게이션은 지도와 무관한 하나의 수평 비행 프로필을 사용합니다. 기본값은 순항 속도
6.5 m/s(보장된 라이다 범위에 대해 센서-제동 계약이 허용하는 속도보다 약간 낮음),
절대 속도 제한 10 m/s, 최대 수평 가속도 4 m/s², 선회 시 횡가속도 6 m/s²입니다.
플래너, 유한 경로 정지 모델, PX4 구성에는 같은 값이 전달되고 `Makefile`의
시뮬레이션 대상에도 같은 순항 속도가 전달됩니다.

개별 실행의 프로필은 환경 변수로 재정의합니다.

```bash
CRUISE_SPEED_MPS=6.5 \
ABSOLUTE_SPEED_LIMIT_MPS=10 \
MAXIMUM_HORIZONTAL_ACCELERATION_MPS2=4 \
./scripts/sim_cooperative_traffic_headless.sh
```

이 값들은 지도 출처와 무관합니다. 복잡한 환경은 기본 프로필을 사용하고, Manhattan은
실험을 위해 명시적으로 더 빠른 프로필을 사용할 수 있습니다.

유한한 3대 요격기 미션을 실행합니다.

```bash
./scripts/sim_intercept_gui.sh
./scripts/sim_intercept_headless.sh
```

지점 간 미션은 계속 기본값입니다. 요격 미션은 서로 격리된 요격기 PX4/ROS 스택
3개와 회피기 스택 1개를 시작합니다. 요격기들은 서로 떨어진 도시 구역 3곳에서
시작합니다. 그중 하나는 회피기의 목적지에서 시작하지만 그 목적지는 물론 그 밖의
어떤 공격기 실측 정보도 받지 않습니다. 회피기는 요격기와 같은 속도 정책으로 고정
목표를 향해 대각선으로 비행합니다. 각 요격기는 거리, 방위각, 고도각, 방사 속도가
포함된 자체 이상적 레이더 측정만 받습니다. 독립적인 가변-dt 추적기가 예측 유도에
사용할 표적 상태를 도출합니다. 현재 표적 추정치가 가려진 동안 스캔 주기는 0.1초에서
3.0초 사이의 결정론적 상관 랜덤 워크를 따릅니다. 플래너가 해당 추정치에 대해 쓸린
원시 자유 공간 가시성을 검증하면 타입이 지정된 명령이 즉시 스캔을 발생시키고 거리
제한 없는 20 Hz 추적 모드를 시작합니다. 스캔 사이에도 추적기 관성 추적과 유도는
20 Hz로 계속됩니다. 시뮬레이션 실측 어댑터가 생성한 타입 지정 물리 표적 실측값은
3개의 시뮬레이션 레이더 어댑터와 미션 판정기만 소비할 수 있습니다. 레이더 측정과
미션 근접도는 별도로 구성한 PX4 원점이 아니라 Gazebo 모델 자세에서 계산됩니다.
네 플래너 모두 상주 월드를 보고하고, 세 추적기가 모두 유효한 표적 위치를 게시하고,
연속된 여러 샘플에서 모든 내비게이션 자세가 Gazebo 자세와 일치하는 것이 확인된 뒤에만
미션 기동을 시작합니다. 이 좌표 일치는 시작 계약입니다. 미션 기동이 시작되면 해당
에피소드 동안 래치됩니다. 이후의 내비게이션-실측 잔차는 진단 정보로 계속 표시되지만
물리적 판정을 중단하거나 편대를 홀드 상태로 전환하지 않습니다.

지도 프레임의 네 시작점과 회피기 목표는 모두
`drone_city_nav/config/intercept_scenario.json`이 소유합니다. 실행기는 표준 월드의
`map_to_sdf` 변환으로 각 Gazebo 생성 위치를 도출합니다. 셸이나 launch 파일에는
별도의 요격 생성 좌표가 없습니다.

연속 유도 목표에는 종단 목표 홀드가 없습니다. 지연을 보상한 해석적 요격 해를
사용하며 최대 15초로 제한합니다. 요격기가 이미 회피기의 이동 회랑보다 앞서 있으면
리드를 부드럽게 최대 1초로 제한합니다. 수직 예측은 표적이 제한 가속도 아래에서
상승 또는 하강을 멈추는 상황을 모델링하고, 결과를 구성된 반개방 비행 포락선으로
제한합니다. 플래너는 현재 표적의 가시성과 예측 요격점까지의 경로를 별도로 취급합니다.
현재 표적이 보이면 직접 MPPI 요격을 계속 활성화하고, 전체 리드 경로가 막히면 직접
모드를 해제하는 대신 예측점을 현재 표적 쪽으로 줄입니다. 기본적으로 세 요격기 모두
측정된 표적 방향을 예측합니다. `INTERCEPT_DIRECTIONAL_HYPOTHESES_ENABLED=true`를
설정하면 나머지 두 요격기에 `+45`도와 `-45`도의 장거리 운동 가설을 할당합니다.
이 오프셋은 30 m 아래에서 연속적으로 0에 수렴하고 횡방향 리드는 70 m로 제한됩니다.
레이더 추적 자체는 회전시키거나 위조하지 않습니다.

어떤 요격기와 회피기 사이든 Gazebo에서 물리적으로 측정한 쓸린 분리 거리가 5 m이면
해당 쌍에 타입이 지정된 `VehicleDestroyed` 이벤트를 게시합니다. 두 기체의 오프보드
노드는 강제 무장을 해제하고 양쪽의 사망을 확인하며, 나머지 요격기들은 타입이 지정된
홀드 목표를 받아 확인된 정지 위치 홀드로 안정화됩니다. 요격기끼리 물리적으로
충돌하거나 5 m 근접 충돌이 발생하면 관련 기체만 파괴되고 다른 요격기를 사용할 수
있는 동안 미션은 계속됩니다. 회피기가 목표에 먼저 도달하면 목표 반경 안에 들어온
첫 공중 샘플이 결과를 래치하고, 생존한 모든 요격기는 추적을 중단해 확인된 정지 위치
홀드로 안정화됩니다. 어떤 기체도 무장 해제되지 않습니다. 이후 관성에 의한 접근은
첫 결과를 바꿀 수 없지만, 포획 반경에 진입하면 일반적인 쌍 무장 해제가 계속 적용됩니다.
회피기의 목표 도달은 요격 실패이지만 기술적으로는 여전히 성공한 시뮬레이션 결과입니다.
GUI 워크플로에서 RViz와 Gazebo는 처음에 공격기 `evader`를 따라갑니다. 기본
`first_living` 정책은 관찰 중인 기체가 사망하고 3초 뒤 시나리오에서 첫 번째 생존
기체를 선택합니다. RViz는 모든 요격기의 경량 경로와 방향 화살표를 계속 표시합니다.
전체 MPPI, 메모리, 라이다 계층은 현재 관람자에서만 라우팅되며 같은 관람자 선택에
따라 전환됩니다. 선택적인 요격기별 메모리 포인트 클라우드는 기본적으로 비활성화되어
있습니다. GUI 워크플로는 어느 결과가 나와도 열린 상태를 유지합니다. 헤드리스
워크플로는 적용 가능한 모든 홀드 및 무장 해제 안정화가 로그에서 확인된 뒤에만
종료합니다. 미션에는 회피기 한 대만 있으며 공격기를 다시 생성하거나 다른 에피소드를
시작하지 않습니다.

유한한 요격기 2대 대 공격기 2대 미션은 별도로 실행합니다.

```bash
./scripts/sim_multi_intercept_gui.sh
./scripts/sim_multi_intercept_headless.sh
```

이 엔트리포인트는 `drone_city_nav/config/multi_intercept_2v2_scenario.json`과 함께
동일한 범용 launch 및 내비게이션 코드를 사용합니다. 공격기들은 목적지에서 가장 먼
도시의 짧은 변에서 시작합니다. `evader_0`는 해당 모서리에서 시작하고 `evader_1`은
그 변을 따라 한 블록 안쪽에서 시작합니다. 요격기들은 반대쪽 짧은 변에서 목적지
모서리 `(54, 378, 18)` 옆에 출발합니다. 두 공격기는 같은 고정 목표로 비행합니다.
각 요격기는 독립된 레이더 시뮬레이터와 다중 표적 추적기를 소유합니다. 해당
`RadarScan`에는 활성 공격기마다 상대 구면 탐지 하나가 들어가며 절대 표적 좌표는
여전히 노출하지 않습니다.

중앙 타입 지정 할당 조정기는 추정 등속 요격 시간을 비교해 결정론적 최소 비용 할당을
계산합니다. 2x2 사례에서는 유효한 추적이 허용할 때 서로 다른 요격기로 활성 공격기
둘을 모두 담당합니다. 할당을 변경하려면 실질적이며 지속되는 비용 개선이 필요하므로
표적이 빠르게 요동하며 바뀌는 일을 방지합니다. 공격기가 요격되거나 목표에 도달하거나
파괴되면 향후 할당에서 즉시 제거하고, 생존한 요격기를 남은 활성 공격기에 재할당합니다.
무선 전송과 통신 장애는 시뮬레이션하지 않습니다.

판정기는 공격기마다 최초의 종단 결과를 정확히 하나 기록합니다. 요격기-공격기 분리
거리가 5 m이면 해당 쌍만 파괴하고 무장을 해제하며, 다른 할당은 계속됩니다. 모든
공격기에 종단 결과가 생기면 유한 에피소드가 끝납니다. 공격기가 여전히 활성 상태인데
남은 요격기가 없으면 실패합니다. 헤드리스 검증은 포획된 모든 쌍에 물리적 Gazebo
근접 증거와 확인된 무장 해제가 있고, 모든 생존자가 위치 홀드를 확인했으며, 어떤
기체도 건물과 충돌하지 않을 것을 요구합니다. 이 지원 시나리오에서는 방향성 운동
가설을 비활성화합니다.

`2x2` GUI는 `evader_0`를 관람자로 시작하고 순환형 `next_living` 정책을 사용합니다.
해당 기체가 파괴된 지 3초 뒤 `evader_1`이 살아 있으면 카메라가 이를 선택합니다.
그렇지 않으면 시나리오 순서대로 계속 진행해 첫 번째 생존 기체로 순환합니다. Gazebo,
RViz `drone_follow` 프레임, 선택된 플래너 진단은 같은 타입 지정 관람자 선택을
소비합니다.

협력 민간 교통 미션을 실행합니다.

```bash
./scripts/sim_cooperative_traffic_gui.sh
./scripts/sim_cooperative_traffic_headless.sh
```

가져온 Urban Circuit Practice 01 환경에서 정적 지도 없는 협력 미션을 실행합니다.
두 엔트리포인트 모두 3D 라이다와 온라인 장애물 메모리만 사용합니다.

```bash
./scripts/sim_cooperative_traffic_urban_gui.sh
./scripts/sim_cooperative_traffic_urban_headless.sh
```

이 대상은 버전이 지정된 환경 릴리스 아티팩트를 검증하고 설치하며, Gazebo Harmonic
충돌 월드를 구체화하고, 모든 정적 내비게이션 아티팩트 경로를 비워 둡니다. 그런 다음
`drone_city_nav/config/cooperative_traffic_urban_scenario.json`에서 4기체 온라인
매핑 시나리오를 시작합니다.

같은 환경에서 기본 단일 드론 정적 지도 없는 비행을 실행합니다.

```bash
./scripts/sim_urban_point_to_point_gui.sh
./scripts/sim_urban_point_to_point_headless.sh
```

시나리오는
`drone_city_nav/config/urban_circuit_practice_01_point_to_point_scenario.json`에
한 번만 정의됩니다. 지도 공간의 시작 자세는 표준 월드 계약에 따라 Gazebo용으로
변환되며, 같은 자세가 PX4 원점과 내비게이션 시작점도 설정합니다. 헤드리스 대상은
영속 전체 3D 플래너, 경로 소유권 연속성, 후속 예약, 물리적 경로 부피 통과, 측정된
런타임 지연도 추가로 검증합니다.

`drone_city_nav/config/cooperative_traffic_scenario.json`의 유한 시나리오는 직선형
`passage_structure_54_162_straight` 3D 통로가 있는 서쪽 내부 도로의 서로 반대쪽
끝에서 민간 드론 두 쌍을 시작합니다. 두 평행 경로는 불과 2 m 떨어져 시작하므로
이륙 직후 의도적으로 협력 분리를 강제하고, 이후 8 m 떨어진 목적지로 펼쳐집니다.
각 경로는 건물 열 사이의 통로를 통해 반대 방향 교통을 운반합니다. 모든 기체는 자체
PX4, 내비게이션, 매핑, MPPI 파이프라인을 소유합니다. 모든 기체는 같은 고도에서
출발하고 순항하며 고정 고도 계층은 할당하지 않습니다.

각 기체는 20 Hz로 현재 상태, 물리적 점유 공간, 유효 기간이 제한된 MPPI 지평선,
활성 통로 사용 정보를 담은 타입 지정 `CooperativeFlightIntent`를 게시합니다. 각
협력 에이전트는 오래되었거나 순서가 뒤바뀐 동료 의도를 독립적으로 거부하고, 5초
지평선에서 연속 최단 접근을 예측하며, 현재 충돌하는 모든 궤적을 함께 고려해 결정론적
시공간 기동을 최적화합니다. 후보 계획은 연속적인 횡방향 또는 수직 변위와 선택적인
제한 진입 시간 이동을 결합합니다. 안전한 계획은 분리 거리, 경로 진행도, 노력, 안정적인
쌍 선호도에 따라 순위가 매겨집니다. 충돌 및 현재 계획 상태는 잠시 래치되었다가
히스테리시스를 적용해 해제됩니다. 그 결과는 금지 그리드, 팽창 장애물, 강제 배제
부피가 아니라 소프트 플래너 선호도와 동료 분리 비용입니다. 원시 물리 장애물만이
유일한 강체 충돌 제약으로 남습니다.

정적 지도 통로 토폴로지는 서로 일치하는 원시 `Occupancy3D`와 `ESDF3D` 아티팩트에서
오프라인으로 도출합니다. 일반화된 컴파일러는 기체 점유 공간이 통과할 수 있는 여유
토폴로지를 분류하고, 임의 방향의 포털 복셀 패치를 추출하며, 희소 중앙 구간 그래프를
저장합니다. 지붕 존재 여부, 축 정렬 포털 가정, 모든 포털 쌍 사이의 간선을 사용하지
않습니다. 이 지문 결속 토폴로지는 시각화, 진단, 선택적 실행 메타데이터를 위한 오프라인
통로 증거이며, 경쟁하는 전략 경로 생성기가 아닙니다.

경로 연관 통로 실행에서 플래너는 원시 `Occupancy3D`로부터 경로 직교 단면을
샘플링하고, 두 횡축에서 드론의 전체 점유 공간을 검증하며, 변화하는 지역 자유 공간
포락선을 만듭니다. 반대 방향 교통은 공유 희소 구간 리소스로 조정하며, 측정 부피가
충분한 분리를 제공하면 결정론적인 연속 오프셋을 사용합니다. 좁거나 그 밖의 충돌
가능성이 있는 통로는 결정론적 통행 우선권으로 진입 시간을 예약합니다. 활성 제한
구간은 통과 도중 절대 교체하지 않습니다. 정적 지도 없는 모드에서는 동료 라이다
반환값을 영속 장애물 메모리에서만 제거합니다. 변경되지 않은 최신 스캔은 계속 즉시
안전 검증에 도달하므로 협력 필터링이 실제 근거리 장애물을 숨길 수 없습니다.

미션 판정기는 준비 상태와 물리적 판정에만 Gazebo 실측값을 사용합니다. 헤드리스
성공을 위해서는 드론 네 대 모두 각자 목표에 도달해 물리적으로 홀드하고, 기체 파괴나
건물 충돌이 없으며, 완전한 최소 분리 거리 보고서가 있어야 합니다. 정적 지도 및 정적
지도 없는 워크플로를 모두 지원합니다. GUI 관람자는 `civilian_0`에서 시작하고 순환형
`next_living` 선택을 사용합니다.

Gazebo 뷰에서 요격기 가시성 마커는 계속 노란색이고 회피기 가시성 마커는 빨간색입니다.
RViz는 계속 역할별 고유 색상을 사용합니다.

미션 결과와 기체 사망은 별개의 계약입니다. 미션 실패는 절대 무장 해제를 요청하지
않습니다. 강제 무장 해제는 래치된 사망 수명 주기만 소유하며, 물리적 Gazebo 충돌이나
타입이 지정된 5 m 근접 사망에만 허용됩니다. 회피기가 물리적으로 추락하면 사망 및
무장 해제가 확인되고, 생존한 요격기는 확인된 정지 위치 홀드를 위한 타입 지정 목표를
받습니다. 요격기 두 대 사이의 타입 지정 근접 충돌도 같은 물리적 사망 계약이며 미션
실패에 따른 무장 해제 경로가 아닙니다.

관련 Gazebo/PX4/ROS 프로세스와 시뮬레이션 컨테이너를 포함해 실행 중인 모든
시뮬레이션 잔여 항목을 중지합니다.

```bash
./scripts/stop_sim.sh
```

아무것도 종료하지 않고 중지 대상을 미리 확인합니다.

```bash
./scripts/stop_sim.sh --dry-run
```

이 프로젝트는 같은 워크스테이션에서 여러 Gazebo 인스턴스를 동시에 지원하지 않으므로
Gazebo GUI 실행은 시작 전에 충돌하는 오래된 Gazebo 시뮬레이터 프로세스를 중지합니다.
정리는 기본적으로 활성화되며 종료 전에 모든 후보 컨테이너와 PID를 기록합니다.
종료하지 않고 후보를 나열하려면 `DRONE_GAZEBO_CLEAN_STALE_DRY_RUN=true`를,
의도적인 디버깅 상황에서만 `DRONE_GAZEBO_CLEAN_STALE_PROCESSES=false`를
사용하십시오.

기본적으로 Gazebo 3D 뷰는 Gazebo의 `CameraTracking` 플러그인을 사용합니다. 지점 간
미션은 PX4가 생성한 모델 `x500_lidar_2d_0`을 따라가며, 요격 미션은 타입 지정 관람자
선택에서 모델을 도출합니다. `ENABLE_GZ_GUI_FOLLOW_CAMERA=false`로 카메라를
비활성화하고, `GZ_GUI_FOLLOW_TARGET`으로 지점 간 대상을 변경하거나,
`GZ_GUI_FOLLOW_OFFSET="-7 0 3.5"`로 3인칭 카메라 오프셋을 조정할 수 있습니다.
실행기는 GUI를 시작하기 전에 초기 모델이 서버 장면에 나타날 때까지 기다린 다음,
결과 대상 상태가 안정적으로 유지될 때까지 ID를 인식하는 네이티브 `CameraTrack`
명령을 반복 게시합니다. 충돌하는 `/gui/follow` 서비스는 의도적으로 사용하지 않습니다.
시뮬레이션 일시 정지 해제는 별도의 Gazebo 월드 제어 작업으로 유지됩니다.

요격 스크립트는 `INTERCEPT_SPECTATOR_INITIAL_VEHICLE_ID`와
`INTERCEPT_SPECTATOR_RESELECTION_POLICY`를 노출합니다. 후자는 `first_living` 또는
`next_living`을 허용합니다. `first_living`은 시나리오에서 인덱스가 가장 낮은 생존
기체를 항상 선택합니다. `next_living`은 파괴된 기체 다음부터 앞으로 탐색하고 시나리오
목록 끝에서 처음으로 순환합니다. `INTERCEPT_SPECTATOR_RESELECTION_DELAY_S`는
인계 지연을 제어하며 기본값은 3초입니다.

기본적으로 RViz도 시각화 전용 `drone_follow` TF 프레임을 대상으로 하는 추적 카메라
디버그 뷰로 열립니다. `ENABLE_RVIZ_FOLLOW_CAMERA=false`로 이 동작을 비활성화하면
실행기가 대신 하향식 RViz 레이아웃을 엽니다. 이 스위치는 RViz 시각화만 바꾸며
내비게이션이나 오프보드 제어에는 영향을 주지 않습니다.

GUI 실행 뒤 결정론적 Gazebo 시작 진단을 검증합니다.

```bash
python3 scripts/validate_gazebo_gui_launch_log.py \
  log/gz_drone_nav.log \
  --gui-log log/gz_gui_drone_nav.log \
  --scene-diagnostics-dir log/gazebo_scene_debug
```

GUI 실행은 Gazebo 서버/월드 오케스트레이션 출력을 `log/gz_drone_nav.log`에,
Gazebo GUI 클라이언트 출력을 `log/gz_gui_drone_nav.log`에 보관합니다. 현재 자유
카메라 위치, 방향, 월드 공간 전방 방향은 `log/gz_gui_camera.jsonl`에 1초마다
샘플링됩니다. 이 동작은 `GZ_GUI_CAMERA_LOG_INTERVAL_S` 또는
`GZ_GUI_CAMERA_LOG_FILE`로 재정의할 수 있습니다. 실행기는 기본적으로
`log/gazebo_scene_debug/` 아래에 크기가 제한된 Gazebo 장면 진단도 수집합니다.
최소 실행이 필요할 때만 `ENABLE_GZ_SCENE_DIAGNOSTICS=false`로 장면 진단만
비활성화하십시오.

헤드리스 스모크 검증을 실행합니다.

```bash
./scripts/sim_headless.sh
```

대화형 컨테이너 셸 안에서 이에 해당하는 명시적 명령은 다음과 같습니다.

```bash
make sim-headless
```

시뮬레이션 실행 중 디버그 rosbag을 기록합니다.

```bash
./scripts/record_debug_bag.sh
```

컨테이너 대상은 `build/`, `install/`, `log/`를 사용합니다.

정적 모드에서는 `production_mppi_node`가 원시 `generated_city.occupancy3d`, 그에
지문 결속된 `generated_city.topology3d`, 미리 계산해 청크로 나눈
`generated_city.esdf3d`를 로드합니다. 세 아티팩트와 `generated_city.sdf`는 모두
같은 표준 월드 명세로부터 생성됩니다. 현재 도시는 `5 x 8` Manhattan 건물 그리드로,
수평 L자형 공중 통로 구조물 2개, 직선 관통 구조물 1개, T자 교차로 1개를 갖습니다.
정적 계획은 별도의 자유 공간 토폴로지 인덱스를 선택적 정적 통로 메타데이터로
로드합니다. 경로 생성은 계속 정적 지도 없는 모드와 동일한 영속 전체 3D 플래너가
소유합니다. 토폴로지 아티팩트는 경쟁하는 검색이나 경로 소유자를 생성하지 않습니다.
수작업으로 작성한 플래너 중심선, 의미론적 차선, 최근접 포털 선택기는 없습니다.
정적 지도 없는 모드에는 하나의 프로덕션 인지 파이프라인이 있습니다. 3D 프로필은
구조화된 모든 스캔을 적중 및 비적중 빔으로 디코딩하고, 완전한 6DoF 획득 자세를
해석하며, 광선을 리비전이 기록된 `unknown/free/occupied` `Occupancy3D`에
통합합니다. 더티 청크는 파생 거리 증거를 갱신하지만 충돌 판정 권한은 갖지 않습니다.
계획은 자유 공간과 미확인 공간을 동일하게 취급합니다. 정확한 원시 점유 형상만 유일한
강체 공간 장애물로 남습니다.

정적 자유 공간 토폴로지 인덱스는 정적 Manhattan 계획을 위한 선택적 호환성 가속으로
유지됩니다. 정적 지도 없는 3D 파이프라인에서는 생성하거나 소비하지 않습니다. 원본
계약은 `docs/world3d.md`, `docs/obstacle_mapping.md`, `docs/configuration.md`에
문서화되어 있습니다.

장애물 토픽은 엄격한 원시/런타임/디버그 계약을 따릅니다.
`/drone_city_nav/obstacle_memory_status`는 업데이트마다 발생하는 경량 하트비트입니다.
프로덕션 내비게이션에서 `/drone_city_nav/raw_obstacle_snapshot_3d`와
`/drone_city_nav/raw_obstacle_delta_3d`는 적응형 기본 스냅숏과 최신 누적 더티 청크를
전달합니다. 영속 통합과 DDS 직렬화는 각각 독립적인 최신값 워커에서 실행됩니다.
대체된 작업은 센서 증거를 오래된 상태로 두지 않고 병합합니다. 더 큰 디버그 표현은
제한된 주기로 게시되며 플래너가 역직렬화하지 않습니다. 원시 그리드는 직접 센서
증거만 포함합니다. 타임스탬프가 정렬된 각 스캔은 먼저
`/drone_city_nav/latest_lidar_obstacle_scan`을 게시합니다. 해당 정보가 최신인 동안
물리적 적중점은 영속 메모리 통합을 기다리지 않고 완전한 유한 경로를 검증합니다.
플래너는 팽창 그리드를 구체화하지 않고 거리에서 파생한 위험 필드를 만듭니다. 정적
모드는 그 대신 표준 Occupancy3D를 직접 로드합니다.
`/drone_city_nav/raw_obstacle_grid`는 시각화 전용이며 플래너나 오프보드 검증에 다시
연결해서는 안 됩니다.

RViz는 선택된 관람자의 최신 3D 반환값을
`/drone_city_nav/current_lidar_returns_3d`에, 다운샘플링한 누적 점유 복셀을
`/drone_city_nav/raw_memory_obstacle_points_3d`에 게시합니다. 현재 포인트 클라우드의
큐 깊이는 1이고 감쇠가 없으며, 누적 메모리는 속도가 제한됩니다. 다른 기체는 경량
자세 및 경로 표시만 유지합니다.

게시되는 모든 목표와 실행 지평선은 구성된 비행 포락선 `1.0 <= z < 32.0 m`를
사용합니다. 원시 충돌 검사는 수평 반경과 동체 상·하단 범위를 포함해 드론의 쓸린
방향성 3D 점유 공간을 사용합니다. 이는 팽창한 금지 영역이 아니라 물리적 기체
형상입니다. ESDF 위험 대역은 유한한 경로 순위 비용으로 유지됩니다.

모든 정상 실행 경로는 구성된 지평선 지속 시간을 사용하고 자체 샘플 안에 도착 속도
프로필을 포함합니다. 최종점의 병진 속도와 요율은 0입니다. 종점 뒤에 별도의 운동
단계를 추가하지 않습니다. 도착 형상화는 일반적인 정적 지도 기동에 사용할 수 있는 더
큰 가속도와 독립적인 보수적 수평 감속 한계를 사용합니다. 유효한 새 순환 지평선 경로가
도착하면 이전 경로나 일시적인 실행 가능 경로 없음 위치 홀드를 즉시 대체합니다. 한 번의
계획 업데이트가 대체 경로를 제공하지 못하면 측정된 기체 상태에서 남은 경로 형상과
남은 제어를 모두 검증합니다. 발산하는 경로는 해당 측정 상태에서 다시 만들며 남은
제어 슬롯 안에 완전한 도착 프로필을 넣습니다. 완전한 원시 월드 검증을 통과한 뒤에만
계속되며 이전 마감 시간을 절대 넘지 않습니다. 따라서 다음 업데이트가 실패했다는
이유만으로 폐기되지 않고 자체 종단 정지 상태에 도달합니다.

헤드리스 실행 뒤 GUI 없이 라이다 투영 스냅숏을 검증합니다.

```bash
python3 scripts/analyze_lidar_projection_snapshots.py \
  log/lidar_debug/snapshots.jsonl
```

프로덕션 MPPI 진단은 `log/mppi/` 아래에 속도가 제한된 JSON Lines 형식으로
작성됩니다. 최근의 전체 레코드는 크기가 제한된 링에도 보존되며 충돌 에피소드가
시작되면 `mppi_error_context.jsonl`로 덤프됩니다. 동기화된 라이다, 원시 그리드,
지역 지평선 스냅숏은 `log/lidar_debug/` 아래에 작성됩니다. 시뮬레이션 래퍼는 실행별
정확한 아티팩트 디렉터리를 출력합니다.

## 자원 예산

모든 헤드리스 비행은 프로세스별 자원 사용량을 기록하고 미션 검사가 이 기록을
읽습니다. r345(392.8 m를 142초에 비행했으며 위 수치와 같은 비행)에서 온보드
프로세스, 내비게이션 노드, DDS 에이전트는 Ryzen 9 5900HX의 p50 기준 2.73코어,
p95 기준 3.36코어를 사용했습니다. 상주 메모리는 798 MiB, GPU 메모리는 206 MiB였고
RTX 3060 Laptop GPU 사용률은 42%였으며 시뮬레이터의 실시간 배율은 1.00이었습니다.
이 측정이 드론 컴퓨터에 관해 말해 주는 것과 말해 주지 못하는 것, 그리고 측정 결과로
배제되지 않는 장치 등급으로 Jetson Orin 제품군을 언급한 배경 가정은
[docs/resource_budget.md](docs/resource_budget.md)에 있습니다.

## 빌드 시스템

승인된 빌드 시스템 엔트리포인트는 최상위 CMake 직접 실행이 아니라 `colcon`입니다.
C++ 패키지 자체는 `drone_city_nav/CMakeLists.txt`에서 현대적인 타깃 기반 CMake를
사용합니다.

프로덕션 내비게이션 서비스는 컴파일 시점에 ROS 컴포지션과 분리됩니다.

```text
drone_city_nav_production_mppi_component  (src/runtime/ros)
  -> drone_city_nav_mppi_runtime          (src/runtime)
  -> drone_city_nav_route_runtime         (src/planning, trajectory, execution)
  -> drone_city_nav_world_runtime         (src/world)
```

이 패키지 전용 라이브러리들은 빌드에만 사용하는 독립 include 루트를 갖습니다. 월드,
경로, MPPI 런타임에는 ROS 의존성이 없습니다. 컴포넌트에는 ROS 캡처/적용/게시
어댑터가 들어 있으며 호환성 코어 통합 라이브러리를 링크하지 않습니다. 헤더 그래프와
매니페스트 테스트는 선언된 `target_link_libraries` 간선에만 의존하지 않고 이 경계를
강제합니다. 자세한 내용은
[`docs/architecture.md`](docs/architecture.md#compile-time-runtime-boundaries)를
참조하십시오.

기존 `build/` 디렉터리와 컴파일 데이터베이스를 이미 사용할 수 있을 때 임시 빌드
디렉터리를 새로 만들지 마십시오. 일반 빌드 명령은 소스 패키지 바깥에 빌드 결과를
두고 도구용 컴파일 데이터베이스를 내보냅니다.

## 의존성

프로젝트 의존성은 다음과 같이 관리합니다.

- `docker/Dockerfile`의 ROS 2 및 Gazebo 시스템 패키지
- 개발 이미지가 `/opt/px4_msgs_ws`에 빌드하는 `px4_msgs`
- `scripts/setup_px4_autopilot.sh`가 `external/`에 복제하고 개발 컨테이너 안에서
  `px4_sitl`로 빌드하는 PX4 Autopilot. 3D 라이다 프로필은 해당 바이너리를 직접
  실행합니다. `scripts/bootstrap.sh`가 복제와 빌드를 모두 수행합니다.

래퍼 스크립트는 `make`, `colcon` 또는 시뮬레이션 명령을 호출하기 전에 컨테이너
안에서 `/opt/ros/${ROS_DISTRO}/setup.bash`와
`/opt/px4_msgs_ws/install/setup.bash`를 source합니다.

새 의존성을 ROS, 시스템 패키지 또는 명확히 리비전을 고정한 외부 체크아웃으로 제공할
수 없는 이유를 문서화하지 않고 저장소에 포함하지 마십시오.

## 포맷 및 정적 분석

포맷에는 저장소의 `.clang-format`을 사용합니다. 파일을 변경하는 `clang-format -i`를
저장소 전체에 실행하지 마십시오. `make format`을 사용하십시오. 현재 환경에서
프로젝트 전체를 의도적으로 정규화할 때만 `./scripts/format_cpp_changed.sh`에
`--all`을 전달하십시오.

리뷰어 검사는 파일을 변경하지 않아야 합니다.

```bash
make quality
```

`clang-tidy`는 컴파일 데이터베이스를 사용할 수 있을 때만 실행합니다. 데이터베이스나
도구가 없으면 검사 스크립트가 건너뛴 검사를 사유와 함께 명시적으로 보고합니다.

## 문서

주요 문서 모음은 `docs/overview.md`에서 시작합니다.

핵심 페이지는 다음과 같습니다.

- `docs/installation.md`
- `docs/build_and_run.md`
- `docs/gazebo_simulation.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/navigation_pipeline.md`
- `docs/world3d.md`
- `docs/environment_candidates.md`
- `environments/environment_manifest.yaml`
- `docs/trajectory_optimization.md`
- `docs/drone_control.md`
- `docs/terminal_capture.md`
- `docs/replanning.md`
- `docs/obstacle_mapping.md`
- `docs/configuration.md`
- `docs/diagnostics.md`
- `docs/testing.md`
- `docs/development.md`
- `docs/troubleshooting.md`
- `docs/performance.md`
