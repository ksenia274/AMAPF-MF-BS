#!/usr/bin/env python3
"""Slides figures (PNG, Russian labels). Run from this folder: python make_figures.py
(a) cbm_random32.png  <- cbm_random32.csv  (cbm on random-32-32-10 scen 1, 60 s limit)
(b) cbm_levels.png    <- cbm_levels.csv    (runs of step 3, scen 1, 60 s limit)
(c) goal_wait_example.png - minimal instance where bs_team without explicit goal waits is wrong
"""
import csv

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # first three slots of the reference palette (validated all-pairs)
MARKERS = ["o", "s", "^"]
plt.rcParams.update({"font.size": 16, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "text.color": INK, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE, "axes.spines.top": False, "axes.spines.right": False})


def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fig_a():
    rows = read("cbm_random32.csv")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, field, scale, title in [(axes[0], "total_ms", 1000, "Время решения, с"),
                                    (axes[1], "nodes_generated", 1, "Узлов дерева ограничений")]:
        for i, k in enumerate((2, 4, 8)):
            pts = [(int(r["N"]), int(r[field]) / scale) for r in rows if int(r["K"]) == k and r["solved"] == "1"]
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color=SERIES[i], lw=2, marker=MARKERS[i], ms=9, mec=SURFACE, mew=2, label=f"K = {k}")
            ax.annotate(f"K = {k}", (xs[-1], ys[-1]), xytext=(8, 0), textcoords="offset points", va="center",
                        color=INK, fontsize=14)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks([16, 32, 64, 128], ["16", "32", "64", "128"])
        ax.set_xlim(12, 200)
        ax.set_xlabel("Число роботов N")
        ax.set_title(title, loc="left", fontsize=17)
        ax.grid(True, which="major", color=GRID, lw=1)
        ax.legend(frameon=False, fontsize=13, loc="upper left")
    fig.suptitle("CBM на Bulk Search, random-32-32-10, K команд (робот i в команде i mod K)", x=0.01, ha="left",
                 fontsize=17)
    fig.tight_layout()
    fig.savefig("cbm_random32.png", dpi=150)


def fig_b():
    rows = read("cbm_levels.csv")
    fig, ax = plt.subplots(figsize=(14, 6))
    names = {"random-32-32-10": "random 32×32", "room-64-64-8": "room 64×64", "Berlin_1_256": "Berlin 256×256"}
    labels, low, high = [], [], []
    for r in rows:
        labels.append(f"{names[r['map']]}\nN = {r['N']}, K = {r['K']}")
        total = int(r["lowlevel_ms"]) + int(r["highlevel_ms"])
        low.append(100 * int(r["lowlevel_ms"]) / total)
        high.append(100 * int(r["highlevel_ms"]) / total)
    y = list(range(len(rows)))[::-1]
    ax.barh(y, low, height=0.6, color=SERIES[0], label="нижний уровень (Bulk Search)", edgecolor=SURFACE, lw=2)
    ax.barh(y, high, left=low, height=0.6, color=SERIES[1], label="верхний уровень (CBS)", edgecolor=SURFACE, lw=2)
    for yi, r, lo in zip(y, rows, low):
        status = f"T = {r['T']}, {int(r['total_ms']) / 1000:.1f} с" if r["solved"] == "1" else "не решено за 60 с"
        ax.text(101, yi, f"{lo:.0f}% / {100 - lo:.0f}%   {status}", va="center", fontsize=14, color=INK)
    ax.set_yticks(y, labels, fontsize=14)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Доля времени, %")
    ax.set_title("Где тратится время CBM (лимит 60 с)", loc="left", fontsize=17)
    ax.legend(frameon=False, fontsize=14, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)
    fig.text(0.01, 0.02, "Прогоны шли параллельно с другими вычислениями: доли надёжнее секунд. "
             "room 64×64 на свободной машине решён за 52 с (T = 43).", fontsize=12, color=INK2)
    fig.tight_layout()
    fig.subplots_adjust(right=0.68, bottom=0.25)
    fig.savefig("cbm_levels.png", dpi=150)


def fig_c():
    # Corridor 1x3, cells 0, 1, 2. Agents A (start 0), B (start 1), goals {1, 2}, constraint: nobody in cell 2 at t = 1.
    # brute force and bs_team: T = 2, routes A: 0 0 1, B: 1 1 2. Without explicit goal waits: "no solution" for every T.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1, 1.1]})
    for ax in (ax1, ax2):
        ax.set_aspect("equal")
        ax.axis("off")
    # left: the instance
    for c in range(3):
        ax1.add_patch(Rectangle((c, 0), 1, 1, fill=False, ec=INK2, lw=2))
        ax1.text(c + 0.5, -0.25, f"клетка {c}", ha="center", va="top", fontsize=14, color=INK2)
    for c in (1, 2):
        ax1.add_patch(Rectangle((c + 0.08, 0.08), 0.84, 0.84, fill=False, ec=INK, lw=2, ls="--"))
    ax1.text(1.5, 1.12, "цели (пунктир): клетки 1 и 2", ha="center", fontsize=14)
    for c, name, col in [(0, "A", SERIES[0]), (1, "B", SERIES[1])]:
        ax1.add_patch(plt.Circle((c + 0.5, 0.5), 0.28, color=col))
        ax1.text(c + 0.5, 0.5, name, ha="center", va="center", color="white", fontsize=18, weight="bold")
    ax1.text(1.5, -0.75, "запрет: в клетке 2 никого\nпри t = 1", ha="center", va="top", fontsize=15)
    ax1.set_xlim(-0.2, 3.2)
    ax1.set_ylim(-1.6, 1.5)
    ax1.set_title("Задача: коридор 1×3, одна команда", loc="left", fontsize=17)
    # right: time-space diagram of the correct solution
    for t in range(3):
        for c in range(3):
            ax2.add_patch(Rectangle((c, t), 1, 1, fill=False, ec=GRID, lw=1.5))
        ax2.text(-0.15, t + 0.5, f"t = {t}", ha="right", va="center", fontsize=14, color=INK2)
    for c in range(3):
        ax2.text(c + 0.5, -0.15, f"клетка {c}", ha="center", va="top", fontsize=14, color=INK2)
    ax2.add_patch(Rectangle((2, 1), 1, 1, fill=False, ec=INK, lw=0, hatch="///"))
    ax2.text(2.5, 1.5, "запрет", ha="center", va="center", fontsize=13, bbox={"fc": SURFACE, "ec": "none"})
    for route, col, name in [([0, 0, 1], SERIES[0], "A"), ([1, 1, 2], SERIES[1], "B")]:
        xs = [c + 0.5 for c in route]
        ys = [t + 0.5 for t in range(3)]
        ax2.plot(xs, ys, color=col, lw=3, marker="o", ms=12, mec=SURFACE, mew=2)
        ax2.text(xs[-1] + 0.12, ys[-1] + 0.3, name, color=INK, fontsize=16, weight="bold")
    ax2.set_xlim(-0.9, 3.1)
    ax2.set_ylim(-0.7, 3.2)
    ax2.set_title("Верно: T = 2, B ждёт в цели 1", loc="left", fontsize=17)
    fig.text(0.01, 0.03, "Исходная версия с запретами: «решения нет» при любом T. Она разрешает роботу, занявшему цель, "
             "уйти из неё только\nв самый ранний момент: B ушёл бы в клетку 2 при t = 1, а там запрет. "
             "Найдено полным перебором: самая маленькая такая задача.", fontsize=13, color=INK2)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.2, wspace=0.15)
    fig.savefig("goal_wait_example.png", dpi=150)


if __name__ == "__main__":
    fig_a()
    fig_b()
    fig_c()
