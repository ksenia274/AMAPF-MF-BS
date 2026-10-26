#!/usr/bin/env python3
"""Compare a Bulk Search executable with brute_force.py on tiny grids.

Usage: compare_brute.py EXE [--grids 1x5:2,2x3:2,2x3:3,3x3:2,2x4:3]
       compare_brute.py EXE --random N [--vertex NV] [--edge NE] [--tmax 8] [--seed 1]
EXE is called as "EXE MAP SCEN K ROUTES [CONSTRAINTS]" and must print "T=<n> ...".
Exhaustive mode: every start/goal set of the given empty grids, no constraints.
Random mode: N random instances (grid up to 3x4 with random obstacles, K = 1..3) with NV vertex and NE edge
constraints at random steps 0..tmax; the routes are also checked by validate.py with the constraints.
Compared: T of EXE with max(T_brute, 1) (the solvers start from T=1); -1 = no solution.
"""
import argparse
import itertools
import os
import random
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brute_force import min_makespan  # noqa: E402
from validate import check, read_routes  # noqa: E402


def write_instance(work, w, h, grid, starts, goals, vertex=(), edge=()):
    mp, sc, cs = (os.path.join(work, n) for n in ("g.map", "g.scen", "g.constraints"))
    with open(mp, "w", newline="\n") as f:
        f.write(f"type octile\nheight {h}\nwidth {w}\nmap\n" + "\n".join(grid) + "\n")
    with open(sc, "w", newline="\n") as f:
        f.write("version 1\n")
        for s, g in zip(starts, goals):
            f.write(f"0\tg.map\t{w}\t{h}\t{s[0]}\t{s[1]}\t{g[0]}\t{g[1]}\t0\n")
    with open(cs, "w", newline="\n") as f:
        for c, t in vertex:
            f.write(f"v {c[0]} {c[1]} {t}\n")
        for u, v, t in edge:
            f.write(f"e {u[0]} {u[1]} {v[0]} {v[1]} {t}\n")
    return mp, sc, cs


def run_exe(exe, args):
    p = subprocess.run([exe] + args, capture_output=True, text=True)
    if "T=" not in p.stdout:
        return None, (p.stdout + p.stderr).strip()
    return int(p.stdout.split("T=")[1].split()[0]), p.stdout.strip()


def exhaustive(exe, work, grids):
    total = bad = 0
    for spec in grids.split(","):
        size, k = spec.split(":")
        h, w = map(int, size.split("x"))
        k = int(k)
        grid = ["." * w] * h
        cells = [(x, y) for y in range(h) for x in range(w)]
        n = 0
        for starts in itertools.combinations(cells, k):
            for goals in itertools.combinations(cells, k):
                mp, sc, _ = write_instance(work, w, h, grid, starts, goals)
                t_exe, out = run_exe(exe, [mp, sc, str(k), os.path.join(work, "g.routes")])
                t_ref = max(min_makespan(w, h, grid, starts, goals), 1)
                n += 1
                if t_exe != t_ref:
                    bad += 1
                    print(f"MISMATCH {h}x{w} starts={starts} goals={goals}: exe {out} brute T={t_ref}")
        print(f"{h}x{w} K={k}: {n} instances")
        total += n
    return total, bad


def random_instances(exe, work, n, nv, ne, tmax, seed):
    rng = random.Random(seed)
    bad = 0
    solved = 0
    for i in range(n):
        h, w = rng.choice([(1, 5), (2, 3), (3, 3), (2, 4), (3, 4)])
        grid = ["".join("@" if rng.random() < 0.15 else "." for _ in range(w)) for _ in range(h)]
        free = [(x, y) for y in range(h) for x in range(w) if grid[y][x] == "."]
        k = rng.randint(1, min(3, len(free)))
        starts, goals = rng.sample(free, k), rng.sample(free, k)
        vertex = {(rng.choice(free), rng.randint(0, tmax)) for _ in range(nv)}
        edge = set()
        for _ in range(ne):
            u = rng.choice(free)
            nbs = [c for c in ((u[0] + 1, u[1]), (u[0] - 1, u[1]), (u[0], u[1] + 1), (u[0], u[1] - 1)) if c in free]
            if nbs:
                edge.add((u, rng.choice(nbs), rng.randint(0, tmax)))
        mp, sc, cs = write_instance(work, w, h, grid, starts, goals, vertex, edge)
        routes_path = os.path.join(work, "g.routes")
        if os.path.exists(routes_path):
            os.remove(routes_path)
        t_exe, out = run_exe(exe, [mp, sc, str(k), routes_path, cs])
        t_ref = min_makespan(w, h, grid, starts, goals, vertex, edge)
        t_ref = max(t_ref, 1) if t_ref != -1 else -1
        problem = None
        if t_exe != t_ref:
            problem = f"exe {out} brute T={t_ref}"
        elif t_exe != -1:
            solved += 1
            T, _, routes = read_routes(routes_path)
            errors = check(w, h, grid, starts, goals, T, routes, vertex, edge)
            if errors:
                problem = f"invalid routes: {errors}"
        if problem:
            bad += 1
            print(f"MISMATCH #{i} grid={grid} starts={starts} goals={goals} vertex={sorted(vertex)} "
                  f"edge={sorted(edge)}: {problem}")
    print(f"random: {n} instances ({solved} solvable), vertex={nv} edge={ne} tmax={tmax} seed={seed}")
    return n, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--grids", default="1x5:2,2x3:2,2x3:3,3x3:2,2x4:3", help="HxW:K,...")
    ap.add_argument("--random", type=int, default=0, help="number of random instances (random mode)")
    ap.add_argument("--vertex", type=int, default=0)
    ap.add_argument("--edge", type=int, default=0)
    ap.add_argument("--tmax", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    exe = os.path.abspath(a.exe)
    work = tempfile.mkdtemp(prefix="compare_brute_")
    if a.random:
        total, bad = random_instances(exe, work, a.random, a.vertex, a.edge, a.tmax, a.seed)
    else:
        total, bad = exhaustive(exe, work, a.grids)
    print(f"total={total} mismatches={bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
