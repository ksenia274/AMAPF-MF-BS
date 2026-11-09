#!/usr/bin/env python3
"""5.2a stage 3: bspen, bscut penal, bscut all, floww on the 16 instances of small_maps_diag.csv.

Usage: small_maps_cut.py OUT.csv [--time-limit 60]
Per instance and variant, sequentially, T from the lower bound:
  cbm --diag, --time-limit: status, nodes, replannings, time, root conflict pairs, root penalty by parts
    (root_pen_wait/enter/swap), median time of a replanning, low-level expansions;
  bspen and bscut also cbm --pen-gap S, --time-limit (S as in small_maps_diag.csv; the floww time is not counted):
    share of the checked replannings above the floww minimum and the mean excess (floww: 0 by definition).
"""
import argparse
import csv
import os
import tempfile

from cbm_bench import map_and_scen
from cbm_paper_exp1 import grouped_scen
from small_maps_diag import fields, run

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS = {"bspen": ["--low", "bspen"], "bscut": ["--low", "bscut", "--cut", "penal"],
            "bscut_all": ["--low", "bscut", "--cut", "all"], "floww": ["--low", "floww"]}
RUN = ["status", "T", "nodes_generated", "nodes_expanded", "lowlevel_calls", "total_ms", "root_conflict_pairs",
       "root_pen_wait", "root_pen_enter", "root_pen_swap", "replan_ms_median", "lowlevel_expansions"]
PEN = ["pen_checks", "pen_gap_share", "pen_gap_mean", "pen_gap_max"]
FIELDS = ["map", "N", "mode", "K", "scen", "group", "variant"] + RUN + ["stride", "pen_status"] + PEN


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_csv")
    ap.add_argument("--time-limit", default="60")
    a = ap.parse_args()
    insts = list(csv.DictReader(open(os.path.join(HERE, "small_maps_diag.csv"))))
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    with open(a.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for inst in insts:
            name, n, mode, s = inst["map"], inst["N"], inst["mode"], inst["scen"]
            mp, src = map_and_scen(name, int(s))
            if mode == "k4":
                scen, k = src, 4
            else:
                scen = os.path.join(tmp, "g.scen")
                k = grouped_scen(src, int(n), scen)
            base = [exe, mp, scen, n, str(k), "-", "--mem-limit", "8000", "--time-limit", a.time_limit]
            for variant, args in VARIANTS.items():
                row = {x: inst[x] for x in ("map", "N", "mode", "K", "scen", "group")}
                row["variant"] = variant
                d = fields(run(base + args + ["--diag"], float(a.time_limit) + 300))
                row.update({x: d.get(x, "") for x in RUN})
                if variant != "floww":
                    row["stride"] = inst["stride"]
                    p = fields(run(base + args + ["--pen-gap", inst["stride"]], 6 * 3600))
                    row["pen_status"] = p.get("status", "")
                    row.update({x: p.get(x, "") for x in PEN})
                w.writerow(row)
                f.flush()
                print({x: row.get(x, "") for x in ("map", "N", "mode", "scen", "variant", "status", "total_ms",
                                                   "nodes_expanded", "lowlevel_calls", "root_conflict_pairs",
                                                   "pen_gap_share", "pen_gap_mean")}, flush=True)


if __name__ == "__main__":
    main()
