"""Shared cumulative-binning semantics for the Python package."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import floor, isfinite
from typing import Any


Accessor = str | Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True)
class Config:
    value: Accessor | None
    cumulative: Accessor | None
    bin_size: float | None
    thresholds: tuple[float, ...] | None
    origin: float
    group_by: Accessor | Sequence[Accessor] | None
    include_source: bool


def cumbin(
    data: Iterable[Mapping[str, Any]],
    spec: Mapping[str, Any] | None = None,
    **options: Any,
) -> list[dict[str, Any]]:
    """Split ordered source rows across cumulative bins."""

    config = _normalize_spec(spec, options)
    cursors: dict[str, float] = {}
    output: list[dict[str, Any]] = []

    for source_index, row in enumerate(data):
        group_key = _key_for(row, config.group_by)
        source_start = cursors.get(group_key, config.origin)
        source_end = (
            _number_from(_read(row, config.cumulative), config.cumulative)
            if config.cumulative is not None
            else source_start + _number_from(_read(row, config.value), config.value)
        )
        source_amount = source_end - source_start

        if source_amount < 0:
            raise ValueError(
                "cumbin requires non-negative amounts and monotone cumulative endpoints"
            )

        cursors[group_key] = source_end

        if source_amount == 0:
            continue

        for segment in _split_interval(source_start, source_end, config):
            result = dict(row) if config.include_source else {}
            result.update(
                {
                    "bin": segment["bin"],
                    "bin_start": segment["bin_start"],
                    "bin_end": segment["bin_end"],
                    "amount": segment["amount"],
                    "source_index": source_index,
                    "source_start": source_start,
                    "source_end": source_end,
                    "source_amount": source_amount,
                    "source_fraction": segment["amount"] / source_amount,
                }
            )
            output.append(result)

    return output


cumulative_bins = cumbin


def summarize_bins(
    rows: Iterable[Mapping[str, Any]],
    *,
    group_by: str | Sequence[str] | None = None,
    amount: str = "amount",
) -> list[dict[str, Any]]:
    """Aggregate cumbin rows by bin and optional grouping fields."""

    group_fields = _as_sequence(group_by)
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}

    for row in rows:
        key = (
            row["bin"],
            row["bin_start"],
            row["bin_end"],
            *[row[field] for field in group_fields],
        )

        if key not in groups:
            groups[key] = {
                "bin": row["bin"],
                "bin_start": row["bin_start"],
                "bin_end": row["bin_end"],
                amount: 0,
                "count": 0,
            }
            for field in group_fields:
                groups[key][field] = row[field]

        groups[key][amount] += _number_from(row["amount"], "amount")
        groups[key]["count"] += 1

    return list(groups.values())


def _normalize_spec(
    spec: Mapping[str, Any] | None,
    options: Mapping[str, Any],
) -> Config:
    merged = {**dict(spec or {}), **dict(options)}
    value = merged.get("value", merged.get("amount"))
    cumulative = merged.get("cumulative")
    bin_size_raw = merged.get("binSize", merged.get("bin_size"))
    thresholds_raw = merged.get("thresholds")
    origin = _number_from(merged.get("origin", 0), "origin")

    if (value is None) == (cumulative is None):
        raise TypeError("cumbin requires exactly one of value or cumulative")

    if (bin_size_raw is None) == (thresholds_raw is None):
        raise TypeError("cumbin requires exactly one of binSize or thresholds")

    bin_size = None
    if bin_size_raw is not None:
        bin_size = _number_from(bin_size_raw, "binSize")
        if bin_size <= 0:
            raise ValueError("cumbin binSize must be positive")

    thresholds = None
    if thresholds_raw is not None:
        thresholds = tuple(_number_from(value, "thresholds") for value in thresholds_raw)
        if len(thresholds) < 2:
            raise ValueError("cumbin thresholds must include at least two boundaries")
        if any(right <= left for left, right in zip(thresholds, thresholds[1:])):
            raise ValueError("cumbin thresholds must be strictly increasing")

    return Config(
        value=value,
        cumulative=cumulative,
        bin_size=bin_size,
        thresholds=thresholds,
        origin=origin,
        group_by=merged.get("groupBy", merged.get("group_by")),
        include_source=merged.get("includeSource", merged.get("include_source", True)),
    )


def _split_interval(start: float, end: float, config: Config) -> list[dict[str, float]]:
    if config.thresholds is not None:
        return _split_by_thresholds(start, end, config.thresholds)

    if config.bin_size is None:
        raise TypeError("cumbin internal error: bin_size is not configured")

    return _split_by_regular_bins(start, end, config.origin, config.bin_size)


def _split_by_regular_bins(
    start: float,
    end: float,
    origin: float,
    bin_size: float,
) -> list[dict[str, float]]:
    segments: list[dict[str, float]] = []
    bin_index = floor((start - origin) / bin_size)

    while origin + bin_index * bin_size < end:
        bin_start = origin + bin_index * bin_size
        bin_end = bin_start + bin_size
        overlap_start = max(start, bin_start)
        overlap_end = min(end, bin_end)
        amount = overlap_end - overlap_start

        if amount > 0:
            segments.append(
                {
                    "bin": bin_index,
                    "bin_start": bin_start,
                    "bin_end": bin_end,
                    "amount": amount,
                }
            )

        bin_index += 1

    return segments


def _split_by_thresholds(
    start: float,
    end: float,
    thresholds: Sequence[float],
) -> list[dict[str, float]]:
    segments: list[dict[str, float]] = []

    for bin_index, (bin_start, bin_end) in enumerate(zip(thresholds, thresholds[1:])):
        if bin_start >= end:
            break

        overlap_start = max(start, bin_start)
        overlap_end = min(end, bin_end)
        amount = overlap_end - overlap_start

        if amount > 0:
            segments.append(
                {
                    "bin": bin_index,
                    "bin_start": bin_start,
                    "bin_end": bin_end,
                    "amount": amount,
                }
            )

    return segments


def _read(row: Mapping[str, Any], accessor: Accessor | None) -> Any:
    if accessor is None:
        return None

    if callable(accessor):
        return accessor(row)

    return row[accessor]


def _key_for(row: Mapping[str, Any], group_by: Accessor | Sequence[Accessor] | None) -> str:
    if group_by is None:
        return ""

    values = [_read(row, field) for field in _as_sequence(group_by)]
    return repr(values)


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return list(value)

    return [value]


def _number_from(value: Any, field: Any) -> float:
    number = float(value)

    if not isfinite(number):
        raise TypeError(f"cumbin expected a finite number for {field}")

    return number

