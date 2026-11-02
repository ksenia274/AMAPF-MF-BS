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
