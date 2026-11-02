// Low level of CBM (Ma, Koenig 2016, sections 2.2 and 3.2) for one team: max-flow on the time-expanded network,
// optionally min-cost flow with weights from the routes of the other teams. Same interface as BulkSearchTeam.
// Min-cost flow is run only on the first T with a flow of K (the paper runs it on every T, only the last one counts).
// Network for makespan T, built from scratch for every T and every call (as in the paper):
//   out_t (t = 0..T) and in_t (t = 1..T) for every cell; wait out_t -> in_{t+1}; turnstile in_t -> out_t;
//   for every grid edge {u,v} and t = 0..T-1 a gadget w, w': u_out_t -> w, v_out_t -> w, w -> w',
//   w' -> u_in_{t+1}, w' -> v_in_{t+1} (the paper writes w -> v_in, a typo); all capacities 1.
// Pruning (ours, does not change the solutions): only cells with dist(nearest start) <= t and
// dist(nearest goal) <= T - t get the nodes of step t.
#pragma once
#include "bs_team.hpp"

namespace bs
{
using namespace std;

class FlowTeam
{
public:
    long long cost = 0;
    int netNodes = 0, netEdges = 0; // of the last network built

    FlowTeam(const Grid &grid, const vector<int> &starts, const vector<int> &goals, bool weighted = false)
        : g(grid), n(grid.numCells), weighted(weighted), startCells(starts), isGoalCell(grid.numCells, 0),
          lastForbiddenAt(grid.numCells, -1)
    {
        for (int goal : goals)
            isGoalCell[goal] = 1;
        distStart = bfs(starts);
        distGoal = bfs(goals);
    }

    void addVertexConstraint(int cell, int t)
    {
        forbiddenVertex.insert((long long)t * n + cell);
        lastForbiddenAt[cell] = max(lastForbiddenAt[cell], t);
    }

    void addEdgeConstraint(int from, int to, int t) { forbiddenEdge.insert(((long long)t * n + from) * n + to); }

    // Routes of the robots of the other teams (cell per step); after its end a robot stays in its last cell.
    void setOtherRoutes(const vector<vector<int>> &routes) { otherRoutes = routes; }

    int solveMinMakespan(int maxT, int minT = 1)
    {
        solvedT = -1;
        for (int s : startCells)
            if (forbiddenVertex.count(s))
                return -1;
        for (int T = max(minT, 1); T <= maxT; ++T)
        {
            build(T);
            if (maxFlow() < (int)startCells.size())
                continue;
            if (weighted)
            {
                for (unsigned int e = 0; e < cap.size(); ++e)
                    cap[e] = e % 2 == 0 ? 1 : 0;
                minCostFlow();
            }
            cost = 0;
            for (unsigned int e = 0; e < cap.size(); e += 2)
                if (cap[e] == 0)
                    cost += edgeCost[e];
            solvedT = T;
            return T;
        }
        return -1;
    }

    bool extractRoutes(vector<vector<int>> &routes) const
    {
        if (solvedT == -1)
            return false;
        vector<char> used(cap.size(), 0);
        routes.assign(startCells.size(), vector<int>());
        for (unsigned int a = 0; a < startCells.size(); ++a)
        {
            int node = source;
            while (node != sink)
            {
                int next = -1;
                for (int e = head[node]; e != -1; e = nextEdge[e])
                    if (e % 2 == 0 && cap[e] == 0 && !used[e] && (node != source || to[e] == outNode(0, startCells[a])))
                    {
                        used[e] = 1, next = to[e];
                        break;
                    }
                if (next == -1)
                {
                    cerr << "agent " << a << ": flow ends at node " << node << endl;
                    return false;
                }
                node = next;
                if (nodeCell[node] != -1)
                    routes[a].push_back(nodeCell[node]);
            }
            if ((int)routes[a].size() != solvedT + 1)
            {
                cerr << "agent " << a << ": route of " << routes[a].size() << " cells for T=" << solvedT << endl;
                return false;
            }
        }
        return true;
    }

private:
    const Grid &g;
    int n;
    bool weighted;
    vector<int> startCells;
    vector<char> isGoalCell;
    vector<int> lastForbiddenAt, distStart, distGoal;
    unordered_set<long long> forbiddenVertex, forbiddenEdge;
    vector<vector<int>> otherRoutes;
    int solvedT = -1, T = 0;

    const int source = 0, sink = 1;
    vector<int> outId, inId, nodeCell; // nodeCell: cell of an out node, -1 for the other nodes
    vector<int> head, nextEdge, to, cap, edgeCost;

    vector<int> bfs(const vector<int> &from) const
    {
        vector<int> d(n, INF);
        queue<int> q;
        for (int c : from)
            if (d[c] == INF)
                d[c] = 0, q.push(c);
        while (!q.empty())
        {
            int c = q.front();
            q.pop();
            for (int nb : g.nebors[c])
                if (d[nb] == INF)
                    d[nb] = d[c] + 1, q.push(nb);
        }
        return d;
    }

    int outNode(int t, int cell) const { return outId[(long long)t * n + cell]; }
    int inNode(int t, int cell) const { return t >= 1 ? inId[(long long)t * n + cell] : -1; }
    bool edgeForbidden(int from, int toCell, int t) const { return forbiddenEdge.count(((long long)t * n + from) * n + toCell); }

    int addNode(int cell = -1)
    {
        head.push_back(-1);
        nodeCell.push_back(cell);
        return head.size() - 1;
    }

    void addEdge(int a, int b, int c = 0)
    {
        for (int k = 0; k < 2; ++k)
        {
            to.push_back(k ? a : b);
            cap.push_back(k ? 0 : 1);
            edgeCost.push_back(k ? -c : c);
            nextEdge.push_back(head[k ? b : a]);
            head[k ? b : a] = to.size() - 1;
        }
    }

    void build(int horizon)
    {
        T = horizon;
        head.clear(), nextEdge.clear(), to.clear(), cap.clear(), edgeCost.clear(), nodeCell.clear();
        addNode(), addNode();
        outId.assign((long long)(T + 1) * n, -1);
        inId.assign((long long)(T + 1) * n, -1);
        for (int t = 0; t <= T; ++t)
            for (int v = 0; v < n; ++v)
                if (distStart[v] <= t && distGoal[v] <= T - t)
                {
                    outId[(long long)t * n + v] = addNode(v);
                    if (t >= 1)
                        inId[(long long)t * n + v] = addNode();
                }

        // (a) one unit per other robot in v at t on the turnstile of (v, t); (b) one unit per other robot moving
        // u -> v at t on v_out_t -> w of the gadget {u,v} (the paper writes (v_in_t, w), which is not an edge).
        unordered_map<long long, int> occupied, moved;
        if (weighted)
            for (auto &r : otherRoutes)
                for (int t = 0; t <= T; ++t)
                {
                    int here = r[min<int>(t, r.size() - 1)];
                    if (t >= 1)
                        ++occupied[(long long)t * n + here];
                    int next = r[min<int>(t + 1, r.size() - 1)];
                    if (t < T && next != here)
                        ++moved[((long long)t * n + here) * n + next];
                }
        auto weight = [](const unordered_map<long long, int> &m, long long key) {
            auto it = m.find(key);
            return it == m.end() ? 0 : it->second;
        };

        for (int s : startCells)
            if (outNode(0, s) != -1)
                addEdge(source, outNode(0, s));
        for (int t = 0; t <= T; ++t)
            for (int v = 0; v < n; ++v)
            {
                int out = outNode(t, v);
                if (out == -1)
                    continue;
                if (t >= 1 && !forbiddenVertex.count((long long)t * n + v))
                    addEdge(inNode(t, v), out, weight(occupied, (long long)t * n + v));
                if (t < T && inNode(t + 1, v) != -1)
                    addEdge(out, inNode(t + 1, v));
                if (t == T && isGoalCell[v] && lastForbiddenAt[v] < T)
                    addEdge(out, sink);
            }
        for (int t = 0; t < T; ++t)
            for (int u = 0; u < n; ++u)
                for (int v : g.nebors[u])
                {
                    if (v < u)
                        continue;
                    bool uv = !edgeForbidden(u, v, t), vu = !edgeForbidden(v, u, t);
                    int fromU = uv ? outNode(t, u) : -1, fromV = vu ? outNode(t, v) : -1;
                    int toU = vu ? inNode(t + 1, u) : -1, toV = uv ? inNode(t + 1, v) : -1;
                    if ((fromU == -1 && fromV == -1) || (toU == -1 && toV == -1))
                        continue;
                    int w = addNode(), w2 = addNode();
                    if (fromU != -1)
                        addEdge(fromU, w, weight(moved, ((long long)t * n + v) * n + u));
                    if (fromV != -1)
                        addEdge(fromV, w, weight(moved, ((long long)t * n + u) * n + v));
                    addEdge(w, w2);
                    if (toU != -1)
                        addEdge(w2, toU);
                    if (toV != -1)
                        addEdge(w2, toV);
                }
        netNodes = head.size();
        netEdges = to.size() / 2;
    }

    int maxFlow()
    {
        int flow = 0;
        vector<int> parentEdge(head.size());
        while (flow < (int)startCells.size())
        {
            fill(parentEdge.begin(), parentEdge.end(), -1);
            parentEdge[source] = -2;
            queue<int> q;
            q.push(source);
            while (!q.empty() && parentEdge[sink] == -1)
            {
                int a = q.front();
                q.pop();
                for (int e = head[a]; e != -1; e = nextEdge[e])
                    if (cap[e] > 0 && parentEdge[to[e]] == -1)
                        parentEdge[to[e]] = e, q.push(to[e]);
            }
            if (parentEdge[sink] == -1)
                break;
            augment(parentEdge);
            ++flow;
        }
        return flow;
    }

    void augment(const vector<int> &parentEdge)
    {
        for (int a = sink; a != source; a = to[parentEdge[a] ^ 1])
            --cap[parentEdge[a]], ++cap[parentEdge[a] ^ 1];
    }

    // Successive shortest paths, Dijkstra with potentials (the initial costs are non-negative).
    void minCostFlow()
    {
        int m = head.size();
        vector<long long> potential(m, 0), dist(m);
        vector<int> parentEdge(m);
        for (unsigned int k = 0; k < startCells.size(); ++k)
        {
            fill(dist.begin(), dist.end(), LLONG_MAX);
            fill(parentEdge.begin(), parentEdge.end(), -1);
            dist[source] = 0;
            priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> q;
            q.push({0, source});
            while (!q.empty())
            {
                auto [d, a] = q.top();
                q.pop();
                if (d != dist[a])
                    continue;
                for (int e = head[a]; e != -1; e = nextEdge[e])
                {
                    long long nd = d + edgeCost[e] + potential[a] - potential[to[e]];
                    if (cap[e] > 0 && nd < dist[to[e]])
                        dist[to[e]] = nd, parentEdge[to[e]] = e, q.push({nd, to[e]});
                }
            }
            if (dist[sink] == LLONG_MAX)
                throw logic_error("min-cost flow is smaller than the max flow");
            for (int a = 0; a < m; ++a)
                if (dist[a] != LLONG_MAX)
                    potential[a] += dist[a];
            augment(parentEdge);
        }
    }
};
} // namespace bs
