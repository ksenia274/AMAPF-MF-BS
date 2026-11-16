#!/usr/bin/env python3
"""Regression: two cbm.exe on the 16 instances of small_maps_diag.csv; every output field except the timings must agree.

Usage: compare_cbm_exe.py OLD_CBM_EXE NEW_CBM_EXE [--low bspen] [--max-nodes 3000] [--t-start lb] [--baseline FILE]
--baseline: the outputs of OLD are read from FILE (JSON); if FILE does not exist, OLD is run once and FILE is written
(with NEW = OLD only that run is made).
"""
import argparse
import csv
import json
import os
import subprocess
import tempfile

from cbm_bench import map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
TIMINGS = {"lowlevel_ms", "highlevel_ms", "total_ms", "replan_ms_median", "replan_ms_p90", "replan_ms_max", "pen_share",
           "peak_mb"}


def run(exe, mp, scen, r, k, a):
    o = subprocess.run([os.path.abspath(exe), mp, scen, r["N"], str(k), "-", "--low", a.low, "--diag",
                        "--max-nodes", a.max_nodes, "--time-limit", "600", "--t-start", a.t_start],
                       capture_output=True, text=True).stdout
    return {x: y for x, y in (t.split("=", 1) for t in o.split() if "=" in t) if x not in TIMINGS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--low", default="bspen")
    ap.add_argument("--max-nodes", default="3000")
    ap.add_argument("--t-start", default="lb")
    ap.add_argument("--baseline")
    a = ap.parse_args()
    saved = json.load(open(a.baseline)) if a.baseline and os.path.exists(a.baseline) else None
    tmp = tempfile.mkdtemp()
    rows = list(csv.DictReader(open(os.path.join(HERE, "small_maps_diag.csv"))))
    differ = 0
    olds = []
    for i, r in enumerate(rows):
        mp, src = map_and_scen(r["map"], int(r["scen"]))
        if r["mode"] == "k4":
            scen, k = src, 4
        else:
            scen = os.path.join(tmp, "g.scen")
            k = grouped_scen(src, int(r["N"]), scen)
        old = saved[i] if saved else run(a.old, mp, scen, r, k, a)
        olds.append(old)
        new = old if os.path.abspath(a.new) == os.path.abspath(a.old) else run(a.new, mp, scen, r, k, a)
        differ += old != new
        print(r["map"], r["N"], r["mode"], r["scen"], "same" if old == new else f"DIFF {[old, new]}",
              new.get("status"), new.get("nodes_generated"), flush=True)
    if a.baseline and not saved:
        json.dump(olds, open(a.baseline, "w"))
    print(f"{a.low} t-start={a.t_start}: compared={len(rows)} differ={differ}")


if __name__ == "__main__":
    main()
