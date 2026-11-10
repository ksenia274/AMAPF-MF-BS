#!/usr/bin/env python3
"""5.2a stage 4, part 1: cost of one low-level call in the root (cbm --root-only) for bs, bspen, bscut (--cut penal).

Usage: replan_cut.py OUT.csv [--resume] [--reps 3] [--time-limit 600] [--mem-limit 8000]
Berlin_1_256, warehouse-10-20-10-2-1, room-64-64-8; N = 128, teams of 5 (as cbm_bench_cactus), scen 1, --t-start lb.
The first team of the root (no other teams: no penalties, no soft cuts) and the last one (the other K-1 teams give
the penalties). Per case the median of --reps runs: time of the call, expansions, hard / soft cuts of its final
network (the cuts and expansions do not depend on the run).
"""
import argparse
import csv
import os
import statistics
import subprocess
import tempfile

from cbm_bench import field, map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = ["room-64-64-8", "warehouse-10-20-10-2-1", "Berlin_1_256"]
VARIANTS = {"bs": ["--low", "bs"], "bspen": ["--low", "bspen"], "bscut": ["--low", "bscut", "--cut", "penal"]}
OUT = ["status", "team", "minT", "T", "tried_T", "expansions", "hard_cuts", "soft_cuts", "final_t_ms", "root_ms"]
FIELDS = ["map", "N", "K", "scen", "which", "variant"] + OUT + ["ms_median", "ms_runs", "cells"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_csv")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--time-limit", default="600")
    ap.add_argument("--mem-limit", default="8000")
    a = ap.parse_args()
    kept = []
    if a.resume and os.path.exists(a.out_csv):
        kept = [r for r in csv.DictReader(open(a.out_csv)) if r["status"]]
    done = {(r["map"], r["which"], r["variant"]) for r in kept}
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    with open(a.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(kept)
        f.flush()
        for name in MAPS:
            mp, src = map_and_scen(name, 1)
            scen = os.path.join(tmp, "g.scen")
            k = grouped_scen(src, 128, scen)
            cells = sum(row.count(".") for row in open(mp).read().split("\n")[4:])
            for which in ("first", "last"):
                for variant, args in VARIANTS.items():
                    if (name, which, variant) in done:
                        continue
                    cmd = [exe, mp, scen, "128", str(k), "-", "--root-only", which, "--t-start", "lb",
                           "--time-limit", a.time_limit, "--mem-limit", a.mem_limit] + args
                    runs = []
                    for _ in range(a.reps):
                        try:
                            out = subprocess.run(cmd, capture_output=True, text=True,
                                                 timeout=float(a.time_limit) * 30 + 120).stdout
                        except subprocess.TimeoutExpired:
                            out = "status=killed"
                        runs.append(out)
                        if field(out, "status") != "solved":
                            break
                    row = {"map": name, "N": 128, "K": k, "scen": 1, "which": which, "variant": variant, "cells": cells}
                    row.update({x: field(runs[-1], x) for x in OUT})
                    ms = [float(field(o, "ms")) for o in runs if field(o, "ms")]
                    row["ms_runs"] = " ".join(f"{x:.1f}" for x in ms)
                    row["ms_median"] = f"{statistics.median(ms):.1f}" if ms else ""
                    w.writerow(row)
                    f.flush()
                    print(row, flush=True)


if __name__ == "__main__":
    main()
