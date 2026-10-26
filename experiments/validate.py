#!/usr/bin/env python3
"""Check an anonymous MAPF solution independently of the solver.

Usage: validate.py MAP.map FILE.scen K ROUTES [CONSTRAINTS]

ROUTES (written by bs_single / bs_team): first line "T K", then K lines "x,y x,y ..." with T+1 positions;
agent i starts at the start of row i of the .scen. Goals are anonymous: the final cells must be
exactly the set of the K goals. Checked: starts, moves (wait or 4-neighbour, free cells),
goal assignment, vertex conflicts, swap (edge) conflicts, and the constraints (format of brute_force.py;
after step T every agent stays in its final cell forever). Exit code 0 iff no violations.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brute_force import read_constraints  # noqa: E402  (only the file format is shared)

MAX_SHOWN = 5


def read_map(path):
    with open(path) as f:
        lines = f.read().split("\n")
    h = int(lines[1].split()[1])
    w = int(lines[2].split()[1])
    grid = [row.strip() for row in lines[4:4 + h]]
    return w, h, grid


def read_scen(path, k):
    starts, goals = [], []
    with open(path) as f:
        next(f)  # "version 1"
        for line in f:
            p = line.split()
            if len(p) < 9:
                continue
            starts.append((int(p[4]), int(p[5])))
            goals.append((int(p[6]), int(p[7])))
            if len(starts) == k:
                break
    return starts, goals


def read_routes(path):
    with open(path) as f:
        T, k = map(int, f.readline().split())
        routes = [[tuple(map(int, xy.split(","))) for xy in line.split()] for line in f if line.strip()]
    return T, k, routes


def check(w, h, grid, starts, goals, T, routes, vertex=(), edge=()):
    """Returns {kind: [messages]}; empty if the solution is valid."""
    errors = {}

    def err(kind, msg):
        errors.setdefault(kind, []).append(msg)

    k = len(starts)
    if len(routes) != k:
        err("format", f"expected {k} routes, got {len(routes)}")
    free = lambda c: 0 <= c[0] < w and 0 <= c[1] < h and grid[c[1]][c[0]] not in "@T"
    for a, r in enumerate(routes):
        if len(r) != T + 1:
            err("format", f"agent {a}: {len(r)} positions instead of T+1={T + 1}")
            continue
        if a < k and r[0] != starts[a]:
            err("start", f"agent {a}: starts at {r[0]}, .scen says {starts[a]}")
        for t, c in enumerate(r):
            if not free(c):
                err("obstacle", f"agent {a}: cell {c} at t={t} is not a free cell")
            if t and abs(c[0] - r[t - 1][0]) + abs(c[1] - r[t - 1][1]) > 1:
                err("jump", f"agent {a}: {r[t - 1]} -> {c} at t={t - 1}->{t} is not a wait or a move")
    if errors:  # positions are unusable, stop before conflict checks
        return errors

    if Counter(r[-1] for r in routes) != Counter(goals):
        missing = Counter(goals) - Counter(r[-1] for r in routes)
        err("goals", f"final cells are not the goal set; goals without an agent: {sorted(missing)[:MAX_SHOWN]}")
    for t in range(T + 1):
        at = {}
        for a, r in enumerate(routes):
            if r[t] in at:
                err("vertex", f"agents {at[r[t]]} and {a} both in {r[t]} at t={t}")
            at[r[t]] = a
    for t in range(T):
        moves = {}
        for a, r in enumerate(routes):
            if r[t] != r[t + 1]:
                moves[(r[t], r[t + 1])] = a
        for (u, v), a in moves.items():
            b = moves.get((v, u))
            if b is not None and a < b:
                err("swap", f"agents {a} and {b} swap {u} <-> {v} at t={t}->{t + 1}")
    for c, t in sorted(vertex, key=lambda p: p[1]):
        for a, r in enumerate(routes):
            if r[min(t, T)] == c:
                err("constraint", f"agent {a} is in {c} at t={t}{' (stays there after T)' if t > T else ''}")
    for u, v, t in sorted(edge, key=lambda p: p[2]):
        for a, r in enumerate(routes):
            if t < T and r[t] == u and r[t + 1] == v:
                err("constraint", f"agent {a} moves {u} -> {v} at t={t}->{t + 1}")
    return errors


def main():
    map_path, scen_path, k, routes_path = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    w, h, grid = read_map(map_path)
    starts, goals = read_scen(scen_path, k)
    vertex, edge = read_constraints(sys.argv[5] if len(sys.argv) > 5 else None)
    T, k_routes, routes = read_routes(routes_path)
    errors = check(w, h, grid, starts, goals, T, routes, vertex, edge)
    if k_routes != k:
        errors.setdefault("format", []).append(f"header says {k_routes} agents, expected {k}")

    # Arrival time of an agent: first step after which it never leaves its final cell.
    arrival = [max((t + 1 for t in range(len(r) - 1) if r[t] != r[-1]), default=0) for r in routes]
    print(f"T={T} agents={len(routes)} last_arrival={max(arrival, default=0)} sum_of_costs={sum(arrival)}")
    if not errors:
        print("OK")
        sys.exit(0)
    for kind, msgs in errors.items():
        print(f"{kind}: {len(msgs)}")
        for m in msgs[:MAX_SHOWN]:
            print("   ", m)
    sys.exit(1)


if __name__ == "__main__":
    main()
