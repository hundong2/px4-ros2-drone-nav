#!/usr/bin/env python3
"""Inspect a point-to-point scenario without starting the simulation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


SCHEMA = "drone_city_nav_point_to_point_scenario_v2"
DEFAULT_MINIMUM_TARGET_Z_M = 1.0
DEFAULT_MAXIMUM_TARGET_Z_M = 32.0


class ScenarioError(ValueError):
    """Raised when an educational scenario check fails."""


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScenarioError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ScenarioError(f"{label} must be finite")
    return result


def vector3(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ScenarioError(f"{label} must contain exactly three numbers")
    return tuple(finite_number(component, f"{label}[{index}]") for index, component in enumerate(value))  # type: ignore[return-value]


def object_field(document: dict[str, Any], name: str) -> dict[str, Any]:
    value = document.get(name)
    if not isinstance(value, dict):
        raise ScenarioError(f"{name} must be an object")
    return value


def string_field(document: dict[str, Any], name: str) -> str:
    value = document.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioError(f"{name} must be a non-empty string")
    return value


def direct_distance(
    start: tuple[float, float, float], goal: tuple[float, float, float]
) -> float:
    return math.sqrt(sum((goal[index] - start[index]) ** 2 for index in range(3)))


def inspect(path: Path) -> None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ScenarioError(f"cannot read scenario: {error}") from error
    except json.JSONDecodeError as error:
        raise ScenarioError(f"invalid JSON at line {error.lineno}: {error.msg}") from error

    if not isinstance(document, dict):
        raise ScenarioError("scenario root must be an object")
    if document.get("schema") != SCHEMA:
        raise ScenarioError(f"schema must be {SCHEMA}")

    world_value = string_field(document, "canonical_world")
    world = (path.parent / world_value).resolve()
    if not world.is_file():
        raise ScenarioError(f"canonical_world does not exist: {world}")

    vehicle = object_field(document, "vehicle")
    model = string_field(vehicle, "gazebo_model_name")
    string_field(vehicle, "px4_model_target")
    start = vector3(vehicle.get("map_start_m"), "vehicle.map_start_m")
    finite_number(vehicle.get("yaw_rad"), "vehicle.yaw_rad")

    navigation_value = document.get("navigation", {})
    if not isinstance(navigation_value, dict):
        raise ScenarioError("navigation must be an object when present")
    minimum_z = finite_number(
        navigation_value.get("minimum_target_z_m", DEFAULT_MINIMUM_TARGET_Z_M),
        "navigation.minimum_target_z_m",
    )
    maximum_z = finite_number(
        navigation_value.get("maximum_target_z_m", DEFAULT_MAXIMUM_TARGET_Z_M),
        "navigation.maximum_target_z_m",
    )
    if minimum_z >= maximum_z:
        raise ScenarioError("target altitude minimum must be below maximum")

    goals_value = document.get("mission_goal_sequence_m")
    if not isinstance(goals_value, list) or not goals_value:
        raise ScenarioError("mission_goal_sequence_m must be a non-empty list")
    goals = [
        vector3(value, f"mission_goal_sequence_m[{index}]")
        for index, value in enumerate(goals_value)
    ]
    for index, goal in enumerate(goals, start=1):
        if not minimum_z <= goal[2] < maximum_z:
            raise ScenarioError(
                f"goal[{index}] z={goal[2]} is outside [{minimum_z}, {maximum_z})"
            )

    print(f"scenario: {path.resolve()}")
    print(f"schema: {SCHEMA}")
    print(f"world: {world} (exists)")
    print(f"vehicle: {model}")
    print(f"start_map_m: ({start[0]:.3f}, {start[1]:.3f}, {start[2]:.3f})")
    print(f"target_altitude_m: [{minimum_z:.3f}, {maximum_z:.3f})")

    total = 0.0
    previous = start
    for index, goal in enumerate(goals, start=1):
        distance = direct_distance(previous, goal)
        total += distance
        print(
            f"goal[{index}]: ({goal[0]:.3f}, {goal[1]:.3f}, {goal[2]:.3f}), "
            f"direct_leg_m={distance:.3f}"
        )
        previous = goal
    print(f"direct_path_total_m: {total:.3f}")
    print("status: educational preflight passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    args = parser.parse_args()
    try:
        inspect(args.scenario)
    except ScenarioError as error:
        print(f"scenario error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
