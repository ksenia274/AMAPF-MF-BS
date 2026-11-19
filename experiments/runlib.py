"""Run IDs, manifests and the run registry, shared by the run scripts and the plot scripts.

A run has an ID R<YYYYMMDD>-<name> and a folder runs/<ID>/ with manifest.json, results.csv (every row has a run_id
column) and run.log. runs/REGISTRY.md is generated from all runs/*/manifest.json (update_registry). Runs made before
the IDs (legacy) have only a manifest.json there, which points to their files in experiments/; a snapshot of a run (a
subset of its CSV) has the ID <ID>@<tag>.
Plot scripts take the ID from the run_id column of the CSV, or else from the manifest that lists the CSV (run_meta).
"""
import csv
import ctypes
import datetime
import hashlib
import json
import os
import platform
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
ID_RE = re.compile(r"^R\d{8}-[a-z0-9][a-z0-9-]*$")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def make_id(name, run_id=None):
    rid = run_id or f"R{datetime.date.today():%Y%m%d}-{name}"
    if not ID_RE.match(rid):
        sys.exit(f"bad run ID {rid!r}: expected R<YYYYMMDD>-<name>, name of a-z, 0-9 and '-'")
    return rid


def git_state():
    def git(*a):
        return subprocess.run(["git", *a], cwd=HERE, capture_output=True, text=True).stdout
    # tracked files only; the runs/ folder itself is not code
    dirty = [ln[3:] for ln in git("status", "--porcelain", "--untracked-files=no").splitlines()
             if not ln[3:].startswith("experiments/runs/")]
    return {"commit": git("rev-parse", "--short", "HEAD").strip(), "dirty": bool(dirty), "dirty_files": dirty}


def machine():
    m = {"node": platform.node(), "os": platform.platform(), "cpu": platform.processor(), "cpus": os.cpu_count(),
         "python": platform.python_version()}
    if os.name == "nt":
        class MemStatus(ctypes.Structure):
            _fields_ = [("len", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (f, ctypes.c_ulonglong) for f in ("total", "avail", "ptotal", "pavail", "vtotal", "vavail", "ext")]
        st = MemStatus()
        st.len = ctypes.sizeof(MemStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            m["ram_mb"] = st.total // 2 ** 20
    return m


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


class Run:
    """runs/<ID>/: manifest.json, results.csv, run.log. resume=True continues an existing run (same params)."""

    def __init__(self, run_id, script, params, resume, note="", exe=None):
        self.id = run_id
        self.dir = os.path.join(RUNS, run_id)
        self.manifest_path = os.path.join(self.dir, "manifest.json")
        self.csv_path = os.path.join(self.dir, "results.csv")
        self.log_path = os.path.join(self.dir, "run.log")
        session = {"started": now(), **git_state(), "argv": sys.argv[1:]}
        if exe:
            session["exe_sha256"] = sha256(exe)
        if os.path.exists(self.manifest_path):
            if not resume:
                sys.exit(f"run {run_id} exists; --resume continues it")
            with open(self.manifest_path, encoding="utf-8") as f:
                self.m = json.load(f)
            if self.m["params"] != params:
                diff = {k: (self.m["params"].get(k), params.get(k)) for k in set(self.m["params"]) | set(params)
                        if self.m["params"].get(k) != params.get(k)}
                sys.exit(f"run {run_id} has other params (old, new): {diff}")
            self.m["finished"] = None
            self.m["sessions"].append(session)
        else:
            if resume:
                sys.exit(f"run {run_id} does not exist, nothing to resume")
            os.makedirs(self.dir)
            self.m = {"run_id": run_id, "script": script, "note": note, "started": session["started"],
                      "finished": None, "commit": session["commit"], "dirty": session["dirty"],
                      "machine": machine(), "params": params,
                      "files": [{"path": "results.csv", "role": "results"}, {"path": "run.log", "role": "log"}],
                      "sessions": [session]}
        self.save()

    def save(self):
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.m, f, ensure_ascii=False, indent=2)
        update_registry()

    def log(self, *args):
        line = " ".join(str(a) for a in args)
        print(line, flush=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def finish(self):
        self.m["finished"] = self.m["sessions"][-1]["finished"] = now()
        self.save()


def manifests():
    out = []
    if os.path.isdir(RUNS):
        for d in sorted(os.listdir(RUNS)):
            p = os.path.join(RUNS, d, "manifest.json")
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    out.append(json.load(f))
    return out


def run_meta(csv_path):
    """(ID, manifest) of the run that wrote csv_path: from its run_id column, else from the manifest listing it."""
    with open(csv_path, newline="") as f:
        rd = csv.DictReader(f)
        ids = {r["run_id"] for r in rd} if "run_id" in (rd.fieldnames or []) else set()
    if len(ids) > 1:
        raise ValueError(f"{csv_path}: several run IDs {sorted(ids)}")
    rid = ids.pop() if ids else None
    target = os.path.normcase(os.path.abspath(csv_path))
    for m in manifests():
        if rid:
            if m["run_id"] == rid.split("@")[0]:
                return rid, m
            continue
        for fl in m["files"]:
            if os.path.normcase(os.path.abspath(os.path.join(RUNS, m["run_id"], fl["path"]))) == target:
                return m["run_id"] + fl.get("snapshot", ""), m
    raise ValueError(f"{csv_path}: " + (f"no manifest for run {rid}" if rid else "no run_id column and no manifest lists it"))


def teams_text(teams):
    kind, k = teams.split(":")
    if kind == "fixed":
        return f"K = {k.replace(',', ', ')}"
    return f"по {k} (K = ⌈N/{k}⌉)" if kind == "size" else f"{k} команды"


def caption(run_id, m, maps):
    p = m["params"]
    return (f"{run_id} · карты: {', '.join(maps)} · лимит {p['time_limit']:g} с · команды {teams_text(p['teams'])} · "
            f"старт T: {p['t_start']}")


def update_registry():
    rows = []
    for m in manifests():
        p = m["params"]
        files = ", ".join(f"`{os.path.normpath(os.path.join('runs', m['run_id'], fl['path'])).replace(os.sep, '/')}`"
                          + (f" ({fl['snapshot']})" if "snapshot" in fl else "") for fl in m["files"])
        state = "legacy" if m.get("legacy") else ("done" if m["finished"] else "not finished")
        if m.get("id_assigned"):
            state += ", ID по дате файла"
        par = p.get("summary") or summary_of(p)
        if p.get("summary") and p.get("t_start") and "старт T" not in par:
            par += f"; старт T {p['t_start']}"
        commit = m["commit"] or "?"
        if m.get("commits_with_results"):
            commit += "; результаты: " + ", ".join(m["commits_with_results"])
        if m.get("dirty"):
            commit += " + changes"
        rows.append(f"| {m['run_id']} | {state} | {(m['started'] or '?')[:16].replace('T', ' ')} | "
                    f"{(m['finished'] or '?')[:16].replace('T', ' ')} | `{m['script']}` | {commit} | "
                    f"{par} | {files} | {m.get('note', '')} |")
    with open(os.path.join(RUNS, "REGISTRY.md"), "w", encoding="utf-8") as f:
        f.write("# Прогоны\n\nФайл создаётся из `runs/*/manifest.json` (`runlib.update_registry`), руками не править.\n"
                "Пути файлов — от `experiments/`. legacy: прогон до появления ID, его manifest заполнен задним числом.\n\n"
                "| ID | состояние | начало | конец | скрипт | коммит | параметры | файлы | что это |\n"
                "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")


def summary_of(p):
    return (f"карты: {', '.join(p['maps'])}; сценарии {p['scens']}; N: "
            + "; ".join(ns if isinstance(ns, str) else ",".join(map(str, ns))
                        for ns in dict.fromkeys(v if isinstance(v, str) else tuple(v) for v in p["N"].values()))
            + f"; команды {teams_text(p['teams'])}; лимит {p['time_limit']:g} с, {p['mem_limit']} МБ; "
            f"варианты {', '.join(p['variants'])}; старт T {p['t_start']}"
            + ("; без правила пропуска" if p.get("stopping_rule") == "none" else "")
            + (f"; продолжение {p['continue_from']}" if p.get("continue_from") else "")
            + (f"; повтор тайм-аутов {p['retry_timeouts']}" if p.get("retry_timeouts") else ""))
