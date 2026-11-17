#!/usr/bin/env python3
"""5.2a stage 1: where the extra entry penalties of the bspen root come from (the 16 instances of small_maps_diag.csv).

Usage: small_maps_entries.py OUT.csv
Per instance: bspen and floww --diag --max-nodes 1 (the root only, T from the lower bound); root_late of cbm
(lateEntries in cbm.cpp; penalty units, i.e. other robots in the cell). Checks that the parts add up and that the
totals equal root_pen_enter / root_pen_wait.
"""
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # experiments/ (this script is in archive/)
sys.path.insert(0, HERE)

from cbm_bench import map_and_scen  # noqa: E402
from cbm_paper_exp1 import grouped_scen  # noqa: E402
from small_maps_diag import fields, run  # noqa: E402

LATE = ["enter_pen", "enter_structural", "enter_pass_through", "enter_no_free", "enter_u_blocked",
        "wait_pen", "wait_avoidable", "wait_no_free", "wait_u_blocked", "wait_start"]
KEYS = LATE + ["root_pen_enter", "root_pen_wait", "root_conflict_pairs"]
LOWS = ["bspen", "floww"]
FIELDS = ["map", "N", "mode", "K", "scen", "group"] + [f"{low}_{k}" for low in LOWS for k in KEYS]


def main():
    out_csv = sys.argv[1]
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
            row = {x: inst[x] for x in ("map", "N", "mode", "K", "scen", "group")}
            for low in LOWS:
                d = fields(run([exe, mp, scen, n, str(k), "-", "--mem-limit", "8000", "--diag", "--low", low,
                                "--max-nodes", "1", "--time-limit", "600"], 900))
                d.update(zip(LATE, map(int, d["root_late"].split(","))))
                row.update({f"{low}_{x}": d[x] for x in KEYS})
                if (d["enter_pen"] != int(d["root_pen_enter"]) or d["wait_pen"] != int(d["root_pen_wait"]) or
                        d["enter_pen"] != sum(d[x] for x in LATE[1:5]) or d["wait_pen"] != sum(d[x] for x in LATE[6:])):
                    sys.exit(f"check failed: {low} {row}")
            w.writerow(row)
            f.flush()
            print({x: row[x] for x in FIELDS if x not in ("K", "group")}, flush=True)


if __name__ == "__main__":
    main()
