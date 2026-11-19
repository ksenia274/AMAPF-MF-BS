#!/usr/bin/env python3
"""Week 7, C1: minimal T against brute force on tiny maps made of corridors (bulks of one cell often overlap).

Usage: test_corridors.py low N [--seed S] [--exe-dir DIR] [--lows bs,bspen,bscut,bscut:all]
           one team (bs_team.exe), 1..4 robots, 0..6 vertex / edge constraints (30%: one more on a goal at
           T0..T0+2), 1..4 robots of other teams walking along the corridors (--others: the order of bspen and
           bscut depends on them); T of every low level = brute force, routes checked by validate.py
       test_corridors.py cbm N [--seed S] [--exe-dir DIR] [--lows bs,bspen,bscut] [--t-start lb|match|1]
           cbm.exe, 2..5 robots in 2..4 teams (robot i in team i % K); T = brute force (colored), routes checked;
           at the node limit (--max-nodes, 2000 if brute force finds no solution) last_key must not exceed the brute
           T (it is a lower bound of the optimum); such runs are counted as "node limit", not checked further
--exe-dir: folder of bs_team.exe / cbm.exe (default: this folder; audit_build.py makes a build with counters, its
"audit late_first=.. flag_prune=.." lines are summed per low level).
Maps (free cells <= 12): a line 1xL; a line with pockets; a cross; a ring with a corridor; two rooms 2x2 joined by a
corridor; a random tree (spanning tree of a 2x3..3x4 grid of rooms, corridors of length 1 between them).
"""
import argparse
import os
import random
import subprocess
import sys
import tempfile
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brute_force import min_makespan  # noqa: E402
from compare_brute import write_instance  # noqa: E402
from test_flow_team import low_args, neighbours  # noqa: E402
from validate import check, read_routes  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def from_cells(w, h, cells):
    return ["".join("." if (x, y) in cells else "@" for x in range(w)) for y in range(h)]


def line(rng):
    L = rng.randint(4, 8)
    return "line", from_cells(L, 1, {(x, 0) for x in range(L)})


def pockets(rng):
    L = rng.randint(4, 6)
    cells = {(x, 1) for x in range(L)}
    for _ in range(rng.randint(1, 3)):
        cells.add((rng.randrange(L), rng.choice([0, 2])))
    return "pockets", from_cells(L, 3, cells)


def cross(rng):
    a = rng.randint(1, 2)
    n = 2 * a + 1
    cells = {(x, a) for x in range(n)} | {(a, y) for y in range(n)}
    return "cross", from_cells(n, n, cells)


def ring(rng):
    w, h = rng.choice([(3, 3), (4, 3), (4, 4)])
    cells = {(x, y) for x in range(w) for y in range(h) if x in (0, w - 1) or y in (0, h - 1)}
    if rng.random() < 0.5:  # a tail corridor out of the ring
        tail = [(x, h) for x in range(rng.randint(1, 2))]
        cells |= set(tail)
        return "ring+tail", from_cells(w, h + 1, cells)
    return "ring", from_cells(w, h, cells)


def rooms(rng):
    c = rng.randint(1, 3)  # corridor length
    w = 4 + c
    cells = {(x, y) for x in range(2) for y in range(2)} | {(x, y) for x in range(2 + c, 4 + c) for y in range(2)}
    cells |= {(x, rng.randint(0, 1)) for x in range(2, 2 + c)} if c else set()
    row = rng.randint(0, 1)
    cells = {(x, y) for x, y in cells if not (2 <= x < 2 + c) or y == row}
    cells |= {(x, row) for x in range(2, 2 + c)}
    return "rooms", from_cells(w, 2, cells)


def tree(rng):
    rw, rh = rng.choice([(2, 3), (3, 2), (3, 3), (3, 4), (4, 3)])
    w, h = 2 * rw - 1, 2 * rh - 1
    seen, cells, stack = {(0, 0)}, {(0, 0)}, [(0, 0)]
    while stack:
        x, y = stack[-1]
        nxt = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if 0 <= x + dx < rw and 0 <= y + dy < rh and (x + dx, y + dy) not in seen]
        if not nxt:
            stack.pop()
            continue
        nx, ny = rng.choice(nxt)
        seen.add((nx, ny))
        cells |= {(2 * nx, 2 * ny), (x + nx, y + ny)}
        stack.append((nx, ny))
    if len(cells) > 12:  # keep the brute force small: cut leaves
        cells = set(sorted(cells, key=lambda c: (c[0] + c[1]))[:12])
        comp, todo = set(), [(0, 0)]
        while todo:
            c = todo.pop()
            if c in cells and c not in comp:
                comp.add(c)
                todo += [(c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)]
        cells = comp
    return "tree", from_cells(w, h, cells)


SHAPES = [line, pockets, cross, ring, rooms, tree]


def random_map(rng):
    name, grid = rng.choice(SHAPES)(rng)
    w, h = len(grid[0]), len(grid)
    free = [(x, y) for y in range(h) for x in range(w) if grid[y][x] == "."]
    return name, w, h, grid, free


def walk(rng, free, start, length):
    r = [start]
    for _ in range(length):
        nbs = neighbours(r[-1], set(free))
        r.append(rng.choice(nbs) if nbs and rng.random() < 0.8 else r[-1])
    return r


def audit(err):
    for ln in err.splitlines():
        if ln.startswith("audit "):
            return {k: int(v) for k, v in (x.split("=") for x in ln.split()[1:])}
    return {}


def run_low(a, rng, work, exe):
    stats = defaultdict(lambda: defaultdict(int))
    bad = []
    for i in range(a.n):
        name, w, h, grid, free = random_map(rng)
        k = rng.randint(1, min(4, len(free) - 1))
        starts, goals = rng.sample(free, k), rng.sample(free, k)
        vertex, edge = set(), set()
        for _ in range(rng.randint(0, 6)):
            u = rng.choice(free)
            nbs = neighbours(u, set(free))
            if rng.random() < 0.5 or not nbs:
                vertex.add((u, rng.randint(0, 8)))
            else:
                edge.add((u, rng.choice(nbs), rng.randint(0, 8)))
        if rng.random() < 0.3:
            t0 = min_makespan(w, h, grid, starts, goals, vertex, edge)
            if t0 != -1:
                vertex.add((rng.choice(goals), max(t0, 1) + rng.randint(0, 2)))
        ref = min_makespan(w, h, grid, starts, goals, vertex, edge)
        ref = max(ref, 1) if ref != -1 else -1
        mp, sc, cs = write_instance(work, w, h, grid, starts, goals, vertex, edge)
        others = [walk(rng, free, rng.choice(free), rng.randint(2, 10)) for _ in range(rng.randint(1, 4))]
        length = max(len(r) for r in others)
        others = [r + [r[-1]] * (length - len(r)) for r in others]
        op = os.path.join(work, "g.others")
        with open(op, "w", newline="\n") as f:
            f.write(f"{length - 1} {len(others)}\n" + "".join(" ".join(f"{x},{y}" for x, y in r) + "\n" for r in others))
        for low in a.lows.split(","):
            rp = os.path.join(work, "g.routes")
            if os.path.exists(rp):
                os.remove(rp)
            p = subprocess.run([exe, mp, sc, str(k), rp, cs, "--others", op, "--t-start", a.t_start] + low_args(low),
                               capture_output=True, text=True, timeout=120)
            out = p.stdout
            t = int(out.split("T=")[1].split()[0]) if "T=" in out else None
            if t is None and "no solution" in (out + p.stderr).lower():
                t = -1
            st = stats[low]
            st["runs"] += 1
            st["solvable"] += ref != -1
            for key, v in audit(p.stderr).items():
                st[key] += v
            problem = None
            if t != ref:
                problem = f"T={t} brute={ref}"
            elif t != -1:
                T, _, routes = read_routes(rp)
                errors = check(w, h, grid, starts, goals, T, routes, vertex, edge)
                if errors:
                    problem = f"invalid routes {errors}"
            if problem:
                st["bad"] += 1
                bad.append(f"{low} #{i} {name} grid={grid} starts={starts} goals={goals} vertex={sorted(vertex)} "
                           f"edge={sorted(edge)} others={others}: {problem}; {out.strip()} {p.stderr.strip()}")
    return stats, bad


def run_cbm(a, rng, work, exe):
    stats = defaultdict(lambda: defaultdict(int))
    bad = []
    for i in range(a.n):
        name, w, h, grid, free = random_map(rng)
        n = rng.randint(2, min(5, len(free) - 1))
        k = rng.randint(2, min(4, n))
        starts, goals = rng.sample(free, n), rng.sample(free, n)
        teams = [j % k for j in range(n)]
        ref = min_makespan(w, h, grid, starts, goals, teams=teams)
        ref = max(ref, 1) if ref != -1 else -1
        mp, sc, _ = write_instance(work, w, h, grid, starts, goals)
        for low in a.lows.split(","):
            rp = os.path.join(work, "g.routes")
            if os.path.exists(rp):
                os.remove(rp)
            # no solution: CBS never stops by itself, a small node limit only checks that nothing is returned
            nodes = a.max_nodes if ref != -1 else 2000
            p = subprocess.run([exe, mp, sc, str(n), str(k), rp, "--max-nodes", str(nodes), "--t-start", a.t_start]
                               + low_args(low), capture_output=True, text=True, timeout=300)
            out = p.stdout
            t = int(out.split("T=")[1].split()[0]) if "T=" in out else None
            st = stats[low]
            st["runs"] += 1
            st["solvable"] += ref != -1
            for key, v in audit(p.stderr).items():
                st[key] += v
            problem = None
            if t == -1 and ref != -1:
                # the last expanded key is a lower bound of the optimum: above the brute T it would be a loss
                last_key = int(out.split("last_key=")[1].split()[0])
                if last_key > ref:
                    problem = f"node limit with last_key {last_key} > brute {ref}"
                else:
                    st["limit"] += 1
            elif t != ref and not (t == -1 and ref == -1):
                problem = f"T={t} brute={ref}"
            elif t != -1:
                T, _, routes = read_routes(rp)
                errors = check(w, h, grid, starts, goals, T, routes, n_teams=k)
                if errors:
                    problem = f"invalid routes {errors}"
            if problem:
                st["bad"] += 1
                bad.append(f"{low} #{i} {name} grid={grid} starts={starts} goals={goals} K={k}: {problem}; "
                           f"{out.strip()} {p.stderr.strip()}")
    return stats, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["low", "cbm"])
    ap.add_argument("n", type=int)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--exe-dir", default=HERE)
    ap.add_argument("--lows")
    ap.add_argument("--t-start", default="lb")
    ap.add_argument("--max-nodes", type=int, default=20000)
    a = ap.parse_args()
    a.lows = a.lows or ("bs,bspen,bscut,bscut:all" if a.mode == "low" else "bs,bspen,bscut")
    exe = os.path.join(a.exe_dir, "bs_team.exe" if a.mode == "low" else "cbm.exe")
    work = tempfile.mkdtemp(prefix="corridors_")
    rng = random.Random(a.seed)
    stats, bad = (run_low if a.mode == "low" else run_cbm)(a, rng, work, exe)
    for line_ in bad:
        print("MISMATCH", line_)
    print(f"{a.mode}: {a.n} instances, seed {a.seed}, t-start {a.t_start}, exe {exe}")
    for low, st in stats.items():
        print(f"  {low}: runs {st['runs']}, solvable {st['solvable']}, mismatches {st['bad']}"
              + (f", node limit {st['limit']}" if a.mode == "cbm" else "")
              + (f", late_first {st['late_first']}, flag_prune {st['flag_prune']}" if "late_first" in st else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
