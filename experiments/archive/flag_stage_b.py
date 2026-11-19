#!/usr/bin/env python3
"""Week 7: does the visited test of stage B (one set for flagged and normal entries) ever drop or shorten a normal
entry because of a flagged one? Re-runs stage B instances with an audit build of the code of stage B.

Usage (from experiments/): archive/flag_stage_b.py AUDIT_CBM_EXE OUT_CSV [--per 5]
  AUDIT_CBM_EXE  cbm.exe of `audit_build.py OUT --rev a615290`
For warehouse and the three cities, bspen and bscut: the `--per` solved instances of cbm_bench_cactus_match.csv with
the largest N (then the smallest scen). Same arguments as stage B (--t-start match, 60 s, 8000 MB). T, nodes and
status must equal the CSV row; the audit counters (flag_prune, flag_trunc, ...) go to OUT_CSV.
"""
import csv
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cbm_bench import field, map_and_scen
from cbm_bench_cactus import LOW_ARGS
from cbm_paper_exp1 import grouped_scen
from test_corridors import audit

MAPS = ["warehouse-10-20-10-2-1", "Berlin_1_256", "Paris_1_256", "Boston_0_256"]


def main():
    exe, out = sys.argv[1], sys.argv[2]
    per = int(sys.argv[sys.argv.index("--per") + 1]) if "--per" in sys.argv else 5
    rows = [r for r in csv.DictReader(open("cbm_bench_cactus_match.csv")) if r["status"] == "solved"]
    tasks = []
    for m in MAPS:
        for v in ("bspen", "bscut"):
            sel = sorted((r for r in rows if r["map"] == m and r["variant"] == v), key=lambda r: (-int(r["N"]), int(r["scen"])))
            tasks += sel[:per]
    tmp = tempfile.mkdtemp()
    keys = None
    with open(out, "w", newline="") as f:
        w = None
        for r in tasks:
            mp, src = map_and_scen(r["map"], int(r["scen"]))
            scen = os.path.join(tmp, "g.scen")
            k = grouped_scen(src, int(r["N"]), scen)
            cmd = [exe, mp, scen, r["N"], str(k), "-"] + LOW_ARGS.get(r["variant"], ["--low", r["variant"]]) + \
                  ["--time-limit", "60", "--mem-limit", "8000", "--t-start", "match"]
            p = subprocess.run(cmd, capture_output=True, text=True)
            a = audit(p.stderr)
            keys = keys or list(a)
            got = {x: field(p.stdout, x) for x in ("status", "T", "nodes_generated", "nodes_expanded", "total_ms")}
            same = all(str(got[x]) == r[x] for x in ("status", "T", "nodes_generated", "nodes_expanded"))
            row = {"map": r["map"], "N": r["N"], "scen": r["scen"], "variant": r["variant"], "T": got["T"],
                   "nodes_expanded": got["nodes_expanded"], "total_ms": got["total_ms"], "stage_b_ms": r["total_ms"],
                   "same_as_stage_b": int(same), **a}
            if w is None:
                w = csv.DictWriter(f, list(row))
                w.writeheader()
            w.writerow(row)
            f.flush()
            print(r["map"], r["N"], r["scen"], r["variant"], "same" if same else "DIFFERENT",
                  " ".join(f"{x}={a.get(x)}" for x in ("flag_prune", "flag_trunc", "flag_push_impl", "flag_push_expl",
                                                       "flag_cancel_impl", "flag_cancel_expl")), flush=True)


if __name__ == "__main__":
    main()
