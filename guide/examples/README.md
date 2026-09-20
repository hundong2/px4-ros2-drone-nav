# 격리형 실습 예제

이 디렉터리의 Python 도구는 학습을 위한 read-only 분석기입니다. Python 3 표준 라이브러리만 사용하며 ROS graph, simulation process, build tree, log를 수정하지 않습니다. 저장소 루트에서 실행하세요. 호스트 Python으로 실행해도 source를 수정하지 않지만, 프로젝트의 고정된 container 환경을 사용하려면 각 명령의 `python3` 앞에 `./scripts/dev_shell.sh`를 붙일 수 있습니다.

> **범위 주의**
>
> 이 도구의 성공은 실제 simulation acceptance를 의미하지 않습니다. 공식 검증은 container workflow의 `make test-scripts`, `make quality`, `./scripts/sim_*_headless.sh`와 mission check가 담당합니다.

## 1. Scenario preflight

### 학습 목표

point-to-point scenario의 schema, canonical world, spawn, goal, target altitude를 읽고 직선 기준 leg 거리를 계산합니다.

### 요구 사항

- Python 3.10 이상
- 저장소 checkout
- simulation, Docker, ROS 2는 불필요

### 실행 명령

```bash
python3 guide/examples/inspect_scenario.py \
  drone_city_nav/config/manhattan_low_altitude_point_to_point_scenario.json
```

### 예상 출력

```text
scenario: ...manhattan_low_altitude_point_to_point_scenario.json
schema: drone_city_nav_point_to_point_scenario_v2
world: ...canonical_city.world3d.json (exists)
vehicle: x500_lidar_2d_0
start_map_m: (54.000, 54.000, 0.300)
target_altitude_m: [1.000, 32.000)
goal[1]: (54.000, 378.000, 5.000), direct_leg_m=324.034
direct_path_total_m: 324.034
status: educational preflight passed
```

거리 값은 spawn에서 goal까지의 3D 직선 길이입니다. obstacle-aware route length, takeoff profile, actual trajectory와 같지 않습니다.

### 코드가 하는 일

- JSON object와 schema를 확인합니다.
- `canonical_world` 상대 경로를 scenario 위치 기준으로 해석합니다.
- vector shape, finite number, target altitude의 half-open interval을 검사합니다.
- waypoint별 Euclidean distance를 출력합니다.

### 정리

파일을 생성하지 않으므로 정리할 항목이 없습니다.

## 2. MPPI compact track 요약

### 학습 목표

`mppi_track.jsonl`의 모든 tick을 읽어 limiter, planning state, execution reason, risk tier, speed/clearance 분포를 요약합니다.

### 요구 사항

- Python 3.10 이상
- 실제 run의 `mppi_track.jsonl` 또는 포함된 sample fixture

### 실행 명령

샘플:

```bash
python3 guide/examples/summarize_mppi_track.py \
  guide/examples/fixtures/sample_mppi_track.jsonl
```

실제 run:

```bash
python3 guide/examples/summarize_mppi_track.py \
  log/runs/<run-id>/mppi/mppi_track.jsonl
```

### 예상 출력

```text
records: 6
malformed_lines: 0
tick_range: 100..105
route_generation_changes: 1
hold_ticks: 3 (50.00%)
...
```

샘플에는 planned tick, route hold, goal hold가 의도적으로 섞여 있습니다. 실제 run에서는 hold가 발생한 tick을 찾은 뒤 full JSONL과 ROS log에서 world/route/revalidation 원인을 확인해야 합니다.

### 코드가 하는 일

- 비어 있지 않은 JSON line을 object로 decode합니다.
- categorical field를 빈도순으로 집계합니다.
- numeric field의 최소, p50, p95, 최대를 계산합니다.
- route generation 전환과 `*_hold` planning state 비율을 계산합니다.
- malformed line은 개수와 line number를 stderr에 보고합니다.

### 정리

입력만 읽으므로 정리할 항목이 없습니다.

## 3. 두 run manifest 비교

### 학습 목표

성능이나 성공률을 비교하기 전에 두 run의 commit, dirty state, configuration/world/scenario hash, runtime profile, effective override가 같은지 확인합니다.

### 요구 사항

- Python 3.10 이상
- 두 `drone_city_nav_runtime_manifest_v1` 파일

### 실행 명령

샘플:

```bash
python3 guide/examples/compare_run_manifests.py \
  guide/examples/fixtures/sample_manifest_a.json \
  guide/examples/fixtures/sample_manifest_b.json
```

실제 run:

```bash
python3 guide/examples/compare_run_manifests.py \
  log/runs/<run-a>/manifest.json \
  log/runs/<run-b>/manifest.json
```

차이가 있으면 CI/실습 check를 실패시키려는 경우:

```bash
python3 guide/examples/compare_run_manifests.py --strict \
  log/runs/<run-a>/manifest.json \
  log/runs/<run-b>/manifest.json
```

### 예상 출력

샘플 manifest는 의도적으로 cruise override가 다릅니다.

```text
repository.commit: SAME
...
effective_overrides: DIFFERENT
  A: {"CRUISE_SPEED_MPS": "5.0", ...}
  B: {"CRUISE_SPEED_MPS": "6.5", ...}
comparison: 1 difference(s)
```

### 코드가 하는 일

- manifest schema를 확인합니다.
- 재현성에 중요한 field를 안정적인 순서로 비교합니다.
- 값 전체를 임의로 정규화하지 않고 semantic JSON 값으로 비교합니다.
- `--strict`일 때 차이가 있으면 exit code 1을 반환합니다.

### 정리

입력만 읽으므로 정리할 항목이 없습니다.

## 4. 예제 자체 검증

syntax를 filesystem mutation 없이 검사합니다.

```bash
python3 - <<'PY'
import ast
from pathlib import Path

for path in sorted(Path("guide/examples").glob("*.py")):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"syntax OK: {path}")
PY
```

샘플 실행:

```bash
python3 guide/examples/inspect_scenario.py \
  drone_city_nav/config/manhattan_low_altitude_point_to_point_scenario.json
python3 guide/examples/summarize_mppi_track.py \
  guide/examples/fixtures/sample_mppi_track.jsonl
python3 guide/examples/compare_run_manifests.py \
  guide/examples/fixtures/sample_manifest_a.json \
  guide/examples/fixtures/sample_manifest_b.json
```

[가이드 시작으로 돌아가기](../README.md)
