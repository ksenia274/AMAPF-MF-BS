// One team = all K agents of the .scen, solved by bs::BulkSearchTeam (bs_team.hpp) or bs::FlowTeam (flow_team.hpp).
// Usage: bs_team MAP.map FILE.scen K [ROUTES|-] [CONSTRAINTS] [--low bs|bspen|bscut|flow|floww] [--others ROUTES]
//                [--t-start 1|lb|match] [--cut penal|all]
//   -> prints optimal makespan T, expansions (bs, bspen, bscut) or the weight of the flow (flow, floww), ms
// --cut (bscut): soft cuts of the waiting chains at the penalized steps (default) or at every step.
// --others: routes of the robots of other teams (format of ROUTES) for the weights of floww / bspen / bscut.
// --t-start lb (default): T starts from bs::teamLowerBound; --t-start 1: from 1; --t-start match: from
// bs::teamMatchBound. Also prints "bound_lb=.. bound_match=.." on stderr; --bounds-only: only that, no search.
// ROUTES: first line "T K", then K lines "x,y x,y ..." (T+1 positions), agent i = row i of .scen.
// CONSTRAINTS (same format as brute_force.py, '#' starts a comment):
//   v x y t            the team may not be in (x,y) at step t
//   e x1 y1 x2 y2 t    the team may not move (x1,y1) -> (x2,y2) between steps t and t+1
#include "flow_team.hpp"
using namespace std;
using namespace std::chrono;

template <class Team>
int run(Team &team, const bs::Grid &grid, int k, const vector<string> &args, int minT);

int main(int argc, char *argv[])
{
    vector<string> args;
    string low = "bs", othersFile, tStart = "lb", cut = "penal";
    bool boundsOnly = false;
    for (int i = 1; i < argc; ++i)
    {
        string a = argv[i];
        if (a == "--low" && i + 1 < argc)
            low = argv[++i];
        else if (a == "--others" && i + 1 < argc)
            othersFile = argv[++i];
        else if (a == "--t-start" && i + 1 < argc)
            tStart = argv[++i];
        else if (a == "--cut" && i + 1 < argc)
            cut = argv[++i];
        else if (a == "--bounds-only")
            boundsOnly = true;
        else
            args.push_back(a);
    }
    if (args.size() < 3 || (low != "bs" && low != "bspen" && low != "bscut" && low != "flow" && low != "floww") ||
        (tStart != "1" && tStart != "lb" && tStart != "match") || (cut != "penal" && cut != "all"))
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen K [ROUTES|-] [CONSTRAINTS] [--low bs|bspen|bscut|flow|floww] [--others ROUTES] [--t-start 1|lb|match] [--cut penal|all]" << endl;
        return 1;
    }
    string mapFile = args[0], scenFile = args[1];
    int k = stoi(args[2]);
    bs::Grid grid;
    if (!grid.load(mapFile))
    {
        cerr << "Couldn't open the file " << mapFile << endl;
        return 1;
    }
    vector<int> starts, goals;
    if (!bs::loadScen(grid, scenFile, k, starts, goals))
        return 1;
    if (k < 1 || (int)starts.size() < k)
    {
        cerr << "K must be in [1, " << starts.size() << "] for " << scenFile << endl;
        return 1;
    }

    int boundLb = bs::teamLowerBound(grid, starts, goals), boundMatch = bs::teamMatchBound(grid, starts, goals);
    cerr << "bound_lb=" << boundLb << " bound_match=" << boundMatch << endl;
    if (boundsOnly)
        return 0;
    int minT = tStart == "lb" ? max(1, boundLb) : tStart == "match" ? max(1, boundMatch) : 1;
    vector<vector<int>> others;
    if (!othersFile.empty())
    {
        ifstream othersIn(othersFile);
        int T, m;
        string pos;
        othersIn >> T >> m;
        for (int i = 0; i < m; ++i)
        {
            others.emplace_back();
            for (int t = 0; t <= T && othersIn >> pos; ++t)
            {
                int x, y;
                sscanf(pos.c_str(), "%d,%d", &x, &y);
                others.back().push_back(grid.id(x, y));
            }
        }
    }
    if (low == "bs" || low == "bspen" || low == "bscut")
    {
        bs::BulkSearchTeam team(grid, starts, goals);
        if (low != "bs" && !others.empty())
            team.setOtherRoutes(others);
        if (low == "bscut")
            team.setCut(cut == "all");
        return run(team, grid, k, args, minT);
    }
    bs::FlowTeam team(grid, starts, goals, low == "floww");
    if (!others.empty())
        team.setOtherRoutes(others);
    return run(team, grid, k, args, minT);
}

template <class Team>
int run(Team &team, const bs::Grid &grid, int k, const vector<string> &args, int minT)
{
    int lastConstraint = 0;
    if (args.size() > 4)
    {
        ifstream constraintsIn(args[4]);
        if (!constraintsIn.good())
        {
            cerr << "Couldn't open the file " << args[4] << endl;
            return 1;
        }
        string line;
        while (getline(constraintsIn, line))
        {
            istringstream ls(line.substr(0, line.find('#')));
            string kind;
            int x, y, x2, y2, t;
            if (!(ls >> kind))
                continue;
            if (kind == "v" && ls >> x >> y >> t && grid.id(x, y) != -1 && t >= 0)
                team.addVertexConstraint(grid.id(x, y), t);
            else if (kind == "e" && ls >> x >> y >> x2 >> y2 >> t && grid.id(x, y) != -1 && grid.id(x2, y2) != -1 &&
                     abs(x - x2) + abs(y - y2) == 1 && t >= 0)
                team.addEdgeConstraint(grid.id(x, y), grid.id(x2, y2), t);
            else
            {
                cerr << "bad constraint line: " << line << endl;
                return 1;
            }
            lastConstraint = max(lastConstraint, t);
        }
    }

    auto start = high_resolution_clock::now();
    // The cap (bound of the original binary search, shifted by the last constraint) only prevents an endless loop
    // on unsolvable inputs.
    int maxT = grid.width * grid.height + k + lastConstraint;
    int T;
    try
    {
        T = team.solveMinMakespan(maxT, minT);
    }
    catch (const logic_error &e)
    {
        cerr << "internal error: " << e.what() << endl;
        return 4;
    }
    auto stop = high_resolution_clock::now();
    if (T == -1)
    {
        cout << "T=-1 (no solution up to T=" << maxT << ")" << endl;
        return 2;
    }
    if constexpr (is_same_v<Team, bs::BulkSearchTeam>)
        cout << "T=" << T << " expansions=" << team.numOfExpansions;
    else
        cout << "T=" << T << " cost=" << team.cost << " net_nodes=" << team.netNodes << " net_edges=" << team.netEdges;
    cout << " ms=" << duration_cast<milliseconds>(stop - start).count() << endl;

    if (args.size() > 3 && args[3] != "-")
    {
        vector<vector<int>> routes;
        if (!team.extractRoutes(routes))
            return 3;
        int fixed = bs::removeSwaps(routes, T);
        if (fixed)
            cerr << "swaps inside the team replaced by waits: " << fixed << endl;
        bs::writeRoutes(grid, args[3], T, routes);
    }
    return 0;
}
