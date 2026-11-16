#!/usr/bin/env python3
"""Week 6, stage A: --t-start match (bs::teamMatchBound) against --t-start lb.

Usage: week6_match.py hard [--resume]   the 16 instances of small_maps_diag.csv, cbm --diag, 60 s, 8000 MB:
                                        match for bs, bspen, bscut, flow, floww; lb for bs and flow (lb of bspen,
                                        bscut, floww: small_maps_cut.csv, the same protocol, not run again)
       week6_match.py root [--resume]   cbm --root-only last, N = 128, random scen 1, teams of 5, 600 s per call:
                                        Berlin, Paris, Boston, room-64-64-8, warehouse; bs, bspen, bscut; lb and match;
                                        floww on Berlin N = 64 with match (lb: week6_prof/, part 2)
       week6_match.py report
Runs are sequential. Output: week6_match_hard.csv, week6_match_root.csv.
"""
import argparse
import csv
import os
import statistics
import subprocess
import tempfile

from cbm_bench import field, map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "cbm.exe")
VARIANTS = {"bs": ["--low", "bs"], "bspen": ["--low", "bspen"], "bscut": ["--low", "bscut", "--cut", "penal"],
            "flow": ["--low", "flow"], "floww": ["--low", "floww"]}
HARD_OUT = ["status", "T", "nodes_generated", "nodes_expanded", "lowlevel_calls", "total_ms", "root_conflict_pairs"]
HARD = os.path.join(HERE, "week6_match_hard.csv")
ROOT = os.path.join(HERE, "week6_match_root.csv")
ROOT_OUT = ["status", "root_ms", "teams_planned", "team_T_max"]
ROOT_MAPS = ["Berlin_1_256", "Paris_1_256", "Boston_0_256", "room-64-64-8", "warehouse-10-20-10-2-1"]


def open_out(path, fields, resume):
    kept = list(csv.DictReader(open(path))) if resume and os.path.exists(path) else []
    f = open(path, "w", newline="")
    w = csv.DictWriter(f, fields)
    w.writeheader()
    w.writerows(kept)
    f.flush()
    return f, w, kept


def hard(resume):
    insts = list(csv.DictReader(open(os.path.join(HERE, "small_maps_diag.csv"))))
    fields = ["map", "N", "mode", "K", "scen", "variant", "t_start"] + HARD_OUT
    f, w, kept = open_out(HARD, fields, resume)
    done = {(r["map"], r["N"], r["mode"], r["scen"], r["variant"], r["t_start"]) for r in kept}
    tmp = tempfile.mkdtemp()
    for inst in insts:
        name, n, mode, s = inst["map"], inst["N"], inst["mode"], inst["scen"]
        mp, src = map_and_scen(name, int(s))
        if mode == "k4":
            scen, k = src, 4
        else:
            scen = os.path.join(tmp, "g.scen")
            k = grouped_scen(src, int(n), scen)
        for v, args in VARIANTS.items():
            for ts in (["lb", "match"] if v in ("bs", "flow") else ["match"]):
                if (name, n, mode, s, v, ts) in done:
                    continue
                cmd = [EXE, mp, scen, n, str(k), "-", "--mem-limit", "8000", "--time-limit", "60", "--diag",
                       "--t-start", ts] + args
                try:
                    out = subprocess.run(cmd, capture_output=True, text=True, timeout=400).stdout
                except subprocess.TimeoutExpired:
                    out = "status=killed"
                row = {"map": name, "N": n, "mode": mode, "K": k, "scen": s, "variant": v, "t_start": ts}
                row.update({x: field(out, x) for x in HARD_OUT})
                w.writerow(row)
                f.flush()
                print(name, n, mode, s, v, ts, row["status"], row["T"], row["total_ms"], flush=True)


def root(resume):
    fields = ["map", "N", "variant", "t_start"] + ROOT_OUT
    f, w, kept = open_out(ROOT, fields, resume)
    done = {(r["map"], r["N"], r["variant"], r["t_start"]) for r in kept}
    tmp = tempfile.mkdtemp()
    jobs = [(m, 128, v, ts) for m in ROOT_MAPS for v in ("bs", "bspen", "bscut") for ts in ("lb", "match")]
    jobs.append(("Berlin_1_256", 64, "floww", "match"))
    for m, n, v, ts in jobs:
        if (m, str(n), v, ts) in done:
            continue
        mp, src = map_and_scen(m, 1)
        scen = os.path.join(tmp, "g.scen")
        k = grouped_scen(src, n, scen)
        cmd = [EXE, mp, scen, str(n), str(k), "-", "--root-only", "last", "--t-start", ts, "--mem-limit", "8000",
               "--time-limit", "1800" if v == "floww" else "600"] + VARIANTS[v]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        row = {"map": m, "N": n, "variant": v, "t_start": ts}
        row.update({x: field(out, x) for x in ROOT_OUT})
        w.writerow(row)
        f.flush()
        print(m, n, v, ts, out.strip()[:200], flush=True)


def report():
    rows = list(csv.DictReader(open(HARD)))
    old = {(r["map"], r["N"], r["mode"], r["scen"], r["variant"]): r
           for r in csv.DictReader(open(os.path.join(HERE, "small_maps_cut.csv"))) if r["variant"] != "bscut_all"}
    insts = list(csv.DictReader(open(os.path.join(HERE, "small_maps_diag.csv"))))
    by = {(r["map"], r["N"], r["mode"], r["scen"], r["variant"], r["t_start"]): r for r in rows}
    print("### 16 hard instances, lb and match\n")
    print("| instance | variant | lb: status | nodes | replans | ms | match: status | nodes | replans | ms | T lb / match |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    bad, summary = [], {}
    for inst in insts:
        key = (inst["map"], inst["N"], inst["mode"], inst["scen"])
        for v in VARIANTS:
            lb = by.get(key + (v, "lb")) or old.get(key + (v,))
            ma = by.get(key + (v, "match"))
            if not lb or not ma:
                continue
            if lb["status"] == ma["status"] == "solved" and lb["T"] != ma["T"]:
                bad.append((key, v, lb["T"], ma["T"]))
            for ts, r in (("lb", lb), ("match", ma)):
                s = summary.setdefault((v, ts), {"solved": 0, "nodes": [], "replans": [], "ms": []})
                s["solved"] += r["status"] == "solved"
                s["nodes"].append(int(r["nodes_expanded"] or 0))
                s["replans"].append(int(r["lowlevel_calls"] or 0))
                s["ms"].append(float(r["total_ms"] or 0))
            print(f"| {inst['map']} {inst['N']} {inst['mode']} s{inst['scen']} | {v} | {lb['status']} | "
                  f"{lb['nodes_expanded']} | {lb['lowlevel_calls']} | {lb['total_ms']} | {ma['status']} | "
                  f"{ma['nodes_expanded']} | {ma['lowlevel_calls']} | {ma['total_ms']} | {lb['T']} / {ma['T']} |")
    print("\n| variant | lb: solved | match: solved | lb: median nodes | match | lb: median replans | match | "
          "lb: median ms | match |")
    print("|---|---|---|---|---|---|---|---|---|")
    for v in VARIANTS:
        a, b = summary.get((v, "lb")), summary.get((v, "match"))
        if a and b:
            md = statistics.median
            print(f"| {v} | {a['solved']}/16 | {b['solved']}/16 | {md(a['nodes']):g} | {md(b['nodes']):g} | "
                  f"{md(a['replans']):g} | {md(b['replans']):g} | {md(a['ms']):g} | {md(b['ms']):g} |")
    print("\nmakespan mismatches (both solved):", bad or "none")

    print("\n### Root, N = 128 (one run per cell)\n")
    rr = {(r["map"], r["N"], r["variant"], r["t_start"]): r for r in csv.DictReader(open(ROOT))}
    print("| map | variant | root lb, ms | root match, ms | lb / match | max T_i lb / match |")
    print("|---|---|---|---|---|---|")
    for m in ROOT_MAPS:
        for v in ("bs", "bspen", "bscut"):
            a, b = rr.get((m, "128", v, "lb")), rr.get((m, "128", v, "match"))
            if a and b:
                x, y = float(a["root_ms"]), float(b["root_ms"])
                print(f"| {m} | {v} | {x:.0f} | {y:.0f} | {x / y:.1f} | {a['team_T_max']} / {b['team_T_max']} |")
    fl = rr.get(("Berlin_1_256", "64", "floww", "match"))
    if fl:
        from week6_part2 import load
        _, root_calls, _ = load("Berlin_1_256", 64, "floww")[0]
        lb_ms = sum(float(c["ms"]) for c in root_calls)
        print(f"| Berlin_1_256 N=64 | floww | {lb_ms:.0f} (part 2, cbm_prof.exe) | {float(fl['root_ms']):.0f} | "
              f"{lb_ms / float(fl['root_ms']):.1f} | — / {fl['team_T_max']} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["hard", "root", "report"])
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    {"hard": lambda: hard(a.resume), "root": lambda: root(a.resume), "report": report}[a.cmd]()


if __name__ == "__main__":
    main()
