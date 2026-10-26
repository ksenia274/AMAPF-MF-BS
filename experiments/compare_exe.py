#!/usr/bin/env python3
"""Regression: run two solvers on the step-1 test set and compare T, expansions and routes.

Usage (from the repo root): python experiments/compare_exe.py EXE_A EXE_B [--quick]
Both are called as "EXE MAP SCEN K ROUTES". The set: t/line*, 11 instances on maps up to 256x256,
and all 25 scens x K = 1, 2, 4, ..., max on 6 small maps (--quick: only the first two parts).
Instances that take more than 120 s in EXE_A are reported as skipped.
"""
import os
import subprocess
import sys
import tempfile

MAPS, SCENS = "data/mapf-map", "data/mapf-scen-random/scen-random"
LARGE = [("empty-8-8", 8), ("empty-8-8", 32), ("random-32-32-10", 64), ("random-32-32-10", 461),
         ("room-64-64-8", 256), ("room-64-64-8", 1000), ("maze-128-128-2", 256), ("maze-128-128-2", 1000),
         ("den520d", 1000), ("Berlin_1_256", 256), ("Berlin_1_256", 1000)]
SWEEP = ["empty-8-8", "empty-16-16", "random-32-32-20", "maze-32-32-2", "room-32-32-4", "one_corridor_25x25"]


def instances(quick):
    for name, k in [("line1", 1), ("line2", 2), ("line0", 1)]:
        yield "experiments/t/line.map", f"experiments/t/{name}.scen", k
    for m, k in LARGE:
        yield f"{MAPS}/{m}.map", f"{SCENS}/{m}-random-1.scen", k
    if quick:
        return
    for m in SWEEP:
        for s in range(1, 26):
            scen = f"{SCENS}/{m}-random-{s}.scen"
            if not os.path.exists(scen):
                continue
            with open(scen) as f:
                n = sum(1 for line in f) - 1
            k = 1
            while True:
                yield f"{MAPS}/{m}.map", scen, k
                if k >= n:
                    break
                k = min(2 * k, n)


def run(exe, args, routes):
    try:
        out = subprocess.run([exe] + args + [routes], capture_output=True, text=True, timeout=120).stdout.split()
    except subprocess.TimeoutExpired:
        return None, None
    with open(routes) as f:
        return (out[0], out[1]), f.read()  # "T=..", "expansions=.."


def main():
    exe_a, exe_b = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    work = tempfile.mkdtemp(prefix="compare_exe_")
    total = bad = skipped = 0
    for mp, sc, k in instances("--quick" in sys.argv):
        args = [mp, sc, str(k)]
        res_a, routes_a = run(exe_a, args, os.path.join(work, "a.routes"))
        if res_a is None:
            skipped += 1
            print(f"SKIPPED (timeout) {sc} K={k}")
            continue
        res_b, routes_b = run(exe_b, args, os.path.join(work, "b.routes"))
        total += 1
        if res_a != res_b or routes_a != routes_b:
            bad += 1
            print(f"MISMATCH {sc} K={k}: {res_a} vs {res_b}, routes {'same' if routes_a == routes_b else 'differ'}")
    print(f"compared={total} mismatches={bad} skipped={skipped}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
