#!/usr/bin/env python3
"""Plots of week 7, stage C2 (series A-D of cbm_bench_cactus.py), one panel per map, one line per low level.

Usage: make_c2.py by-n BENCH.csv[,BENCH2.csv,..] [OUT_DIR]      (series A with stage B, series D)
         <ID>__by_n_solved: share of solved scen by N; <ID>__by_n_nodes: median CT nodes (nodes_generated) of the
         solved runs by N; <ID>__by_n_root: median root_ms by N
       make_c2.py by-k BENCH.csv [OUT_DIR]                       (series B)
         <ID>__by_k_solved, <ID>__by_k_time (median total_ms of the instances solved by every variant of the CSV),
         <ID>__by_k_nodes, <ID>__by_k_conflicts (median root_conflict_pairs, all runs where the root was finished)
       make_c2.py limit BENCH60.csv[,..] BENCH300.csv BENCH600.csv [OUT_DIR]   (series C)
         <ID>__limit_solved: per variant, of the instances retried at 300 s, how many were solved at 300 s and how
         many more at 600 s; <ID>__limit_gap: T of the instances solved at 300 / 600 s against last_key of the same
         instance at 60 s (the lower bound reached by then)
OUT_DIR defaults to the folder of this script; every plot is written as .png and .pdf with the caption of its runs.
Share of solved: over the scen of the map in the CSVs (a sequence that stopped earlier, or was not continued, counts
as not solved). root_ms: rows without it (runs before root_ms was printed) use total_ms when the root was the
solution (nodes_generated = 1) and are left out otherwise.
"""
import csv
import os
import statistics
import sys

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runlib  # noqa: E402
from make_cactus import COLORS, DASHED, LABELS, LARGE, LARGE_MORE, SMALL, SMALL_MORE, VARIANTS, save  # noqa: E402

ORDER = SMALL + LARGE + SMALL_MORE + LARGE_MORE

plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "legend.fontsize": 10})


def load(paths):
    run, rows = [], []
    for p in paths:
        run.append(runlib.run_meta(p))
        with open(p) as f:
            rows += list(csv.DictReader(f))
    return "+".join(r[0] for r in run), run, rows


def caption(run, rows):
    maps = [m for m in ORDER if any(r["map"] == m for r in rows)]
    return "\n".join(runlib.caption(rid, m, maps) for rid, m in run)


def root_ms(r):
    if r.get("root_ms") not in (None, "", "-1", "-1.000"):
        return float(r["root_ms"])
    if r["status"] == "solved" and r["nodes_generated"] == "1":
        return float(r["total_ms"])
    return None


def panels(maps, title_y, draw, out_dir, name, cap, xlabel, xs_of, logy=False, logx=False):
    cols = min(3, len(maps))
    rws = -(-len(maps) // cols)
    fig, axes = plt.subplots(rws, cols, figsize=(4.6 * cols, 3.3 * rws), squeeze=False)
    used = set()
    for ax, m in zip(axes.flat, maps):
        used |= draw(ax, m)
        xs = xs_of(m)
        if logx:
            ax.set_xscale("log", base=2)
            ax.set_xlim(xs[0] / 1.2, xs[-1] * 1.2)
            ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
            ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:g}"))
        else:
            pad = (xs[-1] - xs[0]) * 0.05 or 1
            ax.set_xlim(xs[0] - pad, xs[-1] + pad)
        ax.set_xticks(xs)
        ax.set_title(m)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(title_y)
        if logy:
            ax.set_yscale("log")
            ys = [y for ln in ax.get_lines() for y in ln.get_ydata()]
            if ys:
                lo, hi = min(ys), max(ys)
                if hi / lo < 10:  # at least one decade, so that a major tick is visible
                    mid = (lo * hi) ** 0.5
                    lo, hi = mid / 10 ** 0.5, mid * 10 ** 0.5
                ax.set_ylim(lo / 1.3, hi * 1.3)
            ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:g}"))
            ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.grid(axis="y", color="#dddddd", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    for ax in axes.flat[len(maps):]:
        ax.set_visible(False)
    handles = [plt.Line2D([], [], color=COLORS[v], linewidth=2, linestyle="--" if v in DASHED else "-", marker="o")
               for v in VARIANTS if v in used]
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.06 / rws))
    fig.legend(handles, [LABELS[v] for v in VARIANTS if v in used], loc="upper center", ncol=len(handles),
               bbox_to_anchor=(0.5, 1.0), frameon=False)
    save(fig, out_dir, name, cap)


def line(ax, v, xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if pts:
        # later variants thinner: coinciding lines stay visible as coloured edges
        w = 4.0 - 0.6 * VARIANTS.index(v)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=COLORS[v], linewidth=w, marker="o", markersize=w + 2,
                linestyle="--" if v in DASHED else "-")
        return {v}
    return set()


def median_or_none(xs):
    return statistics.median(xs) if xs else None


def by_axis(rows, axis, out_dir, rid, cap, kinds):
    maps = [m for m in ORDER if any(r["map"] == m for r in rows)]
    variants = [v for v in VARIANTS if any(r["variant"] == v for r in rows)]
    label = {"N": "роботов, N", "K": "команд, K"}[axis]

    def values(m):
        return sorted({int(r[axis]) for r in rows if r["map"] == m})

    def solved(ax, m):
        scens = {r["scen"] for r in rows if r["map"] == m}
        used = set()
        for v in variants:
            xs = values(m)
            ys = [sum(r["status"] == "solved" for r in rows if r["map"] == m and r["variant"] == v and int(r[axis]) == x)
                  / len(scens) for x in xs]
            used |= line(ax, v, xs, ys)
        ax.set_ylim(0, 1.05)
        return used

    def med(get):
        def draw(ax, m):
            used = set()
            for v in variants:
                xs = values(m)
                ys = [median_or_none([y for r in rows if r["map"] == m and r["variant"] == v and int(r[axis]) == x
                                      for y in [get(r, m)] if y is not None]) for x in xs]
                used |= line(ax, v, xs, ys)
            return used
        return draw

    def nodes(r, m):
        return int(r["nodes_generated"]) if r["status"] == "solved" else None

    def conflicts(r, m):
        return int(r["root_conflict_pairs"]) if r["root_conflict_pairs"] not in ("", "-1") else None

    def by_all(r, m):
        if r["status"] != "solved":
            return None
        inst = [q for q in rows if (q["map"], q["N"], q["K"], q["scen"]) == (r["map"], r["N"], r["K"], r["scen"])]
        ok = {q["variant"] for q in inst if q["status"] == "solved"}
        return float(r["total_ms"]) / 1000 if ok >= set(variants) else None

    plots = {"solved": (solved, "доля решённых", False),
             "nodes": (med(nodes), "узлов CT, медиана", True),
             "root": (med(lambda r, m: root_ms(r)), "время корня, мс, медиана", True),
             "time": (med(by_all), "время, с, медиана", True),
             "conflicts": (med(conflicts), "пар конфликтов в корне, медиана", False)}
    prefix = {"N": "by_n", "K": "by_k"}[axis]
    for kind in kinds:
        draw, ylabel, logy = plots[kind]
        panels(maps, ylabel, draw, out_dir, f"{rid}__{prefix}_{kind}", cap, label, values, logy, logx=axis == "K")


def limit(paths60, path300, path600, out_dir):
    _, run60, rows60 = load(paths60)
    rid3, run3, rows300 = load([path300])
    rid6, run6, rows600 = load([path600])
    rid = rid3 + "+" + rid6
    key = lambda r: (r["map"], r["N"], r["K"], r["scen"], r["variant"])  # noqa: E731
    at600 = {key(r): r for r in rows600}
    at60 = {key(r): r for r in rows60}
    variants = [v for v in VARIANTS if any(r["variant"] == v for r in rows300)]
    retried = [r for r in rows300 if r["status"] != "timeout_skipped"]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    for i, v in enumerate(variants):
        rs = [r for r in retried if r["variant"] == v]
        s300 = sum(r["status"] == "solved" for r in rs)
        s600 = sum(at600.get(key(r), {}).get("status") == "solved" for r in rs if r["status"] != "solved")
        ax.barh(i, len(rs), color="none", edgecolor="#bbbbbb", linewidth=1, height=0.6)
        ax.barh(i, s300, color=COLORS[v], height=0.6)
        ax.barh(i, s600, left=s300, color=COLORS[v], alpha=0.45, height=0.6, edgecolor="white", linewidth=2)
        ax.text(len(rs) * 1.02 + 0.3, i, f"{s300} + {s600} из {len(rs)}", va="center", fontsize=10, color="#333333")
    ax.set_yticks(range(len(variants)))
    ax.set_yticklabels([LABELS[v] for v in variants])
    ax.invert_yaxis()
    ax.set_xlabel("задач")
    ax.set_title("Не решённые за 60 с: решено за 300 с (тёмное), ещё за 600 с (светлое), контур — все", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, max(1, max(sum(r["variant"] == v for r in retried) for v in variants)) * 1.35)
    fig.tight_layout()
    save(fig, out_dir, f"{rid}__limit_solved", caption(run3 + run6, rows300))

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    used = set()
    for v in variants:
        pts = []
        for r in rows300 + rows600:
            old = at60.get(key(r))
            if r["variant"] == v and r["status"] == "solved" and old and old.get("last_key") not in (None, "", "-1"):
                pts.append((int(old["last_key"]), int(r["T"])))
        if pts:
            used.add(v)
            ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=28, color=COLORS[v], edgecolors="white",
                       linewidths=1, label=LABELS[v])
    lim = ax.get_xlim()[0], max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot(lim, lim, color="#999999", linewidth=1, linestyle=":")
    ax.set_xlabel("last_key через 60 с (нижняя оценка)")
    ax.set_ylabel("найденный T")
    ax.spines[["top", "right"]].set_visible(False)
    if used:
        ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, out_dir, f"{rid}__limit_gap", caption(run60 + run3 + run6, rows300))


def main():
    mode, args = sys.argv[1], sys.argv[2:]
    here = os.path.dirname(os.path.abspath(__file__))
    if mode == "limit":
        limit(args[0].split(","), args[1], args[2], args[3] if len(args) > 3 else here)
        return
    rid, run, rows = load(args[0].split(","))
    out_dir = args[1] if len(args) > 1 else here
    if mode == "by-n":
        by_axis(rows, "N", out_dir, rid, caption(run, rows), ["solved", "nodes", "root"])
    elif mode == "by-k":
        by_axis(rows, "K", out_dir, rid, caption(run, rows), ["solved", "time", "nodes", "conflicts"])
    else:
        sys.exit("mode: by-n, by-k or limit")


if __name__ == "__main__":
    main()
