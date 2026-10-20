# Experiments for direction A

Built next to:
- AMAPF-MF-BS (Bulk Search, makespan): this repo, `../src/flow-bs.cpp`
- libMultiRobotPlanning (CBS-TA, sum of costs): https://github.com/whoenig/libMultiRobotPlanning

Files:
- `bs_single.cpp` - `#include "../src/flow-bs.cpp"` with its `main()` renamed: solves one instance
  (T = 1, 2, ..., flow is kept between T, as in the original). Prints `T=... expansions=... ms=...`.
- `bs_trace.cpp` - copy of `flow-bs.cpp`, additions marked `// [TRACE]`. With `BS_TRACE=1` prints to stderr
  every augmenting path (raw and decoded: move / wait / in->out / CANCEL ...) and `edges`, `blocks`,
  `timeAssigningGoalCell` after it. Check it still matches the source: `diff --strip-trailing-cr ../src/flow-bs.cpp bs_trace.cpp`.
  Node (cell, idx): idx = 2t is "in"-copy of layer t, idx = 2t+1 is "out"-copy.
- `make_colored_yaml.py` - MovingAI map+scen -> colored MAPF YAML for cbs_ta
  (agent i goes to team i % K; potentialGoals = all goals of the team).
- `t/` - 1x5 corridor (`line*`) and cbs_ta instances `col_N_K.yaml` (random-32-32-10, scen 1) with results `out_N_K.yaml`.

## Build and run (Windows, from the repo root)

Older `libwinpthread-1.dll` (iverilog, gtkwave, swipl) stand earlier on PATH and make `cc1plus.exe` exit
silently with code 1, so put MinGW first:
```
export PATH=/c/ProgramData/mingw64/mingw64/bin:$PATH            # bash
$env:PATH = "C:\ProgramData\mingw64\mingw64\bin;" + $env:PATH   # PowerShell

g++ -O3 -o experiments/bs_single.exe experiments/bs_single.cpp
g++ -O3 -o experiments/bs_trace.exe  experiments/bs_trace.cpp
experiments/bs_single.exe MAP.map FILE.scen K
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
