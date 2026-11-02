#!/usr/bin/env python3
"""Time of one low-level call: the first team in the root (cbm --first-replan), mode k4, scen 1.

Usage: replan_scaling.py OUT.csv [--time-limit 600] [--mem-limit 8000] [--reps 3]
N = 64 on 32x32 maps, 128 otherwise. Each call is repeated --reps times (sequentially) and the median is taken;
a call ending in timeout or memory is not repeated (the repetition would end the same way).
"""
import csv
import os
import statistics
import subprocess
import sys

from cbm_bench import map_and_scen

HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = [("empty-32-32", 64), ("random-32-32-10", 64), ("room-32-32-4", 64), ("maze-32-32-2", 64),
        ("random-64-64-10", 128), ("room-64-64-8", 128), ("warehouse-10-20-10-2-1", 128), ("empty-128-128", 128),
        ("Berlin_1_256", 128), ("empty-256-256", 128)]
FIELDS = ["map", "N", "K", "variant", "status", "T", "ms_median", "ms_runs", "net_nodes", "net_edges", "peak_mb"]


def field(out, name):
    rest = (" " + out).split(" " + name + "=")[1].split() if " " + name + "=" in " " + out else []
    return rest[0] if rest else ""


def main():
    args = sys.argv[1:]
    out_csv = args[0]
    opt = {"--time-limit": "600", "--mem-limit": "8000", "--reps": "3"}
    for i in range(1, len(args), 2):
        opt[args[i]] = args[i + 1]
    exe = os.path.join(HERE, "cbm.exe")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for name, n in MAPS:
            mp, scen = map_and_scen(name, 1)
            for variant in ("bs", "flow", "floww"):
                runs = []
                for _ in range(int(opt["--reps"])):
                    cmd = [exe, mp, scen, str(n), "4", "-", "--low", variant, "--first-replan",
                           "--time-limit", opt["--time-limit"], "--mem-limit", opt["--mem-limit"]]
                    try:
                        out = subprocess.run(cmd, capture_output=True, text=True,
                                             timeout=float(opt["--time-limit"]) + 120).stdout
                    except subprocess.TimeoutExpired:
                        out = "status=killed T=-1"
                    runs.append(out)
                    if field(out, "status") != "solved":
                        break
                ms = [float(field(o, "ms")) for o in runs if field(o, "ms")]
                last = runs[-1]
                row = {"map": name, "N": n, "K": 4, "variant": variant, "status": field(last, "status"),
                       "T": field(last, "T"), "ms_median": f"{statistics.median(ms):.1f}" if ms else "",
                       "ms_runs": " ".join(f"{x:.1f}" for x in ms), "net_nodes": field(last, "net_nodes"),
                       "net_edges": field(last, "net_edges"),
                       "peak_mb": f"{statistics.median(float(field(o, 'peak_mb')) for o in runs if field(o, 'peak_mb')):.1f}"
                       if any(field(o, "peak_mb") for o in runs) else ""}
                w.writerow(row)
                f.flush()
                print(row, flush=True)


if __name__ == "__main__":
    main()
