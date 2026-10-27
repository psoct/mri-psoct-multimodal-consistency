"""Publication-oriented plotting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_roi_correlation(
    df: pd.DataFrame,
    statistics: Mapping[str, float | int],
    output_prefix: str | Path,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    dpi: int = 600,
) -> None:
    """Save a fixed-size ROI scatter plot with a descriptive regression line."""
    sns.set_theme(context="paper", style="ticks", font_scale=1.2)
    figure, axis = plt.subplots(figsize=(2.15, 2.0))
    sns.regplot(
        data=df,
        x="x",
        y="y",
        ci=None,
        truncate=False,
        scatter_kws={"s": 24, "alpha": 0.82, "edgecolor": "white"},
        line_kws={"linewidth": 1.7},
        ax=axis,
    )

    figure.text(
        0.54,
        0.975,
        f"n = {statistics['n']};  r = {statistics['pearson_r']:.3f};  "
        f"ρ = {statistics['spearman_rho']:.3f}",
        va="top",
        ha="center",
        fontsize=8.5,
    )
    axis.set(xlabel="", ylabel="", title="")
    if xlim is not None:
        axis.set_xlim(xlim)
    if ylim is not None:
        axis.set_ylim(ylim)
    axis.tick_params(axis="both", labelsize=9.0)
    sns.despine(ax=axis)
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.88), pad=0.25)

    prefix = str(output_prefix)
    figure.savefig(prefix + ".png", dpi=dpi)
    figure.savefig(prefix + ".pdf")
    plt.close(figure)

