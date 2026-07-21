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

class Game:
    def __init__(self):
        self.my_id = int(input())
        # Agents (données fixes)
        self.agent_count = int(input())
        self.agents = {}
        for _ in range(self.agent_count):
            agent_id, player, shoot_cd, optimal_range, power, bombs = map(int, input().split())
            self.agents[agent_id] = Agent(agent_id, player, shoot_cd, optimal_range, power, bombs)
        # Carte
        w, h = map(int, input().split())
        self.map = GameMap(w, h)
        for y in range(h):
            data = list(map(int, input().split()))
            for x in range(w):
                tile = data[3 * x + 2]
                self.map.grid[y][x] = Tile(tile)
        self.pathfinder = Pathfinder(self.map)
        self.my_agents = []
        self.enemy_agents = []

    def read_turn(self):
        alive = int(input())
        self.my_agents.clear()
        self.enemy_agents.clear()
        for _ in range(alive):
            agent_id, x, y, cooldown, bombs, wetness = map(int, input().split())
            a = self.agents[agent_id]
            a.pos = Pos(x, y)
            a.cooldown = cooldown
            a.bombs = bombs
            a.wetness = wetness
        mine = int(input())
        ids = []
        for _ in range(mine):
            ids.append(int(input()))
        for a in self.agents.values():
            if not a.alive:
                continue
            if a.id in ids:
                self.my_agents.append(a)
            else:
                self.enemy_agents.append(a)

    def closest_enemy(self, agent):
        best = None
        best_dist = 10 ** 9
        for e in self.enemy_agents:
            d = agent.pos.dist(e.pos)
            if d < best_dist:
                best_dist = d
                best = e
        return best

    def move_action(self, agent):
        enemy = self.closest_enemy(agent)
        if enemy is None:
            return "HUNKER_DOWN"
        nxt = self.pathfinder.next_step(agent.pos, enemy.pos)
        if nxt == agent.pos:
            return "HUNKER_DOWN"
        return f"MOVE {nxt.x} {nxt.y}"

    def play(self):
        self.read_turn()
        actions = []
        for agent in self.my_agents:
            actions.append(f"{agent.id};{self.move_action(agent)}")
        print("\n".join(actions))

game = Game()

while True:
    game.play()
