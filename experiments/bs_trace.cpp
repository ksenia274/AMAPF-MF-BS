// Copy of ../src/flow-bs.cpp with tracing. All additions are marked // [TRACE];
// the original main() is replaced by the code after the line 'using namespace std::chrono;'.
// Usage: bs_trace.exe MAP.map FILE.scen K   (tracing is printed only if env BS_TRACE=1)
#include <bits/stdc++.h>
#define mk make_pair
#define fs first
#define sc second
using namespace std;
typedef long long ll;
typedef long double ld;
const int INF = 1e9;
int maxTimestep = 1e9;
const int MX_WIDTH = 100000;
const int MX_HEIGHT = 1;
const int SZ = MX_WIDTH * MX_HEIGHT + 1;
int width;  // chanage it one time to the width of the map.
int height; // chanage it one time to the height of the map.
int heuristic[SZ];

// Classes with operators:
struct Edge
{
    int cellID, timeStep;
    Edge(int cellID, int timeStep) : cellID(cellID), timeStep(timeStep) {}
    bool operator==(const Edge &other) const
    {
        return cellID == other.cellID && timeStep == other.timeStep;
    }
};
bool operator<(Edge a, Edge b)
{
    return a.timeStep != b.timeStep ? a.timeStep < b.timeStep : a.cellID < b.cellID;
}
namespace std
{
    template <>
    struct hash<Edge>
    {
        auto operator()(const Edge &e) const -> size_t
        {
            return e.timeStep * SZ + e.cellID;
        }
    };
}
struct Interval
{
    int l, h;
    Interval() {}
    Interval(int l, int h) : l(l), h(h) {}
};
struct TimestepCostPair
{
    int timeStep;
    bool blockedToMove; // Added to mark the nodes which are blocked to use the move actions because they are created in the infinite blocked interval of a goal cell (and no inverse edge is used yet).
    TimestepCostPair() {}
    TimestepCostPair(int timeStep) : timeStep(timeStep)
    {
        blockedToMove = false;
    }
    TimestepCostPair(int timeStep, bool blockedToMove) : timeStep(timeStep), blockedToMove(blockedToMove) {}
};
bool operator<(TimestepCostPair a, TimestepCostPair b)
{
    return a.timeStep < b.timeStep;
}
struct Node
{
    int parent, cellID;
    TimestepCostPair timeStepCostPair;
    Node() {}
    Node(TimestepCostPair timeStepCostPair, int parent, int cellID) : timeStepCostPair(timeStepCostPair), parent(parent), cellID(cellID) {}
};
bool operator<(Node a, Node b)
{ // inversed to inverse the default priority_queue
    return a.timeStepCostPair.timeStep+heuristic[a.cellID] > b.timeStepCostPair.timeStep+heuristic[b.cellID];
}
const int SZBIG = 1000000;
// storage::
bool mapCell[SZBIG]; // cell=mapCell[id]: true -> obstacle, false -> free
vector<int> nebors[SZ];
int sinkID, mapSize;
vector<int> startCells;
bool isGoalCell[SZ];
// The edges will be stored in the 'edges[destination]'.
set<int> extraToGoalEdges;    // To the goal, it is enough to store the id of the extra nodes which are connected to goal.
set<Edge> edges[SZ];          // between other cells, it is neccessary to store the time step and the id of the next cell.
set<TimestepCostPair> visitedTimeSTeps[SZ];
set<int> blocks[SZ];
int timeAssigningGoalCell[SZ];
inline bool isSink(int cellID)
{
    return cellID == sinkID;
}
int freeCells[SZBIG];
void genAllNeighors()
{ // fill 'map' and 'isGoalCell' sequentially (in 1D arrays), 'width' and 'height' and you are ready to call this function.
    int cntNodes = 0, cntFree=0;
    int di[4] = {0, 0, 1, -1}, dj[4] = {1, -1, 0, 0};
    for (int i = 0; i < height; ++i)
    {
        for (int j = 0; j < width; ++j)
        {
            if (!mapCell[cntNodes])
            {
                freeCells[cntNodes] = cntFree;
                ++cntFree;
            }
            ++cntNodes;
        }
    }
    sinkID = cntFree;
    cntNodes = 0;
    for (int i = 0; i < height; ++i)
    {
        for (int j = 0; j < width; ++j)
        {
            if (!mapCell[cntNodes])
            {
                int cell = freeCells[cntNodes];
                for (int k = 0; k < 4; ++k)
                {
                    int ii = i + di[k];
                    int jj = j + dj[k];
                    int id = cntNodes + dj[k] + di[k] * width;
                    if (ii < height && ii >= 0 && jj < width && jj >= 0)
                    {
                        if (!mapCell[id])
                        {
                            nebors[cell].push_back(freeCells[id]);
                        }
                    }
                }
            }
            ++cntNodes;
        }
    }
}
pair<bool, Interval> checkTimestepAndGetUnvisitedSafeInterval(TimestepCostPair timeStepCostPair, int cellID)
{
    int prevBlock = -1, nxtBlock = maxTimestep;
    auto itr = blocks[cellID].lower_bound(timeStepCostPair.timeStep);
    if (itr != blocks[cellID].end())
    {
        nxtBlock = *itr;
    }
    if (itr != blocks[cellID].begin())
    {
        --itr;
        prevBlock = *itr;
    }
    int nxtVisitedTimestep = maxTimestep + 1;
    auto itrt = visitedTimeSTeps[cellID].upper_bound(TimestepCostPair(timeStepCostPair.timeStep));
    if (itrt != visitedTimeSTeps[cellID].begin())
    {
        --itrt;
        if (itrt->timeStep > prevBlock)
        {
            return mk(false, Interval());
        }
        ++itrt;
    }

    if (itrt != visitedTimeSTeps[cellID].end() && itrt->timeStep <= nxtBlock)
    {
        nxtVisitedTimestep = itrt->timeStep;
        return {true, Interval(timeStepCostPair.timeStep, nxtVisitedTimestep - 1)};
    }
    return {true, Interval(timeStepCostPair.timeStep, nxtBlock)};
}
bool checkTimestep(TimestepCostPair timeStepCostPair, int cellID)
{
    int prevBlock = -1;
    auto itr = blocks[cellID].lower_bound(timeStepCostPair.timeStep);
    if (itr != blocks[cellID].begin())
    {
        --itr;
        prevBlock = *itr;
    }
    auto itrt = visitedTimeSTeps[cellID].upper_bound(TimestepCostPair(timeStepCostPair.timeStep));
    if (itrt != visitedTimeSTeps[cellID].begin())
    {
        --itrt;
        if (itrt->timeStep > prevBlock) //&& prvCost <= timeStepCostPair.cost - timeStepCostPair.timeStep)
        {
            return false;
        }
    }
    return true;
}
bool isThereAnEdgeToGoalFromExtraNode(int cellID)
{
    return extraToGoalEdges.count(cellID);
}
bool isThereAnEdge(int source, int destination, int timeStep)
{
    return edges[destination].count(Edge(source, timeStep));
}
void visit(int cellID, TimestepCostPair timeStepCostPair)
{
    visitedTimeSTeps[cellID].insert(timeStepCostPair);
}
void getAllTimeSteps(int lowestTimeStep, int highestTimeStep, int cellID, vector<pair<int, bool>> &validtimeStepsWithMoveBlocked)
{
    if (isGoalCell[cellID] && timeAssigningGoalCell[cellID] < INF)
    {
        for (auto &it : blocks[cellID])
        {
            if (lowestTimeStep > highestTimeStep)
                break;
            if (it >= lowestTimeStep)
            {
                validtimeStepsWithMoveBlocked.push_back(mk(lowestTimeStep, false));
                lowestTimeStep = it + 2;
            }
        }
        if (lowestTimeStep <= highestTimeStep)
        {
            validtimeStepsWithMoveBlocked.push_back(mk(lowestTimeStep, true));
        }
    }
    else
    {
        for (auto &it : blocks[cellID])
        {
            if (lowestTimeStep > highestTimeStep)
                break;
            if (it >= lowestTimeStep)
            {
                validtimeStepsWithMoveBlocked.push_back(mk(lowestTimeStep, false));
                lowestTimeStep = it + 2;
            }
        }
        if (lowestTimeStep <= highestTimeStep)
        {
            validtimeStepsWithMoveBlocked.push_back(mk(lowestTimeStep, false));
        }
    }
}
void getAllTimestepCostPairs(int cellSource, int cellDestination, Interval it, vector<TimestepCostPair> &result)
{
    vector<pair<int, bool>> timeStepsWithMoveBlocked; // When we move to the infinite blocked interval of a goal cell (the last waiting before connecting to sink node), we don't allow the resulting node to make move actions.
    int lowestTimeStep, highestTimeStep;
    if (it.h % 2 == 0) // the high time step is in the copy 0 of the layer.
    {
        if (isThereAnEdge(cellDestination, cellSource, it.h - 1))
        {
            timeStepsWithMoveBlocked.push_back(mk(it.h - 1, it.h - 1 >= timeAssigningGoalCell[cellDestination]));
        }
        highestTimeStep = it.h;
    }
    else
    {
        if (isThereAnEdge(cellSource, cellDestination, it.h))
        {
            highestTimeStep = it.h - 1;
        }
        else
        {
            highestTimeStep = it.h + 1;
        }
    }
    if (it.l % 2)
    {
        if (isThereAnEdge(cellSource, cellDestination, it.l))
        {
            lowestTimeStep = it.l + 3;
        }
        else
        {
            lowestTimeStep = it.l + 1;
        }
    }
    else
    {
        if (isThereAnEdge(cellDestination, cellSource, it.l - 1))
            lowestTimeStep = it.l - 1;
        else
            lowestTimeStep = it.l + 2;
    }
    if (highestTimeStep >= lowestTimeStep)
    {
        getAllTimeSteps(lowestTimeStep, highestTimeStep, cellDestination, timeStepsWithMoveBlocked);
    }
    for (auto t : timeStepsWithMoveBlocked)
    {
        result.push_back(TimestepCostPair(t.first, t.second));
    }
}
void traceHookSolve(int T);                    // [TRACE]
void traceHookPath(vector<Node> &pathNodes);   // [TRACE]
void traceHookState();                         // [TRACE]
void traceHookFail(int T);                     // [TRACE]
void addPathEdges(vector<Node> &nodes, int sinkNodeID)
{
    Node node1, node2 = nodes[sinkNodeID];
    int par = node2.parent;
    vector<Node> pathNodes;
    pathNodes.push_back(node2);
    while (par != -1)
    {
        node1 = nodes[par];
        Node nodeTmp = node1;
        if (node1.timeStepCostPair.timeStep <= node2.timeStepCostPair.timeStep)
        {
            if (node2.timeStepCostPair.timeStep % 2)
            { // Case when go to the upper bound of the time interval then go downward using negative edge.
                for (int timeStep = node2.timeStepCostPair.timeStep + 1; timeStep >= node1.timeStepCostPair.timeStep; timeStep--)
                {
                    nodeTmp.timeStepCostPair.timeStep = timeStep;
                    pathNodes.push_back(nodeTmp);
                }
            }
            else
            {
                for (int timeStep = node2.timeStepCostPair.timeStep - 1; timeStep >= node1.timeStepCostPair.timeStep; timeStep--)
                {
                    nodeTmp.timeStepCostPair.timeStep = timeStep;
                    pathNodes.push_back(nodeTmp);
                }
            }
        }
        else
        {
            for (int timeStep = node2.timeStepCostPair.timeStep + 1; timeStep <= node1.timeStepCostPair.timeStep; timeStep++)
            {
                nodeTmp.timeStepCostPair.timeStep = timeStep;
                pathNodes.push_back(nodeTmp);
            }
        }
        node2 = node1;
        par = node1.parent;
    }
    reverse(pathNodes.begin(), pathNodes.end());
    traceHookPath(pathNodes); // [TRACE]
    for (unsigned int i = 0; i + 1 < pathNodes.size(); ++i)
    {
        node1 = pathNodes[i];
        node2 = pathNodes[i + 1];
        if (isGoalCell[node1.cellID])
        {
            if (timeAssigningGoalCell[node1.cellID] < node1.timeStepCostPair.timeStep)
            {
                for (int t = timeAssigningGoalCell[node1.cellID] + 1; t <= node1.timeStepCostPair.timeStep; ++t)
                {
                    edges[node1.cellID].insert({node1.cellID, t});
                    blocks[node1.cellID].insert(t);
                }
                timeAssigningGoalCell[node1.cellID] = node1.timeStepCostPair.timeStep;
            }
        }
        if (node1.timeStepCostPair.timeStep > node2.timeStepCostPair.timeStep)
        { // --> the edges is between map-cells (none-extra-none-goal nodes).
            edges[node1.cellID].erase({node2.cellID, node2.timeStepCostPair.timeStep});
            if (node1.cellID == node2.cellID)
            {
                blocks[node1.cellID].erase(node2.timeStepCostPair.timeStep);
            }
        }
        else // if (node1.timeStepCostPair.timeStep < node2.timeStepCostPair.timeStep)
        {    // --> the edge is between map-cells (none-extra-none-goal nodes).
            edges[node2.cellID].insert({node1.cellID, node1.timeStepCostPair.timeStep});
            if (node1.cellID == node2.cellID)
            {
                blocks[node1.cellID].insert(node1.timeStepCostPair.timeStep);
            }
        }
    }
    blocks[node2.cellID].insert(node2.timeStepCostPair.timeStep);
    edges[node2.cellID].insert({node2.cellID, node2.timeStepCostPair.timeStep});
    timeAssigningGoalCell[node2.cellID] = node2.timeStepCostPair.timeStep;
}

vector<Node> nodes;
priority_queue<Node> q;
int numOfExpansions;
void partialReset()
{
    // startCells.clear();
    // memset(isGoalCell, 0, sizeof isGoalCell);
    extraToGoalEdges.clear();
    for (int i = 0; i < SZ; ++i)
    {
        blocks[i].clear();
        edges[i].clear();
        // nebors[i].clear();
        timeAssigningGoalCell[i] = INF; // This value means that this goal is not used yet.
    }
}
void calHeuristics(){
    queue<pair<int, int>> q;
    for(int i=0; i<SZ; ++i){
        if(isGoalCell[i] && timeAssigningGoalCell[i]==INF){
            q.push({i,0});
        }
        heuristic[i]=-1;
    }
    while(!q.empty()){
        auto tmp = q.front();
        q.pop();
        if(heuristic[tmp.first]!=-1){
            continue;
        }
        heuristic[tmp.first]=tmp.second;
        for(auto it:nebors[tmp.first]){
            if(heuristic[it]==-1){
                q.push({it,tmp.second+1});
            }
        }
    }
}
int remainingGoals;
int solve(int min_t)
{
    maxTimestep = min_t*2-1;
    traceHookSolve(min_t); // [TRACE]
    while (remainingGoals)
    {
        calHeuristics();
        // cout<<"Agents remaining: "<<goalsNum<<" "<<numOfExpansions<<endl;
        while (!q.empty())
        {
            q.pop();
        }
        nodes.clear();
        for (auto it : startCells)
        {
            q.push(Node(TimestepCostPair(0, 0), -1, it));
        }
        int sinkNodeID = -1;
        for (int i = 0; i <= sinkID; ++i)
        {
            visitedTimeSTeps[i].clear();
        }
        while (!q.empty())
        {
            Node tp = q.top();
            int nodeID = nodes.size();
            nodes.push_back(tp);
            q.pop();
            int currentCell = tp.cellID;
            TimestepCostPair timeStepCostPair = tp.timeStepCostPair;
            pair<bool, Interval> res = checkTimestepAndGetUnvisitedSafeInterval(timeStepCostPair, currentCell);
            if (!res.first)
            { // visited time step in ths cell.
                continue;
            }
            numOfExpansions++;
            if (isGoalCell[currentCell] && timeAssigningGoalCell[currentCell] == INF && res.second.h == maxTimestep)
            {
                sinkNodeID = nodeID;
                break;
            }
            visit(currentCell, timeStepCostPair);
            vector<int> &nebs = nebors[currentCell];
            Interval currentInterval = res.second;
            // special edge: inverse of wait action.
            if (isThereAnEdge(currentCell, currentCell, currentInterval.l - 1) || currentInterval.l - 1 >= timeAssigningGoalCell[currentCell])
            {
                q.push(Node(TimestepCostPair(currentInterval.l - 1, false), nodeID, currentCell));
            }
            // special edge: infinite node (came from infinite interval and projected to infinite blocked interval).
            if (tp.timeStepCostPair.blockedToMove)
            {
                if (timeStepCostPair.timeStep + 2 <= currentInterval.h)
                {
                    q.push(Node(TimestepCostPair(timeStepCostPair.timeStep + 2, true), tp.parent, currentCell));
                }
            }
            else
            {
                for (auto neborCell : nebs)
                {
                    vector<TimestepCostPair> result;
                    getAllTimestepCostPairs(currentCell, neborCell, currentInterval, result);
                    for (auto it : result)
                    {
                        if (checkTimestep(it, neborCell))
                            q.push(Node(it, nodeID, neborCell));
                    }
                }
            }
        }
        if (sinkNodeID == -1)
        {
            traceHookFail(min_t); // [TRACE]
            return false;
        }
        addPathEdges(nodes, sinkNodeID);
        traceHookState(); // [TRACE]
        remainingGoals--;
    }
    return true;
}
void readMap(string mapName)
{
    ifstream in(mapName.c_str());
    if (!in.good())
    {
        cerr<<"Couldn't open the file "<<mapName<<". Exit"<<endl;
        exit(0);
    }
    string type, height_, width_, map_, row;
    in >> type >> type >> height_ >> height >> width_ >> width >> map_;
    mapSize = height * width;
    int cnt = 0;
    for (int i = 0; i < height; ++i)
    {
        in >> row;
        for (int j = 0; j < width; ++j)
        {
            if (row[j] == '@' || row[j] == 'T')
            {
                mapCell[cnt++] = 1;
            }
            else
            {
                mapCell[cnt++] = 0;
            }
        }
    }
    in.close();
}
void readInputs(string fileName, int numOfAgents)
{
    ifstream in(fileName.c_str());
    if (!in.good())
    {
        cerr<<"Couldn't open the file "<<fileName<<". Exit"<<endl;
        exit(0);
    }
    string version;
    in >> version >> version;
    string num, map_;
    int w, h, r, c;
    double doubleNum;
    int cnt = 0;
    while (in >> num >> map_ && cnt++ < numOfAgents)
    {
        in >> w >> h;
        assert(w == width);
        assert(h == height);
        in >> c >> r;
        startCells.push_back(freeCells[r * width + c]);
        in >> c >> r;
        isGoalCell[freeCells[r * width + c]] = 1;
        in >> doubleNum;
    }
    in.close();
}
int num_of_agents(string fileName)
{
    ifstream in(fileName.c_str());
    if (!in.good())
    {
        cerr<<"Couldn't open the file "<<fileName<<". Exit"<<endl;
        exit(0);
    }
    string version;
    in >> version >> version;
    string num, map;
    int w, h, r, c;
    double doubleNum;
    int cnt = 0;
    while (in >> num >> map)
    {
        in >> w >> h;
        in >> c >> r;
        in >> c >> r;
        in >> doubleNum;
        ++cnt;
    }
    in.close();
    return cnt;
}
void reset()
{
    startCells.clear();
    memset(isGoalCell, 0, sizeof isGoalCell);
    for (int i = 0; i < SZ; ++i)
    {
        nebors[i].clear();
    }
}

vector<string> mapNames = {
    "Berlin_1_256",
    "Boston_0_256",
    "brc202d",
    "den520d",
    "maze-128-128-10",
    "orz900d",
    "Paris_1_256",
    "warehouse-20-40-10-2-2",
    "w_woundedcoast",
    "empty-8-8",
    "empty-16-16",
    "empty-32-32",
    "ht_mansion_n",
    "maze-32-32-2",
    "maze-32-32-4",
    "maze-128-128-1",
    "maze-128-128-2",
    "lak303d",
    "lt_gallowstemplar_n",
    "ost003d",
    "random-32-32-10",
    "random-32-32-20",
    "random-64-64-20",
    "warehouse-10-20-10-2-1",
    "warehouse-20-40-10-2-1",
    "room-32-32-4",
    "room-64-64-8",
    "room-64-64-16",
    "ht_chantry",
    "warehouse-10-20-10-2-2",
    "random-64-64-10",
    "empty-48-48",
    "den312d"

};
map<string, int>estimates[26][1001];
void readEstimations(){
    ifstream in("../data/estimates.txt");
    if (!in.good())
    {
        cerr<<"Couldn't open the estimations file"<<std::endl;
        exit(0);
    }
    string map;
    int scen, numOfAgents, t;
    while (in >> map >> scen >> numOfAgents >> t)
    {
        estimates[scen][numOfAgents][map] = t;
    }
    in.close();
}

using namespace std::chrono;
// ---------------- [TRACE] everything below is new ----------------
// Trace goes to stderr, so stdout holds only the result line (same format as bs_single).
bool traceOn = false;
vector<int> cellPos; // free cell id -> index row*width+col in the map
int pathCounter = 0;

string cellName(int cellID)
{
    int p = cellPos[cellID];
    return "(" + to_string(p / width) + "," + to_string(p % width) + ")";
}
// Network node (cell, idx): idx = 2t is the "in" copy at step t, idx = 2t+1 is the "out" copy.
string nodeName(int cellID, int idx)
{
    return cellName(cellID) + "@" + to_string(idx) + "[t=" + to_string(idx / 2) + (idx % 2 ? ",out]" : ",in]");
}
void traceHookSolve(int T)
{
    if (traceOn)
        cerr << "\n=== solve(T=" << T << "), maxTimestep=" << 2 * T - 1 << ", goals left: " << remainingGoals << " ===" << endl;
}
void traceHookFail(int T)
{
    if (traceOn)
        cerr << "--- no augmenting path for T=" << T << ", flow is kept for T+1" << endl;
}
void traceHookPath(vector<Node> &pathNodes)
{
    if (!traceOn)
        return;
    cerr << "--- path #" << ++pathCounter << " (start " << cellName(pathNodes[0].cellID) << ")" << endl;
    cerr << "    raw (cellID,idx):";
    for (auto &pn : pathNodes)
        cerr << " (" << pn.cellID << "," << pn.timeStepCostPair.timeStep << ")";
    cerr << endl;
    for (unsigned int i = 0; i + 1 < pathNodes.size(); ++i)
    {
        int c1 = pathNodes[i].cellID, i1 = pathNodes[i].timeStepCostPair.timeStep;
        int c2 = pathNodes[i + 1].cellID, i2 = pathNodes[i + 1].timeStepCostPair.timeStep;
        string kind;
        if (i2 == i1 + 1)
            kind = c1 != c2 ? "move" : (i1 % 2 ? "wait" : "in->out");
        else
            kind = string("CANCEL ") + (c1 != c2 ? "move" : (i2 % 2 ? "wait" : "in->out"));
        cerr << "    " << nodeName(c1, i1) << " -> " << nodeName(c2, i2) << "  " << kind << endl;
    }
    const Node &last = pathNodes.back();
    cerr << "    end " << nodeName(last.cellID, last.timeStepCostPair.timeStep)
         << ": goal " << cellName(last.cellID) << " is taken from here up to maxTimestep=" << maxTimestep << endl;
}
void traceHookState()
{
    if (!traceOn)
        return;
    cerr << "    flow edges (src -> dst):";
    for (int d = 0; d < sinkID; ++d)
        for (auto &e : edges[d])
            cerr << " " << cellName(e.cellID) << "@" << e.timeStep << "->" << cellName(d) << "@" << e.timeStep + 1;
    cerr << endl << "    blocks:";
    for (int c = 0; c < sinkID; ++c)
        if (!blocks[c].empty())
        {
            cerr << " " << cellName(c) << "{";
            bool first = true;
            for (int b : blocks[c])
                cerr << (first ? "" : ",") << b, first = false;
            cerr << "}";
        }
    cerr << endl << "    timeAssigningGoalCell:";
    for (int c = 0; c < sinkID; ++c)
        if (isGoalCell[c])
            cerr << " " << cellName(c) << "=" << (timeAssigningGoalCell[c] == INF ? string("INF") : to_string(timeAssigningGoalCell[c]));
    cerr << endl;
}

int main(int argc, char *argv[])
{
    if (argc < 4)
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen K   (trace: env BS_TRACE=1)" << endl;
        return 1;
    }
    const char *env = getenv("BS_TRACE");
    traceOn = env && string(env) == "1";
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
    cellPos.assign(sinkID, -1);
    for (int i = 0; i < mapSize; ++i)
        if (!mapCell[i])
            cellPos[freeCells[i]] = i;
    if (traceOn)
    {
        cerr << "starts:";
        for (int s : startCells)
            cerr << " " << cellName(s);
        cerr << endl << "goals:";
        for (int c = 0; c < sinkID; ++c)
            if (isGoalCell[c])
                cerr << " " << cellName(c);
        cerr << endl;
    }

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
