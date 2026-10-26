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
  vertex and swap conflicts, optional constraints file (agents stay in their goals after T); prints `last_arrival` and `sum_of_costs`, exit code 0 iff OK.
- `bs_trace.cpp` - copy of `flow-bs.cpp`, additions marked `// [TRACE]`. With `BS_TRACE=1` prints to stderr
  every augmenting path (raw and decoded: move / wait / in->out / CANCEL ...) and `edges`, `blocks`,
  `timeAssigningGoalCell` after it. Check it still matches the source: `diff --strip-trailing-cr ../src/flow-bs.cpp bs_trace.cpp`.
  Node (cell, idx): idx = 2t is "in"-copy of layer t, idx = 2t+1 is "out"-copy.
- `bs_team.hpp` - the same search as a class without globals: `bs::Grid` (map, shared) and
  `bs::BulkSearchTeam` (one team: starts, goals, its own flow); `bs_team.cpp` - CLI with the interface of bs_single
  plus `bs_team MAP SCEN K [ROUTES|-] [CONSTRAINTS]`.
  Vertex constraint (v, t): `2t` goes to `blocks[v]` as a cut of the waiting chain (inserted when T > t);
  a goal with a constraint at t >= T can't be final (the agent stays there forever); a constraint at a start at t = 0
  means no solution. With constraints the waits in taken goals are stored explicitly (see the comment in bs_team.hpp):
  the original lets an agent leave its taken goal only at the earliest step, which is not enough with constraints.
  Edge constraint (u -> v, t) = move (u, 2t+1) -> (v, 2t+2): in getAllTimestepCostPairs an even entry y into v is the
  move (u, y-1) -> (v, y); if it is forbidden, the next allowed y+2, y+4, ... inside the same bulk of v is taken.
- `compare_exe.py EXE_A EXE_B` - regression on the step-1 set: T, expansions and routes must be equal
  (bs_single vs bs_team: 1124 instances, 0 mismatches).
- `brute_force.py` - reference minimal makespan by BFS over sets of occupied cells (tiny grids only),
  with optional constraints file (`v x y t`, `e x1 y1 x2 y2 t`); prints `T=...` (T=0 if starts = goals).
- `compare_brute.py EXE` - EXE vs brute_force.py on every start/goal set of 1x5, 2x3, 3x3, 2x4 grids
  (bs_single: 5157 instances, 0 mismatches); `--random N --vertex NV --edge NE` - random tiny instances
  with constraints, routes checked by validate.py (bs_team: vertex constraints 8000, edge and mixed 12000 instances, 0 mismatches).
- `flow_ref.cpp` - independent reference: plain max flow (Dinic) on the full time-expanded network, rebuilt for
  every T from a distance lower bound; no code shared with Bulk Search. `flow_ref MAP SCEN K` prints `T=.. ms=..`.
- `cbm.cpp` - CBM for colored MAPF with makespan: CBS over teams (agent i in team i % K), low level = BulkSearchTeam.
  Node: constraints + plan of every team (unchanged plans shared with the parent), key = max team T. Earliest conflict
  between different teams (vertex, then swap; teams that finished earlier stay in their goals); two children with a
  constraint for one team each; the team is replanned with T from the parent's key. Order: key, then fewer teams in
  conflicts, then the later node. Swaps inside a team are replaced by two waits + exchange of the route tails.
  `cbm MAP SCEN N K [ROUTES|-] [--time-limit SEC] [--max-nodes M]` prints T and the counters
  (nodes generated/expanded, low-level calls, low-level / high-level / total ms); T=-1 = limit hit.
- `compare_cbm.py CBM_EXE --random N --seed S` - cbm vs `brute_force.py --teams` on random tiny colored instances,
  routes checked by `validate.py --teams`.
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
python experiments/validate.py MAP.map FILE.scen K out.routes [CONSTRAINTS] [--teams NT]
experiments/cbm.exe MAP.map FILE.scen N K out.routes --time-limit 60
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

Step 2, bs_team with constraints (2026-10-21):
- optimality: `compare_brute.py bs_team.exe --random 2000 --vertex NV --edge NE --tmax TM --seed S` for
  (NV, NE, TM, S) = (2,0,8,2), (5,0,6,3), (10,0,10,4), (3,0,4,5), (0,5,8,11), (0,15,6,12), (3,6,8,13), (8,12,10,14),
  (2,3,4,15), (0,20,4,16): 20000 instances, T equal to brute force, all routes valid. The constraints change the
  optimal T in 46% (vertex 2), 6% (edge 5), 60% (3+6) and 83% (8+12) of the instances.
- the test catches errors: a mutant without the edge-constraint shift gives 141, without explicit goal waits 57
  mismatches on 1000 instances (vertex 3, edge 6, seed 13).
- large maps: 10 vertex + 10 edge constraints taken from positions and moves of the unconstrained solution,
  routes valid; cost of the explicit goal waits (one irrelevant constraint) and of the 20 constraints:

| map, K | no constraints | explicit goal waits | 20 constraints |
|---|---|---|---|
| random-32-32-10, 64 | T=12, 13 ms | T=12, 15 ms | T=13, 22 ms |
| room-64-64-8, 256 | T=26, 0.20 s | T=26, 0.28 s | T=26, 0.33 s |
| maze-128-128-2, 256 | T=252, 6.6 s | T=252, 20.5 s | T=252, 21.4 s |
| den520d, 1000 | T=45, 3.9 s | T=45, 5.1 s | T=45, 6.1 s |
| Berlin_1_256, 256 | T=51, 2.7 s | T=51, 3.0 s | T=51, 3.3 s |
| Berlin_1_256, 1000 | T=61, 7.2 s | T=61, 8.3 s | T=62, 11.6 s |

Step 3 (2026-10-27):
- early leaving of a taken goal without constraints (see bs_team.hpp): bs_single equals flow_ref on all 25 scens,
  K = 1, 2, 4, ..., max of empty-8-8, -16-16, -32-32, -48-48, random-32-32-10/20, random-64-64-10/20, maze-32-32-2/4,
  room-32-32-4, room-64-64-8/16: 3225 instances, 0 mismatches (flow_ref up to 37 s per instance).
- `brute_force.py --teams`: unchanged for one team (compare_brute.py, 5157 instances, 0 mismatches).
- cbm vs colored brute force (`compare_cbm.py --random 1500 --seed 2/3 --max-nodes 20000`): 3000 instances,
  0 mismatches, routes valid; 10 hit the node limit. Rerun with larger limits: 3 found the optimal T after 15k, 45k,
  296k CT nodes; one (brute T=11, 3x4 grid, 4 agents, 3 teams) not solved within 3M nodes / 123 s.
  CBS with the makespan key has large plateaus: conflicts of teams below the maximum do not raise the key.
- larger maps (scen 1, 60 s): random-32-32-10 N=64 K=4: T=24, 109 nodes, 0.8 s; N=128 K=8: T=22, 2297 nodes, 15 s
  (both valid). room-64-64-8 N=128 K=4, den520d N=256 K=4, Berlin_1_256 N=256 K=8 and N=512 K=4: time limit,
  the low level takes ~99% of the time (~1 s per replanning on Berlin).
