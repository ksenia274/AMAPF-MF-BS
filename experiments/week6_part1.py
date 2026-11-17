#!/usr/bin/env python3
"""Week 6, part 1: from cbm_bench_cactus.csv and small_maps_cut.csv only (no runs).

Usage: week6_part1.py            (prints the markdown tables, writes figures/week6_time_bscut_floww.png/.pdf)
       week6_part1.py --stage-b [NEW.csv] [--suffix S]
           stage B: NEW.csv (default cbm_bench_cactus_match.csv, --t-start match) against cbm_bench_cactus.csv (lb)
           on the maps present in NEW.csv; writes figures/week6_time_bscut_floww<S>.png/.pdf (S defaults to _match)
1.1 small maps: instances solved by both bscut and floww, total_ms of both.
1.2 large maps: per map and variant solved / timeout in the root (root_conflict_pairs = -1) / timeout in the CT /
    timeout_skipped (not run).
1.3 per-instance ratio of the replan medians bscut / bspen on the solved city instances; how the medians of
    small_maps_cut.csv treat the timeouts.
"""
import csv
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SMALL = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8"]
LARGE = ["warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]
CITIES = LARGE[1:]


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return list(csv.DictReader(f))


def part11(rows, fig_name="week6_time_bscut_floww"):
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
        if any(p[0] == m for p in pairs):
            line(m, [p for p in pairs if p[0] == m])
    line("**all small**", pairs)
    slower = sorted((p for p in pairs if p[3] > p[4]), key=lambda p: p[4] / max(p[3], 1))
    print("\nbscut slower than floww:", ", ".join(f"{m} N{n} s{s} ({b:.0f} vs {f:.0f} ms)" for m, n, s, b, f in slower))
    # ms of the run is rounded to whole ms, so ratios of tiny runs are coarse
    print("instances with bscut total_ms < 10:", sum(p[3] < 10 for p in pairs))
    plot(pairs, fig_name)


def plot(pairs, fig_name):
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
        fig.savefig(os.path.join(HERE, "figures", f"{fig_name}.{ext}"), dpi=150)


def part12(rows, maps=LARGE):
    print("\n### 1.2\n")
    variants = ["bs", "bspen", "bscut", "flow", "floww"]
    print("| map | variant | solved | timeout: root | timeout: CT | not run (timeout_skipped) | other |")
    print("|---|---|---|---|---|---|---|")
    for m in maps:
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
    if calls:
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


VARIANTS = ["bs", "bspen", "bscut", "flow", "floww"]


def solved_by(rows):
    """(map, N, scen) -> {variant: row} of the solved runs"""
    out = {}
    for r in rows:
        if r["status"] == "solved":
            out.setdefault((r["map"], r["N"], r["scen"]), {})[r["variant"]] = r
    return out


def stage_b(new_name="cbm_bench_cactus_match.csv", suffix="_match"):
    """Only the maps present in new_name are compared; the old (lb) rows are cut to the same maps."""
    new = load(new_name)
    maps = [m for m in SMALL + LARGE if any(r["map"] == m for r in new)]
    large = [m for m in LARGE if m in maps]
    old = [r for r in load("cbm_bench_cactus.csv") if r["map"] in maps]
    so, sn = solved_by(old), solved_by(new)
    print(f"maps: {', '.join(maps)}\n")
    print("### B.1 solved per map and variant: lb (old) and match (new)\n")
    print("| map | variant | solved lb | solved match |")
    print("|---|---|---|---|")

    def count(solved, ms, v):
        return sum(v in vs for k, vs in solved.items() if k[0] in ms)
    for m in maps + ["**all these maps**"]:
        ms = maps if m == "**all these maps**" else [m]
        for v in VARIANTS:
            print(f"| {m} | {v} | {count(so, ms, v)} | {count(sn, ms, v)} |")
    print("\nruns per variant (old / new):", ", ".join(
        f"{v} {sum(r['variant'] == v for r in old)} / {sum(r['variant'] == v for r in new)}" for v in VARIANTS))
    print("statuses new:", {st: sum(r["status"] == st for r in new) for st in sorted({r["status"] for r in new})})
    print("statuses old:", {st: sum(r["status"] == st for r in old) for st in sorted({r["status"] for r in old})})

    print("\n### B.2 large maps, match")
    if large:
        part12(new, large)
    else:
        print("\nno large map here")

    print("\n### B.3 solved with lb and not with match (lost), and the other way (gained)\n")
    by_old = {(r["map"], r["N"], r["scen"], r["variant"]): r for r in old}
    by_new = {(r["map"], r["N"], r["scen"], r["variant"]): r for r in new}
    for v in VARIANTS:
        lost = [k for k, r in by_old.items()
                if k[3] == v and r["status"] == "solved" and by_new.get(k, {}).get("status") != "solved"]
        gained = [k for k, r in by_new.items()
                  if k[3] == v and r["status"] == "solved" and by_old.get(k, {}).get("status") != "solved"]
        print(f"{v}: lost {len(lost)}, gained {len(gained)}")
        for tag, ks in (("lost", lost), ("gained", gained)):
            for k in sorted(ks, key=lambda k: (k[0], int(k[1]), int(k[2]))):
                o, n = by_old.get(k, {}), by_new.get(k, {})
                print(f"  {tag} {k[0]} N{k[1]} s{k[2]}: lb {o.get('status', '-')} {o.get('total_ms', '')} ms, "
                      f"match {n.get('status', '-')} {n.get('total_ms', '')} ms")

    print("\n### B.4 checks\n")
    bad = [(k, {v: r["T"] for v, r in vs.items()}) for k, vs in sn.items() if len({r["T"] for r in vs.values()}) > 1]
    print(f"match: instances solved by several variants {sum(len(vs) > 1 for vs in sn.values())}, "
          f"makespan differs: {len(bad)} {bad[:5]}")
    cross = [(k, v) for k, vs in sn.items() for v, r in vs.items()
             if k in so and any(o["T"] != r["T"] for o in so[k].values())]
    both = sum(1 for k, vs in sn.items() for v in vs if k in so)
    print(f"match vs lb: solved match runs of instances also solved with lb {both}, "
          f"makespan differs from the lb run: {len(cross)} {cross[:5]}")
    for name, rows in (("match", new), ("lb", old)):
        sol = [r for r in rows if r["status"] == "solved"]
        print(f"{name}: solved {len(sol)}, valid {sum(r['valid'] == '1' for r in sol)}, "
              f"not valid {sum(r['valid'] != '1' for r in sol)}")

    print("\n### B.5 small maps, bscut vs floww (as 1.1), match\n")
    part11(new, "week6_time_bscut_floww" + suffix)

    print("\n### B.6 large maps, bscut vs bspen, total_ms on instances solved by both, match\n")
    if not large:
        print("no large map here")
        return
    print("| map | both solved | bscut faster | equal | bspen faster | median bspen / bscut | median ms bscut | "
          "median ms bspen |")
    print("|---|---|---|---|---|---|---|---|")
    pairs = [(k[0], float(vs["bscut"]["total_ms"]), float(vs["bspen"]["total_ms"])) for k, vs in sn.items()
             if k[0] in LARGE and "bscut" in vs and "bspen" in vs]
    for m in large + ["**all large**"]:
        ps = [p for p in pairs if m == "**all large**" or p[0] == m]
        if not ps:
            print(f"| {m} | 0 | | | | | | |")
            continue
        faster = sum(c < p for _, c, p in ps)
        eq = sum(c == p for _, c, p in ps)
        print(f"| {m} | {len(ps)} | {faster} | {eq} | {len(ps) - faster - eq} | "
              f"{statistics.median(p / max(c, 1) for _, c, p in ps):.2f} | {statistics.median(c for _, c, p in ps):.0f} | "
              f"{statistics.median(p for _, c, p in ps):.0f} |")


def main():
    if "--stage-b" in sys.argv:
        args = sys.argv[sys.argv.index("--stage-b") + 1:]
        suffix = "_match"
        if "--suffix" in args:
            i = args.index("--suffix")
            suffix = args[i + 1]
            del args[i:i + 2]
        stage_b(args[0] if args else "cbm_bench_cactus_match.csv", suffix)
        return
    rows = load("cbm_bench_cactus.csv")
    part11(rows)
    part12(rows)
    part13(rows, load("small_maps_cut.csv"))


if __name__ == "__main__":
    main()
