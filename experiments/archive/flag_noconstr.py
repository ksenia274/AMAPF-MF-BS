"""Week 7, C1: blockedToMove without constraints (explicitGoalWaits off: the code path of the original Bulk Search).

Usage (from experiments/): archive/flag_noconstr.py AUDIT_BS_TEAM_EXE N SEED
Tiny corridor maps of test_corridors.py, 2..6 robots, no constraints, 1..5 robots of other teams; bs, bspen, bscut
against brute force; sums the flag counters of an audit_build.py build.
"""
import os
import random
import subprocess
import sys
import tempfile
from collections import Counter
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, EXP)
import test_corridors as tc  # noqa: E402
from brute_force import min_makespan  # noqa: E402
from compare_brute import write_instance  # noqa: E402
from test_flow_team import low_args  # noqa: E402

exe = sys.argv[1]
N = int(sys.argv[2])
rng = random.Random(int(sys.argv[3]))
work = tempfile.mkdtemp()
tot, bad = Counter(), 0
for i in range(N):
    name, w, h, grid, free = tc.random_map(rng)
    k = rng.randint(2, min(6, len(free) - 1))
    starts, goals = rng.sample(free, k), rng.sample(free, k)
    ref = min_makespan(w, h, grid, starts, goals, set(), set())
    ref = max(ref, 1) if ref != -1 else -1
    mp, sc, cs = write_instance(work, w, h, grid, starts, goals, set(), set())
    others = [tc.walk(rng, free, rng.choice(free), rng.randint(2, 12)) for _ in range(rng.randint(1, 5))]
    L = max(len(r) for r in others)
    others = [r + [r[-1]] * (L - len(r)) for r in others]
    op = os.path.join(work, "g.others")
    with open(op, "w", newline="\n") as f:
        f.write(f"{L - 1} {len(others)}\n" + "".join(" ".join(f"{x},{y}" for x, y in r) + "\n" for r in others))
    for low in ("bs", "bspen", "bscut"):
        p = subprocess.run([exe, mp, sc, str(k), "-", cs, "--others", op, "--t-start", "1"] + low_args(low),
                           capture_output=True, text=True, timeout=120)
        t = int(p.stdout.split("T=")[1].split()[0]) if "T=" in p.stdout else -1
        a = tc.audit(p.stderr)
        tot.update({low + ":" + kk: v for kk, v in a.items() if kk.startswith("flag")})
        if t != ref:
            bad += 1
            print("MISMATCH", low, grid, starts, goals, others, t, ref)
print(N, "instances, mismatches", bad)
for kk in sorted(tot):
    print(" ", kk, tot[kk])
