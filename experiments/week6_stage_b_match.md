maps: empty-32-32, random-32-32-10, room-32-32-4, maze-32-32-2, random-64-64-10, room-64-64-8, warehouse-10-20-10-2-1, Berlin_1_256, Paris_1_256, Boston_0_256

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
| room-64-64-8 | bs | 13 | 14 |
| room-64-64-8 | bspen | 31 | 31 |
| room-64-64-8 | bscut | 39 | 39 |
| room-64-64-8 | flow | 7 | 7 |
| room-64-64-8 | floww | 39 | 39 |
| warehouse-10-20-10-2-1 | bs | 13 | 13 |
| warehouse-10-20-10-2-1 | bspen | 35 | 35 |
| warehouse-10-20-10-2-1 | bscut | 40 | 40 |
| warehouse-10-20-10-2-1 | flow | 0 | 0 |
| warehouse-10-20-10-2-1 | floww | 6 | 12 |
| Berlin_1_256 | bs | 24 | 31 |
| Berlin_1_256 | bspen | 28 | 40 |
| Berlin_1_256 | bscut | 17 | 40 |
| Berlin_1_256 | flow | 0 | 0 |
| Berlin_1_256 | floww | 0 | 0 |
| Paris_1_256 | bs | 21 | 28 |
| Paris_1_256 | bspen | 23 | 40 |
| Paris_1_256 | bscut | 13 | 40 |
| Paris_1_256 | flow | 0 | 0 |
| Paris_1_256 | floww | 0 | 0 |
| Boston_0_256 | bs | 20 | 25 |
| Boston_0_256 | bspen | 25 | 40 |
| Boston_0_256 | bscut | 13 | 40 |
| Boston_0_256 | flow | 0 | 0 |
| Boston_0_256 | floww | 0 | 0 |
| **all these maps** | bs | 243 | 261 |
| **all these maps** | bspen | 313 | 358 |
| **all these maps** | bscut | 322 | 399 |
| **all these maps** | flow | 115 | 115 |
| **all these maps** | floww | 242 | 248 |

runs per variant (old / new): bs 400 / 400, bspen 400 / 400, bscut 400 / 400, flow 400 / 400, floww 400 / 400
statuses new: {'solved': 1381, 'timeout': 227, 'timeout_skipped': 392}
statuses old: {'solved': 1235, 'timeout': 295, 'timeout_skipped': 470}

### B.2 large maps, match

### 1.2

| map | variant | solved | timeout: root | timeout: CT | not run (timeout_skipped) | other |
|---|---|---|---|---|---|---|
| warehouse-10-20-10-2-1 | bs | 13 | 0 | 10 | 17 | 0 |
| warehouse-10-20-10-2-1 | bspen | 35 | 0 | 4 | 1 | 0 |
| warehouse-10-20-10-2-1 | bscut | 40 | 0 | 0 | 0 | 0 |
| warehouse-10-20-10-2-1 | flow | 0 | 0 | 10 | 30 | 0 |
| warehouse-10-20-10-2-1 | floww | 12 | 0 | 10 | 18 | 0 |
| Berlin_1_256 | bs | 31 | 0 | 7 | 2 | 0 |
| Berlin_1_256 | bspen | 40 | 0 | 0 | 0 | 0 |
| Berlin_1_256 | bscut | 40 | 0 | 0 | 0 | 0 |
| Berlin_1_256 | flow | 0 | 3 | 7 | 30 | 0 |
| Berlin_1_256 | floww | 0 | 10 | 0 | 30 | 0 |
| Paris_1_256 | bs | 28 | 0 | 8 | 4 | 0 |
| Paris_1_256 | bspen | 40 | 0 | 0 | 0 | 0 |
| Paris_1_256 | bscut | 40 | 0 | 0 | 0 | 0 |
| Paris_1_256 | flow | 0 | 3 | 7 | 30 | 0 |
| Paris_1_256 | floww | 0 | 10 | 0 | 30 | 0 |
| Boston_0_256 | bs | 25 | 0 | 9 | 6 | 0 |
| Boston_0_256 | bspen | 40 | 0 | 0 | 0 | 0 |
| Boston_0_256 | bscut | 40 | 0 | 0 | 0 | 0 |
| Boston_0_256 | flow | 0 | 3 | 7 | 30 | 0 |
| Boston_0_256 | floww | 0 | 10 | 0 | 30 | 0 |

unfinished roots with more than K replans or expanded CT nodes: 0
finished roots, timeout before the first CT expansion was done: [('Berlin_1_256', '64', '2', 'flow'), ('Paris_1_256', '64', '6', 'flow')]
unfinished roots: replans done / K from 0.08 to 1.00

CT timeouts:
  warehouse-10-20-10-2-1 N64 s1 flow: expanded 77, replans 166, K 13, last_key 121, replan median 375.209 ms
  warehouse-10-20-10-2-1 N192 s1 bs: expanded 2214, replans 4464, K 39, last_key 132, replan median 4.404 ms
  warehouse-10-20-10-2-1 N192 s1 floww: expanded 6, replans 50, K 39, last_key 132, replan median 921.839 ms
  warehouse-10-20-10-2-1 N256 s1 bspen: expanded 1552, replans 3156, K 52, last_key 132, replan median 13.935 ms
  warehouse-10-20-10-2-1 N64 s2 flow: expanded 94, replans 200, K 13, last_key 113, replan median 299.177 ms
  warehouse-10-20-10-2-1 N192 s2 bs: expanded 4094, replans 8226, K 39, last_key 130, replan median 4.733 ms
  warehouse-10-20-10-2-1 N192 s2 bspen: expanded 1704, replans 3447, K 39, last_key 130, replan median 13.442 ms
  warehouse-10-20-10-2-1 N192 s2 floww: expanded 5, replans 48, K 39, last_key 130, replan median 1044.246 ms
  warehouse-10-20-10-2-1 N64 s3 flow: expanded 62, replans 136, K 13, last_key 122, replan median 382.487 ms
  warehouse-10-20-10-2-1 N128 s3 bs: expanded 5413, replans 10852, K 26, last_key 122, replan median 4.072 ms
  warehouse-10-20-10-2-1 N192 s3 floww: expanded 5, replans 48, K 39, last_key 140, replan median 857.013 ms
  warehouse-10-20-10-2-1 N64 s4 flow: expanded 54, replans 121, K 13, last_key 139, replan median 559.821 ms
  warehouse-10-20-10-2-1 N128 s4 bs: expanded 4490, replans 9005, K 26, last_key 139, replan median 3.510 ms
  warehouse-10-20-10-2-1 N128 s4 floww: expanded 8, replans 41, K 26, last_key 139, replan median 931.781 ms
  warehouse-10-20-10-2-1 N256 s4 bspen: expanded 1708, replans 3468, K 52, last_key 139, replan median 13.265 ms
  warehouse-10-20-10-2-1 N64 s5 flow: expanded 20, replans 52, K 13, last_key 135, replan median 1651.876 ms
  warehouse-10-20-10-2-1 N128 s5 bs: expanded 2840, replans 5697, K 26, last_key 135, replan median 7.545 ms
  warehouse-10-20-10-2-1 N128 s5 floww: expanded 4, replans 33, K 26, last_key 135, replan median 998.861 ms
  warehouse-10-20-10-2-1 N64 s6 flow: expanded 21, replans 55, K 13, last_key 135, replan median 1384.342 ms
  warehouse-10-20-10-2-1 N128 s6 bs: expanded 1554, replans 3132, K 26, last_key 135, replan median 11.024 ms
  warehouse-10-20-10-2-1 N128 s6 floww: expanded 4, replans 33, K 26, last_key 135, replan median 1646.104 ms
  warehouse-10-20-10-2-1 N256 s6 bspen: expanded 1057, replans 2166, K 52, last_key 149, replan median 21.278 ms
  warehouse-10-20-10-2-1 N64 s7 flow: expanded 67, replans 147, K 13, last_key 118, replan median 417.722 ms
  warehouse-10-20-10-2-1 N128 s7 bs: expanded 2382, replans 4790, K 26, last_key 139, replan median 8.849 ms
  warehouse-10-20-10-2-1 N128 s7 floww: expanded 4, replans 33, K 26, last_key 139, replan median 1269.542 ms
  warehouse-10-20-10-2-1 N64 s8 flow: expanded 57, replans 126, K 13, last_key 129, replan median 462.705 ms
  warehouse-10-20-10-2-1 N128 s8 bs: expanded 3213, replans 6452, K 26, last_key 129, replan median 6.252 ms
  warehouse-10-20-10-2-1 N128 s8 floww: expanded 6, replans 38, K 26, last_key 129, replan median 803.338 ms
  warehouse-10-20-10-2-1 N64 s9 flow: expanded 23, replans 58, K 13, last_key 143, replan median 897.117 ms
  warehouse-10-20-10-2-1 N64 s9 floww: expanded 4, replans 20, K 13, last_key 143, replan median 2571.252 ms
  warehouse-10-20-10-2-1 N192 s9 bs: expanded 3242, replans 6504, K 39, last_key 143, replan median 4.819 ms
  warehouse-10-20-10-2-1 N64 s10 flow: expanded 50, replans 113, K 13, last_key 135, replan median 573.055 ms
  warehouse-10-20-10-2-1 N128 s10 bs: expanded 2889, replans 5804, K 26, last_key 135, replan median 6.567 ms
  warehouse-10-20-10-2-1 N128 s10 floww: expanded 4, replans 34, K 26, last_key 135, replan median 1289.527 ms
  Berlin_1_256 N64 s1 flow: expanded 1, replans 14, K 13, last_key 233, replan median 5244.267 ms
  Berlin_1_256 N256 s1 bs: expanded 561, replans 1174, K 52, last_key 290, replan median 35.462 ms
  Berlin_1_256 N64 s2 flow: expanded 0, replans 13, K 13, last_key -1, replan median 4553.193 ms
  Berlin_1_256 N256 s2 bs: expanded 380, replans 811, K 52, last_key 299, replan median 50.242 ms
  Berlin_1_256 N64 s3 flow: expanded 1, replans 15, K 13, last_key 266, replan median 2351.126 ms
  Berlin_1_256 N256 s3 bs: expanded 386, replans 823, K 52, last_key 266, replan median 66.667 ms
  Berlin_1_256 N64 s4 flow: expanded 1, replans 15, K 13, last_key 218, replan median 3069.846 ms
  Berlin_1_256 N192 s4 bs: expanded 508, replans 1055, K 39, last_key 259, replan median 45.532 ms
  Berlin_1_256 N64 s6 flow: expanded 2, replans 16, K 13, last_key 217, replan median 3317.249 ms
  Berlin_1_256 N192 s6 bs: expanded 497, replans 1032, K 39, last_key 293, replan median 42.178 ms
  Berlin_1_256 N64 s7 flow: expanded 1, replans 14, K 13, last_key 238, replan median 3449.598 ms
  Berlin_1_256 N256 s8 bs: expanded 416, replans 884, K 52, last_key 293, replan median 52.441 ms
  Berlin_1_256 N256 s9 bs: expanded 464, replans 980, K 52, last_key 308, replan median 46.497 ms
  Berlin_1_256 N64 s10 flow: expanded 1, replans 14, K 13, last_key 264, replan median 3238.724 ms
  Paris_1_256 N64 s2 flow: expanded 1, replans 14, K 13, last_key 308, replan median 3832.837 ms
  Paris_1_256 N192 s2 bs: expanded 351, replans 741, K 39, last_key 308, replan median 77.370 ms
  Paris_1_256 N256 s3 bs: expanded 389, replans 829, K 52, last_key 345, replan median 57.737 ms
  Paris_1_256 N256 s4 bs: expanded 432, replans 915, K 52, last_key 388, replan median 44.418 ms
  Paris_1_256 N64 s5 flow: expanded 1, replans 14, K 13, last_key 290, replan median 3664.626 ms
  Paris_1_256 N192 s5 bs: expanded 531, replans 1101, K 39, last_key 309, replan median 40.936 ms
  Paris_1_256 N64 s6 flow: expanded 0, replans 13, K 13, last_key -1, replan median 2237.103 ms
  Paris_1_256 N192 s6 bs: expanded 394, replans 826, K 39, last_key 362, replan median 51.553 ms
  Paris_1_256 N64 s7 flow: expanded 1, replans 14, K 13, last_key 280, replan median 3239.699 ms
  Paris_1_256 N256 s7 bs: expanded 468, replans 988, K 52, last_key 330, replan median 44.157 ms
  Paris_1_256 N64 s8 flow: expanded 1, replans 14, K 13, last_key 287, replan median 3163.371 ms
  Paris_1_256 N64 s9 flow: expanded 1, replans 15, K 13, last_key 274, replan median 3717.105 ms
  Paris_1_256 N256 s9 bs: expanded 564, replans 1179, K 52, last_key 274, replan median 37.060 ms
  Paris_1_256 N64 s10 flow: expanded 1, replans 15, K 13, last_key 276, replan median 1855.400 ms
  Paris_1_256 N192 s10 bs: expanded 373, replans 785, K 39, last_key 457, replan median 72.289 ms
  Boston_0_256 N64 s1 flow: expanded 2, replans 16, K 13, last_key 270, replan median 3127.675 ms
  Boston_0_256 N192 s1 bs: expanded 312, replans 663, K 39, last_key 317, replan median 55.970 ms
  Boston_0_256 N192 s2 bs: expanded 592, replans 1223, K 39, last_key 296, replan median 34.233 ms
  Boston_0_256 N64 s3 flow: expanded 2, replans 16, K 13, last_key 280, replan median 3427.017 ms
  Boston_0_256 N192 s3 bs: expanded 491, replans 1021, K 39, last_key 340, replan median 45.661 ms
  Boston_0_256 N64 s4 flow: expanded 1, replans 14, K 13, last_key 309, replan median 2433.952 ms
  Boston_0_256 N192 s4 bs: expanded 569, replans 1176, K 39, last_key 326, replan median 43.198 ms
  Boston_0_256 N64 s5 flow: expanded 1, replans 15, K 13, last_key 310, replan median 2747.853 ms
  Boston_0_256 N192 s5 bs: expanded 224, replans 487, K 39, last_key 312, replan median 44.212 ms
  Boston_0_256 N256 s6 bs: expanded 470, replans 991, K 52, last_key 322, replan median 44.168 ms
  Boston_0_256 N256 s7 bs: expanded 440, replans 932, K 52, last_key 295, replan median 47.928 ms
  Boston_0_256 N64 s8 flow: expanded 1, replans 15, K 13, last_key 283, replan median 2912.203 ms
  Boston_0_256 N256 s8 bs: expanded 402, replans 856, K 52, last_key 350, replan median 49.215 ms
  Boston_0_256 N64 s9 flow: expanded 1, replans 15, K 13, last_key 285, replan median 2422.491 ms
  Boston_0_256 N192 s9 bs: expanded 514, replans 1067, K 39, last_key 274, replan median 44.245 ms
  Boston_0_256 N64 s10 flow: expanded 1, replans 14, K 13, last_key 281, replan median 3572.937 ms

### B.3 solved with lb and not with match (lost), and the other way (gained)

bs: lost 8, gained 26
  lost Paris_1_256 N192 s2: lb solved 52900 ms, match timeout 60003 ms
  lost random-64-64-10 N160 s1: lb solved 6523 ms, match timeout 60017 ms
  lost random-64-64-10 N160 s2: lb solved 2637 ms, match timeout 60011 ms
  lost random-64-64-10 N160 s5: lb solved 5307 ms, match timeout 60016 ms
  lost random-64-64-10 N160 s7: lb solved 4767 ms, match timeout 60012 ms
  lost room-32-32-4 N40 s8: lb solved 344 ms, match timeout 60031 ms
  lost room-32-32-4 N40 s10: lb solved 1199 ms, match timeout 60039 ms
  lost warehouse-10-20-10-2-1 N128 s5: lb solved 18951 ms, match timeout 60012 ms
  gained Berlin_1_256 N192 s5: lb timeout 60003 ms, match solved 33458 ms
  gained Berlin_1_256 N192 s7: lb timeout 60003 ms, match solved 42595 ms
  gained Berlin_1_256 N192 s8: lb timeout 60006 ms, match solved 33708 ms
  gained Berlin_1_256 N192 s9: lb timeout 60002 ms, match solved 23017 ms
  gained Berlin_1_256 N256 s5: lb timeout_skipped  ms, match solved 50238 ms
  gained Berlin_1_256 N256 s7: lb timeout_skipped  ms, match solved 47261 ms
  gained Berlin_1_256 N256 s10: lb timeout 60005 ms, match solved 40926 ms
  gained Boston_0_256 N192 s6: lb timeout 60002 ms, match solved 35701 ms
  gained Boston_0_256 N192 s7: lb timeout 60004 ms, match solved 31089 ms
  gained Boston_0_256 N192 s8: lb timeout 60002 ms, match solved 26619 ms
  gained Boston_0_256 N192 s10: lb timeout 60003 ms, match solved 20523 ms
  gained Boston_0_256 N256 s10: lb timeout_skipped  ms, match solved 42900 ms
  gained Paris_1_256 N128 s4: lb timeout 60003 ms, match solved 19688 ms
  gained Paris_1_256 N128 s6: lb timeout 60002 ms, match solved 16005 ms
  gained Paris_1_256 N192 s3: lb timeout 60001 ms, match solved 23996 ms
  gained Paris_1_256 N192 s4: lb timeout_skipped  ms, match solved 55698 ms
  gained Paris_1_256 N192 s7: lb timeout 60003 ms, match solved 17251 ms
  gained Paris_1_256 N192 s8: lb timeout 60004 ms, match solved 31000 ms
  gained Paris_1_256 N256 s1: lb timeout 60002 ms, match solved 47939 ms
  gained Paris_1_256 N256 s8: lb timeout_skipped  ms, match solved 50483 ms
  gained random-32-32-10 N80 s2: lb timeout 60035 ms, match solved 2636 ms
  gained random-64-64-10 N160 s3: lb timeout 60012 ms, match solved 30534 ms
  gained random-64-64-10 N160 s9: lb timeout 60013 ms, match solved 3184 ms
  gained room-32-32-4 N60 s4: lb timeout 60046 ms, match solved 1704 ms
  gained room-64-64-8 N80 s1: lb timeout 60014 ms, match solved 5682 ms
  gained warehouse-10-20-10-2-1 N128 s9: lb timeout 60013 ms, match solved 27840 ms
bspen: lost 9, gained 54
  lost maze-32-32-2 N40 s4: lb solved 5648 ms, match timeout 60023 ms
  lost maze-32-32-2 N60 s8: lb solved 3244 ms, match timeout 60014 ms
  lost maze-32-32-2 N60 s10: lb solved 1399 ms, match timeout 60020 ms
  lost room-64-64-8 N120 s1: lb solved 3298 ms, match timeout 60019 ms
  lost room-64-64-8 N120 s6: lb solved 9081 ms, match timeout 60006 ms
  lost room-64-64-8 N160 s2: lb solved 31136 ms, match timeout 60006 ms
  lost room-64-64-8 N160 s3: lb solved 6495 ms, match timeout 60007 ms
  lost warehouse-10-20-10-2-1 N192 s2: lb solved 8366 ms, match timeout 60010 ms
  lost warehouse-10-20-10-2-1 N256 s4: lb solved 6649 ms, match timeout 60007 ms
  gained Berlin_1_256 N192 s5: lb timeout 60004 ms, match solved 5468 ms
  gained Berlin_1_256 N192 s9: lb timeout 60004 ms, match solved 9923 ms
  gained Berlin_1_256 N256 s1: lb timeout 60005 ms, match solved 9004 ms
  gained Berlin_1_256 N256 s2: lb timeout 60004 ms, match solved 11175 ms
  gained Berlin_1_256 N256 s3: lb timeout 60004 ms, match solved 9190 ms
  gained Berlin_1_256 N256 s4: lb timeout 60005 ms, match solved 8600 ms
  gained Berlin_1_256 N256 s5: lb timeout_skipped  ms, match solved 7294 ms
  gained Berlin_1_256 N256 s6: lb timeout 60005 ms, match solved 7760 ms
  gained Berlin_1_256 N256 s7: lb timeout 60004 ms, match solved 8337 ms
  gained Berlin_1_256 N256 s8: lb timeout 60005 ms, match solved 9632 ms
  gained Berlin_1_256 N256 s9: lb timeout_skipped  ms, match solved 9283 ms
  gained Berlin_1_256 N256 s10: lb timeout 60005 ms, match solved 7411 ms
  gained Boston_0_256 N192 s1: lb timeout 60004 ms, match solved 4908 ms
  gained Boston_0_256 N192 s3: lb timeout 60005 ms, match solved 5917 ms
  gained Boston_0_256 N192 s5: lb timeout 60004 ms, match solved 4287 ms
  gained Boston_0_256 N192 s7: lb timeout 60004 ms, match solved 4747 ms
  gained Boston_0_256 N192 s8: lb timeout 60005 ms, match solved 6467 ms
  gained Boston_0_256 N256 s1: lb timeout_skipped  ms, match solved 12012 ms
  gained Boston_0_256 N256 s2: lb timeout 60006 ms, match solved 9118 ms
  gained Boston_0_256 N256 s3: lb timeout_skipped  ms, match solved 8528 ms
  gained Boston_0_256 N256 s4: lb timeout 60004 ms, match solved 6845 ms
  gained Boston_0_256 N256 s5: lb timeout_skipped  ms, match solved 7041 ms
  gained Boston_0_256 N256 s6: lb timeout 60005 ms, match solved 8963 ms
  gained Boston_0_256 N256 s7: lb timeout_skipped  ms, match solved 7942 ms
  gained Boston_0_256 N256 s8: lb timeout_skipped  ms, match solved 11562 ms
  gained Boston_0_256 N256 s9: lb timeout 60005 ms, match solved 7748 ms
  gained Boston_0_256 N256 s10: lb timeout 60004 ms, match solved 7136 ms
  gained Paris_1_256 N128 s3: lb timeout 60009 ms, match solved 4251 ms
  gained Paris_1_256 N128 s7: lb timeout 60004 ms, match solved 3034 ms
  gained Paris_1_256 N192 s3: lb timeout_skipped  ms, match solved 6342 ms
  gained Paris_1_256 N192 s4: lb timeout 60005 ms, match solved 6116 ms
  gained Paris_1_256 N192 s6: lb timeout 60006 ms, match solved 7176 ms
  gained Paris_1_256 N192 s7: lb timeout_skipped  ms, match solved 5062 ms
  gained Paris_1_256 N192 s10: lb timeout 60005 ms, match solved 5610 ms
  gained Paris_1_256 N256 s1: lb timeout 60006 ms, match solved 8728 ms
  gained Paris_1_256 N256 s2: lb timeout 60005 ms, match solved 9843 ms
  gained Paris_1_256 N256 s3: lb timeout_skipped  ms, match solved 9183 ms
  gained Paris_1_256 N256 s4: lb timeout_skipped  ms, match solved 7485 ms
  gained Paris_1_256 N256 s5: lb timeout 60005 ms, match solved 7390 ms
  gained Paris_1_256 N256 s6: lb timeout_skipped  ms, match solved 12408 ms
  gained Paris_1_256 N256 s7: lb timeout_skipped  ms, match solved 8936 ms
  gained Paris_1_256 N256 s8: lb timeout 60005 ms, match solved 8846 ms
  gained Paris_1_256 N256 s9: lb timeout 60004 ms, match solved 9171 ms
  gained Paris_1_256 N256 s10: lb timeout_skipped  ms, match solved 9015 ms
  gained maze-32-32-2 N40 s2: lb timeout 60034 ms, match solved 3381 ms
  gained room-32-32-4 N60 s8: lb timeout 60023 ms, match solved 427 ms
  gained room-32-32-4 N80 s7: lb timeout 60025 ms, match solved 36816 ms
  gained room-32-32-4 N80 s9: lb timeout 60032 ms, match solved 6791 ms
  gained room-64-64-8 N120 s4: lb timeout 60009 ms, match solved 7282 ms
  gained room-64-64-8 N160 s5: lb timeout 60007 ms, match solved 12497 ms
  gained room-64-64-8 N160 s7: lb timeout 60007 ms, match solved 26870 ms
  gained room-64-64-8 N160 s10: lb timeout 60009 ms, match solved 5551 ms
  gained warehouse-10-20-10-2-1 N192 s1: lb timeout 60006 ms, match solved 2978 ms
  gained warehouse-10-20-10-2-1 N256 s5: lb timeout 60005 ms, match solved 8075 ms
bscut: lost 0, gained 77
  gained Berlin_1_256 N128 s3: lb timeout 60006 ms, match solved 4895 ms
  gained Berlin_1_256 N128 s4: lb timeout 60007 ms, match solved 3736 ms
  gained Berlin_1_256 N128 s9: lb timeout 60009 ms, match solved 4914 ms
  gained Berlin_1_256 N192 s1: lb timeout 60012 ms, match solved 9128 ms
  gained Berlin_1_256 N192 s2: lb timeout 60009 ms, match solved 11544 ms
  gained Berlin_1_256 N192 s3: lb timeout_skipped  ms, match solved 9016 ms
  gained Berlin_1_256 N192 s4: lb timeout_skipped  ms, match solved 7351 ms
  gained Berlin_1_256 N192 s5: lb timeout 60010 ms, match solved 11150 ms
  gained Berlin_1_256 N192 s6: lb timeout 60007 ms, match solved 8543 ms
  gained Berlin_1_256 N192 s7: lb timeout 60008 ms, match solved 10338 ms
  gained Berlin_1_256 N192 s8: lb timeout 60009 ms, match solved 8756 ms
  gained Berlin_1_256 N192 s9: lb timeout_skipped  ms, match solved 9600 ms
  gained Berlin_1_256 N192 s10: lb timeout 60008 ms, match solved 7963 ms
  gained Berlin_1_256 N256 s1: lb timeout_skipped  ms, match solved 13941 ms
  gained Berlin_1_256 N256 s2: lb timeout_skipped  ms, match solved 17716 ms
  gained Berlin_1_256 N256 s3: lb timeout_skipped  ms, match solved 16464 ms
  gained Berlin_1_256 N256 s4: lb timeout_skipped  ms, match solved 13327 ms
  gained Berlin_1_256 N256 s5: lb timeout_skipped  ms, match solved 14269 ms
  gained Berlin_1_256 N256 s6: lb timeout_skipped  ms, match solved 12944 ms
  gained Berlin_1_256 N256 s7: lb timeout_skipped  ms, match solved 13964 ms
  gained Berlin_1_256 N256 s8: lb timeout_skipped  ms, match solved 14749 ms
  gained Berlin_1_256 N256 s9: lb timeout_skipped  ms, match solved 14477 ms
  gained Berlin_1_256 N256 s10: lb timeout_skipped  ms, match solved 13132 ms
  gained Boston_0_256 N128 s2: lb timeout 60006 ms, match solved 4280 ms
  gained Boston_0_256 N128 s3: lb timeout 60006 ms, match solved 3406 ms
  gained Boston_0_256 N128 s5: lb timeout 60009 ms, match solved 2865 ms
  gained Boston_0_256 N128 s6: lb timeout 60010 ms, match solved 3317 ms
  gained Boston_0_256 N128 s7: lb timeout 60009 ms, match solved 4089 ms
  gained Boston_0_256 N128 s8: lb timeout 60006 ms, match solved 4140 ms
  gained Boston_0_256 N128 s10: lb timeout 60009 ms, match solved 3297 ms
  gained Boston_0_256 N192 s1: lb timeout 60008 ms, match solved 7639 ms
  gained Boston_0_256 N192 s2: lb timeout_skipped  ms, match solved 9524 ms
  gained Boston_0_256 N192 s3: lb timeout_skipped  ms, match solved 8983 ms
  gained Boston_0_256 N192 s4: lb timeout 60007 ms, match solved 7341 ms
  gained Boston_0_256 N192 s5: lb timeout_skipped  ms, match solved 6201 ms
  gained Boston_0_256 N192 s6: lb timeout_skipped  ms, match solved 5447 ms
  gained Boston_0_256 N192 s7: lb timeout_skipped  ms, match solved 8308 ms
  gained Boston_0_256 N192 s8: lb timeout_skipped  ms, match solved 9188 ms
  gained Boston_0_256 N192 s9: lb timeout 60008 ms, match solved 5857 ms
  gained Boston_0_256 N192 s10: lb timeout_skipped  ms, match solved 6749 ms
  gained Boston_0_256 N256 s1: lb timeout_skipped  ms, match solved 26380 ms
  gained Boston_0_256 N256 s2: lb timeout_skipped  ms, match solved 17265 ms
  gained Boston_0_256 N256 s3: lb timeout_skipped  ms, match solved 15505 ms
  gained Boston_0_256 N256 s4: lb timeout_skipped  ms, match solved 12928 ms
  gained Boston_0_256 N256 s5: lb timeout_skipped  ms, match solved 11304 ms
  gained Boston_0_256 N256 s6: lb timeout_skipped  ms, match solved 11593 ms
  gained Boston_0_256 N256 s7: lb timeout_skipped  ms, match solved 16128 ms
  gained Boston_0_256 N256 s8: lb timeout_skipped  ms, match solved 17927 ms
  gained Boston_0_256 N256 s9: lb timeout_skipped  ms, match solved 12571 ms
  gained Boston_0_256 N256 s10: lb timeout_skipped  ms, match solved 14038 ms
  gained Paris_1_256 N128 s1: lb timeout 60012 ms, match solved 4409 ms
  gained Paris_1_256 N128 s3: lb timeout 60008 ms, match solved 10058 ms
  gained Paris_1_256 N128 s4: lb timeout 60005 ms, match solved 5292 ms
  gained Paris_1_256 N128 s5: lb timeout 60008 ms, match solved 3398 ms
  gained Paris_1_256 N128 s6: lb timeout 60006 ms, match solved 4275 ms
  gained Paris_1_256 N128 s7: lb timeout 60008 ms, match solved 4541 ms
  gained Paris_1_256 N128 s9: lb timeout 60005 ms, match solved 3589 ms
  gained Paris_1_256 N192 s1: lb timeout_skipped  ms, match solved 8044 ms
  gained Paris_1_256 N192 s2: lb timeout 60010 ms, match solved 11991 ms
  gained Paris_1_256 N192 s3: lb timeout_skipped  ms, match solved 8678 ms
  gained Paris_1_256 N192 s4: lb timeout_skipped  ms, match solved 9375 ms
  gained Paris_1_256 N192 s5: lb timeout_skipped  ms, match solved 6324 ms
  gained Paris_1_256 N192 s6: lb timeout_skipped  ms, match solved 9617 ms
  gained Paris_1_256 N192 s7: lb timeout_skipped  ms, match solved 6895 ms
  gained Paris_1_256 N192 s8: lb timeout 60007 ms, match solved 8157 ms
  gained Paris_1_256 N192 s9: lb timeout_skipped  ms, match solved 6326 ms
  gained Paris_1_256 N192 s10: lb timeout 60008 ms, match solved 6984 ms
  gained Paris_1_256 N256 s1: lb timeout_skipped  ms, match solved 17214 ms
  gained Paris_1_256 N256 s2: lb timeout_skipped  ms, match solved 16634 ms
  gained Paris_1_256 N256 s3: lb timeout_skipped  ms, match solved 15665 ms
  gained Paris_1_256 N256 s4: lb timeout_skipped  ms, match solved 13585 ms
  gained Paris_1_256 N256 s5: lb timeout_skipped  ms, match solved 11970 ms
  gained Paris_1_256 N256 s6: lb timeout_skipped  ms, match solved 15451 ms
  gained Paris_1_256 N256 s7: lb timeout_skipped  ms, match solved 10801 ms
  gained Paris_1_256 N256 s8: lb timeout_skipped  ms, match solved 13708 ms
  gained Paris_1_256 N256 s9: lb timeout_skipped  ms, match solved 13313 ms
  gained Paris_1_256 N256 s10: lb timeout_skipped  ms, match solved 14948 ms
flow: lost 0, gained 0
floww: lost 0, gained 6
  gained warehouse-10-20-10-2-1 N64 s5: lb timeout 60010 ms, match solved 57013 ms
  gained warehouse-10-20-10-2-1 N64 s6: lb timeout 60359 ms, match solved 59481 ms
  gained warehouse-10-20-10-2-1 N64 s10: lb timeout 60364 ms, match solved 31832 ms
  gained warehouse-10-20-10-2-1 N128 s1: lb timeout 60002 ms, match solved 57891 ms
  gained warehouse-10-20-10-2-1 N128 s2: lb timeout 60007 ms, match solved 41925 ms
  gained warehouse-10-20-10-2-1 N128 s3: lb timeout 60009 ms, match solved 57133 ms

### B.4 checks

match: instances solved by several variants 391, makespan differs: 0 []
match vs lb: solved match runs of instances also solved with lb 1284, makespan differs from the lb run: 0 []
match: solved 1381, valid 1381, not valid 0
lb: solved 1235, valid 1235, not valid 0

### B.5 small maps, bscut vs floww (as 1.1), match

### 1.1

| map | both solved | bscut faster | equal | floww faster | median floww / bscut | min | max | median ms bscut | median ms floww |
|---|---|---|---|---|---|---|---|---|---|
| empty-32-32 | 40 | 40 | 0 | 0 | 10.2 | 4.65 | 22 | 32 | 303 |
| random-32-32-10 | 40 | 40 | 0 | 0 | 8.4 | 3.00 | 22 | 34 | 282 |
| room-32-32-4 | 40 | 40 | 0 | 0 | 5.9 | 2.09 | 33 | 86 | 532 |
| maze-32-32-2 | 37 | 37 | 0 | 0 | 12.6 | 4.28 | 80 | 167 | 2683 |
| random-64-64-10 | 40 | 40 | 0 | 0 | 26.6 | 7.24 | 44 | 270 | 6000 |
| room-64-64-8 | 39 | 39 | 0 | 0 | 28.8 | 15.51 | 77 | 586 | 21357 |
| **all small** | 236 | 236 | 0 | 0 | 13.4 | 2.09 | 80 | 94 | 957 |

bscut slower than floww: 
instances with bscut total_ms < 10: 21

### B.6 large maps, bscut vs bspen, total_ms on instances solved by both, match

| map | both solved | bscut faster | equal | bspen faster | median bspen / bscut | median ms bscut | median ms bspen |
|---|---|---|---|---|---|---|---|
| warehouse-10-20-10-2-1 | 35 | 13 | 0 | 22 | 0.89 | 1100 | 1060 |
| Berlin_1_256 | 40 | 2 | 0 | 38 | 0.66 | 6487 | 4406 |
| Paris_1_256 | 40 | 0 | 0 | 40 | 0.70 | 6325 | 4227 |
| Boston_0_256 | 40 | 1 | 0 | 39 | 0.69 | 4864 | 4180 |
| **all large** | 155 | 16 | 0 | 139 | 0.70 | 4275 | 3197 |
