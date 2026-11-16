#!/usr/bin/env python3
"""Week 6, part 2: profile of the root (cbm_prof.exe = cbm.cpp built with -DBS_PROFILE) and the assignment bound.

Usage: week6_part2.py run [--reps 3]   runs cbm_prof.exe --root-only last one by one, raw stderr in week6_prof/
       week6_part2.py report           tables (markdown) from week6_prof/, week6_root_teams.csv, week6_root_T.csv
Instances: random scen 1 of the map, N = 128, teams of 5 (K = 26, as cbm_bench_cactus), --t-start lb, every call with
its own limit of 600 s. Berlin_1_256, room-64-64-8, warehouse-10-20-10-2-1: bs, bspen, bscut (--cut penal), --reps
runs each; Paris_1_256, Boston_0_256: the same variants, one run (for 2.3); Berlin_1_256 N = 64: floww, one run.
Log lines (cbm.cpp, BS_PROFILE): "prof call=.. team=.. ms=.. total=<cycles> prep=.. solve=.. ..." per low-level call,
"prof_T call=.. team=.. T=.. ..." per T tried in it. The call K+1 is the extra call of --root-only at the final T of
the last team; it is not part of the root and is ignored.
Assignment bound (2.3): BFS from every goal of the team; the smallest D such that the robots can be matched to
distinct goals with all distances <= D (bottleneck assignment, here by trying all permutations, teams have <= 5).
"""
import argparse
import collections
import csv
import itertools
import os
import statistics
import subprocess
import tempfile

from cbm_bench import map_and_scen
from cbm_paper_exp1 import grouped_scen

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "week6_prof")
MAIN = ["Berlin_1_256", "room-64-64-8", "warehouse-10-20-10-2-1"]
EXTRA = ["Paris_1_256", "Boston_0_256"]
VARIANTS = {"bs": ["--low", "bs"], "bspen": ["--low", "bspen"], "bscut": ["--low", "bscut", "--cut", "penal"]}
N = 128


def jobs(reps):
    for m in MAIN:
        for v in VARIANTS:
            for r in range(reps):
                yield m, N, v, r
    for m in EXTRA:
        for v in VARIANTS:
            yield m, N, v, 0
    yield "Berlin_1_256", 64, "floww", 0


def log_path(m, n, v, r):
    return os.path.join(LOGS, f"{m}_N{n}_{v}_{r}.log")


def run(reps):
    os.makedirs(LOGS, exist_ok=True)
    tmp = tempfile.mkdtemp()
    for m, n, v, r in jobs(reps):
        out = log_path(m, n, v, r)
        if os.path.exists(out) and "status=" in open(out).read():
            continue
        mp, src = map_and_scen(m, 1)
        scen = os.path.join(tmp, "g.scen")
        k = grouped_scen(src, n, scen)
        args = VARIANTS.get(v, ["--low", v])
        cmd = [os.path.join(HERE, "cbm_prof.exe"), mp, scen, str(n), str(k), "-", "--root-only", "last", "--t-start", "lb",
               "--time-limit", "600" if v != "floww" else "1800", "--mem-limit", "8000"] + args
        p = subprocess.run(cmd, capture_output=True, text=True)
        with open(out, "w") as f:
            f.write(p.stderr + p.stdout)
        print(m, n, v, r, p.stdout.strip()[:160], flush=True)


def kv(line):
    return {a: b for a, b in (x.split("=", 1) for x in line.split()[1:] if "=" in x)}


def parse(path):
    calls, perT, head = {}, collections.defaultdict(list), {}
    for line in open(path):
        if line.startswith("prof_overhead"):
            head = {a: float(b) for a, b in kv(line).items()}
        elif line.startswith("prof_T "):
            d = kv(line)
            perT[int(d["call"])].append(d)
        elif line.startswith("prof "):
            d = kv(line)
            calls[int(d["call"])] = d
        elif line.startswith("status="):
            head["status"] = line.split()[0][7:]
            head["K"] = int(kv("x " + line)["K"])
    k = head["K"]
    root = [calls[c] for c in sorted(calls) if c <= k]
    return head, root, {c: perT[c] for c in perT if c <= k}


def ms(cycles, ghz):
    return float(cycles) / ghz / 1e6


def load(m, n, v):
    runs = []
    r = 0
    while os.path.exists(log_path(m, n, v, r)):
        runs.append(parse(log_path(m, n, v, r)))
        r += 1
    return runs


# 2.1: parts of the call of the last team, cycles -> ms with the TSC frequency of the run, median over the runs
PARTS = ["prep", "cutBuild", "heur", "clear", "check", "cutLookup", "pen", "expand", "addPath", "extract", "swaps", "destroy",
         "other"]
NAMES = {"prep": "подготовка (копия чужих маршрутов, штрафы, конструктор)", "cutBuild": "построение резов",
         "heur": "BFS-эвристика", "clear": "очистка посещённости", "check": "проверки кусков и посещённости",
         "cutLookup": "поиск в множествах резов", "pen": "штрафы (поиск в хеш-таблице)",
         "expand": "раскрытия (остальное в поиске)", "addPath": "разворот пути", "extract": "извлечение маршрутов",
         "swaps": "замена обменов", "destroy": "разрушение решателя", "other": "прочее"}


def parts_of(call, ghz):
    c = {x: float(call[x]) for x in ("total", "prep", "solve", "extract", "destroy", "swaps", "cutBuild", "heur", "clear",
                                       "search", "check", "cutLookup", "pen", "addPath")}
    p = {x: c[x] for x in ("prep", "cutBuild", "heur", "clear", "check", "cutLookup", "pen", "addPath", "extract", "swaps",
                           "destroy")}
    p["expand"] = c["search"] - c["check"] - c["cutLookup"] - c["pen"]
    p["other"] = c["total"] - sum(p.values())
    return {x: ms(y, ghz) for x, y in p.items()}


def report21():
    print("### 2.1 parts of the call of the last team (ms, median of the runs)\n")
    cols = [(m, v) for m in ("Berlin_1_256", "room-64-64-8") for v in ("bspen", "bscut")]
    plain = {(r["map"], r["variant"]): r["ms_median"] for r in csv.DictReader(open(os.path.join(HERE, "replan_cut.csv")))
             if r["which"] == "last"}
    data, extra = {}, {}
    for m, v in cols:
        runs = load(m, N, v)
        per = [parts_of(root[-1], h["tsc_ghz"]) for h, root, _ in runs]
        data[(m, v)] = {x: statistics.median(p[x] for p in per) for x in PARTS}
        last = [root[-1] for _, root, _ in runs]
        h = runs[0][0]
        n_regions = statistics.median(int(c["nCheck"]) + int(c["nCut"]) + int(c["nPen"]) for c in last)
        extra[(m, v)] = {
            "call ms (profiled)": statistics.median(float(c["ms"]) for c in last),
            "call ms (cbm.exe, replan_cut.csv)": float(plain[(m, v)]),
            "measured regions (checks + cut lookups + penalties)": n_regions,
            "estimated cost of their rdtsc pairs, ms": n_regions * h["pair_cycles"] / h["tsc_ghz"] / 1e6,
            "expansions": statistics.median(int(c["expansions"]) for c in last),
            "T tried": int(last[0]["T"]) - int(last[0]["minT"]) + 1}
    print("| часть | " + " | ".join(f"{m} {v}" for m, v in cols) + " |")
    print("|---|" + "---|" * len(cols))
    for x in PARTS:
        print(f"| {NAMES[x]} | " + " | ".join(f"{data[c][x]:.1f}" for c in cols) + " |")
    print("| **сумма** | " + " | ".join(f"**{sum(data[c].values()):.1f}**" for c in cols) + " |")
    for x in extra[cols[0]]:
        print(f"| {x} | " + " | ".join(f"{extra[c][x]:.1f}" if isinstance(extra[c][x], float) else str(extra[c][x]) for c in cols) + " |")
    print()
    for m in ("Berlin_1_256", "room-64-64-8"):
        a, b = data[(m, "bspen")], data[(m, "bscut")]
        diff = sum(b.values()) - sum(a.values())
        print(f"{m}: bscut - bspen = {diff:.1f} ms; of it " + ", ".join(
            f"{NAMES[x]} {b[x] - a[x]:+.1f}" for x in PARTS if abs(b[x] - a[x]) >= 0.05 * abs(diff)))
    print()


def per_T_ms(perT, ghz):
    return [{"T": int(p["T"]), "ok": int(p["ok"]), "paths": int(p.get("paths", 0)),
             **{x: ms(p[x], ghz) for x in ("heur", "clear", "search", "build", "maxflow", "mincost") if x in p}} for p in perT]


def report22(rows_teams, rows_T):
    print("### 2.2 the root call by call\n")
    summary = []
    for m in MAIN + EXTRA:
        for v in VARIANTS:
            runs = load(m, N, v)
            if not runs:
                continue
            K = runs[0][0]["K"]
            ok = all(h.get("status") == "solved" for h, _, _ in runs)
            teams = []
            for i in range(K):
                calls = [root[i] for _, root, _ in runs]
                c0 = calls[0]
                tried = int(c0["T"]) - int(c0["minT"]) + 1 if c0["T"] != "-1" else -1
                # per T: median over the runs of the parts (the T sequence is the same in every run)
                pts = [per_T_ms(perT[i + 1], h["tsc_ghz"]) for h, _, perT in runs]
                Ts = []
                for j in range(len(pts[0])):
                    Ts.append({"T": pts[0][j]["T"], "ok": pts[0][j]["ok"], "paths": pts[0][j]["paths"],
                               **{x: statistics.median(p[j][x] for p in pts) for x in ("heur", "clear", "search")}})
                team = {"map": m, "variant": v, "team": i, "lb": int(c0["minT"]), "T": int(c0["T"]), "tried": tried,
                        "ms": statistics.median(float(c["ms"]) for c in calls), "expansions": int(c0["expansions"]),
                        "fail_ms": sum(t["heur"] + t["clear"] + t["search"] for t in Ts if not t["ok"]),
                        "final_ms": sum(t["heur"] + t["clear"] + t["search"] for t in Ts if t["ok"]),
                        "heur": sum(t["heur"] for t in Ts), "clear": sum(t["clear"] for t in Ts),
                        "search": sum(t["search"] for t in Ts), "perT": Ts, "runs": len(runs)}
                teams.append(team)
                rows_teams.append({x: team[x] for x in team if x != "perT"})
                for t in Ts:
                    rows_T.append({"map": m, "variant": v, "team": i, **t})
            root_ms = sum(t["ms"] for t in teams)
            summary.append((m, v, K, ok, len(runs), root_ms, sum(t["tried"] for t in teams),
                            sum(t["fail_ms"] for t in teams), sum(t["final_ms"] for t in teams),
                            sum(t["heur"] for t in teams), sum(t["clear"] for t in teams), sum(t["search"] for t in teams),
                            teams))
    print("| map | variant | runs | root, ms | T tried (sum over teams) | on T < T_i, ms | on T = T_i, ms | share T < T_i | "
          "heuristic | clearing | search | rest of the calls |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for m, v, K, ok, runs, root_ms, tried, fail, final, heur, clear, search, _ in summary:
        print(f"| {m} | {v} | {runs} | {root_ms:.0f} | {tried} | {fail:.0f} | {final:.0f} | {fail / root_ms:.2f} | "
              f"{heur / root_ms:.2f} | {clear / root_ms:.2f} | {search / root_ms:.2f} | "
              f"{(root_ms - heur - clear - search) / root_ms:.2f} |" + ("" if ok else " (not solved)"))
    print()
    for m in MAIN:
        rows = {v: s[-1] for s in summary for v in VARIANTS if s[0] == m and s[1] == v}
        print(f"#### {m}: every team of the root (call ms: median of the runs)\n")
        print("| team | lb | T_i | T tried | ms bs | ms bspen | ms bscut | expansions bs | bspen | bscut |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for i, t in enumerate(rows["bs"]):
            for v in ("bspen", "bscut"):  # the minimal T does not depend on the variant
                assert (rows[v][i]["lb"], rows[v][i]["T"]) == (t["lb"], t["T"]), (m, v, i)
            print(f"| {i} | {t['lb']} | {t['T']} | {t['tried']} | " + " | ".join(f"{rows[v][i]['ms']:.1f}" for v in VARIANTS)
                  + " | " + " | ".join(str(rows[v][i]["expansions"]) for v in VARIANTS) + " |")
        print()
        tb = rows["bs"]
        pick = {"first": 0, "last": len(tb) - 1, "most T": max(range(len(tb)), key=lambda i: (tb[i]["tried"], -i))}
        print(f"Per T for the first, the last and the team with the most T tried ({m}); ms per T: mean over the "
              "failed T (T < T_i) and the final T (= T_i)\n")
        print("| team | variant | T tried | failed T: heuristic | clearing | search | final T: heuristic | clearing | search | "
              "paths found at the final T |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for name, i in pick.items():
            for v in VARIANTS:
                Ts = rows[v][i]["perT"]
                fail = [t for t in Ts if not t["ok"]]
                fin = [t for t in Ts if t["ok"]]
                f = lambda ts, x: f"{statistics.mean(t[x] for t in ts):.2f}" if ts else "—"
                print(f"| {name} ({i}) | {v} | {len(Ts)} | {f(fail, 'heur')} | {f(fail, 'clear')} | {f(fail, 'search')} | "
                      f"{f(fin, 'heur')} | {f(fin, 'clear')} | {f(fin, 'search')} | {fin[0]['paths'] if fin else '—'} |")
        print()
    return summary


def report22_floww():
    runs = load("Berlin_1_256", 64, "floww")
    if not runs:
        return
    h, root, perT = runs[0]
    print(f"#### Berlin_1_256 N=64 floww (one run, status {h.get('status')})\n")
    print("| team | lb | T_i | T tried | call, s | build, s per T (mean) | max flow, s per T | min-cost flow (final T), s |")
    print("|---|---|---|---|---|---|---|---|")
    total = 0
    for i, c in enumerate(root):
        Ts = per_T_ms(perT.get(i + 1, []), h["tsc_ghz"])
        total += float(c["ms"])
        fin = [t for t in Ts if t["ok"]]
        print(f"| {i} | {c['minT']} | {c['T']} | {len(Ts)} | {float(c['ms']) / 1000:.1f} | "
              f"{statistics.mean(t['build'] for t in Ts) / 1000:.2f} | {statistics.mean(t['maxflow'] for t in Ts) / 1000:.2f} | "
              f"{fin[0]['mincost'] / 1000 if fin else float('nan'):.2f} |")
    print(f"\nroot: {total / 1000:.1f} s over {len(root)} calls\n")


def load_grid(path):
    rows = open(path).read().split("\n")
    h, w = int(rows[1].split()[1]), int(rows[2].split()[1])
    grid = [rows[4 + i][:w] for i in range(h)]
    return grid, w, h


def bfs(grid, w, h, src):
    dist = {src: 0}
    q = collections.deque([src])
    while q:
        x, y = q.popleft()
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in dist and grid[ny][nx] not in "@T":
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return dist


def bounds(m, n):
    """Per team of the grouped scen: (lb, assignment bound)."""
    mp, src = map_and_scen(m, 1)
    tmp = tempfile.mkdtemp()
    scen = os.path.join(tmp, "g.scen")
    k = grouped_scen(src, n, scen)
    grid, w, h = load_grid(mp)
    agents = [line.split() for line in open(scen).read().splitlines()[1:1 + n]]
    res = []
    for team in range(k):
        mine = [agents[i] for i in range(team, n, k)]
        starts = [(int(a[4]), int(a[5])) for a in mine]
        goals = [(int(a[6]), int(a[7])) for a in mine]
        d = [bfs(grid, w, h, g) for g in goals]
        inf = float("inf")
        lb = max(min(dg.get(s, inf) for dg in d) for s in starts)
        assign = min(max(d[p[i]].get(s, inf) for i, s in enumerate(starts)) for p in itertools.permutations(range(len(goals))))
        res.append((lb, assign))
    return res


def report23(summary):
    print("### 2.3 assignment bound\n")
    print("| map | teams | lb = T_i | bound = T_i | bound > lb | T tried now (sum) | T tried with the bound | "
          "share of the root time on T < bound (bs / bspen / bscut) |")
    print("|---|---|---|---|---|---|---|---|")
    errors = []
    detail = []
    for m in MAIN + EXTRA:
        by_v = {s[1]: s[-1] for s in summary if s[0] == m}
        teams = by_v["bs"]
        b = bounds(m, N)
        shares = []
        for v in VARIANTS:
            root_ms = sum(t["ms"] for t in by_v[v])
            saved = 0
            for t, (lb, a) in zip(by_v[v], b):
                saved += sum(x["heur"] + x["clear"] + x["search"] for x in t["perT"] if x["T"] < a)
            shares.append(saved / root_ms)
        now = later = 0
        n_lb = n_a = n_gt = 0
        for i, (t, (lb, a)) in enumerate(zip(teams, b)):
            if lb != t["lb"]:
                errors.append(f"{m} team {i}: lb python {lb} != cbm {t['lb']}")
            if not lb <= a <= t["T"]:
                errors.append(f"{m} team {i}: lb {lb}, bound {a}, T_i {t['T']}")
            now += t["T"] - lb + 1
            later += t["T"] - max(a, lb) + 1
            n_lb += lb == t["T"]
            n_a += a == t["T"]
            n_gt += a > lb
            detail.append((m, i, lb, a, t["T"]))
        print(f"| {m} | {len(teams)} | {n_lb} | {n_a} | {n_gt} | {now} | {later} | " + " / ".join(f"{x:.2f}" for x in shares) + " |")
    print("\nerrors:", errors or "none")
    print("\nper team (map, team, lb, bound, T_i), teams with bound > lb:")
    for m, i, lb, a, T in detail:
        if a > lb:
            print(f"  {m} {i}: {lb} {a} {T}")
    return errors


def report():
    rows_teams, rows_T = [], []
    report21()
    summary = report22(rows_teams, rows_T)
    report22_floww()
    errors = report23(summary)
    for name, rows in (("week6_root_teams.csv", rows_teams), ("week6_root_T.csv", rows_T)):
        with open(os.path.join(HERE, name), "w", newline="") as f:
            w = csv.DictWriter(f, list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    if errors:
        raise SystemExit("assignment bound outside [lb, T_i]: STOP")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "report"])
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    run(a.reps) if a.cmd == "run" else report()


if __name__ == "__main__":
    main()
