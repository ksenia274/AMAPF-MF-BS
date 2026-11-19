#!/usr/bin/env python3
"""Stage B on the two large maps done so far (warehouse-10-20-10-2-1, Berlin_1_256): cbm_bench_cactus_match_big2.csv
(--t-start match) against cbm_bench_cactus.csv (lb). No runs.

Usage: archive/week6_stage_b_big2.py (from experiments/)   (prints markdown; writes figures/cactus_<map>_big2.png/.pdf)
"""
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # experiments/ (this script is in archive/)
from week6_part1 import HERE, VARIANTS, load, solved_by  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "figures"))
import make_cactus  # noqa: E402

MAPS = ["warehouse-10-20-10-2-1", "Berlin_1_256"]


def four(rows, m, v):
    rs = [r for r in rows if r["map"] == m and r["variant"] == v]
    to = [r for r in rs if r["status"] == "timeout"]
    root = sum(r["root_conflict_pairs"] == "-1" for r in to)
    solved = sum(r["status"] == "solved" for r in rs)
    skipped = sum(r["status"] == "timeout_skipped" for r in rs)
    return solved, root, len(to) - root, skipped, len(rs) - solved - len(to) - skipped


def main():
    new = [r for r in load("cbm_bench_cactus_match_big2.csv") if r["map"] in MAPS]
    old = [r for r in load("cbm_bench_cactus.csv") if r["map"] in MAPS]
    assert {r["map"] for r in new} == set(MAPS), {r["map"] for r in new}
    so, sn = solved_by(old), solved_by(new)
    print(f"maps: {', '.join(MAPS)}; rows lb {len(old)}, match {len(new)}\n")

    print("### 1. solved: lb / match\n")
    print("| map | " + " | ".join(VARIANTS) + " |")
    print("|---|" + "---|" * len(VARIANTS))
    for m in MAPS + ["**both maps**"]:
        ms = MAPS if m == "**both maps**" else [m]
        print(f"| {m} | " + " | ".join(
            f"{sum(v in vs for k, vs in so.items() if k[0] in ms)} / {sum(v in vs for k, vs in sn.items() if k[0] in ms)}"
            for v in VARIANTS) + " |")

    print("\n### 2. solved / timeout in the root (root_conflict_pairs = -1) / timeout in the CT / not run "
          "(timeout_skipped)\n")
    print("| map | variant | lb | match | other statuses lb, match |")
    print("|---|---|---|---|---|")
    for m in MAPS:
        for v in VARIANTS:
            a, b = four(old, m, v), four(new, m, v)
            print(f"| {m} | {v} | {' / '.join(map(str, a[:4]))} | {' / '.join(map(str, b[:4]))} | {a[4]}, {b[4]} |")

    print("\n### lost (solved with lb, not with match) and gained\n")
    by_old = {(r["map"], r["N"], r["scen"], r["variant"]): r for r in old}
    by_new = {(r["map"], r["N"], r["scen"], r["variant"]): r for r in new}
    for v in VARIANTS:
        lost = sorted(k for k, r in by_old.items() if k[3] == v and r["status"] == "solved"
                      and by_new.get(k, {}).get("status") != "solved")
        gained = sorted(k for k, r in by_new.items() if k[3] == v and r["status"] == "solved"
                        and by_old.get(k, {}).get("status") != "solved")
        print(f"{v}: lost {len(lost)} {[f'{k[0]} N{k[1]} s{k[2]} ({by_new.get(k, {}).get("status", "-")})' for k in lost]}, "
              f"gained {len(gained)}")

    print("\n### 3. checks\n")
    bad = [k for k, vs in sn.items() if len({r["T"] for r in vs.values()}) > 1]
    print(f"match: instances solved by several variants {sum(len(vs) > 1 for vs in sn.values())}, "
          f"makespan differs: {len(bad)} {bad[:5]}")
    both = sum(1 for k, vs in sn.items() for v in vs if k in so)
    cross = [(k, v) for k, vs in sn.items() for v, r in vs.items()
             if k in so and any(o["T"] != r["T"] for o in so[k].values())]
    print(f"match vs lb: solved match runs of instances also solved with lb {both}, makespan differs: {len(cross)} "
          f"{cross[:5]}")
    for name, rows in (("match", new), ("lb", old)):
        sol = [r for r in rows if r["status"] == "solved"]
        print(f"{name}: solved {len(sol)}, valid {sum(r['valid'] == '1' for r in sol)}, "
              f"not valid {sum(r['valid'] != '1' for r in sol)}")

    print("\n### 4. bscut vs bspen, total_ms on instances solved by both, match\n")
    print("| map | both solved | bscut faster | equal | bspen faster | median bspen / bscut | min | max | "
          "median ms bscut | median ms bspen |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    pairs = [(k[0], float(vs["bscut"]["total_ms"]), float(vs["bspen"]["total_ms"])) for k, vs in sn.items()
             if "bscut" in vs and "bspen" in vs]
    for m in MAPS + ["**both maps**"]:
        ps = [p for p in pairs if m == "**both maps**" or p[0] == m]
        rat = [p / max(c, 1) for _, c, p in ps]
        faster = sum(c < p for _, c, p in ps)
        eq = sum(c == p for _, c, p in ps)
        print(f"| {m} | {len(ps)} | {faster} | {eq} | {len(ps) - faster - eq} | {statistics.median(rat):.2f} | "
              f"{min(rat):.2f} | {max(rat):.2f} | {statistics.median(c for _, c, p in ps):.0f} | "
              f"{statistics.median(p for _, c, p in ps):.0f} |")

    for m in MAPS:
        rs = [r for r in new if r["map"] == m]
        make_cactus.single(rs, m, os.path.join(HERE, "figures"), f"cactus_{m}_big2")
    print("\ncactus: top of the y axis = instances per map:", {m: make_cactus.instances([r for r in new if r["map"] == m])
                                                             for m in MAPS})


if __name__ == "__main__":
    main()
