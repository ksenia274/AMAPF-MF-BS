#!/usr/bin/env python3
"""Week 6, part 1: from cbm_bench_cactus.csv and small_maps_cut.csv only (no runs).

Usage: week6_part1.py            (prints the markdown tables, writes figures/week6_time_bscut_floww.png/.pdf)
1.1 small maps: instances solved by both bscut and floww, total_ms of both.
1.2 large maps: per map and variant solved / timeout in the root (root_conflict_pairs = -1) / timeout in the CT /
    timeout_skipped (not run).
1.3 per-instance ratio of the replan medians bscut / bspen on the solved city instances; how the medians of
    small_maps_cut.csv treat the timeouts.
"""
import csv
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
SMALL = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8"]
LARGE = ["warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]
CITIES = LARGE[1:]


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return list(csv.DictReader(f))


def part11(rows):
    by = {(r["map"], r["N"], r["scen"], r["variant"]): r for r in rows}
    pairs = []
    for (m, n, s, v), r in by.items():
        if v == "bscut" and m in SMALL and r["status"] == "solved":
            f = by.get((m, n, s, "floww"))
            if f and f["status"] == "solved":
                pairs.append((m, int(n), int(s), float(r["total_ms"]), float(f["total_ms"])))
    print("### 1.1\n")
    print("| map | both solved | bscut faster | equal | floww faster | median floww / bscut | min | max | "
          "median ms bscut | median ms floww |")
    print("|---|---|---|---|---|---|---|---|---|---|")

    def line(name, ps):
        ratios = [f / max(b, 1) for _, _, _, b, f in ps]
        faster = sum(b < f for *_, b, f in ps)
        eq = sum(b == f for *_, b, f in ps)
        print(f"| {name} | {len(ps)} | {faster} | {eq} | {len(ps) - faster - eq} | {statistics.median(ratios):.1f} | "
              f"{min(ratios):.2f} | {max(ratios):.0f} | {statistics.median(b for *_, b, f in ps):.0f} | "
              f"{statistics.median(f for *_, b, f in ps):.0f} |")
    for m in SMALL:
        line(m, [p for p in pairs if p[0] == m])
    line("**all small**", pairs)
    slower = sorted((p for p in pairs if p[3] > p[4]), key=lambda p: p[4] / max(p[3], 1))
    print("\nbscut slower than floww:", ", ".join(f"{m} N{n} s{s} ({b:.0f} vs {f:.0f} ms)" for m, n, s, b, f in slower))
    # ms of the run is rounded to whole ms, so ratios of tiny runs are coarse
    print("instances with bscut total_ms < 10:", sum(p[3] < 10 for p in pairs))
    plot(pairs)


def plot(pairs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11})
    fig, ax = plt.subplots(figsize=(6.2, 6))
    xs = [max(p[3], 1) / 1000 for p in pairs]
    ys = [max(p[4], 1) / 1000 for p in pairs]
    ax.scatter(xs, ys, s=28, color="#2E8B57", alpha=0.75, edgecolors="white", linewidths=0.6, zorder=3)
    lo, hi = 1e-3, 100
    ax.plot([lo, hi], [lo, hi], color="#888888", linewidth=1, zorder=2)
    for k, lab in ((10, "floww в 10 раз дольше"), (100, "в 100 раз")):
        ax.plot([lo, hi / k], [lo * k, hi], color="#bbbbbb", linewidth=0.8, linestyle="--", zorder=1)
        ax.annotate(lab, (lo * 1.3, lo * k * 1.3 * 1.15), color="#777777", fontsize=9, ha="left", rotation=45,
                    rotation_mode="anchor")
    ax.annotate("одинаково", (lo * 4, lo * 4 / 1.5), color="#777777", fontsize=9, ha="left", rotation=45,
                rotation_mode="anchor")
    ax.set_xscale("log"), ax.set_yscale("log")
    ax.set_xlim(lo, hi), ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    ax.set_xlabel("время bscut, с")
    ax.set_ylabel("время floww, с")
    ax.set_title(f"Малые карты: {len(pairs)} задач, решённых обоими")
    ax.grid(color="#e5e5e5", linewidth=0.7)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, "figures", f"week6_time_bscut_floww.{ext}"), dpi=150)


def part12(rows):
    print("\n### 1.2\n")
    variants = ["bs", "bspen", "bscut", "flow", "floww"]
    print("| map | variant | solved | timeout: root | timeout: CT | not run (timeout_skipped) | other |")
    print("|---|---|---|---|---|---|---|")
    for m in LARGE:
        for v in variants:
            rs = [r for r in rows if r["map"] == m and r["variant"] == v]
            st = [r["status"] for r in rs]
            to = [r for r in rs if r["status"] == "timeout"]
            root = sum(r["root_conflict_pairs"] == "-1" for r in to)
            other = len(rs) - st.count("solved") - len(to) - st.count("timeout_skipped")
            print(f"| {m} | {v} | {st.count('solved')} | {root} | {len(to) - root} | {st.count('timeout_skipped')} | {other} |")
    # an unfinished root (root_conflict_pairs = -1) must have at most K replans (the last one cut by the limit) and
    # no expanded CT node
    to = [r for r in rows if r["status"] == "timeout" and r["map"] in LARGE]
    bad = [r for r in to if r["root_conflict_pairs"] == "-1" and
           (int(r["lowlevel_calls"]) > int(r["K"]) or r["nodes_expanded"] != "0")]
    print("\nunfinished roots with more than K replans or expanded CT nodes:", len(bad))
    print("finished roots, timeout before the first CT expansion was done:",
          [(r["map"], r["N"], r["scen"], r["variant"]) for r in to if r["root_conflict_pairs"] != "-1" and r["nodes_expanded"] == "0"])
    calls = [int(r["lowlevel_calls"]) / int(r["K"]) for r in to if r["root_conflict_pairs"] == "-1"]
    print(f"unfinished roots: replans done / K from {min(calls):.2f} to {max(calls):.2f}")
    print("\nCT timeouts:")
    for r in rows:
        if r["map"] in LARGE and r["status"] == "timeout" and r["root_conflict_pairs"] != "-1":
            print(f"  {r['map']} N{r['N']} s{r['scen']} {r['variant']}: expanded {r['nodes_expanded']}, "
                  f"replans {r['lowlevel_calls']}, K {r['K']}, last_key {r['last_key']}, replan median {r['replan_ms_median']} ms")


def part13(rows, cut):
    print("\n### 1.3\n")
    by = {(r["map"], r["N"], r["scen"], r["variant"]): r for r in rows}
    ratios = []
    for (m, n, s, v), r in by.items():
        if v == "bscut" and m in CITIES and r["status"] == "solved":
            p = by[(m, n, s, "bspen")]
            if p["status"] == "solved":
                ratios.append((m, int(n), int(s), float(r["replan_ms_median"]), float(p["replan_ms_median"])))
    ratios.sort(key=lambda x: x[3] / x[4])
    print("solved by both, cities:", len(ratios))
    for m, n, s, c, p in ratios:
        print(f"  {m} N{n} s{s}: bscut {c:.0f} ms, bspen {p:.0f} ms, ratio {c / p:.2f}")
    for m in CITIES:
        for n in ("64", "128"):
            b = [float(r["replan_ms_median"]) for r in rows if r["map"] == m and r["N"] == n and r["variant"] == "bscut" and r["status"] == "solved"]
            p = [float(r["replan_ms_median"]) for r in rows if r["map"] == m and r["N"] == n and r["variant"] == "bspen" and r["status"] == "solved"]
            if b and p:
                print(f"  medians over the solved scens {m} N{n}: bscut {statistics.median(b):.0f} ({len(b)}), "
                      f"bspen {statistics.median(p):.0f} ({len(p)}), ratio {statistics.median(b) / statistics.median(p):.2f}")
    print("\nsmall_maps_cut.csv, median ms over the 16 instances:")
    for v in ("bspen", "bscut", "bscut_all", "floww"):
        rs = [r for r in cut if r["variant"] == v]
        ms = [float(r["total_ms"]) for r in rs]
        solved = [float(r["total_ms"]) for r in rs if r["status"] == "solved"]
        print(f"  {v}: median of all 16 (timeouts at their ms) {statistics.median(ms):.1f}; timeouts {len(ms) - len(solved)}; "
              f"median of the solved only {statistics.median(solved):.1f}; timeouts counted as +inf "
              f"{statistics.median(sorted(solved) + [float('inf')] * (len(ms) - len(solved))):.1f}")


def main():
    rows = load("cbm_bench_cactus.csv")
    part11(rows)
    part12(rows)
    part13(rows, load("small_maps_cut.csv"))


if __name__ == "__main__":
    main()
