// Independent reference for the minimal makespan of anonymous MAPF: plain max flow (Dinic) on the full
// time-expanded network, rebuilt for every T. No code is shared with flow-bs.cpp / bs_team.hpp.
// Network for horizon T: source -> (start, 0, in); (c, t, in) -> (c, t, out) capacity 1 (one agent per cell);
// (c, t, out) -> (c', t+1, in) for c' = c or a neighbour; (goal, T, out) -> sink. Solvable iff max flow = K.
// Swaps are not forbidden: for anonymous agents a swap can be replaced by two waits, so the minimal T is the same.
// Usage: flow_ref MAP.map FILE.scen K   -> prints "T=<n> ms=<n>" (T=0 if the starts are the goals)
#include <bits/stdc++.h>
using namespace std;

struct Dinic
{
    struct E
    {
        int to, rev, cap;
    };
    vector<vector<E>> g;
    vector<int> level, it;
    Dinic(int n) : g(n), level(n), it(n) {}
    void add(int a, int b)
    {
        g[a].push_back({b, (int)g[b].size(), 1});
        g[b].push_back({a, (int)g[a].size() - 1, 0});
    }
    bool bfs(int s, int t)
    {
        fill(level.begin(), level.end(), -1);
        queue<int> q;
        level[s] = 0;
        q.push(s);
        while (!q.empty())
        {
            int v = q.front();
            q.pop();
            for (auto &e : g[v])
                if (e.cap && level[e.to] < 0)
                    level[e.to] = level[v] + 1, q.push(e.to);
        }
        return level[t] >= 0;
    }
    int dfs(int v, int t)
    {
        if (v == t)
            return 1;
        for (int &i = it[v]; i < (int)g[v].size(); ++i)
        {
            E &e = g[v][i];
            if (e.cap && level[e.to] == level[v] + 1 && dfs(e.to, t))
            {
                e.cap--, g[e.to][e.rev].cap++;
                return 1;
            }
        }
        return 0;
    }
    int maxflow(int s, int t)
    {
        int f = 0;
        while (bfs(s, t))
        {
            fill(it.begin(), it.end(), 0);
            while (dfs(s, t))
                ++f;
        }
        return f;
    }
};

int main(int argc, char *argv[])
{
    if (argc < 4)
    {
        cerr << "usage: " << argv[0] << " MAP.map FILE.scen K" << endl;
        return 1;
    }
    ifstream in(argv[1]);
    string s, row;
    int h, w;
    in >> s >> s >> s >> h >> s >> w >> s;
    vector<int> id(h * w, -1);
    int n = 0;
    for (int y = 0; y < h; ++y)
    {
        in >> row;
        for (int x = 0; x < w; ++x)
            if (row[x] != '@' && row[x] != 'T')
                id[y * w + x] = n++;
    }
    vector<vector<int>> nb(n);
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x)
            if (id[y * w + x] >= 0)
            {
                int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
                for (int d = 0; d < 4; ++d)
                {
                    int xx = x + dx[d], yy = y + dy[d];
                    if (xx >= 0 && yy >= 0 && xx < w && yy < h && id[yy * w + xx] >= 0)
                        nb[id[y * w + x]].push_back(id[yy * w + xx]);
                }
            }
    int k = atoi(argv[3]);
    vector<int> starts, goals;
    ifstream sc(argv[2]);
    sc >> s >> s;
    string bucket, mp;
    int mw, mh, sx, sy, gx, gy;
    double opt;
    while ((int)starts.size() < k && sc >> bucket >> mp >> mw >> mh >> sx >> sy >> gx >> gy >> opt)
        starts.push_back(id[sy * w + sx]), goals.push_back(id[gy * w + gx]);
    if ((int)starts.size() < k)
    {
        cerr << "not enough agents in " << argv[2] << endl;
        return 1;
    }

    auto start = chrono::high_resolution_clock::now();
    // Lower bound: every agent needs a goal and every goal needs an agent.
    auto bfs = [&](const vector<int> &src) {
        vector<int> d(n, INT_MAX);
        queue<int> q;
        for (int c : src)
            d[c] = 0, q.push(c);
        while (!q.empty())
        {
            int c = q.front();
            q.pop();
            for (int c2 : nb[c])
                if (d[c2] == INT_MAX)
                    d[c2] = d[c] + 1, q.push(c2);
        }
        return d;
    };
    vector<int> dGoal = bfs(goals), dStart = bfs(starts);
    int T = 0;
    for (int c : starts)
        T = max(T, dGoal[c]);
    for (int c : goals)
        T = max(T, dStart[c]);
    if (T == INT_MAX)
    {
        cout << "T=-1" << endl;
        return 2;
    }
    for (;; ++T)
    {
        if (T > n + k) // e.g. a component with more agents than goals
        {
            cout << "T=-1" << endl;
            return 2;
        }
        int layer = 2 * n, src = layer * (T + 1), snk = src + 1;
        Dinic d(snk + 1);
        for (int c : starts)
            d.add(src, 2 * c);
        for (int t = 0; t <= T; ++t)
            for (int c = 0; c < n; ++c)
            {
                d.add(t * layer + 2 * c, t * layer + 2 * c + 1);
                if (t < T)
                {
                    d.add(t * layer + 2 * c + 1, (t + 1) * layer + 2 * c);
                    for (int c2 : nb[c])
                        d.add(t * layer + 2 * c + 1, (t + 1) * layer + 2 * c2);
                }
            }
        for (int c : goals)
            d.add(T * layer + 2 * c + 1, snk);
        if (d.maxflow(src, snk) == k)
            break;
    }
    auto stop = chrono::high_resolution_clock::now();
    cout << "T=" << T << " ms=" << chrono::duration_cast<chrono::milliseconds>(stop - start).count() << endl;
    return 0;
}
