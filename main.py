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

class Action:
    def __init__(self, command, score=0):
        self.command = command
        self.score = score

    def __lt__(self, other):
        return self.score < other.score

class Explosion:
    def __init__(self):
        self.hit_enemies = 0
        self.hit_allies = 0
        self.enemy_damage = 0
        self.ally_damage = 0
        self.score = 0

class Simulator:
    def __init__(self, game):
        self.game = game

    def splash_cells(self, center):
        cells = []
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                p = Pos(center.x+dx, center.y+dy)
                if self.game.map.inside(p):
                    cells.append(p)
        return cells

    def simulate_throw(self, agent, target):
        result = Explosion()
        cells = self.splash_cells(target)
        # ennemis
        for enemy in self.game.enemy_agents:
            if enemy.pos in cells:
                result.hit_enemies += 1
                result.enemy_damage += agent.power
        # alliés
        for ally in self.game.my_agents:
            if ally.id == agent.id:
                continue
            if ally.pos in cells:
                result.hit_allies += 1
                result.ally_damage += agent.power
        return result

    def evaluate_throw(self, explosion):
        score = 0
        score += explosion.enemy_damage*20
        score += explosion.hit_enemies*100
        score -= explosion.ally_damage*200
        score -= explosion.hit_allies*500
        return score

class ActionGenerator:
    def __init__(self, game):
        self.game = game

    def generate(self, agent):
        actions = []
        # Hunker
        actions.append(Action("HUNKER_DOWN", 0))
        # Déplacements
        for p in agent.pos.neighbours():
            if self.game.map.walkable(p):
                actions.append(
                    Action(f"MOVE {p.x} {p.y}", self.score_move(agent, p)))
        # Tir
        if agent.cooldown == 0:
            for enemy in self.game.enemy_agents:
                d = agent.pos.dist(enemy.pos)
                if d <= agent.range:
                    actions.append(Action(f"SHOOT {enemy.id}", self.score_shoot(agent, enemy)))
        # Bombes
        if agent.bombs > 0:
            actions.extend(self.generate_bombs(agent))
        actions.sort(reverse=True)
        return actions

    def score_move(self, agent, pos):
        score = 0
        enemy = self.game.closest_enemy(agent)
        if enemy:
            score -= pos.dist(enemy.pos)
        return score

    def score_shoot(self, agent, enemy):
        d = agent.pos.dist(enemy.pos)
        score = 200
        score -= abs(d - agent.range)
        score += enemy.wetness
        return score

    def generate_bombs(self, agent):
        actions = []
        sim = self.game.simulator
        for enemy in self.game.enemy_agents:
            if agent.pos.dist(enemy.pos)>4:
                continue
            explosion = sim.simulate_throw(agent, enemy.pos)
            score = sim.evaluate_throw(explosion)
            if score<=0:
                continue
            actions.append(Action(f"THROW {enemy.pos.x} {enemy.pos.y}", score))
        return actions

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
        self.generator = ActionGenerator(self)
        self.simulator = Simulator(self)

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

    def best_action(self, agent):
        actions = self.generator.generate(agent)
        return actions[0].command
    
    def play(self):
        self.read_turn()
        actions = []
        for agent in self.my_agents:
            actions.append(f"{agent.id};{self.best_action(agent)}")
        print("\n".join(actions))

game = Game()

while True:
    game.play()
