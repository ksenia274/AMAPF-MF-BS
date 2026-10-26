#!/usr/bin/env python3
"""Compare cbm.exe with brute_force.py (colored) on random tiny instances.

Usage: compare_cbm.py CBM_EXE [--random N] [--seed S] [--max-nodes M]
Instance: grid up to 3x4 with random obstacles, 2..4 agents, 2..3 teams (agent i in team i % K).
Compared: T of cbm with max(T_brute, 1); routes checked by validate.py with --teams. If brute force says
there is no solution, cbm must stop at the node limit (T=-1); cbm hitting the limit on a solvable
instance is reported as LIMIT.
"""
import argparse
import os
import random
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brute_force import min_makespan  # noqa: E402
from compare_brute import write_instance  # noqa: E402
from validate import check, read_routes  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--random", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-nodes", type=int, default=5000)
    a = ap.parse_args()
    exe = os.path.abspath(a.exe)
    work = tempfile.mkdtemp(prefix="compare_cbm_")
    rng = random.Random(a.seed)
    bad = limit = solvable = 0
    nodes = []
    for i in range(a.random):
        h, w = rng.choice([(2, 3), (3, 3), (2, 4), (3, 4)])
        grid = ["".join("@" if rng.random() < 0.15 else "." for _ in range(w)) for _ in range(h)]
        free = [(x, y) for y in range(h) for x in range(w) if grid[y][x] == "."]
        n = rng.randint(2, min(4, len(free)))
        k = rng.randint(2, min(3, n))
        starts, goals = rng.sample(free, n), rng.sample(free, n)
        teams = [j % k for j in range(n)]
        mp, sc, _ = write_instance(work, w, h, grid, starts, goals)
        routes_path = os.path.join(work, "g.routes")
        if os.path.exists(routes_path):
            os.remove(routes_path)
        out = subprocess.run([exe, mp, sc, str(n), str(k), routes_path, "--max-nodes", str(a.max_nodes)],
                             capture_output=True, text=True).stdout.strip()
        t_cbm = int(out.split("T=")[1].split()[0]) if "T=" in out else None
        t_ref = min_makespan(w, h, grid, starts, goals, teams=teams)
        t_ref = max(t_ref, 1) if t_ref != -1 else -1
        problem = None
        if t_ref != -1:
            solvable += 1
        if t_cbm == -1 and t_ref != -1:
            limit += 1
            print(f"LIMIT #{i} grid={grid} starts={starts} goals={goals} K={k}: cbm {out} brute T={t_ref}")
            continue
        if t_cbm != t_ref:
            problem = f"cbm {out} brute T={t_ref}"
        elif t_cbm != -1:
            nodes.append(int(out.split("nodes_generated=")[1].split()[0]))
            T, _, routes = read_routes(routes_path)
            errors = check(w, h, grid, starts, goals, T, routes, n_teams=k)
            if errors:
                problem = f"invalid routes: {errors}"
        if problem:
            bad += 1
            print(f"MISMATCH #{i} grid={grid} starts={starts} goals={goals} K={k}: {problem}")
    nodes.sort()
    med = nodes[len(nodes) // 2] if nodes else 0
    print(f"random: {a.random} instances ({solvable} solvable), seed={a.seed}; "
          f"CT nodes generated: median {med}, max {max(nodes, default=0)}")
    print(f"total={a.random} mismatches={bad} limit={limit}")
    sys.exit(1 if bad or limit else 0)


if __name__ == "__main__":
    main()
