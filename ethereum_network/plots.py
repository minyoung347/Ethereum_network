from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def month_ticks(months: list[str]) -> tuple[list[pd.Timestamp], list[str]]:
    dates = pd.to_datetime(months, format="%Y%m")
    show = list(range(0, len(dates), 2))
    return [dates[i] for i in show], [
        dates[i].strftime("%b\n%Y") if i == 0 or dates[i].year != dates[i - 1].year else dates[i].strftime("%b")
        for i in show
    ]


def plot_distance_timeseries(distance_csv: str | Path, output: str | Path) -> None:
    df = pd.read_csv(distance_csv)
    df["date"] = pd.to_datetime(df["month"], format="%Y%m")

    plt.rcParams["figure.figsize"] = (15, 10)
    plt.rcParams["font.size"] = 24
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    ax1.plot(df["date"], df["euclidean"], marker="o", color="tab:red", label="Euclidean")
    ax2.plot(df["date"], df["cosine_distance"], marker="o", color="tab:blue", label="Cosine")

    ticks, labels = month_ticks(df["month"].tolist())
    for ax in (ax1, ax2):
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
        ax.spines["top"].set_visible(False)
        ax.axvline(pd.Timestamp("2016-04-01"), color="gray", linestyle=":", linewidth=3)
        ax.axvline(pd.Timestamp("2016-07-01"), color="gray", linestyle=":", linewidth=3)

    ax1.set_ylabel("Euclidean distance")
    ax2.set_ylabel("Cosine distance")
    ax1.set_xlabel("month")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="best")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", dpi=200)
    plt.close(fig)
