#!/usr/bin/env python3
"""Make a colored-MAPF instance for libMultiRobotPlanning/cbs_ta from MovingAI files.

Usage: make_colored_yaml.py MAP.map FILE.scen N_AGENTS N_TEAMS OUT.yaml

The first N_AGENTS rows of the .scen file are taken. Agent i goes to team i % N_TEAMS.
Each agent gets all goals of its team as potentialGoals, so CBS-TA solves
colored MAPF (= TAPF with |goals| = |agents| per team) optimally w.r.t. sum of costs.
"""
import sys


def main():
    map_path, scen_path, n, k, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    with open(map_path) as f:
        lines = f.read().split("\n")
    h = int(lines[1].split()[1])
    w = int(lines[2].split()[1])
    grid = lines[4:4 + h]
    obstacles = [(x, y) for y in range(h) for x in range(w) if grid[y][x] in "@T"]

    rows = []
    with open(scen_path) as f:
        next(f)  # "version 1"
        for line in f:
            p = line.split()
            if len(p) < 9:
                continue
            rows.append(((int(p[4]), int(p[5])), (int(p[6]), int(p[7]))))
            if len(rows) == n:
                break

    team_goals = [[g for i, (_, g) in enumerate(rows) if i % k == t] for t in range(k)]
    with open(out, "w", newline="\n") as f:
        f.write(f"map:\n  dimensions: [{w}, {h}]\n  obstacles:\n")
        for x, y in obstacles:
            f.write(f"    - [{x}, {y}]\n")
        f.write("agents:\n")
        for i, (s, _) in enumerate(rows):
            f.write(f"  - name: agent{i}\n    team: {i % k}\n    start: [{s[0]}, {s[1]}]\n    potentialGoals:\n")
            for g in team_goals[i % k]:
                f.write(f"      - [{g[0]}, {g[1]}]\n")


if __name__ == "__main__":
    main()
