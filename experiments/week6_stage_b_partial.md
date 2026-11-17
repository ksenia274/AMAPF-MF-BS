maps: empty-32-32, random-32-32-10, room-32-32-4, maze-32-32-2, random-64-64-10

### B.1 solved per map and variant: lb (old) and match (new)

| map | variant | solved lb | solved match |
|---|---|---|---|
| empty-32-32 | bs | 40 | 40 |
| empty-32-32 | bspen | 40 | 40 |
| empty-32-32 | bscut | 40 | 40 |
| empty-32-32 | flow | 33 | 33 |
| empty-32-32 | floww | 40 | 40 |
| random-32-32-10 | bs | 39 | 40 |
| random-32-32-10 | bspen | 40 | 40 |
| random-32-32-10 | bscut | 40 | 40 |
| random-32-32-10 | flow | 32 | 32 |
| random-32-32-10 | floww | 40 | 40 |
| room-32-32-4 | bs | 20 | 19 |
| room-32-32-4 | bspen | 32 | 35 |
| room-32-32-4 | bscut | 40 | 40 |
| room-32-32-4 | flow | 17 | 17 |
| room-32-32-4 | floww | 40 | 40 |
| maze-32-32-2 | bs | 17 | 17 |
| maze-32-32-2 | bspen | 19 | 17 |
| maze-32-32-2 | bscut | 40 | 40 |
| maze-32-32-2 | flow | 7 | 7 |
| maze-32-32-2 | floww | 37 | 37 |
| random-64-64-10 | bs | 36 | 34 |
| random-64-64-10 | bspen | 40 | 40 |
| random-64-64-10 | bscut | 40 | 40 |
| random-64-64-10 | flow | 19 | 19 |
| random-64-64-10 | floww | 40 | 40 |
| **all these maps** | bs | 152 | 150 |
| **all these maps** | bspen | 171 | 172 |
| **all these maps** | bscut | 200 | 200 |
| **all these maps** | flow | 108 | 108 |
| **all these maps** | floww | 197 | 197 |

runs per variant (old / new): bs 200 / 200, bspen 200 / 200, bscut 200 / 200, flow 200 / 200, floww 200 / 200
statuses new: {'solved': 827, 'timeout': 80, 'timeout_skipped': 93}
statuses old: {'solved': 828, 'timeout': 81, 'timeout_skipped': 91}

### B.2 large maps, match

no large map here

### B.3 solved with lb and not with match (lost), and the other way (gained)

bs: lost 6, gained 4
  lost random-64-64-10 N160 s1: lb solved 6523 ms, match timeout 60017 ms
  lost random-64-64-10 N160 s2: lb solved 2637 ms, match timeout 60011 ms
  lost random-64-64-10 N160 s5: lb solved 5307 ms, match timeout 60016 ms
  lost random-64-64-10 N160 s7: lb solved 4767 ms, match timeout 60012 ms
  lost room-32-32-4 N40 s8: lb solved 344 ms, match timeout 60031 ms
  lost room-32-32-4 N40 s10: lb solved 1199 ms, match timeout 60039 ms
  gained random-32-32-10 N80 s2: lb timeout 60035 ms, match solved 2636 ms
  gained random-64-64-10 N160 s3: lb timeout 60012 ms, match solved 30534 ms
  gained random-64-64-10 N160 s9: lb timeout 60013 ms, match solved 3184 ms
  gained room-32-32-4 N60 s4: lb timeout 60046 ms, match solved 1704 ms
bspen: lost 3, gained 4
  lost maze-32-32-2 N40 s4: lb solved 5648 ms, match timeout 60023 ms
  lost maze-32-32-2 N60 s8: lb solved 3244 ms, match timeout 60014 ms
  lost maze-32-32-2 N60 s10: lb solved 1399 ms, match timeout 60020 ms
  gained maze-32-32-2 N40 s2: lb timeout 60034 ms, match solved 3381 ms
  gained room-32-32-4 N60 s8: lb timeout 60023 ms, match solved 427 ms
  gained room-32-32-4 N80 s7: lb timeout 60025 ms, match solved 36816 ms
  gained room-32-32-4 N80 s9: lb timeout 60032 ms, match solved 6791 ms
bscut: lost 0, gained 0
flow: lost 0, gained 0
floww: lost 0, gained 0

### B.4 checks

match: instances solved by several variants 197, makespan differs: 0 []
match vs lb: solved match runs of instances also solved with lb 827, makespan differs from the lb run: 0 []
match: solved 827, valid 827, not valid 0
lb: solved 828, valid 828, not valid 0

### B.5 small maps, bscut vs floww (as 1.1), match

### 1.1

| map | both solved | bscut faster | equal | floww faster | median floww / bscut | min | max | median ms bscut | median ms floww |
|---|---|---|---|---|---|---|---|---|---|
| empty-32-32 | 40 | 40 | 0 | 0 | 10.2 | 4.65 | 22 | 32 | 303 |
| random-32-32-10 | 40 | 40 | 0 | 0 | 8.4 | 3.00 | 22 | 34 | 282 |
| room-32-32-4 | 40 | 40 | 0 | 0 | 5.9 | 2.09 | 33 | 86 | 532 |
| maze-32-32-2 | 37 | 37 | 0 | 0 | 12.6 | 4.28 | 80 | 167 | 2683 |
| random-64-64-10 | 40 | 40 | 0 | 0 | 26.6 | 7.24 | 44 | 270 | 6000 |
| **all small** | 197 | 197 | 0 | 0 | 10.5 | 2.09 | 80 | 68 | 685 |

bscut slower than floww: 
instances with bscut total_ms < 10: 21

### B.6 large maps, bscut vs bspen, total_ms on instances solved by both, match

no large map here
