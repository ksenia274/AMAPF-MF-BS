// CBM (Ma, Koenig 2016) for colored MAPF with makespan. Low level of one team (--low):
//   bs     Bulk Search (bs_team.hpp);
//   bspen  Bulk Search, OPEN ordered by the penalties of floww (the routes of the other teams);
//   bscut  bspen plus soft cuts of the waiting chains (BulkSearchTeam::setCut, --cut penal or all);
//   flow   max-flow (flow_team.hpp);
//   floww  min-cost flow with the weights of section 3.2 (the routes of the other teams).
// Agent i of the .scen belongs to team i % K (as archive/make_colored_yaml.py) and must end in a goal of its team.
// High level = CBS over teams: a node holds the constraints and the plan of every team, key = max team makespan.
// Usage: cbm MAP.map FILE.scen N K [ROUTES|-] [--time-limit SEC] [--max-nodes M] [--low bs|bspen|bscut|flow|floww]
//            [--t-start 1|lb|match] [--mem-limit MB] [--diag] [--pen-gap S]
//            [--root-only first|last] [--root-low bs|bspen|bscut|flow|floww] [--cut penal|all]
// An unknown argument that starts with "--" (or a flag without its value) is an error (exit code 1); any other
// argument is taken as ROUTES.
// Order of the open list: key, then (as in the CBM paper) fewer teams in conflicts, then the later node.
// Prints "status=solved|timeout|node_limit|memory T=<makespan> nodes_generated=.. nodes_expanded=.. lowlevel_calls=.. lowlevel_ms=.. highlevel_ms=.. total_ms=..
// lowlevel_sum_T=.. swaps_fixed=.. lowlevel_expansions=.. (Bulk Search variants) last_key=.. expanded_by_key=k:n,.." (last_key = max key expanded, i.e. the
// current lower bound at a limit) and root_conflict_pairs, root_conflicting_teams, root_ms (time until the root is
// planned and evaluated; -1 with the other root fields if it was not finished), pruned_unreachable, replan_ms_median/p90/max,
// net_nodes_max/net_edges_max (flow: the network of the final T of a replanning), peak_mb (PeakWorkingSetSize);
// --diag: a second line with the root key, depth, constraints, repeated constraint sets and the number of free
// neighbours of the cells of the first 20 conflicts of the root (swap: the smaller of the two cells).
// --pen-gap S (bspen, bscut; diagnostics only, implies --diag): after every replanning of the root and every S-th other
// one floww is run with the same constraints
// and routes of the other teams from the T of bspen; the diag line gets the penalty of the bspen routes (weights of
// floww) minus the floww minimum, over all replannings and over those of the root. The floww time is not counted
// against the time limit.
// --mem-limit: the process is put into a job object with this memory limit; bad_alloc gives status=memory.
// --t-start lb (default): the low level starts T from max(minT, bs::teamLowerBound); --t-start 1: from minT;
// --t-start match: from max(minT, bs::teamMatchBound) (bottleneck assignment of the team's robots to its goals; it is
// computed once per team, inside the first low-level call). The answer is the same.
// --root-low: the root is planned by this low level, all other replannings by --low.
// --diag also prints root_pen_wait/enter/swap: the penalty (weights of floww) of the root routes of every team
// against the teams planned before it, summed over the teams: wait = steps t >= 1 that stay in a cell with other
// robots, enter = steps t >= 1 that enter such a cell (both weight (a)), swap = opposite moves (weight (b));
// root_late = enter pen, structural, pass-through, no free step, u blocked, wait pen, avoidable, no free step,
// u blocked, start stay (lateEntries()).
// --root-only first|last: only the root, teams 0..0 or 0..K-1 planned one by one (each call with its own time
// limit); for the last planned team prints minT, T, the number of T tried, the time of the call and the time of a
// fresh call that starts at the final T (one network / one flow), plus the root time and the T of the teams;
// Bulk Search variants: expansions of that call (over all T tried) and the hard / soft cuts of its final network
// (BulkSearchTeam::countCuts, not timed).
// T=-1 if a limit was hit (or no solution: then CBS never stops by itself). ROUTES: as bs_team, all N agents.
#include "flow_team.hpp"
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <psapi.h>
#endif
using namespace std;
using namespace std::chrono;

struct VertexConstraint
{
    int cell, t;
};
struct EdgeConstraint
{
    int from, to, t;
};
struct TeamPlan
{
    vector<VertexConstraint> vertex;
    vector<EdgeConstraint> edge;
    int T = -1;
    vector<vector<int>> routes; // routes[i][t]: cell of the i-th agent of the team, t = 0..T
};
struct Conflict
{
    int t = -1;              // vertex: step t; swap: move t -> t+1
    int teamA, teamB;        // teamA < teamB
    int cell, from, to;      // vertex: cell; swap: teamA moves from -> to, teamB moves to -> from
    bool isVertex = true;
};
struct CTNode
{
    vector<shared_ptr<const TeamPlan>> plans; // unchanged plans are shared with the parent
    int key = 0;                              // makespan = max over teams
    int conflictingTeams = 0;                 // teams involved in at least one conflict (tie-breaking)
    Conflict first;                           // earliest conflict, first.t = -1 if none
    long long id = 0;
    int depth = 0;
};

class CBM
{
public:
    long long nodesGenerated = 0, nodesExpanded = 0, lowLevelCalls = 0;
    long long lowLevelSumT = 0; // sum of T over successful low-level calls (for the mean T of a call)
    long long swapsFixed = 0;   // swaps inside a team replaced by two waits
    long long lowLevelExpansions = 0; // Bulk Search variants: expansions summed over the low-level calls
    bool countCuts = false;            // --root-only: count the cuts of the network of every Bulk Search call
    double lowLevelSec = 0;
    string low = "bs";
    string tStart = "lb"; // 1, lb or match
    bool diag = false;       // collect the statistics below (costs a hash of the constraint sets per node)
    int rootKey = -1, maxDepth = 0, maxConstraintsPerTeam = 0;
    long long duplicateConstraintSets = 0; // generated nodes whose constraint sets (per team) were already seen
    map<int, long long> expandedByKey;     // expanded CT nodes per key (cheap, always counted)
    bool timedOut = false;
    long long prunedUnreachable = 0; // children dropped by startsStayReachable() without a low-level call
    int rootConflictPairs = -1; // -1: the root was not finished
    int rootConflictingTeams = -1;
    double rootMs = -1;
    vector<double> replanMs;
    int netNodesMax = 0, netEdgesMax = 0;
    int penGap = 0;
    struct PenCheck
    {
        bool root;
        long long own, best;
    };
    vector<PenCheck> penChecks;
    long long penCheckFailed = 0;
    vector<int> rootConflictDegrees;
    array<long long, 3> rootPenParts{};
    enum // parts of lateEntries()
    {
        EnterPen, EnterStructural, EnterPassThrough, EnterNoFree, EnterBlocked,
        WaitPen, WaitAvoidable, WaitNoFree, WaitBlocked, WaitStart, LateKinds
    };
    array<long long, LateKinds> rootLateEntries{};
    string rootLow;
    bool cutAll = false;

    CBM(const bs::Grid &grid, const vector<int> &starts, const vector<int> &goals, int numTeams)
        : g(grid), teamAgents(numTeams), teamStarts(numTeams), teamGoals(numTeams)
    {
        for (unsigned int i = 0; i < starts.size(); ++i)
        {
            teamAgents[i % numTeams].push_back(i);
            teamStarts[i % numTeams].push_back(starts[i]);
            teamGoals[i % numTeams].push_back(goals[i]);
        }
        for (int team = 0; team < numTeams; ++team)
            for (unsigned int i = 0; i < teamAgents[team].size(); ++i)
                agents.push_back({team, i});
    }

    // Returns the conflict-free node with the minimal makespan, or nullptr if a limit is hit.
    shared_ptr<CTNode> solve(double timeLimitSec, long long maxNodes)
    {
        setDeadline(timeLimitSec);
        auto solveStart = steady_clock::now();
        auto root = make_shared<CTNode>();
        inRoot = true;
        for (unsigned int team = 0; team < teamAgents.size(); ++team)
        {
            auto plan = replan(team, TeamPlan(), 1, root->plans);
            if (!plan)
                return nullptr;
            root->plans.push_back(plan);
        }
        inRoot = false;
        evaluate(*root);
        rootConflictPairs = conflictPairs(*root);
        rootConflictingTeams = root->conflictingTeams;
        rootMs = duration<double, milli>(steady_clock::now() - solveStart).count();
        if (diag)
            rootConflictDegrees = firstConflictDegrees(*root, 20);
        rootKey = root->key;
        noteDiag(*root);
        auto worse = [](const shared_ptr<CTNode> &a, const shared_ptr<CTNode> &b) {
            if (a->key != b->key)
                return a->key > b->key;
            if (a->conflictingTeams != b->conflictingTeams)
                return a->conflictingTeams > b->conflictingTeams;
            return a->id < b->id;
        };
        priority_queue<shared_ptr<CTNode>, vector<shared_ptr<CTNode>>, decltype(worse)> open(worse);
        open.push(root);
        while (!open.empty())
        {
            if (steady_clock::now() > deadline)
                timedOut = true;
            if (timedOut || nodesGenerated >= maxNodes)
                return nullptr;
            auto node = open.top();
            open.pop();
            if (node->first.t == -1)
                return node;
            ++nodesExpanded;
            ++expandedByKey[node->key];
            const Conflict &c = node->first;
            for (int side = 0; side < 2; ++side)
            {
                int team = side == 0 ? c.teamA : c.teamB;
                TeamPlan constraints;
                constraints.vertex = node->plans[team]->vertex;
                constraints.edge = node->plans[team]->edge;
                // The plan of the team satisfies its constraints and has the conflict, so the new constraint
                // can't be in the set already; if it is, the low level ignored a constraint.
                if (c.isVertex)
                {
                    for (auto &v : constraints.vertex)
                        if (v.cell == c.cell && v.t == c.t)
                            throw logic_error("repeated vertex constraint (cell " + to_string(c.cell) + ", t " + to_string(c.t) + ") for team " + to_string(team));
                    constraints.vertex.push_back({c.cell, c.t});
                }
                else
                {
                    EdgeConstraint e = side == 0 ? EdgeConstraint{c.from, c.to, c.t} : EdgeConstraint{c.to, c.from, c.t};
                    for (auto &x : constraints.edge)
                        if (x.from == e.from && x.to == e.to && x.t == e.t)
                            throw logic_error("repeated edge constraint (" + to_string(e.from) + " -> " + to_string(e.to) + ", t " + to_string(e.t) + ") for team " + to_string(team));
                    constraints.edge.push_back(e);
                }
                if (!startsStayReachable(team, constraints))
                {
                    ++prunedUnreachable;
                    continue;
                }
                auto plan = replan(team, constraints, node->key, node->plans); // T from the parent's key (CBM, section 3.2)
                if (timedOut)
                    return nullptr;
                if (!plan)
                    continue;
                auto child = make_shared<CTNode>();
                child->plans = node->plans;
                child->plans[team] = plan;
                child->depth = node->depth + 1;
                evaluate(*child);
                noteDiag(*child);
                open.push(child);
            }
        }
        return nullptr;
    }

    struct RootCall
    {
        int team = -1, minT = 0, T = -1;
        double ms = 0;
        long long expansions = -1, hardCuts = -1, softCuts = -1;
    };

    // Plans teams 0..count-1 of the root one by one, each call with its own time limit; stops at a failure.
    vector<RootCall> planRoot(int count, double timeLimitSec, vector<shared_ptr<const TeamPlan>> &plans)
    {
        vector<RootCall> calls;
        for (int team = 0; team < count; ++team)
        {
            setDeadline(timeLimitSec);
            auto start = steady_clock::now();
            auto plan = replan(team, TeamPlan(), 1, plans);
            calls.push_back({team, startT(team, 1), plan ? plan->T : -1, duration<double>(steady_clock::now() - start).count() * 1000 - lastCountMs,
                             lastExpansions, lastCuts.first, lastCuts.second});
            if (!plan)
                break;
            plans.push_back(plan);
        }
        return calls;
    }

    // Time of a fresh low-level call of `team` that starts at T (the other teams in `plans` give the weights).
    double callAtT(int team, int T, double timeLimitSec, const vector<shared_ptr<const TeamPlan>> &plans)
    {
        setDeadline(timeLimitSec);
        string mode = tStart;
        tStart = "1";
        auto start = steady_clock::now();
        auto plan = replan(team, TeamPlan(), T, plans);
        tStart = mode;
        return plan && plan->T == T ? duration<double>(steady_clock::now() - start).count() * 1000 - lastCountMs : -1;
    }

    int startT(int team, int minT)
    {
        if (tStart == "1")
            return max(minT, 1);
        if (teamStartBound.empty())
            for (unsigned int i = 0; i < teamAgents.size(); ++i)
                teamStartBound.push_back(tStart == "match" ? bs::teamMatchBound(g, teamStarts[i], teamGoals[i])
                                                           : bs::teamLowerBound(g, teamStarts[i], teamGoals[i]));
        return max({minT, 1, teamStartBound[team]});
    }


    // Routes of all agents in the order of the .scen, padded to the makespan.
    vector<vector<int>> routes(const CTNode &node) const
    {
        int n = 0;
        for (auto &agents : teamAgents)
            n += agents.size();
        vector<vector<int>> result(n);
        for (unsigned int team = 0; team < teamAgents.size(); ++team)
            for (unsigned int i = 0; i < teamAgents[team].size(); ++i)
            {
                auto &r = node.plans[team]->routes[i];
                for (int t = 0; t <= node.key; ++t)
                    result[teamAgents[team][i]].push_back(bs::cellAt(r, t));
            }
        return result;
    }

private:
    const bs::Grid &g;
    vector<vector<int>> teamAgents, teamStarts, teamGoals;
    vector<pair<int, int>> agents; // (team, index in team) of every agent, team by team
    long long nextId = 0;
    steady_clock::time_point deadline = steady_clock::time_point::max();
    vector<int> teamStartBound; // per team: lb or the assignment bound (--t-start)
    unordered_set<size_t> seenConstraintSets; // 64-bit hashes of the canonical per-team constraint sets (diag)
    bool inRoot = false;
    long long lastExpansions = -1;
    pair<long long, long long> lastCuts{-1, -1};
    double lastCountMs = 0; // time of countCuts() in the last call, not part of the call
    unsigned long long profPrep = 0, profSolve = 0, profExtract = 0; // -DBS_PROFILE: rdtsc marks of solveTeam

    void setDeadline(double sec) { deadline = steady_clock::now() + duration_cast<steady_clock::duration>(duration<double>(sec)); }

    void noteDiag(const CTNode &node)
    {
        if (!diag)
            return;
        maxDepth = max(maxDepth, node.depth);
        string canon;
        for (auto &plan : node.plans)
        {
            vector<array<int, 4>> cs;
            for (auto &v : plan->vertex)
                cs.push_back({0, v.cell, -1, v.t});
            for (auto &e : plan->edge)
                cs.push_back({1, e.from, e.to, e.t});
            sort(cs.begin(), cs.end());
            maxConstraintsPerTeam = max(maxConstraintsPerTeam, (int)cs.size());
            for (auto &c : cs)
                canon += to_string(c[0]) + "," + to_string(c[1]) + "," + to_string(c[2]) + "," + to_string(c[3]) + ";";
            canon += "|";
        }
        if (!seenConstraintSets.insert(hash<string>()(canon)).second)
            ++duplicateConstraintSets;
    }

#ifdef BS_PROFILE
    // rdtsc marks of one low-level call (-DBS_PROFILE)
    struct CallProfile
    {
        unsigned long long start = 0, count = 0, solverEnd = 0, destroy = 0, swaps = 0;
        bs::LowProfile low;
        vector<bs::FlowTeam::ProfT> flow;
    } callProf;

    // total = the call without countCuts (as `sec`); prep = everything before solveMinMakespan, destroy = the
    // destructor of the solver
    void printProfile(int team, const string &lowName, int minT, int T, double sec) const
    {
        const CallProfile &c = callProf;
        const bs::LowProfile &prof = c.low;
        unsigned long long total = __rdtsc() - c.start - c.count;
        cerr << "prof call=" << lowLevelCalls << " team=" << team << " low=" << lowName << " minT=" << minT << " T=" << T
             << " ms=" << fixed << setprecision(3) << sec * 1000 << " total=" << total << " prep=" << profPrep - c.start
             << " solve=" << profSolve << " extract=" << profExtract << " destroy=" << c.destroy << " swaps=" << c.swaps
             << " cutBuild=" << prof.cutBuild << " heur=" << prof.heur << " clear=" << prof.clear << " search=" << prof.search
             << " check=" << prof.check << " cutLookup=" << prof.cutLookup << " pen=" << prof.pen << " addPath=" << prof.addPath
             << " nCheck=" << prof.nCheck << " nCut=" << prof.nCut << " nPen=" << prof.nPen << " expansions=" << lastExpansions << "\n";
        for (auto &p : prof.perT)
            cerr << "prof_T call=" << lowLevelCalls << " team=" << team << " T=" << p.T << " ok=" << p.ok << " paths=" << p.paths
                 << " heur=" << p.heur << " clear=" << p.clear << " search=" << p.search << "\n";
        for (auto &p : c.flow)
            cerr << "prof_T call=" << lowLevelCalls << " team=" << team << " T=" << p.T << " ok=" << p.ok << " build=" << p.build
                 << " maxflow=" << p.maxFlow << " mincost=" << p.minCost << "\n";
    }
#endif

    // Routes of the robots of the other teams in `plans`, for the low levels that use them (and for --diag in the root).
    vector<vector<int>> otherRoutes(int team, const string &lowName, const vector<shared_ptr<const TeamPlan>> &plans) const
    {
        vector<vector<int>> others;
        if (lowName == "floww" || lowName == "bspen" || lowName == "bscut" || (diag && inRoot))
            for (unsigned int other = 0; other < plans.size(); ++other)
                if ((int)other != team)
                    others.insert(others.end(), plans[other]->routes.begin(), plans[other]->routes.end());
        return others;
    }

    // bs, bspen, bscut. The time of countCuts() is moved out of the call by shifting `start`.
    bool runBulkSearch(int team, const string &lowName, TeamPlan &plan, int minT, const vector<vector<int>> &others,
                       steady_clock::time_point &start)
    {
        bs::BulkSearchTeam solver(g, teamStarts[team], teamGoals[team]);
        if (lowName != "bs")
            solver.setOtherRoutes(others);
        if (lowName == "bscut")
            solver.setCut(cutAll);
        bool ok = solveTeam(solver, team, plan, minT);
        lowLevelExpansions += solver.numOfExpansions;
        lastExpansions = solver.numOfExpansions;
#ifdef BS_PROFILE
        callProf.low = solver.prof;
        unsigned long long countStartCycles = __rdtsc();
#endif
        if (countCuts && ok)
        {
            auto countStart = steady_clock::now();
            lastCuts = solver.countCuts();
            lastCountMs = duration<double>(steady_clock::now() - countStart).count() * 1000;
            start += steady_clock::now() - countStart;
        }
#ifdef BS_PROFILE
        callProf.count = __rdtsc() - countStartCycles;
        callProf.solverEnd = __rdtsc();
#endif
        return ok;
    }

    // flow, floww
    bool runFlow(int team, const string &lowName, TeamPlan &plan, int minT, const vector<vector<int>> &others)
    {
        bs::FlowTeam solver(g, teamStarts[team], teamGoals[team], lowName == "floww");
        if (lowName == "floww")
            solver.setOtherRoutes(others);
        bool ok = solveTeam(solver, team, plan, minT);
        if (ok)
            netNodesMax = max(netNodesMax, solver.netNodes), netEdgesMax = max(netEdgesMax, solver.netEdges);
#ifdef BS_PROFILE
        callProf.flow = solver.profT;
        callProf.solverEnd = __rdtsc();
#endif
        return ok;
    }

    // floww: the weights come from the routes of the other teams in `plans` (at the root: the teams planned so far).
    shared_ptr<const TeamPlan> replan(int team, TeamPlan plan, int minT, const vector<shared_ptr<const TeamPlan>> &plans)
    {
        auto start = steady_clock::now();
#ifdef BS_PROFILE
        unsigned long long startCycles = __rdtsc();
#endif
        ++lowLevelCalls;
        lastExpansions = -1, lastCuts = {-1, -1}, lastCountMs = 0;
        minT = startT(team, minT);
#ifdef BS_PROFILE
        profSolve = profExtract = 0;
        callProf = CallProfile();
        callProf.start = startCycles;
#endif
        const string &lowName = inRoot && !rootLow.empty() ? rootLow : low;
        vector<vector<int>> others = otherRoutes(team, lowName, plans);
        bool ok = lowName == "bs" || lowName == "bspen" || lowName == "bscut" ? runBulkSearch(team, lowName, plan, minT, others, start)
                                                                              : runFlow(team, lowName, plan, minT, others);
#ifdef BS_PROFILE
        unsigned long long swapStart = __rdtsc();
        callProf.destroy = swapStart - callProf.solverEnd;
#endif
        if (ok)
        {
            lowLevelSumT += plan.T;
            swapsFixed += bs::removeSwaps(plan.routes, plan.T);
        }
#ifdef BS_PROFILE
        callProf.swaps = __rdtsc() - swapStart;
#endif
        double sec = duration<double>(steady_clock::now() - start).count();
#ifdef BS_PROFILE
        printProfile(team, lowName, minT, ok ? plan.T : -1, sec);
#endif
        lowLevelSec += sec;
        replanMs.push_back(sec * 1000);
        if (diag && inRoot && ok)
        {
            auto parts = penaltyParts(plan.routes, others, plan.T);
            for (int i = 0; i < 3; ++i)
                rootPenParts[i] += parts[i];
            auto late = lateEntries(plan.routes, others, plan.T);
            for (int i = 0; i < LateKinds; ++i)
                rootLateEntries[i] += late[i];
        }
        if (penGap && ok && (inRoot || lowLevelCalls % penGap == 0))
            checkPenalty(team, plan, others);
        return ok ? make_shared<const TeamPlan>(move(plan)) : nullptr;
    }

    void checkPenalty(int team, const TeamPlan &plan, const vector<vector<int>> &others)
    {
        auto start = steady_clock::now();
        bs::FlowTeam solver(g, teamStarts[team], teamGoals[team], true);
        solver.setOtherRoutes(others);
        int last = 0;
        for (auto &c : plan.vertex)
            solver.addVertexConstraint(c.cell, c.t), last = max(last, c.t);
        for (auto &c : plan.edge)
            solver.addEdgeConstraint(c.from, c.to, c.t), last = max(last, c.t);
        solver.deadline = start + seconds(600);
        int T = solver.solveMinMakespan(g.width * g.height + (int)teamStarts[team].size() + last, plan.T);
        if (T == plan.T)
            penChecks.push_back({inRoot, routesPenalty(plan.routes, others, T), solver.cost});
        else
            ++penCheckFailed;
        deadline += steady_clock::now() - start;
    }

    // Penalty of `routes` with the weights of floww (flow_team.hpp): (a) per other robot in the same cell at t >= 1,
    // (b) per other robot moving v -> u while ours moves u -> v.
    long long routesPenalty(const vector<vector<int>> &routes, const vector<vector<int>> &others, int T) const
    {
        auto p = penaltyParts(routes, others, T);
        return p[0] + p[1] + p[2];
    }

    // The penalty split into {(a) on a wait, (a) on entering the cell, (b)}.
    array<long long, 3> penaltyParts(const vector<vector<int>> &routes, const vector<vector<int>> &others, int T) const
    {
        long long n = g.numCells;
        array<long long, 3> p{};
        auto at = [](const vector<int> &r, int t) { return r[min<int>(t, r.size() - 1)]; };
        unordered_map<long long, int> occupied, moved;
        for (auto &r : others)
            for (int t = 0; t <= T; ++t)
            {
                if (t >= 1)
                    ++occupied[t * n + at(r, t)];
                if (t < T && at(r, t) != at(r, t + 1))
                    ++moved[(t * n + at(r, t)) * n + at(r, t + 1)];
            }
        auto weight = [](const unordered_map<long long, int> &m, long long key) {
            auto it = m.find(key);
            return it == m.end() ? 0 : it->second;
        };
        for (auto &r : routes)
            for (int t = 0; t <= T; ++t)
            {
                if (t >= 1)
                    p[at(r, t) == at(r, t - 1) ? 0 : 1] += weight(occupied, t * n + at(r, t));
                if (t < T && at(r, t) != at(r, t + 1))
                    p[2] += weight(moved, (t * n + at(r, t + 1)) * n + at(r, t));
            }
        return p;
    }

    // Penalties (a) of `routes` and whether entering the same stay later would avoid them. Entering at t' instead of
    // the entry step e means waiting in the previous cell u over e..t'-1; allowed only if that adds no penalty (no
    // other robot in u, no move v -> u at t'-1) and no agent of the team is in u; the stay from t' to the exit is
    // unchanged. Entry penalty at e: structural if some t' in (e, exit] is penalty-free and allowed, else pass-through
    // (the stay is one step), no penalty-free step until the exit, or u blocked. Wait penalty at s: avoidable if the
    // first penalty-free step after s is before the exit and allowed, else none until the exit, u blocked, or the
    // stay is the start (no u). Weighted like penaltyParts.
    array<long long, LateKinds> lateEntries(const vector<vector<int>> &routes, const vector<vector<int>> &others, int T) const
    {
        long long n = g.numCells;
        auto at = [](const vector<int> &r, int t) { return r[min<int>(t, r.size() - 1)]; };
        unordered_map<long long, int> occupied, moved;
        unordered_set<long long> own;
        for (auto &r : others)
            for (int t = 0; t <= T; ++t)
            {
                ++occupied[t * n + at(r, t)];
                if (t < T && at(r, t) != at(r, t + 1))
                    ++moved[(t * n + at(r, t)) * n + at(r, t + 1)];
            }
        for (auto &r : routes)
            for (int t = 0; t <= T; ++t)
                own.insert(t * n + at(r, t));
        auto weight = [](const unordered_map<long long, int> &m, long long key) {
            auto it = m.find(key);
            return it == m.end() ? 0 : it->second;
        };
        array<long long, LateKinds> p{};
        for (auto &r : routes)
            for (int e = 0, x; e <= T; e = x + 1)
            {
                int v = at(r, e);
                x = e;
                while (x < T && at(r, x + 1) == v)
                    ++x;
                // canEnter[t'] for e < t' <= x: waiting in u over e..t'-1 is allowed and step t' in v is penalty-free
                vector<char> canEnter(x + 1, 0);
                if (e > 0)
                {
                    int u = at(r, e - 1);
                    for (int s = e; s < x; ++s)
                    {
                        if (weight(occupied, s * n + u) || own.count(s * n + u))
                            break;
                        canEnter[s + 1] = !weight(moved, (s * n + v) * n + u) && !weight(occupied, (s + 1) * n + v);
                    }
                    long long w = weight(occupied, e * n + v);
                    p[EnterPen] += w;
                    bool anyFree = false;
                    for (int t = e + 1; t <= x; ++t)
                        anyFree = anyFree || !weight(occupied, t * n + v);
                    p[find(canEnter.begin(), canEnter.end(), 1) != canEnter.end() ? EnterStructural
                      : x == e ? EnterPassThrough : !anyFree ? EnterNoFree : EnterBlocked] += w;
                }
                for (int s = max(e + 1, 1); s <= x; ++s)
                {
                    long long ws = weight(occupied, s * n + v);
                    if (!ws)
                        continue;
                    p[WaitPen] += ws;
                    int free = s + 1;
                    while (free <= x && weight(occupied, free * n + v))
                        ++free;
                    p[e == 0 ? WaitStart : free > x ? WaitNoFree : canEnter[free] ? WaitAvoidable : WaitBlocked] += ws;
                }
            }
        return p;
    }

    // Free neighbours of the cells of the first `count` conflicts in time order (one per cell or swapped edge and step).
    vector<int> firstConflictDegrees(const CTNode &node, unsigned int count) const
    {
        vector<int> result;
        long long n = g.numCells;
        for (int t = 0; t <= node.key && result.size() < count; ++t)
        {
            map<int, set<int>> teamsAt;
            map<long long, set<int>> teamsMoving;
            for (unsigned int team = 0; team < teamAgents.size(); ++team)
                for (auto &r : node.plans[team]->routes)
                {
                    int u = bs::cellAt(r, t), v = bs::cellAt(r, t + 1);
                    teamsAt[u].insert(team);
                    if (t < node.key && u != v)
                        teamsMoving[u * n + v].insert(team);
                }
            for (auto &cell : teamsAt)
                if (cell.second.size() > 1 && result.size() < count)
                    result.push_back(g.nebors[cell.first].size());
            for (auto &mv : teamsMoving)
            {
                int u = mv.first / n, v = mv.first % n;
                if (u > v || result.size() >= count)
                    continue;
                auto it = teamsMoving.find(v * n + u);
                if (it == teamsMoving.end())
                    continue;
                bool differ = false;
                for (int a : mv.second)
                    for (int b : it->second)
                        differ = differ || a != b;
                if (differ)
                    result.push_back(min(g.nebors[u].size(), g.nebors[v].size()));
            }
        }
        return result;
    }

    // Upper bound of the search maxT = w*h + k + last (k robots of the team, last = the largest t of its
    // constraints) never cuts off the minimal T* of a solvable team. A vertex constraint t forbids the cell at step
    // t, an edge constraint t forbids the move t -> t+1 (addEdgeConstraint), so from step last+1 on nothing is
    // forbidden. If T* > last+1, the positions of an optimal solution at step last+1 are a solvable unlabeled
    // problem without constraints (its tail solves it), and by Yu, LaValle, "Multi-agent Path Planning and Network
    // Flow" (WAFR 2012, arXiv 1204.5717) it has a solution of length <= k + V - 1 (V free cells; per connected
    // component k_c + V_c - 1, which is not larger). Their model forbids head-on swaps, ours allows them inside a
    // team, so that solution is valid here. Glued after the first last+1 steps:
    // T* <= last + 1 + k + V - 1 = last + k + V <= w*h + k + last.
    template <class Solver>
    bool solveTeam(Solver &solver, int team, TeamPlan &plan, int minT)
    {
        int last = 0;
        for (auto &c : plan.vertex)
            solver.addVertexConstraint(c.cell, c.t), last = max(last, c.t);
        for (auto &c : plan.edge)
            solver.addEdgeConstraint(c.from, c.to, c.t), last = max(last, c.t);
        solver.deadline = deadline;
#ifdef BS_PROFILE
        profPrep = __rdtsc();
#endif
        plan.T = solver.solveMinMakespan(g.width * g.height + (int)teamStarts[team].size() + last, minT);
        timedOut = timedOut || solver.timedOut;
#ifdef BS_PROFILE
        unsigned long long solved = __rdtsc();
        profSolve = solved - profPrep;
        bool ok = plan.T != -1 && solver.extractRoutes(plan.routes);
        profExtract = __rdtsc() - solved;
        return ok;
#else
        return plan.T != -1 && solver.extractRoutes(plan.routes);
#endif
    }

    // For every start alone: the cells reachable at step t under the team's constraints, t = 1, 2, ...; if one of
    // these sets becomes empty, the team has no solution for any T. Waiting is never forbidden by an edge
    // constraint, so |R_{t+1}| >= |R_t| - (vertex constraints at t+1): once |R_t| exceeds the number of vertex
    // constraints after t, R never becomes empty.
    bool startsStayReachable(int team, const TeamPlan &plan) const
    {
        int last = 0;
        long long n = g.numCells;
        unordered_set<long long> vertex, edge;
        for (auto &c : plan.vertex)
            vertex.insert(c.t * n + c.cell), last = max(last, c.t);
        for (auto &c : plan.edge)
            edge.insert((c.t * n + c.from) * n + c.to), last = max(last, c.t);
        vector<int> remaining(last + 2, 0); // remaining[t] = vertex constraints at steps > t
        for (auto &c : plan.vertex)
            for (int t = 0; t < c.t; ++t)
                ++remaining[t];
        vector<int> mark(g.numCells, -1);
        for (int s : teamStarts[team])
        {
            vector<int> reach = {s}, next;
            for (int t = 0; t <= last && (int)reach.size() <= remaining[t]; ++t)
            {
                next.clear();
                for (int u : reach)
                {
                    auto add = [&](int v) {
                        if (mark[v] != t && !vertex.count((t + 1) * n + v) && (u == v || !edge.count((t * n + u) * n + v)))
                            mark[v] = t, next.push_back(v);
                    };
                    add(u);
                    for (int v : g.nebors[u])
                        add(v);
                }
                if (next.empty())
                    return false;
                swap(reach, next);
            }
            fill(mark.begin(), mark.end(), -1);
        }
        return true;
    }

    // Pairs of robots of different teams with at least one vertex or swap conflict.
    int conflictPairs(const CTNode &node) const
    {
        auto pos = [&](unsigned int a, int t) { return bs::cellAt(node.plans[agents[a].first]->routes[agents[a].second], t); };
        set<pair<int, int>> pairs;
        auto note = [&](int a, int b) {
            if (agents[a].first != agents[b].first)
                pairs.insert({min(a, b), max(a, b)});
        };
        long long n = g.numCells;
        for (int t = 0; t <= node.key; ++t)
        {
            unordered_map<int, vector<int>> at;
            unordered_map<long long, vector<int>> moves;
            for (unsigned int a = 0; a < agents.size(); ++a)
            {
                at[pos(a, t)].push_back(a);
                if (t < node.key && pos(a, t) != pos(a, t + 1))
                    moves[pos(a, t) * n + pos(a, t + 1)].push_back(a);
            }
            for (auto &cell : at)
                for (unsigned int i = 0; i < cell.second.size(); ++i)
                    for (unsigned int j = i + 1; j < cell.second.size(); ++j)
                        note(cell.second[i], cell.second[j]);
            for (auto &move : moves)
            {
                auto it = moves.find((move.first % n) * n + move.first / n);
                if (it != moves.end())
                    for (int a : move.second)
                        for (int b : it->second)
                            note(a, b);
            }
        }
        return pairs.size();
    }

    // Finds the earliest conflict between agents of different teams (agents stay in their goals after their
    // team's T) and counts the teams involved in conflicts.
    void evaluate(CTNode &node)
    {
        node.id = nextId++;
        ++nodesGenerated;
        node.key = 0;
        for (auto &plan : node.plans)
            node.key = max(node.key, plan->T);
        auto pos = [&](const pair<int, int> &a, int t) { return bs::cellAt(node.plans[a.first]->routes[a.second], t); };
        vector<char> inConflict(teamAgents.size(), 0);
        node.first = Conflict();
        auto found = [&](Conflict c) {
            inConflict[c.teamA] = inConflict[c.teamB] = 1;
            if (node.first.t == -1)
                node.first = c;
        };
        unordered_map<int, int> at;            // cell -> agent
        unordered_map<long long, int> moves;   // from*n+to -> agent
        long long n = g.numCells;
        for (int t = 0; t <= node.key; ++t)
        {
            at.clear();
            for (unsigned int a = 0; a < agents.size(); ++a)
            {
                int cell = pos(agents[a], t);
                auto it = at.find(cell);
                if (it == at.end())
                    at[cell] = a;
                else if (agents[it->second].first != agents[a].first)
                {
                    Conflict c;
                    c.t = t, c.cell = cell, c.isVertex = true;
                    c.teamA = min(agents[it->second].first, agents[a].first), c.teamB = max(agents[it->second].first, agents[a].first);
                    found(c);
                }
                else
                    throw logic_error("two agents of one team in one cell");
            }
            if (t == node.key)
                break;
            moves.clear();
            for (unsigned int a = 0; a < agents.size(); ++a)
            {
                int u = pos(agents[a], t), v = pos(agents[a], t + 1);
                if (u == v)
                    continue;
                moves[u * n + v] = a;
                auto it = moves.find(v * n + u);
                if (it != moves.end() && agents[it->second].first != agents[a].first)
                {
                    int b = it->second;
                    Conflict c;
                    c.t = t, c.isVertex = false;
                    bool aFirst = agents[a].first < agents[b].first;
                    c.teamA = agents[aFirst ? a : b].first, c.teamB = agents[aFirst ? b : a].first;
                    c.from = aFirst ? u : v, c.to = aFirst ? v : u; // the move of teamA
                    found(c);
                }
            }
            // A vertex conflict at t+1 is found in the next iteration, so swaps at t -> t+1 come first.
        }
        node.conflictingTeams = count(inConflict.begin(), inConflict.end(), 1);
    }
};

struct Options
{
    string mapFile, scenFile, routesFile = "-";
    int numAgents = 0, numTeams = 0;
    double timeLimit = 60;
    long long maxNodes = LLONG_MAX, memLimitMb = 0;
    bool diag = false;
    int penGap = 0;
    string low = "bs", rootOnly, tStart = "lb", rootLow, cut = "penal";
};

// false (with a message) on bad arguments
bool parseArgs(int argc, char *argv[], Options &o)
{
    if (argc < 5)
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen N K [ROUTES|-] [--time-limit SEC] [--max-nodes M] [--low bs|bspen|bscut|flow|floww]"
                " [--t-start 1|lb|match] [--mem-limit MB] [--diag] [--pen-gap S] [--root-only first|last]"
                " [--root-low bs|bspen|bscut|flow|floww] [--cut penal|all]" << endl;
        return false;
    }
    o.mapFile = argv[1], o.scenFile = argv[2];
    o.numAgents = atoi(argv[3]), o.numTeams = atoi(argv[4]);
    for (int i = 5; i < argc; ++i)
    {
        string a = argv[i];
        if (a == "--time-limit" && i + 1 < argc)
            o.timeLimit = atof(argv[++i]);
        else if (a == "--max-nodes" && i + 1 < argc)
            o.maxNodes = atoll(argv[++i]);
        else if (a == "--low" && i + 1 < argc)
            o.low = argv[++i];
        else if (a == "--mem-limit" && i + 1 < argc)
            o.memLimitMb = atoll(argv[++i]);
        else if (a == "--root-only" && i + 1 < argc)
            o.rootOnly = argv[++i];
        else if (a == "--cut" && i + 1 < argc)
            o.cut = argv[++i];
        else if (a == "--root-low" && i + 1 < argc)
            o.rootLow = argv[++i];
        else if (a == "--t-start" && i + 1 < argc)
            o.tStart = argv[++i];
        else if (a == "--diag")
            o.diag = true;
        else if (a == "--pen-gap" && i + 1 < argc)
            o.penGap = max(1, atoi(argv[++i])), o.diag = true;
        else if (a.rfind("--", 0) == 0)
        {
            cerr << "unknown flag or missing value: " << a << endl;
            return false;
        }
        else
            o.routesFile = a;
    }
    return true;
}

bool validOptions(const Options &o)
{
    auto isLow = [](const string &x) { return x == "bs" || x == "bspen" || x == "bscut" || x == "flow" || x == "floww"; };
    if (!isLow(o.low) || (!o.rootLow.empty() && !isLow(o.rootLow)) || (o.tStart != "1" && o.tStart != "lb" && o.tStart != "match") ||
        (o.cut != "penal" && o.cut != "all") || (!o.rootOnly.empty() && o.rootOnly != "first" && o.rootOnly != "last"))
    {
        cerr << "--low and --root-low must be bs, bspen, bscut, flow or floww, --t-start 1, lb or match, --cut penal or all, --root-only first or last" << endl;
        return false;
    }
    return true;
}

// The process is put into a job object with this memory limit (Windows only); false if that fails.
bool setMemoryLimit(long long mb)
{
#ifdef _WIN32
    if (mb > 0)
    {
        HANDLE job = CreateJobObjectA(nullptr, nullptr);
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = {};
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY;
        info.ProcessMemoryLimit = (SIZE_T)mb << 20;
        if (!job || !SetInformationJobObject(job, JobObjectExtendedLimitInformation, &info, sizeof(info)) ||
            !AssignProcessToJobObject(job, GetCurrentProcess()))
        {
            cerr << "couldn't set the memory limit" << endl;
            return false;
        }
    }
#endif
    return true;
}

double peakMb()
{
    double mb = 0;
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS pmc;
    if (K32GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc)))
        mb = pmc.PeakWorkingSetSize / 1048576.0;
#endif
    return mb;
}

#ifdef BS_PROFILE
// Cost of one rdtsc pair (the counters of the profile add it once per measured region) and the TSC frequency.
void printProfileOverhead()
{
    unsigned long long sum = 0;
    for (int i = 0; i < 1000000; ++i)
    {
        unsigned long long a = __rdtsc();
        sum += __rdtsc() - a;
    }
    auto t0 = steady_clock::now();
    unsigned long long c0 = __rdtsc();
    while (steady_clock::now() - t0 < milliseconds(200))
        ;
    double ghz = (__rdtsc() - c0) / (duration<double>(steady_clock::now() - t0).count() * 1e9);
    cerr << "prof_overhead pair_cycles=" << sum / 1e6 << " tsc_ghz=" << ghz << "\n";
}
#endif

// --root-only: plans the root team by team and prints the last call; returns the exit code.
int runRootOnly(CBM &cbm, const Options &o)
{
    vector<shared_ptr<const TeamPlan>> plans;
    vector<CBM::RootCall> calls;
    double finalMs = -1;
    bool outOfMemory = false;
    try
    {
        calls = cbm.planRoot(o.rootOnly == "first" ? 1 : o.numTeams, o.timeLimit, plans);
        if (calls.back().T != -1)
        {
            plans.pop_back();
            cbm.netNodesMax = cbm.netEdgesMax = 0;
            finalMs = cbm.callAtT(calls.back().team, calls.back().T, o.timeLimit, plans);
        }
    }
    catch (const bad_alloc &)
    {
        outOfMemory = true;
    }
    bool ok = !calls.empty() && calls.back().T != -1;
    vector<int> ts;
    double rootMs = 0;
    for (auto &c : calls)
        rootMs += c.ms, ts.push_back(c.T);
    sort(ts.begin(), ts.end());
    CBM::RootCall none;
    auto &c = calls.empty() ? none : calls.back();
    cout << "status=" << (ok ? "solved" : outOfMemory ? "memory" : cbm.timedOut ? "timeout" : "no_solution") << " team=" << c.team
         << " K=" << o.numTeams << " minT=" << c.minT << " T=" << c.T << " tried_T=" << (ok ? c.T - c.minT + 1 : -1) << fixed << setprecision(3)
         << " ms=" << c.ms << " final_t_ms=" << finalMs << " net_nodes=" << cbm.netNodesMax << " net_edges=" << cbm.netEdgesMax
         << " root_ms=" << rootMs << " teams_planned=" << calls.size() << " team_T_median=" << (ts.empty() ? -1 : ts[ts.size() / 2])
         << " team_T_max=" << (ts.empty() ? -1 : ts.back()) << " expansions=" << c.expansions << " hard_cuts=" << c.hardCuts
         << " soft_cuts=" << c.softCuts << setprecision(1) << " peak_mb=" << peakMb() << endl;
    return ok ? 0 : outOfMemory ? 5 : 2;
}

void printResult(CBM &cbm, const shared_ptr<CTNode> &result, const string &status, double total)
{
    auto &ms = cbm.replanMs;
    sort(ms.begin(), ms.end());
    auto quantile = [&](double q) { return ms.empty() ? 0.0 : ms[min<size_t>(ms.size() - 1, (size_t)(q * ms.size()))]; };
    cout << "status=" << status << " T=" << (result ? result->key : -1) << " nodes_generated=" << cbm.nodesGenerated
         << " nodes_expanded=" << cbm.nodesExpanded << " lowlevel_calls=" << cbm.lowLevelCalls
         << " lowlevel_ms=" << (long long)(cbm.lowLevelSec * 1000) << " highlevel_ms=" << (long long)((total - cbm.lowLevelSec) * 1000)
         << " total_ms=" << (long long)(total * 1000) << " lowlevel_sum_T=" << cbm.lowLevelSumT << " swaps_fixed=" << cbm.swapsFixed << " lowlevel_expansions=" << cbm.lowLevelExpansions
         << " last_key=" << (cbm.expandedByKey.empty() ? -1 : cbm.expandedByKey.rbegin()->first) << " expanded_by_key=";
    for (auto &kv : cbm.expandedByKey)
        cout << (kv.first == cbm.expandedByKey.begin()->first ? "" : ",") << kv.first << ":" << kv.second;
    cout << fixed << setprecision(3) << " root_conflict_pairs=" << cbm.rootConflictPairs << " root_conflicting_teams=" << cbm.rootConflictingTeams
         << " root_ms=" << cbm.rootMs << " pruned_unreachable=" << cbm.prunedUnreachable
         << " replan_ms_median=" << quantile(0.5) << " replan_ms_p90=" << quantile(0.9) << " replan_ms_max=" << (ms.empty() ? 0.0 : ms.back())
         << " net_nodes_max=" << cbm.netNodesMax << " net_edges_max=" << cbm.netEdgesMax << setprecision(1) << " peak_mb=" << peakMb() << endl;
}

// The second line of --diag.
void printDiag(const CBM &cbm)
{
    cout << "diag: root_key=" << cbm.rootKey << " max_depth=" << cbm.maxDepth << " max_constraints_per_team=" << cbm.maxConstraintsPerTeam
         << " repeated_constraint_sets=" << cbm.duplicateConstraintSets << " root_conflict_degrees=";
    for (unsigned int i = 0; i < cbm.rootConflictDegrees.size(); ++i)
        cout << (i ? "," : "") << cbm.rootConflictDegrees[i];
    cout << " root_pen_wait=" << cbm.rootPenParts[0] << " root_pen_enter=" << cbm.rootPenParts[1]
         << " root_pen_swap=" << cbm.rootPenParts[2] << " root_late=";
    for (int i = 0; i < CBM::LateKinds; ++i)
        cout << (i ? "," : "") << cbm.rootLateEntries[i];
    if (cbm.penGap)
    {
        for (int rootOnly = 0; rootOnly < 2; ++rootOnly)
        {
            long long checks = 0, positive = 0, gapMax = 0, gapMin = LLONG_MAX, ownSum = 0, bestSum = 0;
            for (auto &c : cbm.penChecks)
                if (!rootOnly || c.root)
                {
                    ++checks, ownSum += c.own, bestSum += c.best, positive += c.own > c.best;
                    gapMax = max(gapMax, c.own - c.best), gapMin = min(gapMin, c.own - c.best);
                }
            string pre = rootOnly ? " root_" : " ";
            double k = max(checks, 1LL);
            cout << fixed << setprecision(3) << pre << "pen_checks=" << checks << pre << "pen_gap_mean=" << (ownSum - bestSum) / k
                 << pre << "pen_gap_max=" << gapMax << pre << "pen_gap_min=" << (checks ? gapMin : 0) << pre << "pen_gap_share=" << positive / k
                 << pre << "pen_own_mean=" << ownSum / k << pre << "pen_min_mean=" << bestSum / k;
        }
        cout << " pen_check_failed=" << cbm.penCheckFailed;
    }
    cout << endl;
}

int main(int argc, char *argv[])
{
    Options o;
    if (!parseArgs(argc, argv, o))
        return 1;
    bs::Grid grid;
    if (!grid.load(o.mapFile))
    {
        cerr << "Couldn't open the file " << o.mapFile << endl;
        return 1;
    }
    vector<int> starts, goals;
    if (!bs::loadScen(grid, o.scenFile, o.numAgents, starts, goals))
        return 1;
    if (o.numAgents < 1 || (int)starts.size() < o.numAgents || o.numTeams < 1 || o.numTeams > o.numAgents)
    {
        cerr << "need 1 <= K <= N <= " << starts.size() << endl;
        return 1;
    }
    if (!validOptions(o) || !setMemoryLimit(o.memLimitMb))
        return 1;
#ifdef BS_PROFILE
    printProfileOverhead();
#endif
    auto start = steady_clock::now();
    CBM cbm(grid, starts, goals, o.numTeams);
    cbm.low = o.low;
    cbm.rootLow = o.rootLow;
    cbm.cutAll = o.cut == "all";
    cbm.countCuts = !o.rootOnly.empty();
    cbm.tStart = o.tStart;
    cbm.diag = o.diag;
    cbm.penGap = o.low == "bspen" || o.low == "bscut" ? o.penGap : 0;
    if (!o.rootOnly.empty())
        return runRootOnly(cbm, o);
    shared_ptr<CTNode> result;
    bool outOfMemory = false;
    try
    {
        result = cbm.solve(o.timeLimit, o.maxNodes);
    }
    catch (const logic_error &e)
    {
        cerr << "internal error: " << e.what() << endl;
        return 4;
    }
    catch (const bad_alloc &)
    {
        outOfMemory = true;
    }
    double total = duration<double>(steady_clock::now() - start).count();
    string status = result ? "solved" : outOfMemory ? "memory" : cbm.timedOut ? "timeout" : cbm.nodesGenerated >= o.maxNodes ? "node_limit" : "no_solution";
    printResult(cbm, result, status, total);
    if (o.diag)
        printDiag(cbm);
    if (outOfMemory)
        return 5;
    if (!result)
        return 2;
    if (o.routesFile != "-")
        bs::writeRoutes(grid, o.routesFile, result->key, cbm.routes(*result));
    return 0;
}
