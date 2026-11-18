#!/usr/bin/env python3
"""Cactus plots of cbm_bench_cactus.py: solved instances by time, one line per low level.

Usage: make_cactus.py BENCH.csv [OUT_DIR]   (OUT_DIR defaults to the folder of this script)
  -> <ID>__cactus_<map>.png/.pdf for every map in BENCH.csv, <ID>__cactus_grid_small, <ID>__cactus_grid_large (maps
     in cells; only when every map of the group is in BENCH.csv), <ID>__cactus_small, <ID>__cactus_large (all
     instances of the group; only when the group has a map in BENCH.csv). ID: the run of BENCH.csv (runlib.run_meta,
     from its run_id column or its manifest); under every plot a small grey line: ID, maps, limit, teams, start T.
Time = total_ms of cbm of the solved runs; times below 0.01 s are drawn at 0.01 s. Every line is labelled at its
right end with the number of solved instances (no legend); y runs to the number of instances (40 per map, 240 / 160
for the groups) on every plot.
"""
import csv
import os
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import runlib  # noqa: E402

VARIANTS = ["bs", "bspen", "bscut", "flow", "floww"]
LABELS = {"bs": "Bulk Search", "bspen": "Bulk Search со штрафами", "bscut": "Bulk Search с резкой", "flow": "Поток без штрафов",
          "floww": "Поток со штрафами"}
COLORS = {"bs": "#6FA0DC", "bspen": "#3B6BA5", "bscut": "#2E8B57", "flow": "#C9822B", "floww": "#B03A5B"}
SMALL = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8"]
LARGE = ["warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]
DASHED = {"bs"}
T_MIN, T_MAX = 0.01, 60
TICKS = [0.01, 0.1, 1, 10, 60]

plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 11,
                     "ytick.labelsize": 11, "legend.fontsize": 11})


def times(rows, variant):
    return sorted(max(T_MIN, float(r["total_ms"]) / 1000) for r in rows
                  if r["variant"] == variant and r["status"] == "solved")


def instances(rows):
    return len({(r["map"], r["N"], r["scen"]) for r in rows})


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


def draw(ax, rows, top, fontsize=11):
    ends = []
    for v in VARIANTS:
        if not any(r["variant"] == v for r in rows):
            continue
        ts = times(rows, v)
        xs = [T_MIN] + ts + [T_MAX]
        ys = [0] + list(range(1, len(ts) + 1)) + [len(ts)]
        ax.step(xs, ys, where="post", color=COLORS[v], linewidth=2, linestyle="--" if v in DASHED else "-")
        ends.append([len(ts), v])
    ax.set_ylim(0, top)
    ax.set_yticks(range(0, top + 1, max(1, top // 8 if top <= 160 else top // 6)))
    # spread the labels at the right ends so that they do not overlap (at least 8% of the height apart) and stay
    # below the top of the axis
    gap = top * 0.08
    ends.sort()
    pos = []
    for y, v in ends:
        pos.append(max(y, pos[-1] + gap) if pos else y)
    for i in reversed(range(len(pos))):
        pos[i] = min(pos[i], top if i == len(pos) - 1 else pos[i + 1] - gap)
    for (y, v), p in zip(ends, pos):
        ax.annotate(f"{LABELS[v]}: {y}", xy=(T_MAX, y), xytext=(T_MAX * 1.25, p), textcoords="data",
                    color=COLORS[v], fontsize=fontsize, va="center", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=COLORS[v], linewidth=0.8) if abs(p - y) > 1e-9 else None)


def save(fig, out_dir, name, caption=None):
    if caption:
        fig.text(0.02, -0.02, "\n".join(textwrap.wrap(caption, 120)), ha="left", va="top", fontsize=8,
                 color="#777777")
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def caption_of(rows, run):
    """run = (ID, manifest) or None (no caption)"""
    if not run:
        return None
    return runlib.caption(run[0], run[1], [m for m in SMALL + LARGE if any(r["map"] == m for r in rows)])


def single(rows, title, out_dir, name, run=None):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    draw(ax, rows, instances(rows))
    style(ax)
    ax.set_title(title)
    fig.subplots_adjust(right=0.68)
    save(fig, out_dir, name, caption_of(rows, run))


def grid(rows, maps, shape, out_dir, name, run=None):
    fig, axes = plt.subplots(*shape, figsize=(7.6 * shape[1], 4.0 * shape[0]))
    for ax, m in zip(axes.flat, maps):
        rs = [r for r in rows if r["map"] == m]
        draw(ax, rs, 40, fontsize=10)
        style(ax)
        ax.set_title(m)
    fig.subplots_adjust(left=0.05, right=0.86, wspace=0.75, hspace=0.4)
    save(fig, out_dir, name, caption_of([r for r in rows if r["map"] in maps], run))


def main():
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    run = runlib.run_meta(path)
    rid = run[0]
    with open(path) as f:
        rows = list(csv.DictReader(f))
    present = {r["map"] for r in rows}
    for m in SMALL + LARGE:
        rs = [r for r in rows if r["map"] == m]
        if rs:
            single(rs, m, out_dir, f"{rid}__cactus_{m}", run)
    # a grid only when every map of the group is there; a group plot when at least one is
    for group, shape, gname, title in ((SMALL, (2, 3), "small", "Малые карты"), (LARGE, (2, 2), "large", "Большие карты")):
        if all(m in present for m in group):
            grid(rows, group, shape, out_dir, f"{rid}__cactus_grid_{gname}", run)
        rs = [r for r in rows if r["map"] in group]
        if rs:
            single(rs, title, out_dir, f"{rid}__cactus_{gname}", run)

if __name__ == "__main__":
    main()
