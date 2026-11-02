#!/usr/bin/env python3
"""Low level alone on random tiny instances: FlowTeam vs BulkSearchTeam vs brute force (bs_team.exe --low ...).

Usage: test_flow_team.py BS_TEAM_EXE --makespan N [--seed S]   (2.1: minimal T of bs, flow, brute force)
       test_flow_team.py BS_TEAM_EXE --weights N [--seed S]    (2.2: weight of floww vs brute-force minimum)
Instance: grid up to 4x4 with random obstacles, 1..4 robots, 0..6 random vertex/edge constraints at steps 0..6;
in 30% of the instances one of them is a vertex constraint on a goal at T0..T0+2 (T0 = optimum without it).
--weights: 1..3 robots of other teams walk randomly; the penalty of a team solution is (a) the number of
(our robot, other robot) pairs in one cell at t = 1..T and (b) the number of our moves v -> u at t with an other
robot moving u -> v at t. The brute force finds the minimal penalty among the solutions with the T of floww.
All routes are checked by validate.py with the constraints.
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
from compare_brute import write_instance  # noqa: E402
from validate import check, read_routes  # noqa: E402


def neighbours(c, free):
    return [n for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)) if n in free]


def random_instance(rng):
    while True:
        h, w = rng.randint(1, 4), rng.randint(1, 4)
        grid = ["".join("@" if rng.random() < 0.15 else "." for _ in range(w)) for _ in range(h)]
        free = [(x, y) for y in range(h) for x in range(w) if grid[y][x] == "."]
        if free:
            break
    k = rng.randint(1, min(4, len(free)))
    starts, goals = rng.sample(free, k), rng.sample(free, k)
    vertex, edge = set(), set()
    for _ in range(rng.randint(0, 6)):
        u = rng.choice(free)
        nbs = neighbours(u, free)
        if rng.random() < 0.5 or not nbs:
            vertex.add((u, rng.randint(0, 6)))
        else:
            edge.add((u, rng.choice(nbs), rng.randint(0, 6)))
    after = False
    if rng.random() < 0.3:
        t0 = min_makespan(w, h, grid, starts, goals, vertex, edge)
        if t0 != -1:
            vertex.add((rng.choice(goals), max(t0, 1) + rng.randint(0, 2)))
            after = True
    return w, h, grid, free, starts, goals, vertex, edge, after


def run(exe, args):
    p = subprocess.run([exe] + args, capture_output=True, text=True)
    out = p.stdout.strip()
    get = lambda name: int(out.split(name + "=")[1].split()[0]) if name + "=" in out else None
    return get("T"), get("cost"), out + p.stderr.strip()


def penalty_of_step(old, new, t, others):
    """Penalty of the step t -> t+1 of our robots (old[i] -> new[i]) for the other robots' routes."""
    at = lambda r, s: r[min(s, len(r) - 1)]
    p = sum(1 for c in new for r in others if at(r, t + 1) == c)
    p += sum(1 for u, v in zip(old, new) if u != v for r in others if at(r, t) == v and at(r, t + 1) == u)
    return p


def min_penalty(w, h, grid, starts, goals, vertex, edge, T, others):
    """Minimal penalty over all solutions with makespan T (None if there is none)."""
    free = {(x, y) for y in range(h) for x in range(w) if grid[y][x] == "."}
    if any((s, 0) in vertex for s in starts):
        return None
    layer = {tuple(sorted(starts)): 0}
    for t in range(T):
        nxt = {}
        for state, cost in layer.items():
            for new in itertools.product(*([c] + neighbours(c, free) for c in state)):
                if len(set(new)) < len(new) or any((c, t + 1) in vertex for c in new):
                    continue
                if any(u != v and (u, v, t) in edge for u, v in zip(state, new)):
                    continue
                moved = {(u, v) for u, v in zip(state, new) if u != v}
                if any((v, u) in moved for u, v in moved):
                    continue
                key = tuple(sorted(new))
                c = cost + penalty_of_step(state, new, t, others)
                if c < nxt.get(key, 1 << 30):
                    nxt[key] = c
        layer = nxt
    goal_state = tuple(sorted(goals))
    if any(c in goals and t >= T for c, t in vertex):
        return None
    return layer.get(goal_state)


def routes_penalty(routes, others):
    T = len(routes[0]) - 1
    return sum(penalty_of_step([r[t] for r in routes], [r[t + 1] for r in routes], t, others) for t in range(T))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--makespan", type=int, default=0)
    ap.add_argument("--weights", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    exe = os.path.abspath(a.exe)
    work = tempfile.mkdtemp(prefix="test_flow_team_")
    rng = random.Random(a.seed)
    n = a.makespan or a.weights
    bad = solvable = goal_after = penalized = 0
    for i in range(n):
        w, h, grid, free, starts, goals, vertex, edge, after = random_instance(rng)
        goal_after += after
        mp, sc, cs = write_instance(work, w, h, grid, starts, goals, vertex, edge)
        routes_path = os.path.join(work, "g.routes")
        t_ref = min_makespan(w, h, grid, starts, goals, vertex, edge)
        t_ref = max(t_ref, 1) if t_ref != -1 else -1
        solvable += t_ref != -1
        k = str(len(starts))
        problems = []
        if a.makespan:
            for low in ("bs", "flow"):
                if os.path.exists(routes_path):
                    os.remove(routes_path)
                t, _, out = run(exe, [mp, sc, k, routes_path, cs, "--low", low])
                if t != t_ref:
                    problems.append(f"{low}: {out} brute T={t_ref}")
                elif t != -1:
                    T, _, routes = read_routes(routes_path)
                    errors = check(w, h, grid, starts, goals, T, routes, vertex, edge)
                    if errors:
                        problems.append(f"{low}: invalid routes {errors}")
        else:
            others = []
            for _ in range(rng.randint(1, 3)):
                r = [rng.choice(free)]
                for _ in range(rng.randint(0, 8)):
                    r.append(rng.choice([r[-1]] + neighbours(r[-1], free)))
                others.append(r)
            length = max(len(r) for r in others)
            others = [r + [r[-1]] * (length - len(r)) for r in others]
            others_path = os.path.join(work, "g.others")
            with open(others_path, "w", newline="\n") as f:
                f.write(f"{length - 1} {len(others)}\n")
                f.writelines(" ".join(f"{x},{y}" for x, y in r) + "\n" for r in others)
            if os.path.exists(routes_path):
                os.remove(routes_path)
            t, cost, out = run(exe, [mp, sc, k, routes_path, cs, "--low", "floww", "--others", others_path])
            if t != t_ref:
                problems.append(f"floww: {out} brute T={t_ref}")
            elif t != -1:
                T, _, routes = read_routes(routes_path)
                errors = check(w, h, grid, starts, goals, T, routes, vertex, edge)
                best = min_penalty(w, h, grid, starts, goals, vertex, edge, T, others)
                own = routes_penalty(routes, others)
                penalized += bool(best)
                if errors:
                    problems.append(f"floww: invalid routes {errors}")
                if not (cost == own == best):
                    problems.append(f"floww cost={cost}, penalty of its routes={own}, brute minimum={best}; "
                                    f"others={others}")
        if problems:
            bad += 1
            print(f"MISMATCH #{i} grid={grid} starts={starts} goals={goals} vertex={sorted(vertex)} "
                  f"edge={sorted(edge)}: {problems}", flush=True)
    print(f"{'makespan' if a.makespan else 'weights'}: {n} instances ({solvable} solvable, "
          f"{goal_after} with a goal constraint at T0..T0+2{f', {penalized} with a positive minimal penalty' if a.weights else ''}), seed={a.seed}")
    print(f"total={n} mismatches={bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
