// Bulk Search (Ali, Yakovlev, AAAI 2024) for one team of anonymous agents, as a class.
// The search is ../src/flow-bs.cpp moved into BulkSearchTeam almost line by line: the former globals are
// members, and the heuristic is stored in the queue node (same ordering as the global operator<), so for the
// same input T and the number of expansions are the same as in bs_single.
// The map (Grid) is shared by all teams; one BulkSearchTeam = one team = its own flow.
#pragma once
#include <bits/stdc++.h>

namespace bs
{
using namespace std;
const int INF = 1e9;

struct Grid
{
    int width = 0, height = 0, numCells = 0; // numCells = number of free cells, free cell ids are 0..numCells-1
    vector<int> freeId;                      // row*width+col -> free cell id, -1 for obstacles
    vector<int> cellPos;                     // free cell id -> row*width+col
    vector<vector<int>> nebors;

    bool load(const string &mapName)
    {
        ifstream in(mapName.c_str());
        if (!in.good())
            return false;
        string type, height_, width_, map_, row;
        in >> type >> type >> height_ >> height >> width_ >> width >> map_;
        freeId.assign(height * width, -1);
        cellPos.clear();
        for (int i = 0; i < height; ++i)
        {
            in >> row;
            for (int j = 0; j < width; ++j)
                if (!(row[j] == '@' || row[j] == 'T'))
                {
                    freeId[i * width + j] = cellPos.size();
                    cellPos.push_back(i * width + j);
                }
        }
        numCells = cellPos.size();
        nebors.assign(numCells, vector<int>());
        int di[4] = {0, 0, 1, -1}, dj[4] = {1, -1, 0, 0}; // same order as genAllNeighors()
        for (int c = 0; c < numCells; ++c)
        {
            int i = cellPos[c] / width, j = cellPos[c] % width;
            for (int k = 0; k < 4; ++k)
            {
                int ii = i + di[k], jj = j + dj[k];
                if (ii < height && ii >= 0 && jj < width && jj >= 0 && freeId[ii * width + jj] != -1)
                    nebors[c].push_back(freeId[ii * width + jj]);
            }
        }
        return true;
    }
    int id(int x, int y) const { return x < 0 || y < 0 || x >= width || y >= height ? -1 : freeId[y * width + x]; }
    int x(int cell) const { return cellPos[cell] % width; }
    int y(int cell) const { return cellPos[cell] / width; }
};

class BulkSearchTeam
{
public:
    long long numOfExpansions = 0;

    // starts and goals are free cell ids of the grid.
    BulkSearchTeam(const Grid &grid, const vector<int> &starts, const vector<int> &goals)
        : g(grid), n(grid.numCells), startCells(starts), isGoalCell(grid.numCells, 0), edges(n), visitedTimeSTeps(n),
          blocks(n), timeAssigningGoalCell(n, INF), heuristic(n)
    {
        for (int goal : goals)
            isGoalCell[goal] = 1;
    }

    // Vertex constraint: the team may not be in `cell` at step t (no flow on (cell, 2t) -> (cell, 2t+1)).
    // Agents stay in their goals forever, so a goal with a constraint at t can be a final cell only for T > t.
    void addVertexConstraint(int cell, int t)
    {
        explicitGoalWaits = true;
        vertexConstraints.push_back({t, cell});
        forbiddenIdx[cell].insert(2 * t);
        lastForbiddenAt[cell] = max(lastForbiddenAt[cell], t);
    }

    // Edge constraint: the team may not move from -> to between steps t and t+1 (no flow on (from, 2t+1) -> (to, 2t+2)).
    void addEdgeConstraint(int from, int to, int t)
    {
        explicitGoalWaits = true;
        forbiddenMoves[(long long)from * n + to].insert(t);
    }

    // Minimal makespan T (as the original main: T = 1, 2, ..., the flow is kept between T); -1 if none up to maxT.
    int solveMinMakespan(int maxT)
    {
        numOfExpansions = 0;
        solvedT = -1;
        for (int s : startCells)
            if (forbiddenIdx[s].count(0))
                return -1; // an agent is in its start at step 0 by definition
        sort(vertexConstraints.begin(), vertexConstraints.end());
        remainingGoals = startCells.size();
        partialReset();
        int T = 1;
        while (T <= maxT && !solve(T))
            ++T;
        solvedT = T <= maxT ? T : -1;
        return solvedT;
    }

    // Follows the flow forward from every start after a successful solveMinMakespan().
    // Flow on (src, idx) -> (dst, idx+1) is stored as edges[dst] containing Edge(src, idx).
    // Node (cell, idx): idx = 2t is the "in" copy at step t, idx = 2t+1 is the "out" copy.
    // After the last stored edge in a taken goal (idx >= timeAssigningGoalCell) the agent stays there implicitly.
    // Returns false (and prints why) if the flow is broken; routes[i][t] is the free cell id of agent i at step t.
    bool extractRoutes(vector<vector<int>> &routes) const
    {
        int T = solvedT;
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
                for (int nb : g.nebors[cell])
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

private:
    struct Edge
    {
        int cellID, timeStep;
        Edge(int cellID, int timeStep) : cellID(cellID), timeStep(timeStep) {}
        bool operator<(const Edge &b) const { return timeStep != b.timeStep ? timeStep < b.timeStep : cellID < b.cellID; }
    };
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
        TimestepCostPair(int timeStep) : timeStep(timeStep), blockedToMove(false) {}
        TimestepCostPair(int timeStep, bool blockedToMove) : timeStep(timeStep), blockedToMove(blockedToMove) {}
        bool operator<(const TimestepCostPair &b) const { return timeStep < b.timeStep; }
    };
    struct Node
    {
        int parent, cellID;
        TimestepCostPair timeStepCostPair;
        int key; // timeStep + heuristic[cellID] at the moment of the push
    };
    struct NodeCmp
    { // inversed to inverse the default priority_queue (as operator< of the original)
        bool operator()(const Node &a, const Node &b) const { return a.key > b.key; }
    };

    const Grid &g;
    int n; // number of free cells
    vector<int> startCells;
    vector<char> isGoalCell;
    // The edges will be stored in the 'edges[destination]'.
    vector<set<Edge>> edges;
    vector<set<TimestepCostPair>> visitedTimeSTeps;
    // Boundaries of the waiting chains ("bulks"): b in blocks[cell] means the edge (cell, b) -> (cell, b+1) is cut,
    // either because the flow uses it or (for b = 2t) because of a vertex constraint at step t.
    // Going backwards is decided by `edges` and timeAssigningGoalCell, never by blocks.
    vector<set<int>> blocks;
    vector<int> timeAssigningGoalCell;
    vector<pair<int, int>> vertexConstraints = {}; // (t, cell), sorted by solveMinMakespan
    unsigned int vertexConstraintsInBlocks = 0;    // prefix of vertexConstraints already inserted into blocks
    vector<set<int>> forbiddenIdx = vector<set<int>>(n);
    vector<int> lastForbiddenAt = vector<int>(n, -1);
    map<long long, set<int>> forbiddenMoves; // from*n+to -> steps t of the forbidden moves
    // The original keeps the wait of an agent in its taken goal implicit (timeAssigningGoalCell) and lets a new
    // path enter that infinite interval only at its earliest step, so the agent there can leave only that early.
    // With constraints leaving later may be necessary, so the waits are stored explicitly up to maxTimestep:
    // the interval becomes a chain of one-node bulks that can be entered and cancelled at any step.
    bool explicitGoalWaits = false;
    int explicitWaitsUpTo = -1; // maxTimestep for which the waits of all taken goals are explicit
    vector<int> heuristic;
    int maxTimestep = INF;
    int remainingGoals = 0;
    int solvedT = -1;
    vector<Node> nodes;
    priority_queue<Node, vector<Node>, NodeCmp> q;

    void push(TimestepCostPair p, int parent, int cellID) { q.push(Node{parent, cellID, p, p.timeStep + heuristic[cellID]}); }

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
                return make_pair(false, Interval());
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
            if (itrt->timeStep > prevBlock)
            {
                return false;
            }
        }
        return true;
    }
    bool isThereAnEdge(int source, int destination, int timeStep)
    {
        return edges[destination].count(Edge(source, timeStep));
    }
    void getAllTimeSteps(int lowestTimeStep, int highestTimeStep, int cellID, vector<pair<int, bool>> &validtimeStepsWithMoveBlocked)
    {
        for (auto &it : blocks[cellID])
        {
            if (lowestTimeStep > highestTimeStep)
                break;
            if (it >= lowestTimeStep)
            {
                validtimeStepsWithMoveBlocked.push_back(make_pair(lowestTimeStep, false));
                lowestTimeStep = it + 2;
            }
        }
        if (lowestTimeStep <= highestTimeStep)
        { // the last interval of a taken goal is its infinite blocked interval
            validtimeStepsWithMoveBlocked.push_back(make_pair(lowestTimeStep, isGoalCell[cellID] && timeAssigningGoalCell[cellID] < INF));
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
                timeStepsWithMoveBlocked.push_back(make_pair(it.h - 1, it.h - 1 >= timeAssigningGoalCell[cellDestination]));
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
        auto forbidden = forbiddenMoves.empty() ? forbiddenMoves.end() : forbiddenMoves.find((long long)cellSource * n + cellDestination);
        for (auto t : timeStepsWithMoveBlocked)
        {
            // An even entry y is the move (cellSource, y-1) -> (cellDestination, y) (odd ones cancel a move
            // cellDestination -> cellSource). If it is forbidden, take the next allowed move into the same bulk of
            // cellDestination: up to its first cut and up to the last move the bulk of cellSource allows.
            if (forbidden != forbiddenMoves.end() && t.first % 2 == 0)
            {
                auto cut = blocks[cellDestination].lower_bound(t.first);
                int last = min(highestTimeStep, cut == blocks[cellDestination].end() ? INF : *cut);
                while (t.first <= last && forbidden->second.count(t.first / 2 - 1))
                    t.first += 2;
                if (t.first > last)
                    continue;
            }
            result.push_back(TimestepCostPair(t.first, t.second));
        }
    }
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
                        checkNotForbidden(node1.cellID, t, "waiting in a taken goal");
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
                    checkNotForbidden(node1.cellID, node2.timeStepCostPair.timeStep, "cancelling a wait");
                    blocks[node1.cellID].erase(node2.timeStepCostPair.timeStep);
                }
            }
            else // if (node1.timeStepCostPair.timeStep < node2.timeStepCostPair.timeStep)
            {    // --> the edge is between map-cells (none-extra-none-goal nodes).
                if (node1.cellID != node2.cellID && !forbiddenMoves.empty())
                {
                    auto f = forbiddenMoves.find((long long)node1.cellID * n + node2.cellID);
                    if (f != forbiddenMoves.end() && f->second.count(node1.timeStepCostPair.timeStep / 2))
                        throw logic_error("flow on a forbidden move " + to_string(node1.cellID) + " -> " + to_string(node2.cellID) +
                                          " at idx " + to_string(node1.timeStepCostPair.timeStep));
                }
                edges[node2.cellID].insert({node1.cellID, node1.timeStepCostPair.timeStep});
                if (node1.cellID == node2.cellID)
                {
                    checkNotForbidden(node1.cellID, node1.timeStepCostPair.timeStep, "flow");
                    blocks[node1.cellID].insert(node1.timeStepCostPair.timeStep);
                }
            }
        }
        checkNotForbidden(node2.cellID, node2.timeStepCostPair.timeStep, "final node");
        blocks[node2.cellID].insert(node2.timeStepCostPair.timeStep);
        edges[node2.cellID].insert({node2.cellID, node2.timeStepCostPair.timeStep});
        timeAssigningGoalCell[node2.cellID] = node2.timeStepCostPair.timeStep;
        if (explicitGoalWaits)
            makeGoalWaitsExplicit(node2.cellID, node2.timeStepCostPair.timeStep + 1, maxTimestep);
    }
    void partialReset()
    {
        for (int i = 0; i < n; ++i)
        {
            blocks[i].clear();
            edges[i].clear();
            timeAssigningGoalCell[i] = INF; // This value means that this goal is not used yet.
        }
        vertexConstraintsInBlocks = 0;
        explicitWaitsUpTo = -1;
    }
    void makeGoalWaitsExplicit(int goal, int from, int to)
    {
        for (int idx = from; idx <= to; ++idx)
        {
            checkNotForbidden(goal, idx, "waiting in a taken goal");
            edges[goal].insert({goal, idx});
            blocks[goal].insert(idx);
        }
    }
    // Extends the explicit waits of all taken goals to the new maxTimestep (called when T grows).
    void extendGoalWaits()
    {
        if (!explicitGoalWaits)
            return;
        for (int goal = 0; goal < n; ++goal)
            if (isGoalCell[goal] && timeAssigningGoalCell[goal] < INF)
                makeGoalWaitsExplicit(goal, max(explicitWaitsUpTo, timeAssigningGoalCell[goal]) + 1, maxTimestep);
        explicitWaitsUpTo = maxTimestep;
    }
    // Cuts the chains at vertex constraints with t <= T-1 (inside the horizon of solve(T)). Later ones are inserted
    // when T grows: inserted now they would change the bulks beyond maxTimestep. The flow kept from smaller T never
    // uses them: outside goals it ends before step T_old, and goals with constraints >= T_old were not final cells.
    void insertVertexConstraints(int T)
    {
        for (; vertexConstraintsInBlocks < vertexConstraints.size() && vertexConstraints[vertexConstraintsInBlocks].first <= T - 1; ++vertexConstraintsInBlocks)
            blocks[vertexConstraints[vertexConstraintsInBlocks].second].insert(2 * vertexConstraints[vertexConstraintsInBlocks].first);
    }
    void checkNotForbidden(int cellID, int idx, const char *what)
    {
        if (forbiddenIdx[cellID].count(idx))
            throw logic_error(string(what) + " at a vertex constraint: cell " + to_string(cellID) + ", idx " + to_string(idx));
    }
    void calHeuristics()
    {
        queue<pair<int, int>> q;
        for (int i = 0; i < n; ++i)
        {
            if (isGoalCell[i] && timeAssigningGoalCell[i] == INF)
            {
                q.push({i, 0});
            }
            heuristic[i] = -1;
        }
        while (!q.empty())
        {
            auto tmp = q.front();
            q.pop();
            if (heuristic[tmp.first] != -1)
            {
                continue;
            }
            heuristic[tmp.first] = tmp.second;
            for (auto it : g.nebors[tmp.first])
            {
                if (heuristic[it] == -1)
                {
                    q.push({it, tmp.second + 1});
                }
            }
        }
    }
    bool solve(int min_t)
    {
        maxTimestep = min_t * 2 - 1;
        insertVertexConstraints(min_t);
        extendGoalWaits();
        while (remainingGoals)
        {
            calHeuristics();
            while (!q.empty())
            {
                q.pop();
            }
            nodes.clear();
            for (auto it : startCells)
            {
                push(TimestepCostPair(0, 0), -1, it);
            }
            int sinkNodeID = -1;
            for (int i = 0; i < n; ++i)
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
                // A goal with a vertex constraint at a step >= min_t can't be final: the agent would stay there.
                if (isGoalCell[currentCell] && timeAssigningGoalCell[currentCell] == INF && res.second.h == maxTimestep &&
                    lastForbiddenAt[currentCell] < min_t)
                {
                    sinkNodeID = nodeID;
                    break;
                }
                visitedTimeSTeps[currentCell].insert(timeStepCostPair);
                const vector<int> &nebs = g.nebors[currentCell];
                Interval currentInterval = res.second;
                // special edge: inverse of wait action.
                if (isThereAnEdge(currentCell, currentCell, currentInterval.l - 1) || currentInterval.l - 1 >= timeAssigningGoalCell[currentCell])
                {
                    push(TimestepCostPair(currentInterval.l - 1, false), nodeID, currentCell);
                }
                // special edge: infinite node (came from infinite interval and projected to infinite blocked interval).
                if (tp.timeStepCostPair.blockedToMove)
                {
                    if (timeStepCostPair.timeStep + 2 <= currentInterval.h)
                    {
                        push(TimestepCostPair(timeStepCostPair.timeStep + 2, true), tp.parent, currentCell);
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
                                push(it, nodeID, neborCell);
                        }
                    }
                }
            }
            if (sinkNodeID == -1)
            {
                return false;
            }
            addPathEdges(nodes, sinkNodeID);
            remainingGoals--;
        }
        return true;
    }
};
} // namespace bs
