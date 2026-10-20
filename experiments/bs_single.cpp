// Solve one AMAPF instance with the original Bulk Search code.
// The algorithm is taken verbatim from ../src/flow-bs.cpp (included below); only its main() is renamed and not used.
// Usage: bs_single MAP.map FILE.scen K [ROUTES]   -> prints optimal makespan T, expansions, ms
// With ROUTES the routes are extracted from the flow and written to that file:
//   first line "T K", then K lines "x,y x,y ..." (T+1 positions, x = column, y = row), agent i = row i of .scen.
#define main flow_bs_original_main
#include "../src/flow-bs.cpp"
#undef main

// Follows the flow forward from every start after a successful solve(T).
// Flow on (src, idx) -> (dst, idx+1) is stored as edges[dst] containing Edge(src, idx).
// Node (cell, idx): idx = 2t is the "in" copy at step t, idx = 2t+1 is the "out" copy.
// After the last stored edge in a taken goal (idx >= timeAssigningGoalCell) the agent stays there implicitly.
// Returns false (and prints why) if the flow is broken; routes[i][t] is the free-cell id of agent i at step t.
bool extractRoutes(int T, vector<vector<int>> &routes)
{
    routes.assign(startCells.size(), vector<int>());
    for (unsigned int a = 0; a < startCells.size(); ++a)
    {
        int cell = startCells[a], idx = 0;
        routes[a].push_back(cell);
        while (idx < 2 * T)
        {
            int next = -1, found = 0;
            if (edges[cell].count(Edge(cell, idx)))
                next = cell, ++found;
            for (int nb : nebors[cell])
                if (edges[nb].count(Edge(cell, idx)))
                    next = nb, ++found;
            if (next != cell && next != -1 && idx % 2 == 0)
            {
                cerr << "agent " << a << ": move edge leaves the \"in\" copy (" << cell << "," << idx << ")" << endl;
                return false;
            }
            if (found > 1)
            {
                cerr << "agent " << a << ": " << found << " flow edges leave (" << cell << "," << idx << ")" << endl;
                return false;
            }
            if (found == 0)
            {
                if (!(isGoalCell[cell] && idx >= timeAssigningGoalCell[cell]))
                {
                    cerr << "agent " << a << ": flow ends at (" << cell << "," << idx << ") outside a taken goal" << endl;
                    return false;
                }
                next = cell; // implicit wait in the goal
            }
            cell = next;
            ++idx;
            if (idx % 2 == 0)
                routes[a].push_back(cell);
        }
    }
    return true;
}

int main(int argc, char *argv[])
{
    if (argc < 4)
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen K [ROUTES]" << endl;
        return 1;
    }
    string mapFile = argv[1], scenFile = argv[2];
    int k = atoi(argv[3]);
    int available = num_of_agents(scenFile);
    if (k < 1 || k > available)
    {
        cerr << "K must be in [1, " << available << "] for " << scenFile << endl;
        return 1;
    }
    readMap(mapFile);
    genAllNeighors();
    readInputs(scenFile, k);

    auto start = high_resolution_clock::now();
    numOfExpansions = 0;
    remainingGoals = k;
    partialReset();
    // As in the original main: flow is kept between T. The cap (bound of the original binary
    // search) only prevents an endless loop, e.g. when two agents of the .scen share a goal.
    int maxT = width * height + k;
    int T = 1;
    while (T <= maxT && !solve(T))
        ++T;
    auto stop = high_resolution_clock::now();
    if (T > maxT)
    {
        cout << "T=-1 (no solution up to T=" << maxT << ") expansions=" << numOfExpansions << endl;
        return 2;
    }
    cout << "T=" << T << " expansions=" << numOfExpansions
         << " ms=" << duration_cast<milliseconds>(stop - start).count() << endl;

    if (argc > 4)
    {
        vector<vector<int>> routes;
        if (!extractRoutes(T, routes))
            return 3;
        vector<int> cellPos(sinkID); // free cell id -> row*width+col
        for (int i = 0; i < mapSize; ++i)
            if (!mapCell[i])
                cellPos[freeCells[i]] = i;
        ofstream out(argv[4]);
        out << T << " " << k << "\n";
        for (auto &route : routes)
        {
            for (unsigned int t = 0; t < route.size(); ++t)
                out << (t ? " " : "") << cellPos[route[t]] % width << "," << cellPos[route[t]] / width;
            out << "\n";
        }
    }
    return 0;
}
