#!/usr/bin/env python3
"""Audit build (week 7, C1): bs_team.exe and cbm.exe with counters of the visited test of Bulk Search.

Usage: audit_build.py OUT_DIR [--mingw C:\\ProgramData\\mingw64\\mingw64\\bin]
Copies bs_team.hpp, flow_team.hpp, bs_team.cpp, cbm.cpp to OUT_DIR, adds counters to the copy of bs_team.hpp and
builds OUT_DIR/bs_team.exe and OUT_DIR/cbm.exe. The search itself is not changed: only ++ of counters. At exit the
programs print to stderr "audit late_first=A flag_prune=B":
  late_first  an entry of a bulk (or bscut piece) expanded after a later entry of the same bulk was expanded: its
              interval stops before that entry (checkTimestepAndGetUnvisitedSafeInterval, the nxtVisited branch);
  flag_prune  an entry that may move (blockedToMove = false) dropped because an entry with blockedToMove = true at
              the same or an earlier step of the bulk was expanded (the visited key has no flag).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PATCHES = [
    ("#pragma once\n",
     "#pragma once\n#include <cstdio>\n"
     "struct AuditCounters\n{\n    long long lateFirst = 0, flagPrune = 0, flagPush[2] = {}, flagCancel[2] = {}, flagExpand[2] = {};\n"
     "    ~AuditCounters()\n    {\n"
     "        fprintf(stderr, \"audit late_first=%lld flag_prune=%lld flag_push_impl=%lld flag_push_expl=%lld \"\n"
     "                \"flag_cancel_impl=%lld flag_cancel_expl=%lld flag_expand_impl=%lld flag_expand_expl=%lld\\n\",\n"
     "                lateFirst, flagPrune, flagPush[0], flagPush[1], flagCancel[0], flagCancel[1], flagExpand[0], flagExpand[1]);\n"
     "    }\n};\n"
     "inline AuditCounters auditCounters;\n"),
    # pop: the entry is dropped
    ("            if (itrt->timeStep > prevBlock)\n            {\n                return make_pair(false, Interval());\n",
     "            if (itrt->timeStep > prevBlock)\n            {\n"
     "                if (itrt->blockedToMove && !timeStepCostPair.blockedToMove)\n"
     "                    ++auditCounters.flagPrune;\n"
     "                return make_pair(false, Interval());\n"),
    # pop: an earlier entry after a later one
    ("            nxtVisitedTimestep = itrt->timeStep;\n            return {true, Interval(timeStepCostPair.timeStep, nxtVisitedTimestep - 1)};\n",
     "            nxtVisitedTimestep = itrt->timeStep;\n            ++auditCounters.lateFirst;\n"
     "            return {true, Interval(timeStepCostPair.timeStep, nxtVisitedTimestep - 1)};\n"),
    # push: the entry is not pushed
    ("            if (itrt->timeStep > prevBlock)\n            {\n                return false;\n",
     "            if (itrt->timeStep > prevBlock)\n            {\n"
     "                if (itrt->blockedToMove && !timeStepCostPair.blockedToMove)\n"
     "                    ++auditCounters.flagPrune;\n"
     "                return false;\n"),
    # flagged nodes: pushed (by the source of the flag), expanded; split by explicitGoalWaits
    ("    void push(TimestepCostPair p, int parent, int cellID, int pen = 0) { q.push(",
     "    void push(TimestepCostPair p, int parent, int cellID, int pen = 0) {\n"
     "        if (p.blockedToMove) ++auditCounters.flagPush[explicitGoalWaits];\n        q.push("),
    ("                timeStepsWithMoveBlocked.push_back(make_pair(it.h - 1, it.h - 1 >= timeAssigningGoalCell[cellDestination]));\n",
     "                timeStepsWithMoveBlocked.push_back(make_pair(it.h - 1, it.h - 1 >= timeAssigningGoalCell[cellDestination]));\n"
     "                if (it.h - 1 >= timeAssigningGoalCell[cellDestination]) ++auditCounters.flagCancel[explicitGoalWaits];\n"),
    ("                if (tp.timeStepCostPair.blockedToMove)\n                {\n",
     "                if (tp.timeStepCostPair.blockedToMove)\n                {\n"
     "                    ++auditCounters.flagExpand[explicitGoalWaits];\n"),
]


def main():
    out = os.path.abspath(sys.argv[1])
    mingw = sys.argv[sys.argv.index("--mingw") + 1] if "--mingw" in sys.argv else r"C:\ProgramData\mingw64\mingw64\bin"
    os.makedirs(out, exist_ok=True)
    for f in ("bs_team.hpp", "flow_team.hpp", "bs_team.cpp", "cbm.cpp"):
        shutil.copy(os.path.join(HERE, f), os.path.join(out, f))
    p = os.path.join(out, "bs_team.hpp")
    with open(p, encoding="utf-8", newline="") as f:
        s = f.read().replace("\r\n", "\n")
    for a, b in PATCHES:
        assert s.count(a) == 1, a
        s = s.replace(a, b)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    env = dict(os.environ, PATH=mingw + os.pathsep + os.environ["PATH"])
    for name in ("bs_team", "cbm"):
        r = subprocess.run(["g++", "-O3", "-static", "-o", name + ".exe", name + ".cpp"], cwd=out, env=env)
        if r.returncode:
            sys.exit(f"build of {name} failed")
    print("built", out)


if __name__ == "__main__":
    main()
