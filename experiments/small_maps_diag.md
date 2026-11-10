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

Unsolved in `--weights 1000`: 336 of 1000 instances are unsolvable at any T (brute force reaches a fixpoint of its
layers, T = -1; no time or T limit in the brute force or in bs_team): 115 a start on a vertex constraint at t = 0,
40 starts and goals in different components, 181 because of the other constraints. Every low level returned T = -1
on exactly these 336 (0 mismatches), so the 664 are all solvable instances, not a limit.

### Known approximations of bscut

- (a) A piece is expanded once, at its first extraction; a later, cheaper path into its already visited beginning
  is not expanded (as in Bulk Search, only the unvisited prefix of an earlier entry is).
- (b) Negative costs of cancelling are not counted: cancelling a move or a wait of the own flow (a reverse
  residual edge) costs 0, not minus the penalty it removes; only entries and waits across soft cuts cost.
- (c) Swaps of two robots of one team on an edge are replaced by two waits (removeSwaps). Measured (replay of
  `--weights 1000`, seed 1, with a bs_team build that can skip the replacement): bscut penal 13 swaps in 13
  instances, bscut all 44 in 37, bspen 0; the penalty of the routes with and without the replacement is equal on
  all of them (never higher, never lower). In CBM (`compare_cbm.py --random 3000`) the replacement worked 43 238
  times for bscut penal and 348 360 for bscut all (0 for bs, bspen); not measured for the penalty there, by
  construction it can not grow (same cells at every step, only moves removed).

### Interpretation

- Both modes keep the minimal T and valid routes. On small instances bscut reaches the minimal penalty more often
  than bspen (0.83-0.84 vs 0.74) and halves the mean excess.
- `all` has no bulks at all and still leaves 16% of the instances above the minimum, so the rest of the excess
  comes not from the bulks but from the greedy search of one path at a time (approximations (a), (b)). `penal`
  (0.834) closes almost everything cutting can give (`all` 0.839).

## Stage 3: bscut in CBM on the 16 instances (2026-11-10)

`small_maps_cut.py small_maps_cut.csv`: the 16 instances of `small_maps_diag.csv`, variants bspen, bscut
(`--cut penal`), bscut all (`--cut all`), floww; T from the lower bound, `--time-limit 60 --mem-limit 8000`,
sequentially. Per variant one run with `--diag` (status, nodes, replans, time, root) and, for the BS variants, one
run with `--pen-gap S` (S as in `small_maps_diag.csv`, the floww time is not counted). Root penalty = root_pen_wait
+ root_pen_enter + root_pen_swap of `--diag`. Expansions per replan = `lowlevel_expansions / lowlevel_calls`
(the new cbm field, the sum of the Bulk Search expansions of all replans; floww has none).

### Measured

Summary (medians over the 16 instances; pen-gap columns are means over the instances):

| variant | solved | CT expanded | replans | ms | root pairs | replan ms median | exp. per replan (sum / sum) | pen-gap share | pen-gap mean excess |
|---|---|---|---|---|---|---|---|---|---|
| bspen | 9/16 | 550.5 | 1120.5 | 10148 | 43.5 | 4.1555 | 3129 | 0.770 | 3.683 |
| bscut | 16/16 | 6.5 | 23.5 | 737.5 | 33 | 16.611 | 26972 | 0.280 | 1.324 |
| bscut_all | 13/16 | 6.5 | 23.5 | 8637 | 34.5 | 335.156 | 499888 | 0.319 | 1.476 |
| floww | 16/16 | 5 | 20.5 | 5398 | 21 | 305.543 | — | — | — |

Share of the root penalty gap closed, (pen_bspen − pen_mode) / (pen_bspen − pen_floww):

| map | N | mode | scen | bspen | bscut penal | bscut all | floww | closed penal | closed all |
|---|---|---|---|---|---|---|---|---|---|
| room-32-32-4 | 40 | g5 | 3 | 15 | 14 | 14 | 12 | 0.33 | 0.33 |
| maze-32-32-2 | 64 | k4 | 2 | 63 | 42 | 41 | 12 | 0.41 | 0.43 |
| maze-32-32-2 | 64 | g5 | 2 | 158 | 120 | 110 | 74 | 0.45 | 0.57 |
| maze-32-32-2 | 64 | g5 | 3 | 82 | 67 | 65 | 55 | 0.56 | 0.63 |
| room-64-64-8 | 128 | g5 | 1 | 250 | 138 | 180 | 132 | 0.95 | 0.59 |
| room-64-64-8 | 128 | g5 | 3 | 211 | 145 | 143 | 108 | 0.64 | 0.66 |
| room-32-32-4 | 40 | g5 | 1 | 13 | 10 | 7 | 8 | 0.60 | 1.20 |
| room-32-32-4 | 40 | g5 | 2 | 15 | 9 | 9 | 5 | 0.60 | 0.60 |
| maze-32-32-2 | 64 | k4 | 1 | 36 | 22 | 31 | 9 | 0.52 | 0.19 |
| maze-32-32-2 | 64 | k4 | 3 | 23 | 17 | 15 | 8 | 0.40 | 0.53 |
| maze-32-32-2 | 64 | g5 | 1 | 113 | 64 | 75 | 50 | 0.78 | 0.60 |
| maze-32-32-2 | 40 | g5 | 1 | 54 | 33 | 39 | 29 | 0.84 | 0.60 |
| maze-32-32-2 | 40 | g5 | 2 | 37 | 27 | 28 | 10 | 0.37 | 0.33 |
| room-64-64-8 | 64 | g5 | 1 | 40 | 19 | 29 | 17 | 0.91 | 0.48 |
| room-64-64-8 | 64 | g5 | 3 | 52 | 45 | 42 | 42 | 0.70 | 1.00 |
| room-64-64-8 | 128 | g5 | 2 | 151 | 115 | 116 | 59 | 0.39 | 0.38 |

- Pooled (sums over the 16: bspen 1313, bscut penal 887, bscut all 944, floww 630): penal closes 0.62 of the gap,
  all 0.54.
- Per instance: penal median 0.58 (0.33-0.95), all median 0.58 (0.19-1.20). penal closes more than all on 7
  instances, less on 7, equal on 2.
- Closed > 1 (room-32-32-4 N40 scen 1, all 7 < floww 8): the root of each mode is planned against the paths of the
  other teams from the same mode, so floww is not a lower bound for the root of another mode.

Per instance:

| map | N | mode | scen | variant | status | CT expanded | replans | ms | root pairs | root pen w/e/s = sum | pen-gap share / mean | replan ms median | exp. per replan |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| room-32-32-4 | 40 | g5 | 3 | bspen | timeout | 21769 | 43546 | 60043 | 15 | 4/6/5 = 15 | 0.250 / 0.396 (timeout) | 1.089 | 1484 |
| room-32-32-4 | 40 | g5 | 3 | bscut | solved | 6 | 20 | 66 | 15 | 2/7/5 = 14 | 0.125 / 0.125 | 2.967 | 2553 |
| room-32-32-4 | 40 | g5 | 3 | bscut_all | solved | 5 | 18 | 389 | 15 | 1/7/6 = 14 | 0.250 / 0.250 | 19.733 | 23748 |
| room-32-32-4 | 40 | g5 | 3 | floww | solved | 5 | 18 | 233 | 12 | 1/6/5 = 12 | — | 13.947 | — |
| maze-32-32-2 | 64 | k4 | 2 | bspen | timeout | 2378 | 4759 | 60014 | 70 | 21/34/8 = 63 | 0.932 / 7.484 (timeout) | 8.915 | 11435 |
| maze-32-32-2 | 64 | k4 | 2 | bscut | solved | 6 | 16 | 517 | 54 | 9/26/7 = 42 | 0.500 / 6.000 | 30.590 | 19897 |
| maze-32-32-2 | 64 | k4 | 2 | bscut_all | solved | 3 | 10 | 4641 | 52 | 7/32/2 = 41 | 0.500 / 5.500 | 494.015 | 425772 |
| maze-32-32-2 | 64 | k4 | 2 | floww | solved | 3 | 10 | 5241 | 26 | 1/10/1 = 12 | — | 478.651 | — |
| maze-32-32-2 | 64 | g5 | 2 | bspen | timeout | 8272 | 16556 | 60019 | 153 | 46/90/22 = 158 | 0.783 / 4.373 (timeout) | 2.866 | 2567 |
| maze-32-32-2 | 64 | g5 | 2 | bscut | solved | 12 | 37 | 1354 | 110 | 25/76/19 = 120 | 0.615 / 2.692 | 15.060 | 23232 |
| maze-32-32-2 | 64 | g5 | 2 | bscut_all | solved | 10 | 33 | 9051 | 107 | 28/64/18 = 110 | 0.615 / 2.692 | 179.774 | 252801 |
| maze-32-32-2 | 64 | g5 | 2 | floww | solved | 9 | 31 | 4905 | 73 | 3/57/14 = 74 | — | 129.652 | — |
| maze-32-32-2 | 64 | g5 | 3 | bspen | timeout | 9136 | 18095 | 60020 | 84 | 22/46/14 = 82 | 0.986 / 4.293 (timeout) | 2.460 | 2274 |
| maze-32-32-2 | 64 | g5 | 3 | bscut | solved | 17 | 47 | 1051 | 63 | 9/50/8 = 67 | 0.154 / 0.769 | 18.293 | 10975 |
| maze-32-32-2 | 64 | g5 | 3 | bscut_all | solved | 12 | 37 | 8703 | 74 | 10/41/14 = 65 | 0.231 / 0.692 | 245.500 | 203169 |
| maze-32-32-2 | 64 | g5 | 3 | floww | solved | 16 | 45 | 8373 | 56 | 0/45/10 = 55 | — | 226.868 | — |
| room-64-64-8 | 128 | g5 | 1 | bspen | solved | 701 | 1428 | 13644 | 164 | 33/169/48 = 250 | 0.903 / 5.069 | 7.608 | 8704 |
| room-64-64-8 | 128 | g5 | 1 | bscut | solved | 18 | 62 | 4007 | 90 | 6/100/32 = 138 | 0.179 / 0.643 | 25.464 | 43928 |
| room-64-64-8 | 128 | g5 | 1 | bscut_all | timeout | 13 | 52 | 60007 | 105 | 11/140/29 = 180 | 0.296 / 1.185 (timeout) | 916.037 | 847570 |
| room-64-64-8 | 128 | g5 | 1 | floww | solved | 18 | 62 | 42208 | 77 | 1/108/23 = 132 | — | 716.269 | — |
| room-64-64-8 | 128 | g5 | 3 | bspen | timeout | 2863 | 5751 | 60006 | 158 | 16/148/47 = 211 | 0.798 / 3.097 (timeout) | 8.669 | 9864 |
| room-64-64-8 | 128 | g5 | 3 | bscut | solved | 19 | 64 | 4345 | 110 | 3/103/39 = 145 | 0.370 / 1.037 | 30.835 | 41479 |
| room-64-64-8 | 128 | g5 | 3 | bscut_all | timeout | 14 | 53 | 60007 | 116 | 8/90/45 = 143 | 0.370 / 1.296 (timeout) | 1019.429 | 799106 |
| room-64-64-8 | 128 | g5 | 3 | floww | solved | 19 | 64 | 46390 | 88 | 2/79/27 = 108 | — | 802.784 | — |
| room-32-32-4 | 40 | g5 | 1 | bspen | solved | 9 | 26 | 55 | 14 | 0/8/5 = 13 | 0.538 / 0.731 | 1.441 | 2777 |
| room-32-32-4 | 40 | g5 | 1 | bscut | solved | 4 | 16 | 82 | 11 | 0/7/3 = 10 | 0.000 / 0.000 | 3.550 | 4676 |
| room-32-32-4 | 40 | g5 | 1 | bscut_all | solved | 4 | 16 | 754 | 8 | 2/3/2 = 7 | 0.000 / 0.000 | 41.866 | 52118 |
| room-32-32-4 | 40 | g5 | 1 | floww | solved | 3 | 14 | 360 | 8 | 0/6/2 = 8 | — | 27.490 | — |
| room-32-32-4 | 40 | g5 | 2 | bspen | solved | 23 | 54 | 108 | 20 | 6/8/1 = 15 | 0.778 / 1.741 | 1.135 | 1763 |
| room-32-32-4 | 40 | g5 | 2 | bscut | solved | 3 | 14 | 91 | 13 | 2/6/1 = 9 | 0.214 / 0.357 | 4.765 | 5972 |
| room-32-32-4 | 40 | g5 | 2 | bscut_all | solved | 4 | 16 | 1008 | 15 | 3/5/1 = 9 | 0.188 / 0.375 | 57.998 | 64400 |
| room-32-32-4 | 40 | g5 | 2 | floww | solved | 3 | 14 | 536 | 7 | 0/3/2 = 5 | — | 44.194 | — |
| maze-32-32-2 | 64 | k4 | 1 | bspen | timeout | 4866 | 9736 | 60020 | 33 | 6/21/9 = 36 | 0.920 / 4.514 (timeout) | 5.445 | 5445 |
| maze-32-32-2 | 64 | k4 | 1 | bscut | solved | 3 | 10 | 232 | 20 | 4/14/4 = 22 | 0.500 / 3.250 | 20.406 | 15335 |
| maze-32-32-2 | 64 | k4 | 1 | bscut_all | solved | 4 | 12 | 4296 | 28 | 6/17/8 = 31 | 0.500 / 4.500 | 422.448 | 328826 |
| maze-32-32-2 | 64 | k4 | 1 | floww | solved | 5 | 14 | 5555 | 9 | 1/7/1 = 9 | — | 384.217 | — |
| maze-32-32-2 | 64 | k4 | 3 | bspen | solved | 392 | 788 | 6652 | 23 | 11/7/5 = 23 | 0.801 / 7.043 | 7.937 | 6969 |
| maze-32-32-2 | 64 | k4 | 3 | bscut | solved | 2 | 8 | 299 | 17 | 3/8/6 = 17 | 0.400 / 1.400 | 27.572 | 25788 |
| maze-32-32-2 | 64 | k4 | 3 | bscut_all | solved | 2 | 8 | 4548 | 15 | 4/7/4 = 15 | 0.600 / 1.200 | 743.808 | 506954 |
| maze-32-32-2 | 64 | k4 | 3 | floww | solved | 1 | 6 | 4726 | 8 | 0/3/5 = 8 | — | 634.663 | — |
| maze-32-32-2 | 64 | g5 | 1 | bspen | solved | 400 | 813 | 2907 | 122 | 29/63/21 = 113 | 0.912 / 8.431 | 2.453 | 2690 |
| maze-32-32-2 | 64 | g5 | 1 | bscut | solved | 22 | 57 | 1781 | 81 | 13/35/16 = 64 | 0.500 / 1.722 | 15.293 | 18381 |
| maze-32-32-2 | 64 | g5 | 1 | bscut_all | solved | 12 | 37 | 12520 | 92 | 21/37/17 = 75 | 0.625 / 2.438 | 235.022 | 302450 |
| maze-32-32-2 | 64 | g5 | 1 | floww | solved | 12 | 37 | 7602 | 61 | 1/38/11 = 50 | — | 185.713 | — |
| maze-32-32-2 | 40 | g5 | 1 | bspen | solved | 54 | 116 | 481 | 49 | 6/36/12 = 54 | 0.845 / 3.078 | 2.427 | 4397 |
| maze-32-32-2 | 40 | g5 | 1 | bscut | solved | 7 | 22 | 747 | 38 | 4/22/7 = 33 | 0.273 / 0.773 | 12.697 | 24469 |
| maze-32-32-2 | 40 | g5 | 1 | bscut_all | solved | 7 | 22 | 8571 | 41 | 8/23/8 = 39 | 0.273 / 1.045 | 247.865 | 358245 |
| maze-32-32-2 | 40 | g5 | 1 | floww | solved | 5 | 18 | 4219 | 23 | 0/22/7 = 29 | — | 202.433 | — |
| maze-32-32-2 | 40 | g5 | 2 | bspen | timeout | 11679 | 23366 | 60025 | 38 | 21/12/4 = 37 | 0.740 / 2.693 (timeout) | 2.262 | 2331 |
| maze-32-32-2 | 40 | g5 | 2 | bscut | solved | 4 | 16 | 414 | 28 | 12/11/4 = 27 | 0.333 / 1.167 | 6.787 | 19479 |
| maze-32-32-2 | 40 | g5 | 2 | bscut_all | solved | 5 | 18 | 4917 | 28 | 12/12/4 = 28 | 0.308 / 1.000 | 201.116 | 258594 |
| maze-32-32-2 | 40 | g5 | 2 | floww | solved | 4 | 16 | 2685 | 13 | 0/7/3 = 10 | — | 146.873 | — |
| room-64-64-8 | 64 | g5 | 1 | bspen | solved | 17 | 47 | 732 | 29 | 4/30/6 = 40 | 0.660 / 1.404 | 7.419 | 21411 |
| room-64-64-8 | 64 | g5 | 1 | bscut | solved | 7 | 27 | 1238 | 16 | 0/16/3 = 19 | 0.000 / 0.000 | 17.929 | 39116 |
| room-64-64-8 | 64 | g5 | 1 | bscut_all | solved | 6 | 25 | 31803 | 18 | 1/25/3 = 29 | 0.080 / 0.080 | 915.743 | 952240 |
| room-64-64-8 | 64 | g5 | 1 | floww | solved | 8 | 29 | 19695 | 17 | 0/13/4 = 17 | — | 598.435 | — |
| room-64-64-8 | 64 | g5 | 3 | bspen | solved | 27 | 67 | 613 | 26 | 3/41/8 = 52 | 0.672 / 1.687 | 5.982 | 10818 |
| room-64-64-8 | 64 | g5 | 3 | bscut | solved | 6 | 25 | 728 | 21 | 0/39/6 = 45 | 0.080 / 0.080 | 13.446 | 22772 |
| room-64-64-8 | 64 | g5 | 3 | bscut_all | solved | 7 | 27 | 26242 | 21 | 0/35/7 = 42 | 0.074 / 0.074 | 1030.790 | 689415 |
| room-64-64-8 | 64 | g5 | 3 | floww | solved | 5 | 23 | 14087 | 19 | 0/37/5 = 42 | — | 555.004 | — |
| room-64-64-8 | 128 | g5 | 2 | bspen | solved | 155 | 336 | 3357 | 120 | 8/102/41 = 151 | 0.807 / 2.886 | 6.389 | 9671 |
| room-64-64-8 | 128 | g5 | 2 | bscut | solved | 21 | 68 | 3874 | 79 | 3/86/26 = 115 | 0.235 / 1.176 | 21.208 | 37716 |
| room-64-64-8 | 128 | g5 | 2 | bscut_all | timeout | 18 | 61 | 60003 | 82 | 2/89/25 = 116 | 0.188 / 1.281 (timeout) | 718.522 | 646990 |
| room-64-64-8 | 128 | g5 | 2 | floww | solved | 21 | 68 | 36012 | 60 | 1/37/21 = 59 | — | 560.443 | — |

- bspen: 7 timeouts (CT nodes in the thousands); bscut penal: 0; bscut all: 3, all on room-64-64-8 N128 (replan
  median 0.7-1.0 s, 13-18 CT nodes in 60 s); floww: 0.
- CT expanded: bscut penal 2-22, all 2-18, floww 1-21, bspen 9-21769.
- Replan cost (medians over instances): bspen 4.2 ms, penal 16.6 ms, all 335 ms, floww 306 ms; expansions per
  replan 3.1 k / 27 k / 500 k.
- Time: penal is the fastest variant on 11 of 16 instances; all is slower than floww on 13 of 16.
- pen-gap rows marked (timeout) cover the replans done before the limit.

### Interpretation

- Cutting removes most of the CT blow-up of bspen: with bscut the CT is about as small as with floww, while a replan stays
  ~20 times cheaper than a floww one. This is the best combination of the four.
- penal closes about 0.6 of the root penalty gap; all closes no more (0.54 pooled), at a ~20 times higher replan
  cost. Cutting everywhere does not pay: the cuts around the penalized steps are the ones that matter.
- The rest of the gap (about 0.4) is not about bulks (all has none): it comes from planning one path at a time
  greedily against the other teams, consistent with stage 2. Even so the remaining extra penalty does not grow the
  CT on these 16 instances.

# 5.2а, этап 4

## Part 1: cost of one replanning (2026-11-10)

`replan_cut.py replan_cut.csv`: cbm `--root-only first|last`, N = 128, teams of 5 (K = 26), scen 1, `--t-start lb`;
bs, bspen, bscut (`--cut penal`). first = team 0 (no other teams yet), last = team 25 (25 teams planned before
it). ms = time of that call (median of 3 runs, all T tried from minT); expansions = Bulk Search expansions of
the call over all T tried; hard / soft cuts = cuts of the waiting chains in the network of the final T (new
`BulkSearchTeam::countCuts`, not timed); pieces = free cells + hard + soft cuts. ms of the whole root: the 26
calls one by one (last run).

### Measured

| map | team | variant | minT | T | T tried | ms (median of 3) | expansions | hard cuts | soft cuts | pieces | ms of the whole root |
|---|---|---|---|---|---|---|---|---|---|---|---|
| room-64-64-8 | first (0) | bs | 48 | 53 | 6 | 14.2 | 22908 | 234 | 0 | 3466 | 14 |
| room-64-64-8 | first (0) | bspen | 48 | 53 | 6 | 14.9 | 22908 | 234 | 0 | 3466 | 15 |
| room-64-64-8 | first (0) | bscut | 48 | 53 | 6 | 16.9 | 22908 | 234 | 0 | 3466 | 17 |
| room-64-64-8 | last (25) | bs | 45 | 66 | 22 | 30.5 | 55088 | 136 | 0 | 3368 | 717 |
| room-64-64-8 | last (25) | bspen | 45 | 66 | 22 | 60.3 | 83929 | 148 | 0 | 3380 | 1825 |
| room-64-64-8 | last (25) | bscut | 45 | 66 | 22 | 293.4 | 191609 | 158 | 12223 | 15613 | 3129 |
| warehouse-10-20-10-2-1 | first (0) | bs | 75 | 103 | 29 | 82.8 | 181604 | 246 | 0 | 5945 | 85 |
| warehouse-10-20-10-2-1 | first (0) | bspen | 75 | 103 | 29 | 88.8 | 181604 | 246 | 0 | 5945 | 89 |
| warehouse-10-20-10-2-1 | first (0) | bscut | 75 | 103 | 29 | 93.0 | 181604 | 246 | 0 | 5945 | 93 |
| warehouse-10-20-10-2-1 | last (25) | bs | 61 | 61 | 1 | 1.9 | 2680 | 146 | 0 | 5845 | 1308 |
| warehouse-10-20-10-2-1 | last (25) | bspen | 61 | 61 | 1 | 4.9 | 2498 | 146 | 0 | 5845 | 1673 |
| warehouse-10-20-10-2-1 | last (25) | bscut | 61 | 61 | 1 | 11.7 | 4152 | 170 | 12099 | 17968 | 4048 |
| Berlin_1_256 | first (0) | bs | 155 | 180 | 26 | 1019.7 | 1301820 | 605 | 0 | 48145 | 993 |
| Berlin_1_256 | first (0) | bspen | 155 | 180 | 26 | 1088.9 | 1301820 | 605 | 0 | 48145 | 1089 |
| Berlin_1_256 | first (0) | bscut | 155 | 180 | 26 | 1178.4 | 1301820 | 605 | 0 | 48145 | 1178 |
| Berlin_1_256 | last (25) | bs | 264 | 264 | 1 | 84.7 | 92782 | 865 | 0 | 48405 | 28606 |
| Berlin_1_256 | last (25) | bspen | 264 | 264 | 1 | 106.9 | 92368 | 865 | 0 | 48405 | 35938 |
| Berlin_1_256 | last (25) | bscut | 264 | 264 | 1 | 200.4 | 97845 | 865 | 47757 | 96162 | 59864 |

- first: no other teams, so bspen and bscut search exactly as bs (same expansions and cuts); the time differs by
  5-19% (the penalty lookups).
- last: bscut makes 12 099-47 757 soft cuts (3.8 and 2.1 times the free cells of room / warehouse, 1.0 per cell on
  Berlin); the network has 2.0-4.6 times the pieces of bspen.
- last, time of the call: bscut vs bspen 4.8x on room-64-64-8 (T tried 22), 2.4x on warehouse (T tried 1), 1.9x on
  Berlin (T tried 1); expansions 2.3x, 1.7x, 1.06x.
- Whole root: bscut 3.1 s / 4.0 s / 59.9 s vs bspen 1.8 / 1.7 / 35.9 s and bs 0.7 / 1.3 / 28.6 s.
