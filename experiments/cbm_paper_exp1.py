#!/usr/bin/env python3
"""Repeats experiment 1 of CBM (Ma, Koenig 2016, table 1) with our cbm: teams of 5 consecutive agents.

Usage: cbm_paper_exp1.py OUT.csv [--time-limit SEC] [--scens 20] [--ns 10,15,...] [--low bs]
       cbm_paper_exp1.py --summary OUT.csv   (markdown table next to the numbers of the paper)

Map random-32-32-10, scen random-1..20, the first N agents. cbm puts agent i into team i % K, so the first N rows
of the .scen are reordered (row 5g+m -> m*K+g, K = N/5) into a temporary file: team g = original agents 5g..5g+4.
Runs are sequential; every solution is checked by validate.py --teams K.
"""
import csv
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
MAP = os.path.join(DATA, "mapf-map", "random-32-32-10.map")
SCEN = os.path.join(DATA, "mapf-scen-random", "scen-random", "random-32-32-10-random-{}.scen")
FIELDS = ["N", "K", "scen", "solved", "T", "valid", "nodes_generated", "nodes_expanded", "lowlevel_calls",
          "lowlevel_ms", "total_ms", "last_key", "expanded_by_key", "exit"]


def grouped_scen(path, n, out):
    with open(path) as f:
        lines = f.read().splitlines()
    rows = lines[1:1 + n]
    k = n // 5
    new = [None] * n
    for i, row in enumerate(rows):
        new[(i % 5) * k + i // 5] = row
    with open(out, "w") as f:
        f.write("\n".join([lines[0]] + new) + "\n")


def field(out, name):
    rest = (" " + out).split(" " + name + "=")[1].split() if " " + name + "=" in " " + out else []
    return rest[0] if rest and "=" not in rest[0] else ""


# Ma, Koenig 2016, table 1 (30x30, 10% obstacles, teams of 5, limit 5 min): success rate of CBM without weights;
# CBM with weights: success rate 1.0 everywhere and the mean time in seconds.
PAPER_RATE = [0.72, 0.44, 0.22, 0.08, 0.02, 0, 0, 0, 0]
PAPER_W_TIME = [0.34, 0.57, 0.78, 1.07, 1.71, 1.92, 2.95, 3.66, 5.32]


def summary(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    print("| N | K | solved | mean time, s (solved) | mean makespan (solved) | mean CT nodes expanded (solved) | "
          "mean replans (solved) | unsolved: nodes expanded | unsolved: last key (expanded at it) | invalid | "
          "paper CBM rate | paper CBM-w rate | paper CBM-w time, s |")
    print("|" + "---|" * 13)
    for i, n in enumerate(sorted({int(r["N"]) for r in rows})):
        rs = [r for r in rows if int(r["N"]) == n]
        ok = [r for r in rs if r["solved"] == "1"]
        bad = [r for r in rs if r["solved"] != "1"]
        unsolved_nodes = ", ".join(r["nodes_expanded"] for r in bad) or "-"
        keys = ", ".join(r["last_key"] + "(" + r["expanded_by_key"].split(",")[-1].split(":")[-1] + ")" for r in bad) or "-"
        invalid = sum(1 for r in ok if r["valid"] != "1")
        print(f"| {n} | {rs[0]['K']} | {len(ok)}/{len(rs)} = {len(ok) / len(rs):.2f} | "
              f"{mean([int(r['total_ms']) / 1000 for r in ok]):.2f} | {mean([int(r['T']) for r in ok]):.1f} | "
              f"{mean([int(r['nodes_expanded']) for r in ok]):.0f} | {mean([int(r['lowlevel_calls']) for r in ok]):.0f} | "
              f"{unsolved_nodes} | {keys} | {invalid} | {PAPER_RATE[i]} | 1.0 | {PAPER_W_TIME[i]} |")


def main():
    args = sys.argv[1:]
    if args[0] == "--summary":
        return summary(args[1])
    out_csv = args[0]
    opt = {"--time-limit": "60", "--scens": "20", "--ns": "10,15,20,25,30,35,40,45,50", "--low": ""}
    for i in range(1, len(args), 2):
        opt[args[i]] = args[i + 1]
    exe = os.path.join(HERE, "cbm.exe")
    tmp = tempfile.mkdtemp()
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for n in map(int, opt["--ns"].split(",")):
            k = n // 5
            for s in range(1, int(opt["--scens"]) + 1):
                scen = os.path.join(tmp, f"s{s}_n{n}.scen")
                routes = os.path.join(tmp, "r.routes")
                grouped_scen(SCEN.format(s), n, scen)
                if os.path.exists(routes):
                    os.remove(routes)
                cmd = [exe, MAP, scen, str(n), str(k), routes, "--time-limit", opt["--time-limit"]]
                if opt["--low"]:
                    cmd += ["--low", opt["--low"]]
                p = subprocess.run(cmd, capture_output=True, text=True)
                o = p.stdout
                t = int(field(o, "T") or -1)
                valid = ""
                if t != -1:
                    v = subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), MAP, scen, str(n), routes,
                                        "--teams", str(k)], capture_output=True, text=True)
                    valid = int(v.returncode == 0)
                row = {"N": n, "K": k, "scen": s, "solved": int(t != -1), "T": t, "valid": valid, "exit": p.returncode}
                for name in FIELDS[6:13]:
                    row[name] = field(o, name)
                w.writerow(row)
                f.flush()
                print(n, s, o.strip().split("\n")[0][:150], "valid=" + str(valid), flush=True)


if __name__ == "__main__":
    main()
