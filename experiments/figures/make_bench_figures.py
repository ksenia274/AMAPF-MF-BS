#!/usr/bin/env python3
"""Bar charts of cbm_bench.py results: median replanning time and share of solved instances per map.

Usage: make_bench_figures.py BENCH.csv OUT_PREFIX   -> OUT_PREFIX_replan.png, OUT_PREFIX_solved.png
One panel per team mode (k4, g5); bars = variants; the value is written on every bar.
Median replanning time of a map = median over its runs of the per-run median.
"""
import csv
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLORS = {"bs": "#2a78d6", "flow": "#eb6834", "floww": "#1baf7a", "bs-late": "#eda100"}
MODES = {"k4": "K = 4 teams", "g5": "teams of 5"}


def bars(rows, value, ylabel, title, fmt, out, sharey):
    maps = list(dict.fromkeys(r["map"] for r in rows))
    variants = [v for v in COLORS if any(r["variant"] == v for r in rows)]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), sharey=sharey)
    width = 0.8 / len(variants)
    for ax, (mode, mode_title) in zip(axes, MODES.items()):
        for i, v in enumerate(variants):
            xs, ys = [], []
            for j, m in enumerate(maps):
                rs = [r for r in rows if r["map"] == m and r["variant"] == v and r["mode"] == mode]
                y = value(rs)
                if y is None:
                    continue
                xs.append(j + (i - (len(variants) - 1) / 2) * width)
                ys.append(y)
            b = ax.bar(xs, ys, width * 0.92, color=COLORS[v], label=v)
            ax.bar_label(b, labels=[fmt(y) for y in ys], fontsize=7, padding=2, rotation=90, color="#333333")
        ax.set_xticks(range(len(maps)))
        ax.set_xticklabels(maps, rotation=20, ha="right", fontsize=9)
        ax.set_title(mode_title, fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.margins(y=0.25)
        ax.set_ylabel(ylabel)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, loc="upper center", ncol=len(labels), bbox_to_anchor=(0.5, 0.94))
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main():
    path, prefix = sys.argv[1], sys.argv[2]
    with open(path) as f:
        rows = list(csv.DictReader(f))

    def replan(rs):
        xs = [float(r["replan_ms_median"]) for r in rs if r["replan_ms_median"] not in ("", "0.000")]
        return statistics.median(xs) if xs else None

    def solved(rs):
        return sum(r["status"] == "solved" for r in rs) / len(rs) if rs else None

    bars(rows, replan, "ms", "Median time of one replanning (all N of the map)",
         lambda y: f"{y:.1f}" if y < 100 else f"{y:.0f}", prefix + "_replan.png", False)
    bars(rows, solved, "share solved", "Share of instances solved in 60 s (all N of the map)",
         lambda y: f"{y:.2f}", prefix + "_solved.png", True)


if __name__ == "__main__":
    main()
