# Experiments for direction A

Built next to:
- AMAPF-MF-BS (Bulk Search, makespan): this repo, `../src/flow-bs.cpp`
- libMultiRobotPlanning (CBS-TA, sum of costs): https://github.com/whoenig/libMultiRobotPlanning

Files:
- `bs_single.cpp` - `#include "../src/flow-bs.cpp"` with its `main()` renamed: solves one instance
  (T = 1, 2, ..., flow is kept between T, as in the original). Prints `T=... expansions=... ms=...`.
  With a 4th argument writes the routes extracted from the flow: line `T K`, then K lines `x,y x,y ...`
  (T+1 positions, agent i = row i of the .scen). Extraction follows `edges` forward from every start;
  after the last stored edge in a taken goal (`idx >= timeAssigningGoalCell`) the agent stays there implicitly.
- `validate.py` - independent checker of such a routes file: starts, moves, final cells = goal set,
  vertex and swap conflicts; prints `last_arrival` and `sum_of_costs`, exit code 0 iff OK.
- `bs_trace.cpp` - copy of `flow-bs.cpp`, additions marked `// [TRACE]`. With `BS_TRACE=1` prints to stderr
  every augmenting path (raw and decoded: move / wait / in->out / CANCEL ...) and `edges`, `blocks`,
  `timeAssigningGoalCell` after it. Check it still matches the source: `diff --strip-trailing-cr ../src/flow-bs.cpp bs_trace.cpp`.
  Node (cell, idx): idx = 2t is "in"-copy of layer t, idx = 2t+1 is "out"-copy.
- `make_colored_yaml.py` - MovingAI map+scen -> colored MAPF YAML for cbs_ta
  (agent i goes to team i % K; potentialGoals = all goals of the team).
- `t/` - 1x5 corridor (`line*`) and cbs_ta instances `col_N_K.yaml` (random-32-32-10, scen 1) with results `out_N_K.yaml`.

## Build and run (Windows, from the repo root)

Older `libwinpthread-1.dll` (iverilog, gtkwave, swipl) stand earlier on PATH and make `cc1plus.exe` exit
silently with code 1. `build.ps1` puts MinGW first on PATH only while building and links statically,
so the .exe run with any PATH (the `-Wreturn-type` warning about the original main is harmless):
```
.\experiments\build.ps1
experiments/bs_single.exe MAP.map FILE.scen K [out.routes]
python experiments/validate.py MAP.map FILE.scen K out.routes
BS_TRACE=1 experiments/bs_trace.exe experiments/t/line.map experiments/t/line2.scen 2
python experiments/make_colored_yaml.py MAP.map FILE.scen N K out.yaml
```

## Checks

| instance | K | expected T | got |
|---|---|---|---|
| `t/line1.scen` (0 -> 4) | 1 | 4 | 4 |
| `t/line2.scen` (0,1 -> 3,4) | 2 | 3 | 3 |
| `t/line0.scen` (2 -> 2) | 1 | 1 | 1 |
| `Berlin_1_256-random-1.scen` | 256 | 51 (`data/estimates.txt`) | 51, ~2.7 s, 3 296 748 expansions |

Routes + `validate.py` (2026-10-20), all OK, no swap conflicts found:
- `t/line*`; empty-8-8, random-32-32-10, room-64-64-8, maze-128-128-2, den520d, Berlin_1_256 (scen 1, K up to 1000);
- all 25 scens, K = 1, 2, 4, ..., max: empty-8-8, empty-16-16, random-32-32-20, maze-32-32-2, room-32-32-4,
  one_corridor_25x25 (scen 1) - 1110 instances;
- every start/goal set on 1x5 (K=2), 2x3 (K=2,3), 3x3 (K=2), 2x4 (K=3) - 5157 instances.

`estimates.txt` holds lower bounds, so T > estimate is possible (room-64-64-8: 26 vs 25 for K=256, 17 vs 13 for K=1000).
The source has no explicit swap prohibition, so swaps are not excluded in principle - keep validating.
