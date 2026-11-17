#!/usr/bin/env python3
"""bs::teamMatchBound on large teams: bound_match of bs_team.exe --bounds-only against an independent computation
(BFS in Python, binary search over D, perfect matching checked by scipy.optimize.linear_sum_assignment).

Usage: check_match_bound.py [BS_TEAM_EXE]
Instances: the first K agents of random scen 1..3 of every map of the cactus run, K = 5, 16, 32, 64 (one team).
"""
import collections
import os
import subprocess
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

from cbm_bench import load_grid, map_and_scen

HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = ["empty-32-32", "random-32-32-10", "room-32-32-4", "maze-32-32-2", "random-64-64-10", "room-64-64-8",
        "warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]


def bfs(grid, w, h, src):
    dist = np.full((h, w), -1, dtype=np.int64)
    dist[src[1], src[0]] = 0
    q = collections.deque([src])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and dist[ny, nx] < 0 and grid[ny][nx] not in "@T":
                dist[ny, nx] = dist[y, x] + 1
                q.append((nx, ny))
    return dist


def bound(d):
    """d[i][j] = distance robot i -> goal j (-1 unreachable)."""
    values = sorted({int(x) for x in d.ravel() if x >= 0})

    def perfect(D):
        cost = np.where((d >= 0) & (d <= D), 0, 1)
        r, c = linear_sum_assignment(cost)
        return cost[r, c].sum() == 0
    if not values or not perfect(values[-1]):
        return 10 ** 9
    lo, hi = 0, len(values) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if perfect(values[mid]) else (mid + 1, hi)
    return values[lo]


def main():
    exe = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "bs_team.exe"))
    bad = total = above = 0
    for m in MAPS:
        for s in (1, 2, 3):
            mp, sc = map_and_scen(m, s)
            grid, w, h = load_grid(mp)
            agents = [line.split() for line in open(sc).read().splitlines()[1:]]
            for k in (5, 16, 32, 64):
                out = subprocess.run([exe, mp, sc, str(k), "--bounds-only"], capture_output=True, text=True).stderr
                lb = int(out.split("bound_lb=")[1].split()[0])
                got = int(out.split("bound_match=")[1].split()[0])
                starts = [(int(a[4]), int(a[5])) for a in agents[:k]]
                dists = [bfs(grid, w, h, (int(a[6]), int(a[7]))) for a in agents[:k]]
                d = np.array([[dists[j][y, x] for j in range(k)] for x, y in starts])
                ref = bound(d)
                total += 1
                above += got > lb
                if got != ref or got < lb:
                    bad += 1
                    print(f"MISMATCH {m} scen {s} K={k}: lb {lb}, bs_team {got}, python {ref}")
    print(f"total={total} mismatches={bad}; bound_match > lb on {above}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
