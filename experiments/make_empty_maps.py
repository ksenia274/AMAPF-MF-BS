#!/usr/bin/env python3
"""Our own maps empty-128-128 and empty-256-256 (not in the MovingAI set) with random scens in maps/.

Usage: make_empty_maps.py [--agents 1000] [--scens 3]
Scen as MovingAI random scens: starts pairwise distinct, goals pairwise distinct, all in the largest connected
component (4-neighbour; an empty map is one component), chosen uniformly by random.Random(<size> * 100 + s).
The last column is the shortest 4-neighbour path length, on an empty map the Manhattan distance (MovingAI writes the
octile length; our solvers ignore it), the first one the bucket = length // 4.
"""
import os
import random
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))


def largest_component(grid, w, h):
    seen, best = set(), []
    for y in range(h):
        for x in range(w):
            if grid[y][x] != "." or (x, y) in seen:
                continue
            comp, q = [], deque([(x, y)])
            seen.add((x, y))
            while q:
                c = q.popleft()
                comp.append(c)
                for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)):
                    if 0 <= n[0] < w and 0 <= n[1] < h and grid[n[1]][n[0]] == "." and n not in seen:
                        seen.add(n)
                        q.append(n)
            if len(comp) > len(best):
                best = comp
    return best


def main():
    args = sys.argv[1:]
    agents = int(args[args.index("--agents") + 1]) if "--agents" in args else 1000
    scens = int(args[args.index("--scens") + 1]) if "--scens" in args else 3
    out = os.path.join(HERE, "maps")
    os.makedirs(out, exist_ok=True)
    for size in (128, 256):
        name = f"empty-{size}-{size}"
        grid = ["." * size] * size
        with open(os.path.join(out, name + ".map"), "w", newline="\n") as f:
            f.write(f"type octile\nheight {size}\nwidth {size}\nmap\n" + "\n".join(grid) + "\n")
        comp = largest_component(grid, size, size)
        for s in range(1, scens + 1):
            rng = random.Random(size * 100 + s)
            starts, goals = rng.sample(comp, agents), rng.sample(comp, agents)
            with open(os.path.join(out, f"{name}-random-{s}.scen"), "w", newline="\n") as f:
                f.write("version 1\n")
                for (sx, sy), (gx, gy) in zip(starts, goals):
                    d = abs(sx - gx) + abs(sy - gy)
                    f.write(f"{d // 4}\t{name}.map\t{size}\t{size}\t{sx}\t{sy}\t{gx}\t{gy}\t{d}\n")


if __name__ == "__main__":
    main()
