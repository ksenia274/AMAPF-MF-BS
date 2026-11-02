// CBM (Ma, Koenig 2016) for colored MAPF with makespan, low level = Bulk Search (bs_team.hpp).
// Agent i of the .scen belongs to team i % K (as make_colored_yaml.py) and must end in a goal of its team.
// High level = CBS over teams: a node holds the constraints and the plan of every team, key = max team makespan.
// Usage: cbm MAP.map FILE.scen N K [ROUTES|-] [--time-limit SEC] [--max-nodes M] [--tie later|earlier] [--diag]
// Prints "T=<makespan> nodes_generated=.. nodes_expanded=.. lowlevel_calls=.. lowlevel_ms=.. highlevel_ms=.. total_ms=..
// lowlevel_sum_T=.. swaps_fixed=.." (--diag: a second line with the root key, depth, constraints, repeated
// constraint sets and the keys of the expanded nodes);
// T=-1 if a limit was hit (or no solution: then CBS never stops by itself). ROUTES: as bs_team, all N agents.
#include "bs_team.hpp"
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
    bool tieEarlier = false; // among nodes with equal key and conflicting teams: the earlier node first
    bool diag = false;       // collect the statistics below (costs a hash of the constraint sets per node)
    int rootKey = -1, maxDepth = 0, maxConstraintsPerTeam = 0;
    long long duplicateConstraintSets = 0; // generated nodes whose constraint sets (per team) were already seen
    map<int, long long> expandedByKey;

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
        auto start = steady_clock::now();
        auto root = make_shared<CTNode>();
        for (unsigned int team = 0; team < teamAgents.size(); ++team)
        {
            auto plan = replan(team, TeamPlan(), 1);
            if (!plan)
                return nullptr;
            root->plans.push_back(plan);
        }
        evaluate(*root);
        rootKey = root->key;
        noteDiag(*root);
        bool earlier = tieEarlier;
        auto worse = [earlier](const shared_ptr<CTNode> &a, const shared_ptr<CTNode> &b) {
            if (a->key != b->key)
                return a->key > b->key;
            if (a->conflictingTeams != b->conflictingTeams)
                return a->conflictingTeams > b->conflictingTeams;
            return earlier ? a->id > b->id : a->id < b->id; // default: the later node first (depth-first)
        };
        priority_queue<shared_ptr<CTNode>, vector<shared_ptr<CTNode>>, decltype(worse)> open(worse);
        open.push(root);
        while (!open.empty())
        {
            if (duration<double>(steady_clock::now() - start).count() > timeLimitSec || nodesGenerated >= maxNodes)
                return nullptr;
            auto node = open.top();
            open.pop();
            if (node->first.t == -1)
                return node;
            ++nodesExpanded;
            if (diag)
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
                auto plan = replan(team, constraints, node->key); // T from the parent's key (CBM, section 3.2)
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

    shared_ptr<const TeamPlan> replan(int team, TeamPlan plan, int minT)
    {
        auto start = steady_clock::now();
        ++lowLevelCalls;
        bs::BulkSearchTeam solver(g, teamStarts[team], teamGoals[team]);
        int last = 0;
        for (auto &c : plan.vertex)
            solver.addVertexConstraint(c.cell, c.t), last = max(last, c.t);
        for (auto &c : plan.edge)
            solver.addEdgeConstraint(c.from, c.to, c.t), last = max(last, c.t);
        plan.T = solver.solveMinMakespan(g.width * g.height + (int)teamStarts[team].size() + last, minT);
        bool ok = plan.T != -1 && solver.extractRoutes(plan.routes);
        if (ok)
        {
            lowLevelSumT += plan.T;
            swapsFixed += removeSwapsInTeam(plan);
        }
        lowLevelSec += duration<double>(steady_clock::now() - start).count();
        return ok ? make_shared<const TeamPlan>(move(plan)) : nullptr;
    }

    // A swap of two agents of one team is replaced by two waits and the agents exchange the rest of their routes:
    // the cells occupied at every step stay the same, so no new conflicts appear (never observed with Bulk Search).
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
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen N K [ROUTES|-] [--time-limit SEC] [--max-nodes M] [--tie later|earlier] [--diag]" << endl;
        return 1;
    }
    string mapFile = argv[1], scenFile = argv[2], routesFile = "-";
    int numAgents = atoi(argv[3]), numTeams = atoi(argv[4]);
    double timeLimit = 60;
    long long maxNodes = LLONG_MAX;
    bool tieEarlier = false, diag = false;
    for (int i = 5; i < argc; ++i)
    {
        string a = argv[i];
        if (a == "--time-limit" && i + 1 < argc)
            timeLimit = atof(argv[++i]);
        else if (a == "--max-nodes" && i + 1 < argc)
            maxNodes = atoll(argv[++i]);
        else if (a == "--tie" && i + 1 < argc)
            tieEarlier = string(argv[++i]) == "earlier";
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

    auto start = steady_clock::now();
    CBM cbm(grid, starts, goals, numTeams);
    cbm.tieEarlier = tieEarlier;
    cbm.diag = diag;
    shared_ptr<CTNode> result;
    try
    {
        result = cbm.solve(timeLimit, maxNodes);
    }
    catch (const logic_error &e)
    {
        cerr << "internal error: " << e.what() << endl;
        return 4;
    }
    double total = duration<double>(steady_clock::now() - start).count();
    cout << "T=" << (result ? result->key : -1) << " nodes_generated=" << cbm.nodesGenerated
         << " nodes_expanded=" << cbm.nodesExpanded << " lowlevel_calls=" << cbm.lowLevelCalls
         << " lowlevel_ms=" << (long long)(cbm.lowLevelSec * 1000) << " highlevel_ms=" << (long long)((total - cbm.lowLevelSec) * 1000)
         << " total_ms=" << (long long)(total * 1000) << " lowlevel_sum_T=" << cbm.lowLevelSumT << " swaps_fixed=" << cbm.swapsFixed << endl;
    if (diag)
    {
        cout << "diag: root_key=" << cbm.rootKey << " max_depth=" << cbm.maxDepth << " max_constraints_per_team=" << cbm.maxConstraintsPerTeam
             << " repeated_constraint_sets=" << cbm.duplicateConstraintSets << " expanded_by_key=";
        for (auto &kv : cbm.expandedByKey)
            cout << kv.first << ":" << kv.second << " ";
        cout << endl;
    }
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
