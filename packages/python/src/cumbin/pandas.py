"""Pandas convenience wrappers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .core import cumbin


def cumbin_frame(df: Any, spec: Mapping[str, Any] | None = None, **options: Any) -> Any:
    """Return a Pandas DataFrame containing cumbin segment rows."""

    import pandas as pd

    rows = cumbin(df.to_dict("records"), spec, **options)
    return pd.DataFrame.from_records(rows)


def plot_cumbin(
    df: Any,
    spec: Mapping[str, Any] | None = None,
    *,
    x: str = "bin_start",
    y: str = "amount",
    kind: str = "bar",
    **options: Any,
) -> Any:
    """Compute cumulative bins and delegate plotting to Pandas."""

    plot_options = dict(options)
    transform_options = plot_options.pop("transform_options", {})
    frame = cumbin_frame(df, spec, **transform_options)
    return frame.plot(x=x, y=y, kind=kind, **plot_options)

