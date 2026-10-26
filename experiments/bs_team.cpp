// One team = all K agents of the .scen, solved by bs::BulkSearchTeam (bs_team.hpp).
// Usage: bs_team MAP.map FILE.scen K [ROUTES|-] [CONSTRAINTS]
//   -> prints optimal makespan T, expansions, ms (same as bs_single)
// ROUTES: first line "T K", then K lines "x,y x,y ..." (T+1 positions), agent i = row i of .scen.
// CONSTRAINTS (same format as brute_force.py, '#' starts a comment):
//   v x y t            the team may not be in (x,y) at step t
//   e x1 y1 x2 y2 t    the team may not move (x1,y1) -> (x2,y2) between steps t and t+1
#include "bs_team.hpp"
using namespace std;
using namespace std::chrono;

int main(int argc, char *argv[])
{
    if (argc < 4)
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen K [ROUTES|-] [CONSTRAINTS]" << endl;
        return 1;
    }
    string mapFile = argv[1], scenFile = argv[2];
    int k = atoi(argv[3]);
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
    while ((int)starts.size() < k && in >> num >> mapName >> w >> h >> sx >> sy >> gx >> gy >> optimal)
    {
        starts.push_back(grid.id(sx, sy));
        goals.push_back(grid.id(gx, gy));
        if (starts.back() == -1 || goals.back() == -1)
        {
            cerr << "start or goal of agent " << starts.size() - 1 << " is not a free cell" << endl;
            return 1;
        }
    }
    if (k < 1 || (int)starts.size() < k)
    {
        cerr << "K must be in [1, " << starts.size() << "] for " << scenFile << endl;
        return 1;
    }

    bs::BulkSearchTeam team(grid, starts, goals);
    int lastConstraint = 0;
    if (argc > 5)
    {
        ifstream constraintsIn(argv[5]);
        if (!constraintsIn.good())
        {
            cerr << "Couldn't open the file " << argv[5] << endl;
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
        T = team.solveMinMakespan(maxT);
    }
    catch (const logic_error &e)
    {
        cerr << "internal error: " << e.what() << endl;
        return 4;
    }
    auto stop = high_resolution_clock::now();
    if (T == -1)
    {
        cout << "T=-1 (no solution up to T=" << maxT << ") expansions=" << team.numOfExpansions << endl;
        return 2;
    }
    cout << "T=" << T << " expansions=" << team.numOfExpansions
         << " ms=" << duration_cast<milliseconds>(stop - start).count() << endl;

    if (argc > 4 && string(argv[4]) != "-")
    {
        vector<vector<int>> routes;
        if (!team.extractRoutes(routes))
            return 3;
        ofstream out(argv[4]);
        out << T << " " << k << "\n";
        for (auto &route : routes)
        {
            for (unsigned int t = 0; t < route.size(); ++t)
                out << (t ? " " : "") << grid.x(route[t]) << "," << grid.y(route[t]);
            out << "\n";
        }
    }
    return 0;
}
