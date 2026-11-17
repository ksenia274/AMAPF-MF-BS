#!/usr/bin/env python3
"""Why bspen solves fewer instances of stage 3a than floww: diagnostics of single instances (not timing).

Usage: small_maps_diag.py OUT.csv [--checks 200]
Instances: those of cbm_bench_5_1.csv (maps of 3a) solved by floww and not by bspen, plus 10 solved by both
(same maps and modes). Per instance, sequentially:
  bspen --diag, 600 s: status, time, root key, expanded nodes per key, depth, replannings, repeated constraint sets;
  bspen --pen-gap S, 60 s (floww time excluded): penalty of the bspen routes minus the floww minimum on the same T,
    S = ceil(replannings of bspen in 5.1 / --checks), every replanning of the root is checked;
  floww --diag --max-nodes 1: the root only (conflicting pairs, free neighbours of the cells of the first 20
    conflicts; the bspen root comes from the first run).
"""
import csv
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # experiments/ (this script is in archive/)
sys.path.insert(0, HERE)

from cbm_bench import map_and_scen  # noqa: E402
from cbm_paper_exp1 import grouped_scen  # noqa: E402

MAPS_3A = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8"]
BOTH = [("room-32-32-4", "40", "g5", "1"), ("room-32-32-4", "40", "g5", "2"), ("maze-32-32-2", "64", "k4", "1"),
        ("maze-32-32-2", "64", "k4", "3"), ("maze-32-32-2", "64", "g5", "1"), ("maze-32-32-2", "40", "g5", "1"),
        ("maze-32-32-2", "40", "g5", "2"), ("room-64-64-8", "64", "g5", "1"), ("room-64-64-8", "64", "g5", "3"),
        ("room-64-64-8", "128", "g5", "2")]
FIELDS = ["map", "N", "mode", "K", "scen", "group", "floww_T", "bspen_5_1_calls",
          "status", "total_ms", "T", "root_key", "last_key", "expanded", "expanded_by_key", "max_depth", "lowlevel_calls",
          "repeated_constraint_sets", "stride", "pen_status", "pen_checks", "pen_gap_mean", "pen_gap_max", "pen_gap_min",
          "pen_gap_share", "pen_own_mean", "pen_min_mean", "root_pen_checks", "root_pen_gap_mean", "root_pen_gap_max",
          "root_pen_gap_share", "root_pen_own_mean", "root_pen_min_mean", "pen_check_failed",
          "bspen_root_pairs", "floww_root_pairs", "bspen_root_degrees", "floww_root_degrees"]


def fields(out):
    d = {}
    for tok in out.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            d[k] = v
    return d


def run(cmd, timeout):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return "status=killed"


def main():
    out_csv = sys.argv[1]
    checks = int(sys.argv[sys.argv.index("--checks") + 1]) if "--checks" in sys.argv else 200
    rows = {(r["map"], r["N"], r["mode"], r["scen"], r["variant"]): r
            for r in csv.DictReader(open(os.path.join(HERE, "cbm_bench_5_1.csv"))) if r["map"] in MAPS_3A}
    failed = [k[:4] for k, r in rows.items() if k[4] == "floww" and r["status"] == "solved"
              and rows[k[:4] + ("bspen",)]["status"] != "solved"]
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    log = open(out_csv[:-4] + ".log", "w")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for group, insts in (("floww_only", failed), ("both", BOTH)):
            for name, n, mode, s in insts:
                mp, src = map_and_scen(name, int(s))
                if mode == "k4":
                    scen, k = src, 4
                else:
                    scen = os.path.join(tmp, "g.scen")
                    k = grouped_scen(src, int(n), scen)
                base = [exe, mp, scen, n, str(k), "-", "--mem-limit", "8000"]
                calls = int(rows[(name, n, mode, s, "bspen")]["lowlevel_calls"])
                stride = max(1, math.ceil(calls / checks))
                row = {"map": name, "N": n, "mode": mode, "K": k, "scen": s, "group": group, "stride": stride,
                       "floww_T": rows[(name, n, mode, s, "floww")]["T"], "bspen_5_1_calls": calls}
                o = run(base + ["--low", "bspen", "--diag", "--time-limit", "600"], 900)
                d = fields(o)
                row.update({key: d.get(key, "") for key in ("status", "total_ms", "T", "root_key", "last_key",
                                                              "expanded_by_key", "max_depth", "lowlevel_calls",
                                                              "repeated_constraint_sets")})
                row["expanded"] = d.get("nodes_expanded", "")
                row["bspen_root_pairs"] = d.get("root_conflict_pairs", "")
                row["bspen_root_degrees"] = d.get("root_conflict_degrees", "")
                p = run(base + ["--low", "bspen", "--pen-gap", str(stride), "--time-limit", "60"], 6 * 3600)
                dp = fields(p)
                row["pen_status"] = dp.get("status", "")
                for key in FIELDS[FIELDS.index("pen_checks"):FIELDS.index("bspen_root_pairs")]:
                    row[key] = dp.get(key, "")
                r = run(base + ["--low", "floww", "--diag", "--max-nodes", "1", "--time-limit", "600"], 900)
                dr = fields(r)
                row["floww_root_pairs"] = dr.get("root_conflict_pairs", "")
                row["floww_root_degrees"] = dr.get("root_conflict_degrees", "")
                for text in (o, p, r):
                    log.write(f"{name} {n} {mode} {s}: {text.strip()}\n")
                log.flush()
                w.writerow(row)
                f.flush()
                print({key: row[key] for key in ("map", "N", "mode", "scen", "status", "T", "floww_T", "root_key",
                                                  "last_key", "pen_checks", "pen_gap_mean", "root_pen_gap_mean")},
                      flush=True)


if __name__ == "__main__":
    main()
