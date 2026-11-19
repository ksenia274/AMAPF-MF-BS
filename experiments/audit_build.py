#!/usr/bin/env python3
"""Audit build (week 7, C1): bs_team.exe and cbm.exe with counters of the visited test of Bulk Search.

Usage: audit_build.py OUT_DIR [--rev GIT_REV] [--mingw C:\\ProgramData\\mingw64\\mingw64\\bin]
Copies bs_team.hpp, flow_team.hpp, bs_team.cpp, cbm.cpp (from the working copy, or from GIT_REV) to OUT_DIR, adds
counters to the copy of bs_team.hpp and builds OUT_DIR/bs_team.exe and OUT_DIR/cbm.exe. The search itself is not
changed: only ++ of counters. At exit the programs print to stderr "audit late_first=A flag_prune=B ...":
  late_first  an entry of a bulk (or bscut piece) expanded after a later entry of the same bulk was expanded: its
              interval stops before that entry (checkTimestepAndGetUnvisitedSafeInterval, the nxtVisited branch);
  flag_prune  an entry that may move (blockedToMove = false) meets an expanded entry with blockedToMove = true at the
              same or an earlier step of its bulk. Before the fix of the visited test (no visitedBlocked) the entry
              is dropped; after the fix it is kept;
  flag_trunc  an entry that may move whose first expanded later entry in the bulk has blockedToMove = true: its
              interval stops before that entry, before and after the fix (rule (B) is not changed by it);
  flag_push_*, flag_cancel_*, flag_expand_*  flagged entries pushed, of them from the cancel of a move out of a taken
              goal, flagged entries expanded; impl/expl = explicitGoalWaits off/on.
flag_prune = 0 in a run means the fix changes nothing in that run.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PATCHES = [
    ("#pragma once\n",
     "#pragma once\n#include <cstdio>\n"
     "struct AuditCounters\n{\n"
     "    long long lateFirst = 0, flagPrune = 0, flagTrunc = 0, flagPush[2] = {}, flagCancel[2] = {}, flagExpand[2] = {};\n"
     "    ~AuditCounters()\n    {\n"
     "        fprintf(stderr, \"audit late_first=%lld flag_prune=%lld flag_trunc=%lld flag_push_impl=%lld flag_push_expl=%lld \"\n"
     "                \"flag_cancel_impl=%lld flag_cancel_expl=%lld flag_expand_impl=%lld flag_expand_expl=%lld\\n\",\n"
     "                lateFirst, flagPrune, flagTrunc, flagPush[0], flagPush[1], flagCancel[0], flagCancel[1], flagExpand[0],\n"
     "                flagExpand[1]);\n"
     "    }\n};\n"
     "inline AuditCounters auditCounters;\n"),
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

# before the fix: one visited set for both kinds of entries
PATCHES_ONE_SET = [
    # pop: the entry is dropped
    ("            if (itrt->timeStep > prevBlock)\n            {\n                return make_pair(false, Interval());\n",
     "            if (itrt->timeStep > prevBlock)\n            {\n"
     "                if (itrt->blockedToMove && !timeStepCostPair.blockedToMove)\n"
     "                    ++auditCounters.flagPrune;\n"
     "                return make_pair(false, Interval());\n"),
    # pop: the interval stops before a later expanded entry
    ("            nxtVisitedTimestep = itrt->timeStep;\n            return {true, Interval(timeStepCostPair.timeStep, nxtVisitedTimestep - 1)};\n",
     "            nxtVisitedTimestep = itrt->timeStep;\n            ++auditCounters.lateFirst;\n"
     "            if (itrt->blockedToMove && !timeStepCostPair.blockedToMove)\n"
     "                ++auditCounters.flagTrunc;\n"
     "            return {true, Interval(timeStepCostPair.timeStep, nxtVisitedTimestep - 1)};\n"),
    # push: the entry is not pushed
    ("            if (itrt->timeStep > prevBlock)\n            {\n                return false;\n",
     "            if (itrt->timeStep > prevBlock)\n            {\n"
     "                if (itrt->blockedToMove && !timeStepCostPair.blockedToMove)\n"
     "                    ++auditCounters.flagPrune;\n"
     "                return false;\n"),
]

# after the fix (visitedBlocked): count where the old rule would have dropped or shortened a normal entry
PATCHES_TWO_SETS = [
    ("        if (coveredBy(visitedTimeSTeps[cellID], ts, prevBlock) || (flagged && coveredBy(visitedBlocked[cellID], ts, prevBlock)))\n"
     "            return make_pair(false, Interval());\n",
     "        if (coveredBy(visitedTimeSTeps[cellID], ts, prevBlock) || (flagged && coveredBy(visitedBlocked[cellID], ts, prevBlock)))\n"
     "            return make_pair(false, Interval());\n"
     "        if (!flagged && coveredBy(visitedBlocked[cellID], ts, prevBlock))\n"
     "            ++auditCounters.flagPrune;\n"
     "        else if (!flagged && nextVisited(visitedBlocked[cellID], ts) < min(nextVisited(visitedTimeSTeps[cellID], ts), nxtBlock + 1))\n"
     "            ++auditCounters.flagTrunc;\n"),
    ("            return {true, Interval(ts, nxtVisitedTimestep - 1)};\n",
     "        {\n            ++auditCounters.lateFirst;\n            return {true, Interval(ts, nxtVisitedTimestep - 1)};\n        }\n"),
    ("        return !coveredBy(visitedTimeSTeps[cellID], ts, prevBlock) &&\n",
     "        if (!timeStepCostPair.blockedToMove && !coveredBy(visitedTimeSTeps[cellID], ts, prevBlock) &&\n"
     "            coveredBy(visitedBlocked[cellID], ts, prevBlock))\n"
     "            ++auditCounters.flagPrune;\n"
     "        return !coveredBy(visitedTimeSTeps[cellID], ts, prevBlock) &&\n"),
]


def main():
    out = os.path.abspath(sys.argv[1])
    mingw = sys.argv[sys.argv.index("--mingw") + 1] if "--mingw" in sys.argv else r"C:\ProgramData\mingw64\mingw64\bin"
    rev = sys.argv[sys.argv.index("--rev") + 1] if "--rev" in sys.argv else None
    os.makedirs(out, exist_ok=True)
    for f in ("bs_team.hpp", "flow_team.hpp", "bs_team.cpp", "cbm.cpp"):
        if rev:
            src = subprocess.run(["git", "show", f"{rev}:experiments/{f}"], cwd=HERE, capture_output=True, check=True).stdout
            with open(os.path.join(out, f), "wb") as g:
                g.write(src)
        else:
            shutil.copy(os.path.join(HERE, f), os.path.join(out, f))
    p = os.path.join(out, "bs_team.hpp")
    with open(p, encoding="utf-8", newline="") as f:
        s = f.read().replace("\r\n", "\n")
    for a, b in PATCHES + (PATCHES_TWO_SETS if "visitedBlocked" in s else PATCHES_ONE_SET):
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
