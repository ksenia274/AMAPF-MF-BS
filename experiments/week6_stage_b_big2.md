maps: warehouse-10-20-10-2-1, Berlin_1_256; rows lb 400, match 400

### 1. solved: lb / match

| map | bs | bspen | bscut | flow | floww |
|---|---|---|---|---|---|
| warehouse-10-20-10-2-1 | 13 / 13 | 35 / 35 | 40 / 40 | 0 / 0 | 6 / 12 |
| Berlin_1_256 | 24 / 31 | 28 / 40 | 17 / 40 | 0 / 0 | 0 / 0 |
| **both maps** | 37 / 44 | 63 / 75 | 57 / 80 | 0 / 0 | 6 / 12 |

### 2. solved / timeout in the root (root_conflict_pairs = -1) / timeout in the CT / not run (timeout_skipped)

| map | variant | lb | match | other statuses lb, match |
|---|---|---|---|---|
| warehouse-10-20-10-2-1 | bs | 13 / 0 / 10 / 17 | 13 / 0 / 10 / 17 | 0, 0 |
| warehouse-10-20-10-2-1 | bspen | 35 / 0 / 4 / 1 | 35 / 0 / 4 / 1 | 0, 0 |
| warehouse-10-20-10-2-1 | bscut | 40 / 0 / 0 / 0 | 40 / 0 / 0 / 0 | 0, 0 |
| warehouse-10-20-10-2-1 | flow | 0 / 0 / 10 / 30 | 0 / 0 / 10 / 30 | 0, 0 |
| warehouse-10-20-10-2-1 | floww | 6 / 7 / 3 / 24 | 12 / 0 / 10 / 18 | 0, 0 |
| Berlin_1_256 | bs | 24 / 0 / 10 / 6 | 31 / 0 / 7 / 2 | 0, 0 |
| Berlin_1_256 | bspen | 28 / 7 / 3 / 2 | 40 / 0 / 0 / 0 | 0, 0 |
| Berlin_1_256 | bscut | 17 / 10 / 0 / 13 | 40 / 0 / 0 / 0 | 0, 0 |
| Berlin_1_256 | flow | 0 / 10 / 0 / 30 | 0 / 3 / 7 / 30 | 0, 0 |
| Berlin_1_256 | floww | 0 / 10 / 0 / 30 | 0 / 10 / 0 / 30 | 0, 0 |

### lost (solved with lb, not with match) and gained

bs: lost 1 ['warehouse-10-20-10-2-1 N128 s5 (timeout)'], gained 8
bspen: lost 2 ['warehouse-10-20-10-2-1 N192 s2 (timeout)', 'warehouse-10-20-10-2-1 N256 s4 (timeout)'], gained 14
bscut: lost 0 [], gained 23
flow: lost 0 [], gained 0
floww: lost 0 [], gained 6

### 3. checks

match: instances solved by several variants 75, makespan differs: 0 []
match vs lb: solved match runs of instances also solved with lb 182, makespan differs: 0 []
match: solved 211, valid 211, not valid 0
lb: solved 163, valid 163, not valid 0

### 4. bscut vs bspen, total_ms on instances solved by both, match

| map | both solved | bscut faster | equal | bspen faster | median bspen / bscut | min | max | median ms bscut | median ms bspen |
|---|---|---|---|---|---|---|---|---|---|
| warehouse-10-20-10-2-1 | 35 | 13 | 0 | 22 | 0.89 | 0.47 | 3.77 | 1100 | 1060 |
| Berlin_1_256 | 40 | 2 | 0 | 38 | 0.66 | 0.48 | 1.16 | 6487 | 4406 |
| **both maps** | 75 | 15 | 0 | 60 | 0.74 | 0.47 | 3.77 | 3064 | 2512 |

cactus: top of the y axis = instances per map: {'warehouse-10-20-10-2-1': 40, 'Berlin_1_256': 40}
