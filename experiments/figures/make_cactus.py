#!/usr/bin/env python3
"""Cactus plots of cbm_bench_cactus.py: solved instances by time, one line per low level.

Usage: make_cactus.py BENCH.csv [OUT_DIR]   (OUT_DIR defaults to the folder of this script)
  -> cactus_<map>.png/.pdf for every map, cactus_grid_small, cactus_grid_large (maps in cells, one legend),
     cactus_small, cactus_large (all instances of the group).
Time = total_ms of cbm of the solved runs; times below 0.01 s are drawn at 0.01 s.
"""
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

VARIANTS = ["bs", "bspen", "flow", "floww"]
LABELS = {"bs": "Bulk Search", "bspen": "Bulk Search со штрафами", "flow": "Поток без штрафов",
          "floww": "Поток со штрафами"}
COLORS = {"bs": "#6FA0DC", "bspen": "#3B6BA5", "flow": "#C9822B", "floww": "#B03A5B"}
SMALL = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8"]
LARGE = ["warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]
T_MIN, T_MAX = 0.01, 60
TICKS = [0.01, 0.1, 1, 10, 60]

plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 11,
                     "ytick.labelsize": 11, "legend.fontsize": 11})


def times(rows, variant):
    return sorted(max(T_MIN, float(r["total_ms"]) / 1000) for r in rows
                  if r["variant"] == variant and r["status"] == "solved")


def instances(rows):
    return len({(r["map"], r["N"], r["scen"]) for r in rows})


def best(rows):
    return max(len(times(rows, v)) for v in VARIANTS)


def style(ax):
    ax.set_xscale("log")
    ax.set_xlim(T_MIN, T_MAX)
    ax.set_xticks(TICKS)
    ax.set_xticklabels([f"{t:g}".replace(".", ",") for t in TICKS])
    ax.minorticks_off()
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlabel("время, с")
    ax.set_ylabel("решено задач")
    ax.yaxis.get_major_locator().set_params(integer=True)


def draw(ax, rows, end_labels):
    top = max(best(rows), 1)
    ends = []
    for v in VARIANTS:
        ts = times(rows, v)
        xs = [T_MIN] + ts + [T_MAX]
        ys = [0] + list(range(1, len(ts) + 1)) + [len(ts)]
        ax.step(xs, ys, where="post", color=COLORS[v], linewidth=2, label=LABELS[v])
        ends.append([len(ts), v])
    ax.set_ylim(0, top * 1.08)
    if end_labels:
        # spread the labels at the right ends so that they do not overlap (at least 7% of the height apart)
        gap = top * 1.08 * 0.07
        ends.sort()
        pos = []
        for y, v in ends:
            pos.append(max(y, pos[-1] + gap) if pos else y)
        for (y, v), p in zip(ends, pos):
            ax.annotate(f"{LABELS[v]}: {y}", xy=(T_MAX, y), xytext=(T_MAX * 1.25, p), textcoords="data",
                        color=COLORS[v], fontsize=11, va="center", annotation_clip=False,
                        arrowprops=dict(arrowstyle="-", color=COLORS[v], linewidth=0.8) if abs(p - y) > 1e-9 else None)


def save(fig, out_dir, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def single(rows, title, out_dir, name):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    draw(ax, rows, True)
    style(ax)
    ax.set_title(f"{title}: решено {best(rows)} из {instances(rows)}")
    fig.subplots_adjust(right=0.68)
    save(fig, out_dir, name)


def grid(rows, maps, shape, out_dir, name):
    fig, axes = plt.subplots(*shape, figsize=(5.2 * shape[1], 4.0 * shape[0]))
    for ax, m in zip(axes.flat, maps):
        rs = [r for r in rows if r["map"] == m]
        draw(ax, rs, False)
        style(ax)
        ax.set_title(f"{m}: решено {best(rs)} из {instances(rs)}")
    handles = [Line2D([], [], color=COLORS[v], linewidth=2) for v in VARIANTS]
    fig.legend(handles, [LABELS[v] for v in VARIANTS], loc="lower center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save(fig, out_dir, name)


def main():
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for m in SMALL + LARGE:
        rs = [r for r in rows if r["map"] == m]
        if rs:
            single(rs, m, out_dir, f"cactus_{m}")
    grid(rows, SMALL, (2, 3), out_dir, "cactus_grid_small")
    grid(rows, LARGE, (2, 2), out_dir, "cactus_grid_large")
    single([r for r in rows if r["map"] in SMALL], "Малые карты", out_dir, "cactus_small")
    single([r for r in rows if r["map"] in LARGE], "Большие карты", out_dir, "cactus_large")


if __name__ == "__main__":
    main()
