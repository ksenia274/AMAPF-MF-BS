#!/usr/bin/env python3
"""CBM on MovingAI maps for cactus plots: teams of 5, random scen 1..10, low levels bs, bspen, bscut, flow, floww.

Usage: cbm_bench_cactus.py (--name NAME | --run-id R<YYYYMMDD>-<name>) [--note TEXT] [--resume] [--scens 1-10]
                           [--time-limit 60] [--mem-limit 8000] [--maps M1,M2,..] [--variants V1,V2,..]
                           [--t-start lb|1|match] [--ns SPEC] [--teams K1,K2,..] [--no-skip]
                           [--continue-from CSV[:V1+V2],..] [--retry-timeouts CSV[:V1+V2],..]
       cbm_bench_cactus.py --summary CSV       (markdown table; makespan check over the variants; solved by one
                                                  of floww / bspen and not by bscut and vice versa)
       cbm_bench_cactus.py --summary CSV1,CSV2,..  (the rows of several runs together: for the makespan check across
                                                  runs; the table then counts an instance once per run)
The run ID is R<today>-NAME unless --run-id is given; output in runs/<ID>/ (manifest.json, results.csv with a
run_id column, run.log), see runlib.py. --resume needs --run-id and the same parameters.
Instance: random scen s of the map, the first N agents, K = ceil(N/5) teams of consecutive agents (as cbm_bench g5).
Stopping rule of the Bulk Search paper: within a scen N grows; once a variant does not solve an instance, the larger
N of that scen are not run for it and are written as timeout_skipped. T starts from the lower bound (the default).
Runs are sequential; every solution is checked by validate.py --teams K; the CSV is flushed after every run.
--resume: keeps the rows of results.csv and runs only the missing ones (rows with status error, i.e. cbm printed
nothing, are run again).
bscut = --low bscut --cut penal.
--ns SPEC: N instead of the default lists: "100,120" for all maps, or "KEY:100,120/KEY:.." with KEY a map name or a
  group of the default lists (32, 64, large).
--teams K1,K2,..: K teams (agent i in team i % K, as in cbm) for every K instead of teams of 5; every N is run with
  every K, the stopping rule is per K.
--no-skip: no stopping rule, every N is run.
--continue-from CSV[:V1+V2],..: a sequence (map, scen, variant) is run only if its largest N in the CSVs is solved;
  ":V1+V2" takes only these variants of that CSV.
--retry-timeouts CSV[:V1+V2],..: per sequence (map, scen, variant) of the CSVs, the N of that sequence in the CSVs
  from its first unsolved N (not timeout_skipped) on; sequences that solved all their N are not run. For a larger
  --time-limit on the timeouts of earlier runs.
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile
import time

import runlib
from cbm_bench import field, map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
SMALL = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8"]
LARGE = ["warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]
# not in the default --maps (week 7, series D)
SMALL_MORE = ["random-32-32-20", "maze-32-32-4", "room-64-64-16", "den312d"]
LARGE_MORE = ["ost003d", "warehouse-20-40-10-2-1"]
NS ={"32": [20, 40, 60, 80], "64": [40, 80, 120, 160], "large": [64, 128, 192, 256]}
VARIANTS = ["bs", "bspen", "bscut", "flow", "floww"]
LOW_ARGS = {"bscut": ["--low", "bscut", "--cut", "penal"]}
OUT_FIELDS = ["status", "T", "nodes_generated", "nodes_expanded", "lowlevel_calls", "lowlevel_ms", "total_ms",
              "root_conflict_pairs", "root_conflicting_teams", "root_ms", "pruned_unreachable", "replan_ms_median", "peak_mb",
              "last_key"]
FIELDS = ["run_id", "map", "group", "N", "K", "scen", "variant"] + OUT_FIELDS + ["valid", "exit", "wall_s"]
TEAM_SIZE = 5


def group_of(name):
    if name in LARGE + LARGE_MORE:
        return "large"
    return "32" if "-32-32" in name else "64"


def ns_of(name, spec=None):
    if spec:
        parts = dict(p.split(":") for p in spec.split("/")) if ":" in spec else {"": spec}
        for key in (name, group_of(name), ""):
            if key in parts:
                return [int(x) for x in parts[key].split(",")]
    return NS[group_of(name)]


def read_sequences(spec):
    """(map, scen, variant) -> {N: status} over the CSVs of spec "CSV[:V1+V2],.."."""
    seqs = {}
    for item in spec.split(","):
        path, vs = (item, "") if os.path.exists(item) else item.rsplit(":", 1)
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                if not vs or r["variant"] in vs.split("+"):
                    seqs.setdefault((r["map"], r["scen"], r["variant"]), {})[int(r["N"])] = r["status"]
    return seqs


def sequence_ns(args, seqs, name, s, variant):
    """The N to run for the sequence (map, scen, variant)."""
    if args.retry_timeouts:
        seq = seqs.get((name, str(s), variant), {})
        bad = [n for n in sorted(seq) if seq[n] not in ("solved", "timeout_skipped")]
        return [n for n in sorted(seq) if n >= bad[0]] if bad else []
    if args.continue_from:
        seq = seqs.get((name, str(s), variant))
        if not seq or seq[max(seq)] != "solved":
            return []
    return ns_of(name, args.ns)


def params_of(args):
    maps = args.maps.split(",")
    p = {"maps": maps, "scens": args.scens, "N": {m: ns_of(m, args.ns) for m in maps},
         "teams": f"fixed:{args.teams}" if args.teams else f"size:{TEAM_SIZE}",
         "time_limit": float(args.time_limit), "mem_limit": int(args.mem_limit), "variants": args.variants.split(","),
         "low_args": {v: LOW_ARGS.get(v, ["--low", v]) for v in args.variants.split(",")}, "t_start": args.t_start,
         "stopping_rule": "none" if args.no_skip else "within a scen, after a failure the larger N are timeout_skipped"}
    if args.continue_from:
        p["continue_from"] = args.continue_from
    if args.retry_timeouts:
        p["retry_timeouts"] = args.retry_timeouts
        p["N"] = {m: "from the first unsolved N of --retry-timeouts" for m in maps}
    return p


def run(args):
    opt = {"--" + k.replace("_", "-"): v for k, v in vars(args).items()}
    lo, hi = map(int, opt["--scens"].split("-"))
    exe = os.path.join(HERE, "cbm.exe")
    rid = runlib.make_id(args.name, args.run_id)
    rn = runlib.Run(rid, "cbm_bench_cactus.py", params_of(args), args.resume, args.note, exe)
    out_csv = rn.csv_path
    kept = []
    if args.resume and os.path.exists(out_csv):
        with open(out_csv) as f:
            kept = [r for r in csv.DictReader(f) if r["status"] not in ("", "error")]
    done = {(r["map"], r["N"], r["K"], r["scen"], r["variant"]): r["status"] for r in kept}
    spec = args.continue_from or args.retry_timeouts
    seqs = read_sequences(spec) if spec else None
    ks = [int(x) for x in args.teams.split(",")] if args.teams else [None]
    tmp = tempfile.mkdtemp()
    limit = float(opt["--time-limit"])
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(kept)
        f.flush()
        for name in opt["--maps"].split(","):
            group = "small" if name in SMALL + SMALL_MORE else "large"
            for s in range(lo, hi + 1):
                failed = set()  # (variant, fixed K)
                todo = {v: sequence_ns(args, seqs, name, s, v) for v in opt["--variants"].split(",")}
                for n, k_fixed in [(n, kf) for n in sorted(set().union(*todo.values())) for kf in ks]:
                    mp, src = map_and_scen(name, s)
                    scen = os.path.join(tmp, "g.scen")
                    k = grouped_scen(src, n, scen, k_fixed)
                    for variant in opt["--variants"].split(","):
                        if n not in todo[variant]:
                            continue
                        key = (name, str(n), str(k), str(s), variant)
                        if key in done:
                            if done[key] != "solved" and not args.no_skip:
                                failed.add((variant, k_fixed))
                            continue
                        row = {"run_id": rid, "map": name, "group": group, "N": n, "K": k, "scen": s, "variant": variant, "valid": ""}
                        ts = ""  # the --t-start actually passed to cbm, for the log
                        if (variant, k_fixed) in failed:
                            row.update({"status": "timeout_skipped", "T": -1})
                        else:
                            routes = os.path.join(tmp, "r.routes")
                            if os.path.exists(routes):
                                os.remove(routes)
                            cmd = [exe, mp, scen, str(n), str(k), routes] + LOW_ARGS.get(variant, ["--low", variant]) + ["--time-limit",
                                   opt["--time-limit"], "--mem-limit", opt["--mem-limit"], "--t-start", opt["--t-start"]]
                            ts = "t-start=" + cmd[cmd.index("--t-start") + 1]
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
                        if row["status"] != "solved" and not args.no_skip:
                            failed.add((variant, k_fixed))
                        w.writerow(row)
                        f.flush()
                        rn.log(name, n, f"K={k}", s, variant,row["status"], row["T"], row.get("total_ms", ""),
                               "valid=" + str(row["valid"]), ts)
    rn.finish()


def summary(paths):
    rows = []
    for path in paths.split(","):
        with open(path) as f:
            rows += list(csv.DictReader(f))
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
            by_inst.setdefault((r["map"], r["N"], r["K"], r["scen"]), {})[r["variant"]] = r["T"]
    bad = [(k, ts) for k, ts in by_inst.items() if len(set(ts.values())) > 1]
    common = sum(len(ts) > 1 for ts in by_inst.values())
    invalid = sum(r["status"] == "solved" and r["valid"] != "1" for r in rows)
    if "bscut" in variants:
        print()
        for other in ("floww", "bspen"):
            for group in ("small", "large"):
                ts = [ts for k, ts in by_inst.items() if (k[0] in SMALL + SMALL_MORE) == (group == "small")]
                print(f"{group}: solved by {other} and not by bscut: {sum(other in t and 'bscut' not in t for t in ts)}; "
                      f"by bscut and not by {other}: {sum('bscut' in t and other not in t for t in ts)}")
        print(f"instances solved by bscut and another variant: {sum('bscut' in t and len(t) > 1 for t in by_inst.values())}")
    print(f"\nmakespan mismatches on the {common} instances solved by several variants: {len(bad)} {bad[:5]}; "
          f"invalid solutions: {invalid}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CBM cactus benchmark (see the module docstring)")
    ap.add_argument("--summary", metavar="CSV[,CSV2,..]", help="print the table of the CSVs instead of running")
    ap.add_argument("--name", help="run ID = R<today>-NAME")
    ap.add_argument("--run-id")
    ap.add_argument("--note", default="", help="one line for runs/REGISTRY.md")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--scens", default="1-10")
    ap.add_argument("--time-limit", default="60")
    ap.add_argument("--mem-limit", default="8000")
    ap.add_argument("--maps", default=",".join(SMALL + LARGE))
    ap.add_argument("--variants", default=",".join(VARIANTS))
    ap.add_argument("--t-start", default="lb", choices=["lb", "1", "match"])
    ap.add_argument("--ns", help="N per map or group, see the module docstring")
    ap.add_argument("--teams", help="K1,K2,..: fixed numbers of teams instead of teams of 5")
    ap.add_argument("--no-skip", action="store_true")
    ap.add_argument("--continue-from", metavar="CSV[:V1+V2],..")
    ap.add_argument("--retry-timeouts", metavar="CSV[:V1+V2],..")
    a = ap.parse_args()
    if a.continue_from and a.retry_timeouts:
        ap.error("--continue-from and --retry-timeouts exclude each other")
    unknown = set(a.maps.split(",")) - set(SMALL + LARGE + SMALL_MORE + LARGE_MORE)
    if unknown:
        ap.error(f"unknown maps: {sorted(unknown)}")
    if a.summary:
        summary(a.summary)
    elif not (a.name or a.run_id):
        ap.error("--name or --run-id is needed")
    elif a.resume and not a.run_id:
        ap.error("--resume needs --run-id")
    else:
        run(a)
