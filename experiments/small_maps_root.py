#!/usr/bin/env python3
"""The 16 instances of small_maps_diag.csv: penalty of the root routes by parts, and bspen with a floww root.

Usage: small_maps_root.py OUT.csv [--time-limit 60]
Per instance, sequentially (T from the lower bound):
  bspen and floww --diag --max-nodes 1: the root only; root_pen_wait/enter/swap of cbm (penalty with the weights of
    floww of every team against the teams planned before it, summed over the teams);
  bspen --diag and bspen --root-low floww --diag, --time-limit: status, nodes, replannings.
"""
import csv
import os
import subprocess
import sys
import tempfile

from cbm_bench import map_and_scen
from cbm_paper_exp1 import grouped_scen
from small_maps_diag import fields, run

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ["root_pen_wait", "root_pen_enter", "root_pen_swap"]
RUN = ["status", "T", "total_ms", "nodes_generated", "nodes_expanded", "lowlevel_calls", "root_conflict_pairs",
       "root_key", "max_depth"]
FIELDS = (["map", "N", "mode", "K", "scen", "group", "floww_T"] + [f"bspen_{p}" for p in PARTS] +
          [f"floww_{p}" for p in PARTS] + ["bspen_root_pairs", "floww_root_pairs"] + [f"base_{x}" for x in RUN] +
          [f"rootfloww_{x}" for x in RUN])


def main():
    out_csv = sys.argv[1]
    limit = sys.argv[sys.argv.index("--time-limit") + 1] if "--time-limit" in sys.argv else "60"
    insts = list(csv.DictReader(open(os.path.join(HERE, "small_maps_diag.csv"))))
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    with open(out_csv, "w", newline="") as f:
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
            base = [exe, mp, scen, n, str(k), "-", "--mem-limit", "8000", "--diag"]
            row = {x: inst[x] for x in ("map", "N", "mode", "K", "scen", "group", "floww_T")}
            for low in ("bspen", "floww"):
                d = fields(run(base + ["--low", low, "--max-nodes", "1", "--time-limit", "600"], 900))
                row.update({f"{low}_{p}": d.get(p, "") for p in PARTS})
                row[f"{low}_root_pairs"] = d.get("root_conflict_pairs", "")
            for pre, extra in (("base", []), ("rootfloww", ["--root-low", "floww"])):
                d = fields(run(base + ["--low", "bspen", "--time-limit", limit] + extra, float(limit) + 300))
                row.update({f"{pre}_{x}": d.get(x, "") for x in RUN})
            w.writerow(row)
            f.flush()
            print({x: row[x] for x in FIELDS if x not in ("K", "group")}, flush=True)


if __name__ == "__main__":
    main()
