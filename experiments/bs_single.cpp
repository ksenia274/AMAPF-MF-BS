// Solve one AMAPF instance with the original Bulk Search code.
// The algorithm is taken verbatim from ../src/flow-bs.cpp (included below); only its main() is renamed and not used.
// Usage: bs_single MAP.map FILE.scen K   -> prints optimal makespan T, expansions, ms
#define main flow_bs_original_main
#include "../src/flow-bs.cpp"
#undef main

int main(int argc, char *argv[])
{
    if (argc < 4)
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen K" << endl;
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
    return 0;
}
