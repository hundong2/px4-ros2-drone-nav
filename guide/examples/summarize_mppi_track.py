#!/usr/bin/env python3
"""Summarize the compact per-tick MPPI JSONL diagnostic stream."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


CATEGORICAL_FIELDS = (
    "limiter",
    "planning_state",
    "execution_reason",
    "risk_tier",
    "control_selection",
)
NUMERIC_FIELDS = (
    "reference_speed_mps",
    "unslewed_reference_speed_mps",
    "head_speed_mps",
    "minimum_esdf_m",
    "contact_distance_m",
    "constrained_clearance_m",
    "distance_to_constraint_m",
    "distance_to_unobserved_m",
)


def finite_values(records: Iterable[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for record in records:
        value = record.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        numeric = float(value)
        if math.isfinite(numeric):
            values.append(numeric)
    return sorted(values)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("percentile requires a non-empty sample")
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def load_records(path: Path) -> tuple[list[dict[str, Any]], list[int]]:
    records: list[dict[str, Any]] = []
    malformed: list[int] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"cannot read input: {error}") from error
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(line_number)
            continue
        if not isinstance(value, dict):
            malformed.append(line_number)
            continue
        records.append(value)
    return records, malformed


def count_transitions(values: list[Any]) -> int:
    return sum(current != previous for previous, current in zip(values, values[1:]))


def print_counter(field: str, records: list[dict[str, Any]], top: int) -> None:
    counter = Counter(
        str(record[field]) for record in records if field in record
    )
    print(f"{field}:")
    if not counter:
        print("  <no samples>")
        return
    for value, count in counter.most_common(top):
        ratio = 100.0 * count / len(records)
        print(f"  {value}: {count} ({ratio:.2f}%)")


def summarize(path: Path, top: int) -> int:
    records, malformed = load_records(path)
    if not records:
        print("track error: no valid JSON object records", file=sys.stderr)
        return 2

    ticks = [
        int(record["tick"])
        for record in records
        if isinstance(record.get("tick"), int) and not isinstance(record.get("tick"), bool)
    ]
    route_generations = [record.get("route_generation") for record in records]
    hold_count = sum(
        str(record.get("planning_state", "")).endswith("_hold")
        for record in records
    )

    print(f"input: {path.resolve()}")
    print(f"records: {len(records)}")
    print(f"malformed_lines: {len(malformed)}")
    if malformed:
        print(f"malformed_line_numbers: {','.join(map(str, malformed))}", file=sys.stderr)
    if ticks:
        print(f"tick_range: {min(ticks)}..{max(ticks)}")
    print(f"route_generation_changes: {count_transitions(route_generations)}")
    print(f"hold_ticks: {hold_count} ({100.0 * hold_count / len(records):.2f}%)")

    for field in CATEGORICAL_FIELDS:
        print_counter(field, records, top)

    print("numeric_fields:")
    for field in NUMERIC_FIELDS:
        values = finite_values(records, field)
        if not values:
            continue
        print(
            f"  {field}: n={len(values)} min={values[0]:.3f} "
            f"p50={percentile(values, 0.50):.3f} "
            f"p95={percentile(values, 0.95):.3f} max={values[-1]:.3f}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("track", type=Path)
    parser.add_argument("--top", type=int, default=8)
    args = parser.parse_args()
    if args.top <= 0:
        parser.error("--top must be positive")
    try:
        return summarize(args.track, args.top)
    except ValueError as error:
        print(f"track error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
