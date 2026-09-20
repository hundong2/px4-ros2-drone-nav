#!/usr/bin/env python3
"""Compare reproducibility-critical fields in two runtime manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


SCHEMA = "drone_city_nav_runtime_manifest_v1"
FIELD_PATHS: tuple[tuple[str, ...], ...] = (
    ("repository", "commit"),
    ("repository", "describe"),
    ("repository", "dirty"),
    ("repository", "status_sha256"),
    ("configuration", "path"),
    ("configuration", "sha256"),
    ("world", "path"),
    ("world", "sha256"),
    ("mission", "type"),
    ("mission", "goal_sequence_xyz_m"),
    ("mission", "scenario", "path"),
    ("mission", "scenario", "sha256"),
    ("runtime_profile", "lidar_profile"),
    ("runtime_profile", "static_map_enabled"),
    ("constrained_route_volume_bounds_m",),
    ("raw_snapshot_bounds_m",),
    ("effective_overrides",),
)


class ManifestError(ValueError):
    """Raised when a runtime manifest cannot be compared."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ManifestError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ManifestError(
            f"invalid JSON in {path} at line {error.lineno}: {error.msg}"
        ) from error
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise ManifestError(f"{path} is not a {SCHEMA} document")
    return document


def nested_value(document: dict[str, Any], path: Sequence[str]) -> Any:
    value: Any = document
    for component in path:
        if not isinstance(value, dict) or component not in value:
            return None
        value = value[component]
    return value


def display(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def compare(first: dict[str, Any], second: dict[str, Any]) -> int:
    differences = 0
    for path in FIELD_PATHS:
        label = ".".join(path)
        first_value = nested_value(first, path)
        second_value = nested_value(second, path)
        if first_value == second_value:
            print(f"{label}: SAME")
            continue
        differences += 1
        print(f"{label}: DIFFERENT")
        print(f"  A: {display(first_value)}")
        print(f"  B: {display(second_value)}")
    print(f"comparison: {differences} difference(s)")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()
    try:
        first = load_manifest(args.first)
        second = load_manifest(args.second)
    except ManifestError as error:
        print(f"manifest error: {error}", file=sys.stderr)
        return 2
    differences = compare(first, second)
    return 1 if args.strict and differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
