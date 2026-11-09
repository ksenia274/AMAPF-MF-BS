# Why bspen solves fewer instances of 3a than floww (2026-11-04)

`python small_maps_diag.py small_maps_diag.csv` (raw output: small_maps_diag.log); t-start check: small_maps_tstart.csv.
All runs sequential, cbm with `--t-start lb` (the default since 8e4a4e5; stage 5.1 ran with T from 1).

Instances: the 6 of cbm_bench_5_1.csv (maps of 3a) solved by floww in 60 s and not by bspen (group floww_only),
and 10 solved by both in 5.1, on the same maps and modes (group both).

## Measured

### 1-2. bspen --diag, 600 s

| instance | group | floww T | bspen status | time, s | root key | last key | expanded (all at key) | max depth | replans | repeated sets |
|---|---|---|---|---|---|---|---|---|---|---|
| room-32-32-4 40 g5 s3 | floww_only | 28 | timeout | 600.4 | 28 | 28 | 28:234544 | 103 | 469095 | 1213 |
| maze-32-32-2 64 k4 s2 | floww_only | 70 | timeout | 600.1 | 70 | 70 | 70:17175 | 3469 | 34354 | 0 |
| maze-32-32-2 64 g5 s2 | floww_only | 96 | timeout | 600.2 | 96 | 96 | 96:84841 | 572 | 169694 | 0 |
| maze-32-32-2 64 g5 s3 | floww_only | 114 | timeout | 600.2 | 114 | 114 | 114:95309 | 374 | 186484 | 0 |
| room-64-64-8 128 g5 s1 | floww_only | 95 | solved | 13.0 | 95 | 95 | 95:701 | 225 | 1428 | 10 |
| room-64-64-8 128 g5 s3 | floww_only | 102 | solved | 131.2 | 102 | 102 | 102:6707 | 279 | 13440 | 3807 |
| room-32-32-4 40 g5 s1 | both | 37 | solved | 0.1 | 37 | 37 | 37:9 | 9 | 26 | 0 |
| room-32-32-4 40 g5 s2 | both | 44 | solved | 0.1 | 44 | 44 | 44:23 | 23 | 54 | 0 |
| maze-32-32-2 64 k4 s1 | both | 60 | timeout | 600.2 | 60 | 60 | 60:48919 | 509 | 97841 | 0 |
| maze-32-32-2 64 k4 s3 | both | 83 | solved | 6.9 | 83 | 83 | 83:392 | 392 | 788 | 0 |
| maze-32-32-2 64 g5 s1 | both | 107 | solved | 2.8 | 107 | 107 | 107:400 | 362 | 813 | 0 |
| maze-32-32-2 40 g5 s1 | both | 107 | solved | 0.5 | 107 | 107 | 107:54 | 46 | 116 | 0 |
| maze-32-32-2 40 g5 s2 | both | 96 | timeout | 600.3 | 96 | 96 | 96:116502 | 132 | 233012 | 0 |
| room-64-64-8 64 g5 s1 | both | 95 | solved | 0.7 | 95 | 95 | 95:17 | 17 | 47 | 0 |
| room-64-64-8 64 g5 s3 | both | 102 | solved | 0.6 | 102 | 102 | 102:27 | 26 | 67 | 0 |
| room-64-64-8 128 g5 s2 | both | 85 | solved | 3.2 | 85 | 85 | 85:155 | 145 | 336 | 0 |

In all 16 instances the root key already equals the makespan of floww and every expanded node has that key
(expanded_by_key has one entry): no plateau below the answer, bspen stays at the key of the answer and does not
find a conflict-free node there.

Status changed against 5.1 (60 s, T from 1): room-64-64-8 128 g5 s1 and s3 are solved now (13 s, 131 s);
maze-32-32-2 64 k4 s1 and 40 g5 s2 (solved in 5.1) are not solved in 600 s. Check with both starts:

| instance | --t-start | limit, s | status | time, s | expanded | replans | root conflict pairs | max depth |
|---|---|---|---|---|---|---|---|---|
| maze-32-32-2 64 k4 s1 | 1 | 60 | solved | 33.5 | 2257 | 4518 | 35 | 610 |
| maze-32-32-2 64 k4 s1 | lb | 60 | timeout | 60.0 | 5068 | 10140 | 33 | 375 |
| maze-32-32-2 40 g5 s2 | 1 | 60 | solved | 1.0 | 174 | 356 | 43 | 44 |
| maze-32-32-2 40 g5 s2 | lb | 60 | timeout | 60.0 | 12009 | 24026 | 38 | 116 |
| room-64-64-8 128 g5 s1 | 1 | 600 | timeout | 600.1 | 32702 | 65430 | 181 | 366 |
| room-64-64-8 128 g5 s3 | 1 | 600 | timeout | 600.1 | 26716 | 53458 | 185 | 260 |

room-64-64-8 128 g5 with lb: see the table above (solved). The makespan is the same with both starts; only the
routes of the low level, and with them the CT, differ.

### 3. Penalty of the bspen routes minus the floww minimum on the same T

`--pen-gap S`: every replanning of the root and every S-th other one is checked by floww with the same constraints
and routes of the other teams (S = ceil(replans of bspen in 5.1 / 200)); 60 s, floww time not counted. Penalty =
weights of floww: (a) per other robot in the cell at t >= 1 (waits included), (b) per opposite move of another
robot. pen_check_failed = 0 everywhere (floww always found a flow at the T of bspen), minimum gap 0 everywhere.

| instance | group | S | checks | gap mean | gap max | share gap > 0 | bspen pen mean | min pen mean | root: checks | root: gap mean | root: gap max | root: share > 0 | root: bspen pen mean | root: min pen mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| room-32-32-4 40 g5 s3 | floww_only | 223 | 220 | 0.405 | 5 | 0.259 | 1.182 | 0.777 | 8 | 0.375 | 2 | 0.250 | 1.875 | 1.500 |
| maze-32-32-2 64 k4 s2 | floww_only | 22 | 226 | 7.504 | 48 | 0.929 | 13.066 | 5.562 | 4 | 11.000 | 22 | 0.750 | 15.750 | 4.750 |
| maze-32-32-2 64 g5 s2 | floww_only | 112 | 166 | 4.301 | 17 | 0.783 | 7.494 | 3.193 | 13 | 5.462 | 16 | 0.769 | 12.154 | 6.692 |
| maze-32-32-2 64 g5 s3 | floww_only | 68 | 283 | 4.283 | 24 | 0.986 | 5.385 | 1.102 | 13 | 2.538 | 10 | 0.692 | 6.308 | 3.769 |
| room-64-64-8 128 g5 s1 | floww_only | 31 | 72 | 5.069 | 21 | 0.903 | 7.653 | 2.583 | 26 | 4.038 | 21 | 0.769 | 9.615 | 5.577 |
| room-64-64-8 128 g5 s3 | floww_only | 26 | 257 | 3.043 | 32 | 0.798 | 4.868 | 1.825 | 26 | 3.346 | 32 | 0.615 | 8.115 | 4.769 |
| room-32-32-4 40 g5 s1 | both | 1 | 26 | 0.731 | 3 | 0.538 | 1.154 | 0.423 | 8 | 0.375 | 2 | 0.250 | 1.625 | 1.250 |
| room-32-32-4 40 g5 s2 | both | 1 | 54 | 1.741 | 5 | 0.778 | 1.944 | 0.204 | 8 | 1.375 | 4 | 0.625 | 1.875 | 0.500 |
| maze-32-32-2 64 k4 s1 | both | 23 | 420 | 4.531 | 48 | 0.919 | 6.714 | 2.183 | 4 | 7.000 | 18 | 0.750 | 9.000 | 2.000 |
| maze-32-32-2 64 k4 s3 | both | 5 | 161 | 7.043 | 41 | 0.801 | 8.571 | 1.528 | 4 | 3.500 | 8 | 0.750 | 5.750 | 2.250 |
| maze-32-32-2 64 g5 s1 | both | 9 | 102 | 8.431 | 32 | 0.912 | 9.716 | 1.284 | 13 | 5.231 | 14 | 0.846 | 8.692 | 3.462 |
| maze-32-32-2 40 g5 s1 | both | 1 | 116 | 3.078 | 12 | 0.845 | 3.707 | 0.629 | 8 | 2.875 | 9 | 0.750 | 6.750 | 3.875 |
| maze-32-32-2 40 g5 s2 | both | 2 | 10022 | 2.705 | 16 | 0.741 | 3.616 | 0.910 | 8 | 2.875 | 12 | 0.625 | 4.625 | 1.750 |
| room-64-64-8 64 g5 s1 | both | 1 | 47 | 1.404 | 6 | 0.660 | 2.298 | 0.894 | 13 | 0.923 | 3 | 0.462 | 3.077 | 2.154 |
| room-64-64-8 64 g5 s3 | both | 1 | 67 | 1.687 | 6 | 0.672 | 2.418 | 0.731 | 13 | 0.692 | 4 | 0.308 | 4.000 | 3.308 |
| room-64-64-8 128 g5 s2 | both | 5 | 88 | 2.886 | 25 | 0.807 | 4.216 | 1.330 | 26 | 2.615 | 25 | 0.654 | 5.808 | 3.192 |

Mean over floww_only (6): gap 4.10, share > 0 0.78, root gap 4.46, root share > 0 0.64, root conflict pairs bspen / floww 107.3 / 55.3.

Mean over both (10): gap 3.42, share > 0 0.77, root gap 2.75, root share > 0 0.60, root conflict pairs bspen / floww 47.4 / 22.5.

### 4. Root: conflicting pairs and cells of the first 20 conflicts

Free neighbours of the cell (swap: the smaller of the two): <= 2 corridor or dead end / 3 / 4 open; fewer than 20
when the root has fewer conflicts (one per cell or swapped edge and step). Map: share of all free cells.

| instance | group | pairs bspen | pairs floww | bspen <=2/3/4 | floww <=2/3/4 | map <=2/3/4 |
|---|---|---|---|---|---|---|
| room-32-32-4 40 g5 s3 | floww_only | 15 | 12 | 8/2/5 | 8/1/3 | 0.37/0.41/0.22 |
| maze-32-32-2 64 k4 s2 | floww_only | 70 | 26 | 1/9/10 | 9/7/4 | 0.17/0.74/0.10 |
| maze-32-32-2 64 g5 s2 | floww_only | 153 | 73 | 0/13/7 | 0/13/7 | 0.17/0.74/0.10 |
| maze-32-32-2 64 g5 s3 | floww_only | 84 | 56 | 8/10/2 | 6/11/3 | 0.17/0.74/0.10 |
| room-64-64-8 128 g5 s1 | floww_only | 164 | 77 | 9/1/10 | 9/1/10 | 0.09/0.37/0.53 |
| room-64-64-8 128 g5 s3 | floww_only | 158 | 88 | 6/1/13 | 7/1/12 | 0.09/0.37/0.53 |
| room-32-32-4 40 g5 s1 | both | 14 | 8 | 8/3/3 | 5/1/2 | 0.37/0.41/0.22 |
| room-32-32-4 40 g5 s2 | both | 20 | 7 | 5/10/5 | 4/1/2 | 0.37/0.41/0.22 |
| maze-32-32-2 64 k4 s1 | both | 33 | 9 | 2/14/4 | 0/9/0 | 0.17/0.74/0.10 |
| maze-32-32-2 64 k4 s3 | both | 23 | 8 | 3/15/2 | 0/6/2 | 0.17/0.74/0.10 |
| maze-32-32-2 64 g5 s1 | both | 122 | 61 | 1/15/4 | 2/15/3 | 0.17/0.74/0.10 |
| maze-32-32-2 40 g5 s1 | both | 49 | 23 | 3/16/1 | 2/14/4 | 0.17/0.74/0.10 |
| maze-32-32-2 40 g5 s2 | both | 38 | 13 | 0/16/4 | 1/9/3 | 0.17/0.74/0.10 |
| room-64-64-8 64 g5 s1 | both | 29 | 17 | 8/4/8 | 7/7/6 | 0.09/0.37/0.53 |
| room-64-64-8 64 g5 s3 | both | 26 | 19 | 7/1/12 | 6/2/12 | 0.09/0.37/0.53 |
| room-64-64-8 128 g5 s2 | both | 120 | 60 | 10/4/6 | 11/3/6 | 0.09/0.37/0.53 |

Pooled by map (share of conflicts, in brackets their number):

| map | bspen <=2/3/4 | floww <=2/3/4 | map <=2/3/4 |
|---|---|---|---|
| room-32-32-4 | 0.43/0.31/0.27 (49) | 0.63/0.11/0.26 (27) | 0.37/0.41/0.22 |
| maze-32-32-2 | 0.11/0.68/0.21 (160) | 0.15/0.65/0.20 (130) | 0.17/0.74/0.10 |
| room-64-64-8 | 0.40/0.11/0.49 (100) | 0.40/0.14/0.46 (100) | 0.09/0.37/0.53 |

## Interpretation

- Not a plateau: the root key is already optimal and the whole search runs at it. What fails is finding a
  conflict-free node among the nodes of one key, i.e. the order of expansion and the routes the low level gives.
- The penalty order of bspen is a heuristic, not a minimum: in 26-99% of the checked replannings its routes have a
  larger penalty than the floww minimum (mean gap 0.4-8.4, max 48), also in the root. In the root bspen leaves
  about twice as many conflicting pairs as floww. Each CT node then carries more conflicts to resolve.
- The gap does not separate the two groups (solved instances have similar gaps); the outcome is very sensitive to
  the routes: the same instance flips between solved in 1 s and unsolved in 600 s when only the first T of the low
  level changes (t-start 1 vs lb), in both directions. So 89 vs 94 is partly the systematic gap (more root
  conflicts) and partly this variance; 6 instances are a small sample (with lb 2 of them are solved and 2 of
  the 10 of group both are not, in 600 s).
- Cells: on the room maps the first conflicts are in cells with <= 2 free neighbours (the doors between rooms)
  far more often than such cells occur (room-64-64-8: 0.40 of the conflicts for both variants, 0.09 of the cells;
  room-32-32-4: 0.43 bspen, 0.63 floww, 0.37 of the cells). On maze-32-32-2 (corridors 2 wide, mostly 3
  neighbours) the shares follow the map. Where the conflicts are differs little between bspen and floww; how many
  differs about twofold.
- A likely source of the gap: bspen charges a penalty only on entering a cell (waits inside a bulk are free), while
  floww charges every step in a cell occupied by another robot, waits included; and the order is greedy over the
  augmenting paths, not a min-cost flow.

# Continuation (2026-11-04)

## Старт T

### Measured

`cbm_bench_cactus.py cbm_bench_cactus_tstart1.csv --maps maze-32-32-2,room-32-32-4 --variants bs,bspen --t-start 1`:
the instances of the cactus run (scen 1-10, N 20/40/60/80, teams of 5, 60 s, 8000 MB, the same stopping rule),
T of the low level from 1 instead of the lower bound. Start lb: cbm_bench_cactus.csv. 160 runs, 0.6 h.

| map | variant | solved, start lb | solved, start 1 | only lb | only 1 |
|---|---|---|---|---|---|
| maze-32-32-2 | bs | 17/40 | 17/40 | 0: - | 0: - |
| maze-32-32-2 | bspen | 19/40 | 19/40 | 2: N60 s1, N60 s8 | 2: N40 s2, N40 s9 |
| room-32-32-4 | bs | 20/40 | 18/40 | 3: N40 s5, N40 s8, N60 s1 | 1: N60 s2 |
| room-32-32-4 | bspen | 32/40 | 33/40 | 1: N80 s10 | 2: N80 s7, N80 s9 |

Makespan equal on all 82 runs solved with both starts; invalid solutions 0; no memory or killed. Every
instance solved with only one start was a timeout (not timeout_skipped) with the other start.

### Interpretation

- The start of T does not explain bspen < floww: the totals differ by at most 2 per map and variant, in both
  directions. The flips of single instances (up to 3 of 40 per variant) are the same sensitivity to the routes
  seen in "1-2" above, not a systematic effect.

## Откуда лишний штраф

### Measured

`small_maps_root.py small_maps_root.csv`; root only (`--max-nodes 1`), T from the lower bound. Penalty with the
weights of floww of every team against the teams planned before it (the routes the low level saw), summed over
the teams: wait = steps t >= 1 that stay in a cell where another robot is at t (ours entered earlier), enter =
steps t >= 1 into a cell with another robot, swap = opposite moves. Check: the bspen sum equals root pen mean x
root checks of `--pen-gap` (table 3) on all 16; root conflict pairs equal table 4.

| instance | group | bspen wait | bspen enter | bspen swap | bspen total | floww wait | floww enter | floww swap | floww total | pairs bspen / floww |
|---|---|---|---|---|---|---|---|---|---|---|
| room-32-32-4 40 g5 s3 | floww_only | 4 | 6 | 5 | 15 | 1 | 6 | 5 | 12 | 15 / 12 |
| maze-32-32-2 64 k4 s2 | floww_only | 21 | 34 | 8 | 63 | 1 | 10 | 1 | 12 | 70 / 26 |
| maze-32-32-2 64 g5 s2 | floww_only | 46 | 90 | 22 | 158 | 3 | 57 | 14 | 74 | 153 / 73 |
| maze-32-32-2 64 g5 s3 | floww_only | 22 | 46 | 14 | 82 | 0 | 45 | 10 | 55 | 84 / 56 |
| room-64-64-8 128 g5 s1 | floww_only | 33 | 169 | 48 | 250 | 1 | 108 | 23 | 132 | 164 / 77 |
| room-64-64-8 128 g5 s3 | floww_only | 16 | 148 | 47 | 211 | 2 | 79 | 27 | 108 | 158 / 88 |
| room-32-32-4 40 g5 s1 | both | 0 | 8 | 5 | 13 | 0 | 6 | 2 | 8 | 14 / 8 |
| room-32-32-4 40 g5 s2 | both | 6 | 8 | 1 | 15 | 0 | 3 | 2 | 5 | 20 / 7 |
| maze-32-32-2 64 k4 s1 | both | 6 | 21 | 9 | 36 | 1 | 7 | 1 | 9 | 33 / 9 |
| maze-32-32-2 64 k4 s3 | both | 11 | 7 | 5 | 23 | 0 | 3 | 5 | 8 | 23 / 8 |
| maze-32-32-2 64 g5 s1 | both | 29 | 63 | 21 | 113 | 1 | 38 | 11 | 50 | 122 / 61 |
| maze-32-32-2 40 g5 s1 | both | 6 | 36 | 12 | 54 | 0 | 22 | 7 | 29 | 49 / 23 |
| maze-32-32-2 40 g5 s2 | both | 21 | 12 | 4 | 37 | 0 | 7 | 3 | 10 | 38 / 13 |
| room-64-64-8 64 g5 s1 | both | 4 | 30 | 6 | 40 | 0 | 13 | 4 | 17 | 29 / 17 |
| room-64-64-8 64 g5 s3 | both | 3 | 41 | 8 | 52 | 0 | 37 | 5 | 42 | 26 / 19 |
| room-64-64-8 128 g5 s2 | both | 8 | 102 | 41 | 151 | 1 | 37 | 21 | 59 | 120 / 60 |
| **sum floww_only** | | 142 | 493 | 144 | 779 | 8 | 305 | 80 | 393 | |
| **sum both** | | 94 | 328 | 112 | 534 | 3 | 173 | 61 | 237 | |
| **sum all** | | 236 | 821 | 256 | 1313 | 11 | 478 | 141 | 630 | |

Excess of bspen over floww, all 16: wait 225, enter 343, swap 115 (of 683: 0.33, 0.50, 0.17).

### Interpretation

- The wait part is almost absent in floww (11 over 16 instances) and is 236 in bspen: Bulk Search charges
  the penalty only on entering a bulk, so staying in a cell that another robot reaches later is free for it.
  That is 33% of the excess. The rest is entries (50%) and swaps (17%): the
  greedy order over augmenting paths does not reach the minimum even for the penalties it does see.
- By map (share of the excess wait / enter / swap): maze-32-32-2 0.49 / 0.38 / 0.13 (wait the largest part in 5
  of 8 instances), room-32-32-4 0.50 / 0.39 / 0.11 (small numbers), room-64-64-8 0.17 / 0.62 / 0.20 (entries
  dominate in all 5).

## Корень от floww

### Measured

`cbm --low bspen --root-low floww`: the K calls of the root by floww, every other replanning by bspen; same
script, 60 s, T from the lower bound. Base = plain bspen in the same run (60 s). Replans include the K calls of
the root; time includes the floww root.

| instance | group | base | base: s | base: expanded | base: replans | root floww | s | expanded | generated | replans | root pairs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| room-32-32-4 40 g5 s3 | floww_only | timeout | 60.0 | 22711 | 45430 | solved | 0.2 | 23 | 47 | 54 | 12 |
| maze-32-32-2 64 k4 s2 | floww_only | timeout | 60.0 | 2395 | 4793 | timeout | 60.0 | 2097 | 4195 | 4198 | 26 |
| maze-32-32-2 64 g5 s2 | floww_only | timeout | 60.0 | 8176 | 16364 | timeout | 60.0 | 8681 | 17360 | 17373 | 73 |
| maze-32-32-2 64 g5 s3 | floww_only | timeout | 60.0 | 9105 | 18034 | timeout | 60.0 | 9274 | 18549 | 18561 | 56 |
| room-64-64-8 128 g5 s1 | floww_only | solved | 13.2 | 701 | 1428 | timeout | 60.0 | 2597 | 5193 | 5219 | 77 |
| room-64-64-8 128 g5 s3 | floww_only | timeout | 60.0 | 2999 | 6024 | solved | 24.2 | 518 | 1037 | 1062 | 88 |
| room-32-32-4 40 g5 s1 | both | solved | 0.1 | 9 | 26 | solved | 0.3 | 21 | 43 | 50 | 8 |
| room-32-32-4 40 g5 s2 | both | solved | 0.1 | 23 | 54 | solved | 0.3 | 25 | 51 | 58 | 7 |
| maze-32-32-2 64 k4 s1 | both | timeout | 60.0 | 5182 | 10367 | solved | 6.8 | 396 | 793 | 796 | 9 |
| maze-32-32-2 64 k4 s3 | both | solved | 6.4 | 392 | 788 | solved | 3.9 | 31 | 63 | 66 | 8 |
| maze-32-32-2 64 g5 s1 | both | solved | 2.9 | 400 | 813 | timeout | 60.0 | 7545 | 15089 | 15102 | 61 |
| maze-32-32-2 40 g5 s1 | both | solved | 0.5 | 54 | 116 | solved | 2.8 | 92 | 185 | 192 | 23 |
| maze-32-32-2 40 g5 s2 | both | timeout | 60.0 | 11795 | 23597 | solved | 1.8 | 65 | 131 | 138 | 13 |
| room-64-64-8 64 g5 s1 | both | solved | 0.7 | 17 | 47 | solved | 9.0 | 21 | 43 | 55 | 17 |
| room-64-64-8 64 g5 s3 | both | solved | 0.6 | 27 | 67 | timeout | 60.0 | 3302 | 6603 | 6616 | 19 |
| room-64-64-8 128 g5 s2 | both | solved | 3.3 | 155 | 336 | solved | 15.8 | 291 | 583 | 608 | 60 |
| **solved floww_only** | | 1/6 | | | | 2/6 | | | | | |
| **solved both** | | 8/10 | | | | 8/10 | | | | | |

Makespan of every solved run equals floww: True. Root conflict pairs with --root-low floww equal those of floww
in all 16 (same root).

### Interpretation

- A floww root does not fix the six problem instances: 2 of 6 solved (room-32-32-4 40 s3, room-64-64-8 128 s3)
  instead of 1 (room-64-64-8 128 s1, now lost); the three maze-32-32-2 instances stay unsolved with about the same
  number of nodes as the base. Over all 16: 10 vs 9, with flips in both directions (group both: gains maze 64
  k4 s1 and 40 g5 s2, loses maze 64 g5 s1 and room-64-64-8 64 s3).
- So the root with half the conflicts is not enough: after the first replannings bspen again leaves routes with
  more penalty than floww (table 3: gap > 0 in most replannings, not only the root). The difference is in every
  replanning, and on maze about half of it is the wait part, which bspen does not see at all.

# 5.2а

## Stage 1: where the extra entries come from (2026-11-09)

### Measured

`small_maps_entries.py small_maps_entries.csv`: the 16 instances, root only (`--max-nodes 1`), T from the lower
bound; `root_late` of `cbm --diag` (lateEntries in cbm.cpp). Units: penalty units (other robots in the cell at
the step), as root_pen_enter / root_pen_wait above. Every team against the teams planned before it.

A stay = maximal run of steps e..x of a robot in one cell v (exit = x, the robot is in another cell at x+1 or
x = T). "Enter later at t'" = wait in the previous cell u over e..t'-1 instead, then stay in v from t' to x as
before. Allowed if it adds no penalty (no other robot in u over e..t'-1, no other robot moving v -> u at t'-1)
and no robot of the own team is in u then.

- Entry penalty at e: **structural** if some t' in (e, x] has no other robot in v and is allowed; otherwise
  **other**, split into: pass-through (x = e, the robot leaves v at the next step, so no later entry into the
  same stay exists), no penalty-free step in (e, x], u blocked (a penalty-free t' exists but waiting in u is not
  allowed).
- Wait penalty at s (robot in v at s-1 and s, another robot in v at s): **avoidable** if the first penalty-free
  step f > s of v satisfies f <= x and entering at f is allowed; otherwise: no penalty-free step until the exit,
  u blocked, or the stay is the start cell (no u).

bspen:

| instance | group | entry pen | structural | other | other: pass-through | other: no free step | other: u blocked | wait pen | avoidable | no free step | u blocked | start cell |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| room-32-32-4 40 g5 s3 | floww_only | 6 | 0 | 6 | 6 | 0 | 0 | 4 | 1 | 1 | 2 | 0 |
| maze-32-32-2 64 k4 s2 | floww_only | 34 | 0 | 34 | 34 | 0 | 0 | 21 | 1 | 0 | 20 | 0 |
| maze-32-32-2 64 g5 s2 | floww_only | 90 | 0 | 90 | 89 | 0 | 1 | 46 | 9 | 2 | 35 | 0 |
| maze-32-32-2 64 g5 s3 | floww_only | 46 | 0 | 46 | 46 | 0 | 0 | 22 | 2 | 0 | 20 | 0 |
| room-64-64-8 128 g5 s1 | floww_only | 169 | 0 | 169 | 169 | 0 | 0 | 33 | 4 | 2 | 27 | 0 |
| room-64-64-8 128 g5 s3 | floww_only | 148 | 0 | 148 | 148 | 0 | 0 | 16 | 3 | 0 | 13 | 0 |
| room-32-32-4 40 g5 s1 | both | 8 | 0 | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| room-32-32-4 40 g5 s2 | both | 8 | 0 | 8 | 8 | 0 | 0 | 6 | 3 | 0 | 3 | 0 |
| maze-32-32-2 64 k4 s1 | both | 21 | 0 | 21 | 21 | 0 | 0 | 6 | 0 | 1 | 5 | 0 |
| maze-32-32-2 64 k4 s3 | both | 7 | 0 | 7 | 7 | 0 | 0 | 11 | 2 | 0 | 9 | 0 |
| maze-32-32-2 64 g5 s1 | both | 63 | 0 | 63 | 62 | 0 | 1 | 29 | 2 | 1 | 26 | 0 |
| maze-32-32-2 40 g5 s1 | both | 36 | 0 | 36 | 36 | 0 | 0 | 6 | 0 | 0 | 6 | 0 |
| maze-32-32-2 40 g5 s2 | both | 12 | 0 | 12 | 12 | 0 | 0 | 21 | 2 | 1 | 18 | 0 |
| room-64-64-8 64 g5 s1 | both | 30 | 0 | 30 | 30 | 0 | 0 | 4 | 1 | 1 | 2 | 0 |
| room-64-64-8 64 g5 s3 | both | 41 | 0 | 41 | 41 | 0 | 0 | 3 | 0 | 0 | 3 | 0 |
| room-64-64-8 128 g5 s2 | both | 102 | 1 | 101 | 101 | 0 | 0 | 8 | 2 | 2 | 4 | 0 |
| **sum, bspen** | | 821 | 1 | 820 | 818 | 0 | 2 | 236 | 32 | 11 | 193 | 0 |
| **sum, floww** | | 478 | 0 | 478 | 478 | 0 | 0 | 11 | 0 | 11 | 0 | 0 |

Checks (in the script, all 16, both low levels): structural + other = all entry penalties; the parts of the
waits add up; the totals equal root_pen_enter / root_pen_wait of cbm (and the table "Откуда лишний штраф").
Per-instance floww numbers: small_maps_entries.csv.

### Interpretation

- A late entry without a shift of the tail removes 1 of 821 entry penalty units and 14% of the extra waits (32
  of 236 wait penalty units); alternatives with a shift were not checked.
- By the definition (entry later into the same stay, same exit) a pass-through (e = x) has an empty (e, x], so the
  818 pass-throughs are "other" by definition, not because a later crossing was checked and found impossible.
  Waiting in u and crossing v later with the rest of the route shifted was not checked, so these numbers do not
  say how much bscut can change the entries.

## Stage 2: low level bscut (2026-11-10)

`--low bscut [--cut penal|all]` in cbm and bs_team (bs_team.hpp, `setCut`). bs and bspen are unchanged (see the
regression below).

- Same penalties as floww / bspen: (cell, step) with a robot of another team; an opposite move u -> v at t while
  another robot moves v -> u at t.
- Soft cuts of the waiting chains: `penal` (default) around every step t >= 1 with another robot in the cell (each
  such step is a piece of its own, the steps between them one piece); `all` at every step. A soft cut leaves the
  edge usable; hard blocks (flow, vertex constraints) stay as in Bulk Search. No soft cuts after a taken goal (that
  time is occupied by the team anyway) and none at the last step of the horizon.
- Pieces of one cell follow each other without a block; waiting across a soft cut is an explicit transition
  (wait into the next piece) that costs the robots in the cell at the new step.
- Entry into a piece of a neighbour: the earliest one, and, if it has an opposite move, also the earliest one in
  the same piece without (the detour of forbiddenMoves, soft). With `all` a piece is one step, so the second entry
  never exists there; the later pieces get their own earliest entry.
- OPEN as bspen: accumulated penalty, then the key of Bulk Search. A piece is expanded at its first extraction; as
  in Bulk Search, an earlier entry into a partly visited piece expands only its unvisited prefix (needed for the
  minimal T; no node is expanded twice). No (step, penalty) pairs.
- addPathEdges unchanged: a forward step inside one cell (the transition) is filled as a wait chain.

Deviations / fixes found by the checks:
- After a soft cut b the next piece is entered at max(b+1, first move from the source interval); b+1 alone gave
  an entry at the step of the source node (no move), and the flow broke.
- bscut (mostly `all`) gives swaps of two robots of one team on an edge (a valid flow without the edge gadget).
  As in cbm (removeSwapsInTeam) they are replaced by two waits; the function moved to bs_team.hpp (removeSwaps)
  and bs_team uses it too (prints the number on stderr). Same T, same cells per step, no new moves, so constraints
  and penalties can only stay or drop. bs and bspen made none in the tests below.

### Measured

| check | bs | bspen | bscut penal | bscut all |
|---|---|---|---|---|
| 2.1: minimal T = brute force, 1000 instances (`test_flow_team.py --makespan 1000`), validator | 0 / 1000 | 0 / 1000 | 0 / 1000 | 0 / 1000 |
| 2.2: with other robots (`--weights 1000`): T = brute force, validator, penalty >= minimum | | 0 / 1000 | 0 / 1000 | 0 / 1000 |
| penalty = minimum (floww), share of the 664 solved | | 0.742 | 0.834 | 0.839 |
| mean excess over the minimum (max) | | 0.684 (10) | 0.364 (9) | 0.352 (9) |
| 2.3: CBM vs brute force, 3000 instances: wrong | 0 | 0 | 0 | 0 |
| 2.3: node limit 5000 hit on a solvable instance | 14 | 12 | 10 | 9 |

- `--makespan` has no other robots, so `penal` cuts nothing there; the T of `penal` with cuts is checked by
  `--weights` (T = brute force there too) and by CBM (others = the other teams).
- floww `--weights 1000`: 0 mismatches (cost = penalty of its routes = brute minimum), as before.
- Node limit: CBM stops at 5000 CT nodes without an answer (not a wrong answer); the same instances for bs and
  bspen with the old cbm.exe.
- Regression against the exe of 2d4b024 (built from HEAD): `test_flow_team.py --makespan 1000 --lows bs,bspen` and
  `--weights 1000 --low bspen`: same summary lines; `compare_cbm.py --random 3000` for bs and bspen: same output
  (same limit instances, same CT node median / max, same pruned children); `compare_cbm_exe.py OLD NEW --low bspen`
  and `--low bs` (the 16 instances, 3000 CT nodes, all fields except timings): 16 / 16 equal for both;
  `compare_exe.py OLD NEW --quick` (bs_team, bs: T, expansions, routes): 14 / 14 equal.

### Interpretation

- Both modes keep the minimal T and valid routes. On small instances bscut reaches the minimal penalty more often
  than bspen (0.83-0.84 vs 0.74) and halves the mean excess; `all` and `penal` hardly differ there, i.e. on these
  instances the bulks hide little beyond the penalized steps. Whether this carries over to the 16 instances is
  stage 3.
