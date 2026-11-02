// CBM (Ma, Koenig 2016) for colored MAPF with makespan, low level = Bulk Search (bs_team.hpp, --low bs; --low bspen:
// OPEN ordered by the penalties of floww) or max-flow / min-cost flow with the weights of section 3.2
// (flow_team.hpp, --low flow / floww).
// Agent i of the .scen belongs to team i % K (as make_colored_yaml.py) and must end in a goal of its team.
// High level = CBS over teams: a node holds the constraints and the plan of every team, key = max team makespan.
// Usage: cbm MAP.map FILE.scen N K [ROUTES|-] [--time-limit SEC] [--max-nodes M] [--low bs|bspen|flow|floww]
//            [--tiebreak conflicts|late] [--tie later|earlier] [--t-start 1|lb] [--mem-limit MB] [--diag]
//            [--root-only first|last]
// Order of the open list: key, then (conflicts, as in the CBM paper) fewer teams in conflicts, then the later node
// (--tie earlier: the earlier one); --tiebreak late skips the number of conflicting teams.
// Prints "status=solved|timeout|node_limit|memory T=<makespan> nodes_generated=.. nodes_expanded=.. lowlevel_calls=.. lowlevel_ms=.. highlevel_ms=.. total_ms=..
// lowlevel_sum_T=.. swaps_fixed=.. last_key=.. expanded_by_key=k:n,.." (last_key = max key expanded, i.e. the
// current lower bound at a limit) and root_conflict_pairs, pruned_unreachable, replan_ms_median/p90/max,
// net_nodes_max/net_edges_max (flow: the network of the final T of a replanning), peak_mb (PeakWorkingSetSize);
// --diag: a second line with the root key, depth, constraints, repeated constraint sets.
// --mem-limit: the process is put into a job object with this memory limit; bad_alloc gives status=memory.
// --t-start lb: the low level starts T from max(minT, bs::teamLowerBound) instead of minT (the answer is the same).
// --root-only first|last: only the root, teams 0..0 or 0..K-1 planned one by one (each call with its own time
// limit); for the last planned team prints minT, T, the number of T tried, the time of the call and the time of a
// fresh call that starts at the final T (one network / one flow), plus the root time and the T of the teams.
// pen_share (bspen): share of the low-level rdtsc cycles spent on the penalties.
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
    double lowLevelSec = 0;
    bool tieEarlier = false;
    bool tieConflicts = true;
    string low = "bs";
    bool tStartLb = false;
    bool diag = false;       // collect the statistics below (costs a hash of the constraint sets per node)
    int rootKey = -1, maxDepth = 0, maxConstraintsPerTeam = 0;
    long long duplicateConstraintSets = 0; // generated nodes whose constraint sets (per team) were already seen
    map<int, long long> expandedByKey;     // expanded CT nodes per key (cheap, always counted)
    bool timedOut = false;
    long long prunedUnreachable = 0; // children dropped by startsStayReachable() without a low-level call
    int rootConflictPairs = -1; // -1: the root was not finished
    vector<double> replanMs;
    int netNodesMax = 0, netEdgesMax = 0;

    CBM(const bs::Grid &grid, const vector<int> &starts, const vector<int> &goals, int numTeams)
        : g(grid), teamAgents(numTeams), teamStarts(numTeams), teamGoals(numTeams)
    {
        for (unsigned int i = 0; i < starts.size(); ++i)
        {
            teamAgents[i % numTeams].push_back(i);
            teamStarts[i % numTeams].push_back(starts[i]);
            teamGoals[i % numTeams].push_back(goals[i]);
        }
    }

    // Returns the conflict-free node with the minimal makespan, or nullptr if a limit is hit.
    shared_ptr<CTNode> solve(double timeLimitSec, long long maxNodes)
    {
        deadline = steady_clock::now() + duration_cast<steady_clock::duration>(duration<double>(timeLimitSec));
        auto root = make_shared<CTNode>();
        for (unsigned int team = 0; team < teamAgents.size(); ++team)
        {
            auto plan = replan(team, TeamPlan(), 1, root->plans);
            if (!plan)
                return nullptr;
            root->plans.push_back(plan);
        }
        evaluate(*root);
        rootConflictPairs = conflictPairs(*root);
        rootKey = root->key;
        noteDiag(*root);
        bool earlier = tieEarlier, conflicts = tieConflicts;
        auto worse = [earlier, conflicts](const shared_ptr<CTNode> &a, const shared_ptr<CTNode> &b) {
            if (a->key != b->key)
                return a->key > b->key;
            if (conflicts && a->conflictingTeams != b->conflictingTeams)
                return a->conflictingTeams > b->conflictingTeams;
            return earlier ? a->id > b->id : a->id < b->id;
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
    };

    // Plans teams 0..count-1 of the root one by one, each call with its own time limit; stops at a failure.
    vector<RootCall> planRoot(int count, double timeLimitSec, vector<shared_ptr<const TeamPlan>> &plans)
    {
        vector<RootCall> calls;
        for (int team = 0; team < count; ++team)
        {
            deadline = steady_clock::now() + duration_cast<steady_clock::duration>(duration<double>(timeLimitSec));
            auto start = steady_clock::now();
            auto plan = replan(team, TeamPlan(), 1, plans);
            calls.push_back({team, startT(team, 1), plan ? plan->T : -1, duration<double>(steady_clock::now() - start).count() * 1000});
            if (!plan)
                break;
            plans.push_back(plan);
        }
        return calls;
    }

    // Time of a fresh low-level call of `team` that starts at T (the other teams in `plans` give the weights).
    double callAtT(int team, int T, double timeLimitSec, const vector<shared_ptr<const TeamPlan>> &plans)
    {
        deadline = steady_clock::now() + duration_cast<steady_clock::duration>(duration<double>(timeLimitSec));
        bool lb = tStartLb;
        tStartLb = false;
        auto start = steady_clock::now();
        auto plan = replan(team, TeamPlan(), T, plans);
        tStartLb = lb;
        return plan && plan->T == T ? duration<double>(steady_clock::now() - start).count() * 1000 : -1;
    }

    int startT(int team, int minT)
    {
        if (!tStartLb)
            return max(minT, 1);
        if (teamLb.empty())
            for (unsigned int i = 0; i < teamAgents.size(); ++i)
                teamLb.push_back(bs::teamLowerBound(g, teamStarts[i], teamGoals[i]));
        return max({minT, 1, teamLb[team]});
    }

    double penShare() const { return lowLevelCycles ? (double)penaltyCycles / lowLevelCycles : 0; }

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
                    result[teamAgents[team][i]].push_back(r[min<int>(t, r.size() - 1)]);
            }
        return result;
    }

private:
    const bs::Grid &g;
    vector<vector<int>> teamAgents, teamStarts, teamGoals;
    long long nextId = 0;
    steady_clock::time_point deadline = steady_clock::time_point::max();
    vector<int> teamLb;
    unsigned long long penaltyCycles = 0, lowLevelCycles = 0;
    unordered_set<size_t> seenConstraintSets; // 64-bit hashes of the canonical per-team constraint sets (diag)

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

    // floww: the weights come from the routes of the other teams in `plans` (at the root: the teams planned so far).
    shared_ptr<const TeamPlan> replan(int team, TeamPlan plan, int minT, const vector<shared_ptr<const TeamPlan>> &plans)
    {
        auto start = steady_clock::now();
        unsigned long long startCycles = __rdtsc();
        ++lowLevelCalls;
        minT = startT(team, minT);
        vector<vector<int>> others;
        if (low == "floww" || low == "bspen")
            for (unsigned int other = 0; other < plans.size(); ++other)
                if ((int)other != team)
                    others.insert(others.end(), plans[other]->routes.begin(), plans[other]->routes.end());
        bool ok;
        if (low == "bs" || low == "bspen")
        {
            bs::BulkSearchTeam solver(g, teamStarts[team], teamGoals[team]);
            if (low == "bspen")
                solver.setOtherRoutes(others);
            ok = solveTeam(solver, team, plan, minT);
            penaltyCycles += solver.penaltyCycles;
        }
        else
        {
            bs::FlowTeam solver(g, teamStarts[team], teamGoals[team], low == "floww");
            if (low == "floww")
                solver.setOtherRoutes(others);
            ok = solveTeam(solver, team, plan, minT);
            if (ok)
                netNodesMax = max(netNodesMax, solver.netNodes), netEdgesMax = max(netEdgesMax, solver.netEdges);
        }
        if (ok)
        {
            lowLevelSumT += plan.T;
            swapsFixed += removeSwapsInTeam(plan);
        }
        double sec = duration<double>(steady_clock::now() - start).count();
        lowLevelCycles += __rdtsc() - startCycles;
        lowLevelSec += sec;
        replanMs.push_back(sec * 1000);
        return ok ? make_shared<const TeamPlan>(move(plan)) : nullptr;
    }

    template <class Solver>
    bool solveTeam(Solver &solver, int team, TeamPlan &plan, int minT)
    {
        int last = 0;
        for (auto &c : plan.vertex)
            solver.addVertexConstraint(c.cell, c.t), last = max(last, c.t);
        for (auto &c : plan.edge)
            solver.addEdgeConstraint(c.from, c.to, c.t), last = max(last, c.t);
        solver.deadline = deadline;
        plan.T = solver.solveMinMakespan(g.width * g.height + (int)teamStarts[team].size() + last, minT);
        timedOut = timedOut || solver.timedOut;
        return plan.T != -1 && solver.extractRoutes(plan.routes);
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
        vector<pair<int, int>> agents;
        for (unsigned int team = 0; team < teamAgents.size(); ++team)
            for (unsigned int i = 0; i < teamAgents[team].size(); ++i)
                agents.push_back({team, i});
        auto pos = [&](unsigned int a, int t) {
            auto &r = node.plans[agents[a].first]->routes[agents[a].second];
            return r[min<int>(t, r.size() - 1)];
        };
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

    // A swap of two agents of one team is replaced by two waits and the agents exchange the rest of their routes:
    // the cells occupied at every step stay the same, so no new conflicts appear (never observed with Bulk Search;
    // impossible with flow: the gadget lets one robot through an edge per step).
    static int removeSwapsInTeam(TeamPlan &plan)
    {
        int fixed = 0;
        auto &r = plan.routes;
        for (int t = 0; t < plan.T; ++t)
            for (unsigned int a = 0; a < r.size(); ++a)
                for (unsigned int b = a + 1; b < r.size(); ++b)
                    if (r[a][t] != r[a][t + 1] && r[a][t] == r[b][t + 1] && r[a][t + 1] == r[b][t])
                    {
                        ++fixed;
                        for (int s = t + 1; s <= plan.T; ++s)
                            swap(r[a][s], r[b][s]);
                    }
        return fixed;
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
        vector<pair<int, int>> agents; // (team, index in team)
        for (unsigned int team = 0; team < teamAgents.size(); ++team)
            for (unsigned int i = 0; i < teamAgents[team].size(); ++i)
                agents.push_back({team, i});
        auto pos = [&](const pair<int, int> &a, int t) {
            auto &r = node.plans[a.first]->routes[a.second];
            return r[min<int>(t, r.size() - 1)];
        };
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

int main(int argc, char *argv[])
{
    if (argc < 5)
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen N K [ROUTES|-] [--time-limit SEC] [--max-nodes M] [--low bs|flow|floww] [--tiebreak conflicts|late] [--tie later|earlier] [--mem-limit MB] [--diag]" << endl;
        return 1;
    }
    string mapFile = argv[1], scenFile = argv[2], routesFile = "-";
    int numAgents = atoi(argv[3]), numTeams = atoi(argv[4]);
    double timeLimit = 60;
    long long maxNodes = LLONG_MAX, memLimitMb = 0;
    bool tieEarlier = false, tieConflicts = true, diag = false;
    string low = "bs", rootOnly, tStart = "1";
    for (int i = 5; i < argc; ++i)
    {
        string a = argv[i];
        if (a == "--time-limit" && i + 1 < argc)
            timeLimit = atof(argv[++i]);
        else if (a == "--max-nodes" && i + 1 < argc)
            maxNodes = atoll(argv[++i]);
        else if (a == "--tie" && i + 1 < argc)
            tieEarlier = string(argv[++i]) == "earlier";
        else if (a == "--low" && i + 1 < argc)
            low = argv[++i];
        else if (a.rfind("--low=", 0) == 0)
            low = a.substr(6);
        else if (a == "--tiebreak" && i + 1 < argc)
            tieConflicts = string(argv[++i]) != "late";
        else if (a.rfind("--tiebreak=", 0) == 0)
            tieConflicts = a.substr(11) != "late";
        else if (a == "--mem-limit" && i + 1 < argc)
            memLimitMb = atoll(argv[++i]);
        else if (a == "--root-only" && i + 1 < argc)
            rootOnly = argv[++i];
        else if (a == "--t-start" && i + 1 < argc)
            tStart = argv[++i];
        else if (a == "--diag")
            diag = true;
        else
            routesFile = a;
    }
    bs::Grid grid;
    if (!grid.load(mapFile))
    {
        cerr << "Couldn't open the file " << mapFile << endl;
        return 1;
    }
    vector<int> starts, goals;
    ifstream in(scenFile);
    string version, num, mapName;
    int w, h, sx, sy, gx, gy;
    double optimal;
    in >> version >> version;
    while ((int)starts.size() < numAgents && in >> num >> mapName >> w >> h >> sx >> sy >> gx >> gy >> optimal)
    {
        starts.push_back(grid.id(sx, sy));
        goals.push_back(grid.id(gx, gy));
        if (starts.back() == -1 || goals.back() == -1)
        {
            cerr << "start or goal of agent " << starts.size() - 1 << " is not a free cell" << endl;
            return 1;
        }
    }
    if (numAgents < 1 || (int)starts.size() < numAgents || numTeams < 1 || numTeams > numAgents)
    {
        cerr << "need 1 <= K <= N <= " << starts.size() << endl;
        return 1;
    }

    if ((low != "bs" && low != "bspen" && low != "flow" && low != "floww") || (tStart != "1" && tStart != "lb") ||
        (!rootOnly.empty() && rootOnly != "first" && rootOnly != "last"))
    {
        cerr << "--low must be bs, bspen, flow or floww, --t-start 1 or lb, --root-only first or last" << endl;
        return 1;
    }
#ifdef _WIN32
    if (memLimitMb > 0)
    {
        HANDLE job = CreateJobObjectA(nullptr, nullptr);
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = {};
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY;
        info.ProcessMemoryLimit = (SIZE_T)memLimitMb << 20;
        if (!job || !SetInformationJobObject(job, JobObjectExtendedLimitInformation, &info, sizeof(info)) ||
            !AssignProcessToJobObject(job, GetCurrentProcess()))
        {
            cerr << "couldn't set the memory limit" << endl;
            return 1;
        }
    }
#endif

    auto start = steady_clock::now();
    CBM cbm(grid, starts, goals, numTeams);
    cbm.tieEarlier = tieEarlier;
    cbm.tieConflicts = tieConflicts;
    cbm.low = low;
    cbm.tStartLb = tStart == "lb";
    cbm.diag = diag;
    auto peakMb = []() {
        double mb = 0;
#ifdef _WIN32
        PROCESS_MEMORY_COUNTERS pmc;
        if (K32GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc)))
            mb = pmc.PeakWorkingSetSize / 1048576.0;
#endif
        return mb;
    };
    if (!rootOnly.empty())
    {
        vector<shared_ptr<const TeamPlan>> plans;
        vector<CBM::RootCall> calls;
        double finalMs = -1;
        bool outOfMemory = false;
        try
        {
            calls = cbm.planRoot(rootOnly == "first" ? 1 : numTeams, timeLimit, plans);
            if (calls.back().T != -1)
            {
                plans.pop_back();
                cbm.netNodesMax = cbm.netEdgesMax = 0;
                finalMs = cbm.callAtT(calls.back().team, calls.back().T, timeLimit, plans);
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
             << " K=" << numTeams << " minT=" << c.minT << " T=" << c.T << " tried_T=" << (ok ? c.T - c.minT + 1 : -1) << fixed << setprecision(3)
             << " ms=" << c.ms << " final_t_ms=" << finalMs << " net_nodes=" << cbm.netNodesMax << " net_edges=" << cbm.netEdgesMax
             << " root_ms=" << rootMs << " teams_planned=" << calls.size() << " team_T_median=" << (ts.empty() ? -1 : ts[ts.size() / 2])
             << " team_T_max=" << (ts.empty() ? -1 : ts.back()) << setprecision(1) << " peak_mb=" << peakMb() << endl;
        return ok ? 0 : outOfMemory ? 5 : 2;
    }
    shared_ptr<CTNode> result;
    bool outOfMemory = false;
    try
    {
        result = cbm.solve(timeLimit, maxNodes);
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
    string status = result ? "solved" : outOfMemory ? "memory" : cbm.timedOut ? "timeout" : cbm.nodesGenerated >= maxNodes ? "node_limit" : "no_solution";
    auto &ms = cbm.replanMs;
    sort(ms.begin(), ms.end());
    auto quantile = [&](double q) { return ms.empty() ? 0.0 : ms[min<size_t>(ms.size() - 1, (size_t)(q * ms.size()))]; };
    cout << "status=" << status << " T=" << (result ? result->key : -1) << " nodes_generated=" << cbm.nodesGenerated
         << " nodes_expanded=" << cbm.nodesExpanded << " lowlevel_calls=" << cbm.lowLevelCalls
         << " lowlevel_ms=" << (long long)(cbm.lowLevelSec * 1000) << " highlevel_ms=" << (long long)((total - cbm.lowLevelSec) * 1000)
         << " total_ms=" << (long long)(total * 1000) << " lowlevel_sum_T=" << cbm.lowLevelSumT << " swaps_fixed=" << cbm.swapsFixed
         << " last_key=" << (cbm.expandedByKey.empty() ? -1 : cbm.expandedByKey.rbegin()->first) << " expanded_by_key=";
    for (auto &kv : cbm.expandedByKey)
        cout << (kv.first == cbm.expandedByKey.begin()->first ? "" : ",") << kv.first << ":" << kv.second;
    cout << fixed << setprecision(3) << " root_conflict_pairs=" << cbm.rootConflictPairs << " pruned_unreachable=" << cbm.prunedUnreachable
         << " replan_ms_median=" << quantile(0.5) << " replan_ms_p90=" << quantile(0.9) << " replan_ms_max=" << (ms.empty() ? 0.0 : ms.back())
         << " pen_share=" << cbm.penShare() << " net_nodes_max=" << cbm.netNodesMax << " net_edges_max=" << cbm.netEdgesMax << setprecision(1) << " peak_mb=" << peakMb() << endl;
    if (diag)
    {
        cout << "diag: root_key=" << cbm.rootKey << " max_depth=" << cbm.maxDepth << " max_constraints_per_team=" << cbm.maxConstraintsPerTeam
             << " repeated_constraint_sets=" << cbm.duplicateConstraintSets << endl;
    }
    if (outOfMemory)
        return 5;
    if (!result)
        return 2;
    if (routesFile != "-")
    {
        ofstream out(routesFile);
        auto routes = cbm.routes(*result);
        out << result->key << " " << numAgents << "\n";
        for (auto &route : routes)
        {
            for (unsigned int t = 0; t < route.size(); ++t)
                out << (t ? " " : "") << grid.x(route[t]) << "," << grid.y(route[t]);
            out << "\n";
        }
    }
    return 0;
}
