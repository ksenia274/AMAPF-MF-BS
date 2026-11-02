#!/usr/bin/env python3
"""Time of one low-level call in the root (cbm --root-only), scen 1, mode k4 unless said otherwise.

Usage: replan_scaling.py OUT.csv [--time-limit 600] [--mem-limit 8000] [--reps 3]
N = 64 on 32x32 maps, 128 otherwise. Cases: the first team of the root with --t-start 1 and lb, the last team of
the root with --t-start lb (floww and bspen have the weights of the teams planned before it); bs, flow, floww.
Plus the whole root of mode g5 (teams of 5) on Berlin_1_256 and empty-256-256, N = 128, bs.
Each case is repeated --reps times (sequentially), the median is taken; a case is not repeated if it ended in
timeout or memory or took more than 60 s (repetitions of such calls differed by < 1% in stage 3b).
"""
import csv
import os
import statistics
import subprocess
import sys
import tempfile

from cbm_bench import map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = [("empty-32-32", 64), ("random-32-32-10", 64), ("room-32-32-4", 64), ("maze-32-32-2", 64),
        ("random-64-64-10", 128), ("room-64-64-8", 128), ("warehouse-10-20-10-2-1", 128), ("empty-128-128", 128),
        ("Berlin_1_256", 128), ("empty-256-256", 128)]
CASES = [("first", "1"), ("first", "lb"), ("last", "lb")]
FIELDS = ["map", "N", "mode", "K", "variant", "t_start", "team", "status", "minT", "T", "tried_T", "ms_median", "ms_runs",
          "final_t_ms_median", "net_nodes", "net_edges", "peak_mb", "root_ms_median", "teams_planned", "team_T_median",
          "team_T_max"]


def field(out, name):
    rest = (" " + out).split(" " + name + "=")[1].split() if " " + name + "=" in " " + out else []
    return rest[0] if rest else ""


def measure(cmd, opt):
    runs = []
    for _ in range(int(opt["--reps"])):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=float(opt["--time-limit"]) * 6 + 120).stdout
        except subprocess.TimeoutExpired:
            out = "status=killed T=-1"
        runs.append(out)
        if field(out, "status") != "solved" or float(field(out, "ms") or 0) > 60000:
            break
    med = lambda name: statistics.median(float(field(o, name)) for o in runs) if all(field(o, name) for o in runs) else ""
    last = runs[-1]
    row = {name: field(last, name) for name in ("status", "minT", "T", "tried_T", "net_nodes", "net_edges",
                                                "teams_planned", "team_T_median", "team_T_max")}
    row["team"] = field(last, "team")
    row["ms_runs"] = " ".join(field(o, "ms") for o in runs)
    for name, key in (("ms", "ms_median"), ("final_t_ms", "final_t_ms_median"), ("peak_mb", "peak_mb"), ("root_ms", "root_ms_median")):
        v = med(name)
        row[key] = f"{v:.1f}" if v != "" else ""
    return row


def main():
    args = sys.argv[1:]
    out_csv = args[0]
    opt = {"--time-limit": "600", "--mem-limit": "8000", "--reps": "3"}
    for i in range(1, len(args), 2):
        opt[args[i]] = args[i + 1]
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    limits = ["--time-limit", opt["--time-limit"], "--mem-limit", opt["--mem-limit"]]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()

        def emit(row):
            w.writerow(row)
            f.flush()
            print(row, flush=True)

        for which, t_start in CASES:
            for name, n in MAPS:
                mp, scen = map_and_scen(name, 1)
                for variant in ("bs", "flow", "floww"):
                    cmd = [exe, mp, scen, str(n), "4", "-", "--low", variant, "--root-only", which, "--t-start", t_start] + limits
                    emit({"map": name, "N": n, "mode": "k4", "K": 4, "variant": variant, "t_start": t_start, **measure(cmd, opt)})
        for name in ("Berlin_1_256", "empty-256-256"):
            mp, src = map_and_scen(name, 1)
            scen = os.path.join(tmp, "g.scen")
            k = grouped_scen(src, 128, scen)
            for t_start in ("1", "lb"):
                cmd = [exe, mp, scen, "128", str(k), "-", "--low", "bs", "--root-only", "last", "--t-start", t_start] + limits
                emit({"map": name, "N": 128, "mode": "g5", "K": k, "variant": "bs", "t_start": t_start, **measure(cmd, opt)})


if __name__ == "__main__":
    main()
