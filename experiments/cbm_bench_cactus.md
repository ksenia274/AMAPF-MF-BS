# CBM on MovingAI maps: cactus plots (2026-11-04)

`python cbm_bench_cactus.py cbm_bench_cactus.csv` (sequential, 6.6 h of runs), table: `--summary`,
figures: `python figures/make_cactus.py cbm_bench_cactus.csv` -> figures/cactus_*.png / .pdf.

- Maps: small - empty-32-32, random-32-32-10, room-32-32-4, maze-32-32-2, random-64-64-10, room-64-64-8;
  large - warehouse-10-20-10-2-1, Berlin_1_256, Paris_1_256, Boston_0_256 (all MovingAI).
- random scen 1..10, the first N agents; N: 32x32 - 20, 40, 60, 80; 64x64 - 40, 80, 120, 160; large - 64, 128, 192, 256.
- Teams of 5 consecutive agents, K = ceil(N/5) (N = 64: 12 teams of 5 and one of 4; N = 192: 36 of 5 and 3 of 4).
- Low levels bs, bspen, flow, floww; T starts from the lower bound (the default since 8e4a4e5); 60 s, --mem-limit 8000.
- Stopping rule of the Bulk Search paper: within a scen N grows; after the first unsolved instance of a variant the
  larger N of that scen are not run for it (timeout_skipped, counted as unsolved). All 264 unsolved runs are timeouts,
  no memory or killed runs. "solved" = solved / instances of the map (4 N x 10 scen = 40).
- Cactus time = total_ms of cbm; every solution passed validate.py --teams K.

Expected time before the run: about 7-8 h (worst case 1600 runs x ~62 s = 27 h), so all 10 scens were kept.

| map | solved: bs | solved: bspen | solved: flow | solved: floww | timeout_skipped: bs / bspen / flow / floww | memory / killed |
|---|---|---|---|---|---|---|
| empty-32-32 | 40/40 | 40/40 | 33/40 | 40/40 | 0 / 0 / 2 / 0 | 0 / 0 |
| random-32-32-10 | 39/40 | 40/40 | 32/40 | 40/40 | 0 / 0 / 2 / 0 | 0 / 0 |
| room-32-32-4 | 20/40 | 32/40 | 17/40 | 40/40 | 10 / 3 / 13 / 0 | 0 / 0 |
| maze-32-32-2 | 17/40 | 19/40 | 7/40 | 37/40 | 13 / 11 / 23 / 2 | 0 / 0 |
| random-64-64-10 | 36/40 | 40/40 | 19/40 | 40/40 | 1 / 0 / 11 / 0 | 0 / 0 |
| room-64-64-8 | 13/40 | 31/40 | 7/40 | 39/40 | 17 / 1 / 23 / 0 | 0 / 0 |
| **all small** | **165/240** | **202/240** | **115/240** | **236/240** | | |
| warehouse-10-20-10-2-1 | 13/40 | 35/40 | 0/40 | 6/40 | 17 / 1 / 30 / 24 | 0 / 0 |
| Berlin_1_256 | 24/40 | 28/40 | 0/40 | 0/40 | 6 / 2 / 30 / 30 | 0 / 0 |
| Paris_1_256 | 21/40 | 23/40 | 0/40 | 0/40 | 9 / 7 / 30 / 30 | 0 / 0 |
| Boston_0_256 | 20/40 | 25/40 | 0/40 | 0/40 | 10 / 5 / 30 / 30 | 0 / 0 |
| **all large** | **78/160** | **111/160** | **0/160** | **6/160** | | |

makespan mismatches on the 280 instances solved by several variants: 0 []; invalid solutions: 0
