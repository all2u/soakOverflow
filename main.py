import sys
from collections import deque
from dataclasses import dataclass

def debug(*args):
    print(*args, file=sys.stderr, flush=True)

@dataclass(frozen=True)
class Pos:
    x: int
    y: int

    def dist(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def neighbours(self):
        return (
            Pos(self.x + 1, self.y),
            Pos(self.x - 1, self.y),
            Pos(self.x, self.y + 1),
            Pos(self.x, self.y - 1),
        )

class Agent:
    def __init__(self, agent_id, player, shoot_cd, optimal_range, power, bombs):
        self.id = agent_id
        self.player = player
        self.base_cd = shoot_cd
        self.range = optimal_range
        self.power = power
        self.max_bombs = bombs
        self.pos = Pos(0, 0)
        self.cooldown = 0
        self.bombs = bombs
        self.wetness = 0

    @property
    def alive(self):
        return self.wetness < 100

class Tile:
    EMPTY = 0
    LOW = 1
    HIGH = 2

    def __init__(self, t):
        self.type = t

    @property
    def walkable(self):
        return self.type == Tile.EMPTY

class GameMap:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.grid = [[Tile(Tile.EMPTY) for _ in range(w)] for _ in range(h)]

    def inside(self, p):
        return 0 <= p.x < self.w and 0 <= p.y < self.h

    def walkable(self, p):
        return self.inside(p) and self.grid[p.y][p.x].walkable

class Pathfinder:
    def __init__(self, game_map):
        self.map = game_map

    def next_step(self, start, goal):
        if start == goal:
            return start
        q = deque([start])
        parent = {start: None}
        while q:
            cur = q.popleft()
            if cur == goal:
                break
            for nxt in cur.neighbours():
                if nxt in parent:
                    continue
                if not self.map.walkable(nxt):
                    continue
                parent[nxt] = cur
                q.append(nxt)
        if goal not in parent:
            return start
        cur = goal
        while parent[cur] != start:
            cur = parent[cur]
            if cur is None:
                return start
        return cur

