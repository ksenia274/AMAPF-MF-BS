#!/usr/bin/env python3
"""CBM on MovingAI maps for cactus plots: teams of 5, random scen 1..10, low levels bs, bspen, bscut, flow, floww.

Usage: cbm_bench_cactus.py OUT.csv [--resume] [--scens 1-10] [--time-limit 60] [--mem-limit 8000]
                           [--maps M1,M2,..] [--variants V1,V2,..] [--t-start lb|1]
       cbm_bench_cactus.py OUT.csv --summary     (markdown table; makespan check over the variants; solved by one
                                                  of floww / bspen and not by bscut and vice versa)
Instance: random scen s of the map, the first N agents, K = ceil(N/5) teams of consecutive agents (as cbm_bench g5).
Stopping rule of the Bulk Search paper: within a scen N grows; once a variant does not solve an instance, the larger
N of that scen are not run for it and are written as timeout_skipped. T starts from the lower bound (the default).
Runs are sequential; every solution is checked by validate.py --teams K; the CSV is flushed after every run.
--resume: keeps the rows of OUT.csv and runs only the missing ones (rows with status error, i.e. cbm printed
nothing, are run again).
bscut = --low bscut --cut penal.
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile
import time

from cbm_bench import field, map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
SMALL = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8"]
LARGE = ["warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]
NS = {"32": [20, 40, 60, 80], "64": [40, 80, 120, 160], "large": [64, 128, 192, 256]}
VARIANTS = ["bs", "bspen", "bscut", "flow", "floww"]
LOW_ARGS = {"bscut": ["--low", "bscut", "--cut", "penal"]}
OUT_FIELDS = ["status", "T", "nodes_generated", "nodes_expanded", "lowlevel_calls", "lowlevel_ms", "total_ms",
              "root_conflict_pairs", "pruned_unreachable", "replan_ms_median", "peak_mb", "last_key"]
FIELDS = ["map", "group", "N", "K", "scen", "variant"] + OUT_FIELDS + ["valid", "exit", "wall_s"]


def ns_of(name):
    if name in LARGE:
        return NS["large"]
    return NS["32"] if "-32-32" in name else NS["64"]


def run(args):
    out_csv = args.out_csv
    opt = {"--" + k.replace("_", "-"): v for k, v in vars(args).items()}
    lo, hi = map(int, opt["--scens"].split("-"))
    kept = []
    if opt.get("--resume") and os.path.exists(out_csv):
        with open(out_csv) as f:
            kept = [r for r in csv.DictReader(f) if r["status"] not in ("", "error")]
    done = {(r["map"], r["N"], r["scen"], r["variant"]): r["status"] for r in kept}
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    limit = float(opt["--time-limit"])
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(kept)
        f.flush()
        for name in opt["--maps"].split(","):
            group = "small" if name in SMALL else "large"
            for s in range(lo, hi + 1):
                failed = set()
                for n in ns_of(name):
                    mp, src = map_and_scen(name, s)
                    scen = os.path.join(tmp, "g.scen")
                    k = grouped_scen(src, n, scen)
                    for variant in opt["--variants"].split(","):
                        key = (name, str(n), str(s), variant)
                        if key in done:
                            if done[key] != "solved":
                                failed.add(variant)
                            continue
                        row = {"map": name, "group": group, "N": n, "K": k, "scen": s, "variant": variant, "valid": ""}
                        if variant in failed:
                            row.update({"status": "timeout_skipped", "T": -1})
                        else:
                            routes = os.path.join(tmp, "r.routes")
                            if os.path.exists(routes):
                                os.remove(routes)
                            cmd = [exe, mp, scen, str(n), str(k), routes] + LOW_ARGS.get(variant, ["--low", variant]) + ["--time-limit",
                                   opt["--time-limit"], "--mem-limit", opt["--mem-limit"], "--t-start", opt["--t-start"]]
                            start = time.perf_counter()
                            try:
                                p = subprocess.run(cmd, capture_output=True, text=True, timeout=limit + 120)
                                out, code = p.stdout, p.returncode
                            except subprocess.TimeoutExpired:
                                out, code = "status=killed T=-1", "killed"
                            row["wall_s"] = f"{time.perf_counter() - start:.1f}"
                            row["exit"] = code
                            for fld in OUT_FIELDS:
                                row[fld] = field(out, fld)
                            if not row["status"]:
                                row["status"] = "error"
                            if row["status"] == "solved":
                                v = subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), mp, scen, str(n),
                                                    routes, "--teams", str(k)], capture_output=True, text=True)
                                row["valid"] = int(v.returncode == 0)
                        if row["status"] != "solved":
                            failed.add(variant)
                        w.writerow(row)
                        f.flush()
                        print(name, n, s, variant, row["status"], row["T"], row.get("total_ms", ""),
                              "valid=" + str(row["valid"]), flush=True)


def summary(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    maps = list(dict.fromkeys(r["map"] for r in rows))
    variants = [v for v in VARIANTS if any(r["variant"] == v for r in rows)]
    print("| map | " + " | ".join(f"solved: {v}" for v in variants) + " | timeout_skipped: " +
          " / ".join(variants) + " | memory / killed |")
    print("|" + "---|" * (len(variants) + 3))
    for group in ("small", "large"):
        for m in [m for m in maps if any(r["map"] == m and r["group"] == group for r in rows)]:
            rs = [r for r in rows if r["map"] == m]
            cells = []
            for v in variants:
                rv = [r for r in rs if r["variant"] == v]
                cells.append(f"{sum(r['status'] == 'solved' for r in rv)}/{len(rv)}")
            skipped = " / ".join(str(sum(r["status"] == "timeout_skipped" for r in rs if r["variant"] == v)) for v in variants)
            other = f"{sum(r['status'] == 'memory' for r in rs)} / {sum(r['status'] == 'killed' for r in rs)}"
            print(f"| {m} | " + " | ".join(cells) + f" | {skipped} | {other} |")
        rs = [r for r in rows if r["group"] == group]
        if rs:
            cells = [f"{sum(r['status'] == 'solved' for r in rs if r['variant'] == v)}/"
                     f"{sum(r['variant'] == v for r in rs)}" for v in variants]
            print(f"| **all {group}** | " + " | ".join(f"**{c}**" for c in cells) + " | | |")
    by_inst = {}
    for r in rows:
        if r["status"] == "solved":
            by_inst.setdefault((r["map"], r["N"], r["scen"]), {})[r["variant"]] = r["T"]
    bad = [(k, ts) for k, ts in by_inst.items() if len(set(ts.values())) > 1]
    common = sum(len(ts) > 1 for ts in by_inst.values())
    invalid = sum(r["status"] == "solved" and r["valid"] != "1" for r in rows)
    if "bscut" in variants:
        print()
        for other in ("floww", "bspen"):
            for group in ("small", "large"):
                ts = [ts for k, ts in by_inst.items() if (k[0] in SMALL) == (group == "small")]
                print(f"{group}: solved by {other} and not by bscut: {sum(other in t and 'bscut' not in t for t in ts)}; "
                      f"by bscut and not by {other}: {sum('bscut' in t and other not in t for t in ts)}")
        print(f"instances solved by bscut and another variant: {sum('bscut' in t and len(t) > 1 for t in by_inst.values())}")
    print(f"\nmakespan mismatches on the {common} instances solved by several variants: {len(bad)} {bad[:5]}; "
          f"invalid solutions: {invalid}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CBM cactus benchmark (see the module docstring)")
    ap.add_argument("out_csv")
    ap.add_argument("--summary", action="store_true", help="print the table of OUT_CSV instead of running")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--scens", default="1-10")
    ap.add_argument("--time-limit", default="60")
    ap.add_argument("--mem-limit", default="8000")
    ap.add_argument("--maps", default=",".join(SMALL + LARGE))
    ap.add_argument("--variants", default=",".join(VARIANTS))
    ap.add_argument("--t-start", default="lb", choices=["lb", "1"])
    a = ap.parse_args()
    unknown = set(a.maps.split(",")) - set(SMALL + LARGE)
    if unknown:
        ap.error(f"unknown maps: {sorted(unknown)}")
    if a.summary:
        summary(a.out_csv)
    else:
        run(a)
