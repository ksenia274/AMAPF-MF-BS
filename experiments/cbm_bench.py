#!/usr/bin/env python3
"""Stage 3: CBM with the low levels bs, flow, floww and the tie-breaks conflicts / late on MovingAI maps.

Usage: cbm_bench.py OUT.csv [--stage 3a|3b] [--scens 1,2,3] [--time-limit 60] [--mem-limit 8000]
       cbm_bench.py --summary OUT.csv          (markdown table; makespan check over the variants)
Instance: random scen s of the map, the first N agents. Modes: k4 - K = 4 teams, agent i in team i % 4;
g5 - K = ceil(N/5) teams of consecutive agents (5 each, the last ones 4 if 5 does not divide N).
Runs are sequential; every solution is checked by validate.py --teams K. A run that does not finish within the time
limit + 120 s is killed (status killed).
"""
import csv
import os
import statistics
import subprocess
import sys
import tempfile
import time

from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
STAGES = {
    "3a": [("empty-32-32", [20, 40, 64]), ("random-32-32-10", [20, 40, 64]), ("room-32-32-4", [20, 40, 64]),
           ("maze-32-32-2", [20, 40, 64]), ("random-64-64-10", [64, 128]), ("room-64-64-8", [64, 128])],
    "3b": [("warehouse-10-20-10-2-1", [64, 128]), ("empty-128-128", [64, 128]), ("Berlin_1_256", [64, 128, 256]),
           ("empty-256-256", [64, 128, 256])],
    "smoke": [("empty-32-32", [20]), ("room-64-64-8", [64])],
}
OWN_MAPS = os.path.join(HERE, "maps")


def map_and_scen(name, s):
    """MovingAI files, or our own maps (make_empty_maps.py) from maps/."""
    if os.path.exists(os.path.join(OWN_MAPS, name + ".map")):
        return os.path.join(OWN_MAPS, name + ".map"), os.path.join(OWN_MAPS, f"{name}-random-{s}.scen")
    return (os.path.join(DATA, "mapf-map", name + ".map"),
            os.path.join(DATA, "mapf-scen-random", "scen-random", f"{name}-random-{s}.scen"))
VARIANTS = {"bs": ["--low", "bs"], "flow": ["--low", "flow"], "floww": ["--low", "floww"],
            "bs-late": ["--low", "bs", "--tiebreak", "late"]}
OUT_FIELDS = ["status", "T", "nodes_generated", "nodes_expanded", "lowlevel_calls", "lowlevel_ms", "total_ms",
              "root_conflict_pairs", "pruned_unreachable", "replan_ms_median", "replan_ms_p90", "replan_ms_max",
              "net_nodes_max", "net_edges_max", "peak_mb", "last_key"]
FIELDS = ["map", "N", "mode", "K", "scen", "variant"] + OUT_FIELDS + ["valid", "exit", "wall_s"]


def field(out, name):
    rest = (" " + out).split(" " + name + "=")[1].split() if " " + name + "=" in " " + out else []
    return rest[0] if rest and "=" not in rest[0] else ""


def run(args):
    out_csv = args[0]
    opt = {"--stage": "3a", "--scens": "1,2,3", "--time-limit": "60", "--mem-limit": "8000"}
    for i in range(1, len(args), 2):
        opt[args[i]] = args[i + 1]
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    limit = float(opt["--time-limit"])
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for name, ns in STAGES[opt["--stage"]]:
            for n in ns:
                for mode in ("k4", "g5"):
                    for s in map(int, opt["--scens"].split(",")):
                        mp, src = map_and_scen(name, s)
                        if mode == "k4":
                            scen, k = src, 4
                        else:
                            scen = os.path.join(tmp, "g.scen")
                            k = grouped_scen(src, n, scen)
                        for variant, flags in VARIANTS.items():
                            routes = os.path.join(tmp, "r.routes")
                            if os.path.exists(routes):
                                os.remove(routes)
                            cmd = [exe, mp, scen, str(n), str(k), routes, "--time-limit", opt["--time-limit"],
                                   "--mem-limit", opt["--mem-limit"]] + flags
                            start = time.perf_counter()
                            try:
                                p = subprocess.run(cmd, capture_output=True, text=True, timeout=limit + 120)
                                out, code = p.stdout, p.returncode
                            except subprocess.TimeoutExpired:
                                out, code = "status=killed T=-1", "killed"
                            wall = time.perf_counter() - start
                            row = {"map": name, "N": n, "mode": mode, "K": k, "scen": s, "variant": variant,
                                   "exit": code, "wall_s": f"{wall:.1f}", "valid": ""}
                            for fld in OUT_FIELDS:
                                row[fld] = field(out, fld)
                            if row["status"] == "solved":
                                v = subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), mp, scen, str(n),
                                                    routes, "--teams", str(k)], capture_output=True, text=True)
                                row["valid"] = int(v.returncode == 0)
                            w.writerow(row)
                            f.flush()
                            print(name, n, mode, s, variant, row["status"], row["T"], row["total_ms"],
                                  "valid=" + str(row["valid"]), flush=True)


def summary(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    variants = list(dict.fromkeys(r["variant"] for r in rows))
    med = lambda xs: f"{statistics.median(xs):.1f}" if xs else "-"
    mean = lambda xs: f"{statistics.mean(xs):.0f}" if xs else "-"
    print("| map | N | mode | K | variant | solved | timeout | memory | other | median time, s (solved) | "
          "median replan, ms | p90 replan, ms | max replan, ms | mean CT nodes expanded (solved) | mean replans (solved) | "
          "root conflict pairs (mean) | pruned unreachable (sum) | max peak, MB | max network nodes / edges |")
    print("|" + "---|" * 19)
    groups = list(dict.fromkeys((r["map"], r["N"], r["mode"]) for r in rows))
    for g in groups:
        for v in variants:
            rs = [r for r in rows if (r["map"], r["N"], r["mode"]) == g and r["variant"] == v]
            if not rs:
                continue
            ok = [r for r in rs if r["status"] == "solved"]
            count = lambda st: sum(r["status"] == st for r in rs)
            other = len(rs) - len(ok) - count("timeout") - count("memory")
            nums = lambda rr, k: [float(r[k]) for r in rr if r[k] != ""]
            net = "-" if v.startswith("bs") else f"{max(nums(rs, 'net_nodes_max'), default=0):.0f} / {max(nums(rs, 'net_edges_max'), default=0):.0f}"
            print(f"| {g[0]} | {g[1]} | {g[2]} | {rs[0]['K']} | {v} | {len(ok)}/{len(rs)} | {count('timeout')} | "
                  f"{count('memory')} | {other} | {med([float(r['total_ms']) / 1000 for r in ok])} | "
                  f"{med(nums(rs, 'replan_ms_median'))} | {med(nums(rs, 'replan_ms_p90'))} | "
                  f"{max(nums(rs, 'replan_ms_max'), default=0):.1f} | {mean(nums(ok, 'nodes_expanded'))} | "
                  f"{mean(nums(ok, 'lowlevel_calls'))} | {mean([x for x in nums(rs, 'root_conflict_pairs') if x >= 0])} | "
                  f"{sum(nums(rs, 'pruned_unreachable')):.0f} | {max(nums(rs, 'peak_mb'), default=0):.0f} | {net} |")
    by_instance = {}
    for r in rows:
        if r["status"] == "solved":
            by_instance.setdefault((r["map"], r["N"], r["mode"], r["scen"]), {})[r["variant"]] = r["T"]
    bad = {key: ts for key, ts in by_instance.items() if len(set(ts.values())) > 1}
    invalid = [r for r in rows if r["status"] == "solved" and r["valid"] != "1"]
    print(f"\nmakespan mismatches on instances solved by several variants: {len(bad)} {bad}")
    print(f"invalid solutions: {len(invalid)}")


if __name__ == "__main__":
    if sys.argv[1] == "--summary":
        summary(sys.argv[2])
    else:
        run(sys.argv[1:])
