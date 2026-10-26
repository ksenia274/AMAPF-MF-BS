#!/usr/bin/env python3
"""Reference minimal makespan for anonymous MAPF by BFS over joint positions (tiny grids only).

Usage: brute_force.py MAP.map FILE.scen K [CONSTRAINTS]   -> prints "T=<min makespan>" or "T=-1"

State at step t = set of occupied cells (agents are anonymous). Each agent waits or moves to a
4-neighbour; forbidden: two agents in one cell, two agents swapping along an edge, constraints.
Solved at step T if the set equals the goal set and no goal has a vertex constraint at a time >= T
(agents stay at their goals forever). T=0 is possible (starts = goals); bs_single starts from T=1.

CONSTRAINTS file (shared with bs_team and validate.py), '#' starts a comment:
  v x y t            the team may not be in (x,y) at step t
  e x1 y1 x2 y2 t    the team may not move (x1,y1) -> (x2,y2) between steps t and t+1
"""
import itertools
import sys


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


def read_constraints(path):
    """Returns ({(cell, t)}, {(from, to, t)})."""
    vertex, edge = set(), set()
    if path is None:
        return vertex, edge
    with open(path) as f:
        for line in f:
            p = line.split("#")[0].split()
            if not p:
                continue
            if p[0] == "v":
                vertex.add(((int(p[1]), int(p[2])), int(p[3])))
            elif p[0] == "e":
                edge.add(((int(p[1]), int(p[2])), (int(p[3]), int(p[4])), int(p[5])))
            else:
                raise ValueError(f"bad constraint line: {line!r}")
    return vertex, edge


def min_makespan(w, h, grid, starts, goals, vertex=(), edge=()):
    free = lambda c: 0 <= c[0] < w and 0 <= c[1] < h and grid[c[1]][c[0]] not in "@T"
    options = {}  # cell -> [cell itself, free neighbours]
    for y in range(h):
        for x in range(w):
            if free((x, y)):
                options[(x, y)] = [(x, y)] + [c for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if free(c)]
    vertex, edge = set(vertex), set(edge)
    last = max([t for _, t in vertex] + [t + 1 for _, _, t in edge] + [0])  # no constraints after this step
    goal_set = tuple(sorted(goals))
    last_at_goal = max([t for c, t in vertex if c in set(goals)] + [-1])

    layer = {tuple(sorted(starts))} if not any((s, 0) in vertex for s in starts) else set()
    t = 0
    while True:
        if goal_set in layer and last_at_goal < t:
            return t
        nxt = set()
        for state in layer:
            for new in itertools.product(*(options[c] for c in state)):
                if len(set(new)) < len(new):
                    continue  # vertex conflict
                if any((c, t + 1) in vertex for c in new):
                    continue
                if any(u != v and (u, v, t) in edge for u, v in zip(state, new)):
                    continue
                moved = {(u, v) for u, v in zip(state, new) if u != v}
                if any((v, u) in moved for u, v in moved):
                    continue  # swap conflict
                nxt.add(tuple(sorted(new)))
        # After the last constraint everybody may wait, so layers only grow; a fixpoint means no solution
        # (t > last also guarantees that the goal test above was not blocked by a goal constraint).
        if t > last and nxt == layer:
            return -1
        layer, t = nxt, t + 1


def main():
    map_path, scen_path, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
    w, h, grid = read_map(map_path)
    starts, goals = read_scen(scen_path, k)
    vertex, edge = read_constraints(sys.argv[4] if len(sys.argv) > 4 else None)
    print(f"T={min_makespan(w, h, grid, starts, goals, vertex, edge)}")


if __name__ == "__main__":
    main()
