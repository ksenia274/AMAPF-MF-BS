#!/usr/bin/env python3
"""Regression: two cbm.exe on the 16 instances of small_maps_diag.csv; every output field except the timings must agree.

Usage: compare_cbm_exe.py OLD_CBM_EXE NEW_CBM_EXE [--low bspen] [--max-nodes 3000]
"""
import argparse
import csv
import os
import subprocess
import tempfile

from cbm_bench import map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
TIMINGS = {"lowlevel_ms", "highlevel_ms", "total_ms", "replan_ms_median", "replan_ms_p90", "replan_ms_max", "pen_share",
           "peak_mb"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--low", default="bspen")
    ap.add_argument("--max-nodes", default="3000")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    rows = list(csv.DictReader(open(os.path.join(HERE, "small_maps_diag.csv"))))
    differ = 0
    for r in rows:
        mp, src = map_and_scen(r["map"], int(r["scen"]))
        if r["mode"] == "k4":
            scen, k = src, 4
        else:
            scen = os.path.join(tmp, "g.scen")
            k = grouped_scen(src, int(r["N"]), scen)
        outs = []
        for exe in (a.old, a.new):
            o = subprocess.run([os.path.abspath(exe), mp, scen, r["N"], str(k), "-", "--low", a.low, "--diag",
                                "--max-nodes", a.max_nodes, "--time-limit", "600"], capture_output=True, text=True).stdout
            outs.append({x: y for x, y in (t.split("=", 1) for t in o.split() if "=" in t) if x not in TIMINGS})
        differ += outs[0] != outs[1]
        print(r["map"], r["N"], r["mode"], r["scen"], "same" if outs[0] == outs[1] else f"DIFF {outs}",
              outs[1].get("status"), outs[1].get("nodes_generated"), flush=True)
    print(f"{a.low}: compared={len(rows)} differ={differ}")


if __name__ == "__main__":
    main()
