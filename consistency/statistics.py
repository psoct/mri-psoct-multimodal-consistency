"""ROI aggregation and correlation statistics."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


def summarize_regions(
    first: np.ndarray,
    second: np.ndarray,
    labels: np.ndarray,
    mask: np.ndarray | None = None,
    min_vox: int = 50,
    aggregation: Literal["mean", "median"] = "mean",
) -> pd.DataFrame:
    """Return paired modality summaries for every retained atlas region."""
    if first.shape != second.shape or first.shape != labels.shape:
        raise ValueError("Modality arrays and labels must have identical shapes")
    if mask is not None and mask.shape != labels.shape:
        raise ValueError("Mask and labels must have identical shapes")
    if min_vox < 1:
        raise ValueError("min_vox must be at least 1")
    if aggregation not in {"mean", "median"}:
        raise ValueError("aggregation must be 'mean' or 'median'")

    selected = np.ones(labels.shape, dtype=bool) if mask is None else mask.astype(bool)
    region_ids = labels[selected]
    x_values = first[selected]
    y_values = second[selected]

    finite = np.isfinite(region_ids) & np.isfinite(x_values) & np.isfinite(y_values)
    region_ids = region_ids[finite].astype(int)
    x_values = x_values[finite]
    y_values = y_values[finite]
    reducer = np.mean if aggregation == "mean" else np.median

    rows = []
    for region_id in np.unique(region_ids):
        if region_id == 0:
            continue
        region_mask = region_ids == region_id
        voxel_count = int(region_mask.sum())
        if voxel_count < min_vox:
            continue
        rows.append(
            {
                "region_id": int(region_id),
                "n_vox": voxel_count,
                "x": float(reducer(x_values[region_mask])),
                "y": float(reducer(y_values[region_mask])),
            }
        )

    return pd.DataFrame(rows, columns=["region_id", "n_vox", "x", "y"])


def compute_correlations(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Calculate Pearson and Spearman correlations from finite ROI summaries."""
    valid = df[["x", "y"]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < 3:
        raise ValueError("At least three valid regions are required")

    pearson_r, pearson_p = pearsonr(valid["x"], valid["y"])
    spearman_rho, spearman_p = spearmanr(valid["x"], valid["y"])
    return valid, {
        "n": int(len(valid)),
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_rho": float(spearman_rho),
        "spearman_p": float(spearman_p),
    }

