# CBM experiment 1 (Ma, Koenig 2016, table 1) with our CBM + Bulk Search

`python cbm_paper_exp1.py cbm_paper_exp1.csv` (2026-11-02, sequential, 60 s per instance), summary: `--summary`.

- Map random-32-32-10 (MovingAI). The paper used its own random 30x30 grids with 10% obstacles; this is the closest
  standard analogue, not the same instances.
- Instance (N, s): scen random-s, s = 1..20, the first N agents; team g = agents 5g..5g+4 (K = N/5).
- Our CBM unchanged (no weights, low level = Bulk Search, root T from 1). Every solution passed validate.py --teams.
- The paper's limit was 5 min, ours 60 s. Paper columns: CBM without weights (success rate) and CBM with weights
  (success rate, mean time); paper machine and implementation differ, so times are not comparable directly.

| N | K | solved | mean time, s (solved) | mean makespan (solved) | mean CT nodes expanded (solved) | mean replans (solved) | unsolved: nodes expanded | unsolved: last key (expanded at it) | invalid | paper CBM rate | paper CBM-w rate | paper CBM-w time, s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 2 | 20/20 = 1.00 | 0.01 | 25.4 | 1 | 4 | - | - | 0 | 0.72 | 1.0 | 0.34 |
| 15 | 3 | 20/20 = 1.00 | 0.02 | 26.4 | 2 | 7 | - | - | 0 | 0.44 | 1.0 | 0.57 |
| 20 | 4 | 20/20 = 1.00 | 0.04 | 27.4 | 5 | 14 | - | - | 0 | 0.22 | 1.0 | 0.78 |
| 25 | 5 | 20/20 = 1.00 | 0.06 | 28.0 | 10 | 25 | - | - | 0 | 0.08 | 1.0 | 1.07 |
| 30 | 6 | 20/20 = 1.00 | 0.07 | 28.8 | 14 | 35 | - | - | 0 | 0.02 | 1.0 | 1.71 |
| 35 | 7 | 20/20 = 1.00 | 0.10 | 28.8 | 20 | 48 | - | - | 0 | 0 | 1.0 | 1.92 |
| 40 | 8 | 20/20 = 1.00 | 0.14 | 29.0 | 31 | 70 | - | - | 0 | 0 | 1.0 | 2.95 |
| 45 | 9 | 20/20 = 1.00 | 0.18 | 29.1 | 45 | 100 | - | - | 0 | 0 | 1.0 | 3.66 |
| 50 | 10 | 19/20 = 0.95 | 0.29 | 29.3 | 82 | 174 | 19070 | 26(19070) | 0 | 0 | 1.0 | 5.32 |

Unsolved: N=50, scen 16 - all 19070 expanded nodes have key 26 = the root key (a plateau). Rerun with 300 s and
`--diag`: still unsolved, 97063 expanded, all at key 26, depth up to 138, 7250 repeated constraint sets.

## Low level: Bulk Search vs max-flow vs min-cost flow (2026-11-02)

Same 180 instances, same high level (tie-break `conflicts`, the default), 60 s, sequential:
`cbm_paper_exp1.py cbm_paper_exp1_flow.csv --low flow`, `... cbm_paper_exp1_floww.csv --low floww`.
Means over the instances solved by that variant.

| N | solved: bs | solved: flow | solved: floww | mean time, s: bs | mean time, s: flow | mean time, s: floww | mean makespan: bs | mean makespan: flow | mean makespan: floww | mean CT nodes expanded: bs | mean CT nodes expanded: flow | mean CT nodes expanded: floww | mean replans: bs | mean replans: flow | mean replans: floww |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 20/20 | 20/20 | 20/20 | 0.01 | 0.04 | 0.07 | 25.40 | 25.40 | 25.40 | 1.05 | 1.15 | 0.10 | 4.10 | 4.30 | 2.20 |
| 15 | 20/20 | 20/20 | 20/20 | 0.02 | 0.07 | 0.09 | 26.40 | 26.40 | 26.40 | 1.80 | 2.50 | 0.25 | 6.60 | 8.00 | 3.50 |
| 20 | 20/20 | 20/20 | 20/20 | 0.04 | 0.17 | 0.19 | 27.45 | 27.45 | 27.45 | 4.75 | 9.30 | 0.65 | 13.50 | 22.60 | 5.30 |
| 25 | 20/20 | 20/20 | 20/20 | 0.06 | 0.25 | 0.16 | 28.00 | 28.00 | 28.00 | 9.95 | 13.95 | 0.75 | 24.90 | 32.90 | 6.50 |
| 30 | 20/20 | 20/20 | 20/20 | 0.07 | 1.87 | 0.20 | 28.80 | 28.80 | 28.80 | 14.45 | 110.15 | 0.80 | 34.90 | 226.30 | 7.60 |
| 35 | 20/20 | 20/20 | 20/20 | 0.10 | 1.15 | 0.24 | 28.80 | 28.80 | 28.80 | 20.45 | 69.20 | 1.05 | 47.90 | 145.40 | 9.10 |
| 40 | 20/20 | 20/20 | 20/20 | 0.14 | 5.21 | 0.30 | 29.00 | 29.00 | 29.00 | 31.25 | 319.85 | 1.35 | 70.50 | 647.70 | 10.70 |
| 45 | 20/20 | 19/20 | 20/20 | 0.18 | 6.20 | 0.34 | 29.05 | 29.21 | 29.05 | 45.40 | 407.84 | 1.70 | 99.80 | 824.68 | 12.40 |
| 50 | 19/20 | 18/20 | 20/20 | 0.29 | 5.03 | 0.39 | 29.26 | 28.67 | 29.10 | 82.11 | 335.17 | 2.05 | 174.21 | 680.33 | 14.10 |

makespan mismatches on common solutions: 0 []; invalid solutions: 0

Unsolved: bs - N=50 scen 16 (plateau, above). flow - N=45 scen 12, N=50 scen 12 (5 nodes expanded, 317 s: one
replanning of a team whose start is shut in at t=1 - vertex constraints (9,28), (9,27), (10,28) at 1, edge
(9,28)->(8,28) at 0, (9,29) is an obstacle - so there is no solution for any T; FlowTeam builds the network for
every T = 26..1030 from scratch, the time limit is checked only between CT expansions) and N=50 scen 5
(time limit, 2154 nodes, all at key 40). bs_team gives T=-1 for the same team subproblem as well.

## Tie-break: `conflicts` vs `late` (2026-11-02)

`conflicts` (key, fewer conflicting teams, later node) is what cbm did before the flag (all runs above);
`late` = key, later node. `cbm_paper_exp1.py cbm_paper_exp1_late.csv --tiebreak late`:

| N | solved: conflicts | solved: late | mean time, s: conflicts | mean time, s: late | mean makespan: conflicts | mean makespan: late | mean CT nodes expanded: conflicts | mean CT nodes expanded: late | mean replans: conflicts | mean replans: late |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 20/20 | 20/20 | 0.01 | 0.01 | 25.40 | 25.40 | 1.05 | 1.70 | 4.10 | 5.40 |
| 15 | 20/20 | 20/20 | 0.02 | 0.02 | 26.40 | 26.40 | 1.80 | 3.00 | 6.60 | 9.00 |
| 20 | 20/20 | 20/20 | 0.04 | 0.04 | 27.45 | 27.45 | 4.75 | 6.90 | 13.50 | 17.80 |
| 25 | 20/20 | 20/20 | 0.06 | 0.05 | 28.00 | 28.00 | 9.95 | 10.30 | 24.90 | 25.60 |
| 30 | 20/20 | 20/20 | 0.07 | 0.08 | 28.80 | 28.80 | 14.45 | 17.55 | 34.90 | 41.10 |
| 35 | 20/20 | 20/20 | 0.10 | 0.12 | 28.80 | 28.80 | 20.45 | 29.20 | 47.90 | 65.40 |
| 40 | 20/20 | 20/20 | 0.14 | 0.15 | 29.00 | 29.00 | 31.25 | 39.10 | 70.50 | 86.20 |
| 45 | 20/20 | 20/20 | 0.18 | 0.18 | 29.05 | 29.05 | 45.40 | 50.35 | 99.80 | 109.70 |
| 50 | 19/20 | 20/20 | 0.29 | 0.22 | 29.26 | 29.10 | 82.11 | 68.30 | 174.21 | 146.60 |

makespan mismatches on common solutions: 0 []; invalid solutions: 0

N=50 scen 16, 300 s, `--diag`: conflicts - unsolved, 95291 expanded, all at key 26 = root key, depth 138,
7250 repeated constraint sets; late - T=26 (valid), 0.4 s, 139 expanded (all at key 26), depth 139, 0 repeated sets.
