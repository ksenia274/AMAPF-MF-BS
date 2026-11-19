# archive/

One-off analysis scripts. Their results are already in the CSV files and in the journals; they are kept so the
numbers can be reproduced. Results (CSV, `week6_prof/`, `figures/`) stay in `experiments/`, and the scripts still
read and write there: run them from `experiments/`, e.g. `python archive/replan_cut.py replan_cut.csv`.

| Script | What it did | Results | Journal |
|---|---|---|---|
| `replan_scaling.py` | time of one low-level call in the root, stages 3b and 3c | `replan_scaling.csv`, `replan_scaling_3c.csv` | `cbm_bench_3b.md` |
| `small_maps_diag.py` | why bspen solves fewer instances than floww: the 16 hard instances | `small_maps_diag.csv`, `small_maps_diag.log` | `small_maps_diag.md`, first part (2026-11-04) |
| `small_maps_root.py` | penalty of the root by parts, bspen with a floww root | `small_maps_root.csv` | `small_maps_diag.md`, «Откуда лишний штраф» and «Корень от floww» |
| `small_maps_entries.py` | where the extra entry penalties of bspen come from | `small_maps_entries.csv` | `small_maps_diag.md`, 5.2а stage 1 |
| `small_maps_cut.py` | bspen, bscut penal / all, floww on the 16 instances | `small_maps_cut.csv` | `small_maps_diag.md`, 5.2а stage 3 |
| `replan_cut.py` | cost of one root call for bs, bspen, bscut | `replan_cut.csv` | `small_maps_diag.md`, 5.2а этап 4, part 1 |
| `week6_part2.py` | rdtsc profile of the root (`cbm_prof.exe`), assignment bound | `week6_prof/`, `week6_root_teams.csv`, `week6_root_T.csv`, `week6_part2_report.txt` | `small_maps_diag.md`, Неделя 6, часть 2 |
| `week6_match.py` | stage A: `--t-start match` against `lb` | `week6_match_hard.csv`, `week6_match_root.csv` | `small_maps_diag.md`, Этап A |
| `week6_stage_b_big2.py` | stage B on warehouse and Berlin, before the run ended (R20261117-big-match@big2) | `week6_stage_b_big2.md`, `cbm_bench_cactus_match_big2.csv` | report of 2026-11-17 |
| `flag_noconstr.py` | week 7, C1: blockedToMove without constraints, bs / bspen / bscut against brute force (needs an `audit_build.py` build) | — | `week7_c1_audit.md`, section 5 |
| `make_colored_yaml.py` | instance for CBS-TA (libMultiRobotPlanning), comparison of 2026-10-20 | — | — |

`small_maps_cut.py`, `small_maps_entries.py` and `small_maps_root.py` import `small_maps_diag.py`, and
`week6_match.py report` imports `week6_part2.py`, so they stay together here.
