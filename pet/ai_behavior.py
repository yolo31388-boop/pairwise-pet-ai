"""宠物AI行为树。

行为节点按优先级依次检查前置条件；寻路使用 A* 并在受阻时重规划；
目标选择综合威胁/血量/距离；技能决策检查冷却与怒气。
"""
from dataclasses import dataclass, field
import heapq

FLEE_HP_RATIO = 0.10
STUCK_LIMIT = 2
PATH_MARGIN = 5


@dataclass
class Pet:
    pid: str
    hp: int = 100
    max_hp: int = 100
    position: tuple = (0, 0)
    target: str = None
    behavior: str = "idle"
    rage: int = 100
    skill_cooldown: dict = field(default_factory=dict)
    path: list = field(default_factory=list)
    stuck_count: int = 0


class AISystem:
    def __init__(self):
        self.pets: dict[str, Pet] = {}

    def select_node(self, pet: Pet) -> str:
        """按优先级选择行为节点，每个节点都必须先通过前置条件。"""
        hp_ratio = pet.hp / pet.max_hp if pet.max_hp > 0 else 0.0
        nodes = [
            ("flee", lambda p: hp_ratio < FLEE_HP_RATIO),
            ("attack", lambda p: p.target is not None and p.hp > 0),
            ("follow", lambda p: True),
        ]
        for node, precondition in nodes:
            if precondition(pet):
                return node
        return "follow"

    def calculate_path(self, start: tuple, end: tuple, obstacles: list) -> list:
        """A* 网格寻路，返回从 start 到 end 且不经过障碍物的路径。"""
        start = tuple(start)
        end = tuple(end)
        blocked = {tuple(o) for o in obstacles}
        if end in blocked or start in blocked:
            return []
        if start == end:
            return [start]

        coords = [start, end, *blocked]
        min_x = min(c[0] for c in coords) - PATH_MARGIN
        max_x = max(c[0] for c in coords) + PATH_MARGIN
        min_y = min(c[1] for c in coords) - PATH_MARGIN
        max_y = max(c[1] for c in coords) + PATH_MARGIN

        def heuristic(pos):
            return abs(pos[0] - end[0]) + abs(pos[1] - end[1])

        open_set = [(heuristic(start), 0, start)]
        best_g = {start: 0}
        came_from = {}
        while open_set:
            _, g, current = heapq.heappop(open_set)
            if g > best_g.get(current, float("inf")):
                continue
            if current == end:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (current[0] + dx, current[1] + dy)
                if nxt in blocked:
                    continue
                if not (min_x <= nxt[0] <= max_x and min_y <= nxt[1] <= max_y):
                    continue
                new_g = g + 1
                if new_g < best_g.get(nxt, float("inf")):
                    best_g[nxt] = new_g
                    came_from[nxt] = current
                    heapq.heappush(open_set, (new_g + heuristic(nxt), new_g, nxt))
        return []

    def update_movement(self, pet: Pet, goal: tuple, obstacles: list) -> tuple:
        """沿路径推进一格；路径失效或下一步被挡住时立即重规划。

        连续多次无法前进也会触发重规划，避免永远卡在障碍物前。
        """
        goal = tuple(goal)
        blocked = {tuple(o) for o in obstacles}
        path = [tuple(p) for p in pet.path]

        if not path or path[-1] != goal:
            path = self.calculate_path(pet.position, goal, obstacles)
            pet.stuck_count = 0

        current = tuple(pet.position)
        while path and path[0] == current:
            path.pop(0)

        if path and path[0] in blocked:
            pet.stuck_count += 1
            path = self.calculate_path(current, goal, obstacles)
            while path and path[0] == current:
                path.pop(0)

        if path:
            pet.position = path.pop(0)
            pet.stuck_count = 0
        else:
            pet.stuck_count += 1
            if pet.stuck_count >= STUCK_LIMIT:
                pet.path = self.calculate_path(pet.position, goal, obstacles)
                pet.stuck_count = 0
                return pet.position

        pet.path = path
        return pet.position

    def select_target(self, pet: Pet, enemies: list) -> str:
        """综合威胁等级、血量（优先残血）和距离打分，选价值最高的目标。"""
        alive = [e for e in enemies if e.get("hp", 0) > 0]
        if not alive:
            return None

        max_threat = max(e.get("threat", 0) for e in alive) or 1
        max_hp = max(e.get("hp", 0) for e in alive) or 1
        max_dist = max(e.get("distance", 0) for e in alive) or 1

        def score(enemy):
            threat = enemy.get("threat", 0) / max_threat
            low_hp = 1.0 - enemy.get("hp", 0) / max_hp
            closeness = 1.0 - enemy.get("distance", 0) / max_dist
            return 0.5 * threat + 0.3 * low_hp + 0.2 * closeness

        return max(alive, key=score)["id"]

    def decide_skill(self, pet: Pet, skills: list) -> str:
        """检查冷却和怒气，优先可用大招，否则用其他可用技能或普通攻击。"""
        usable = []
        for skill in skills:
            sid = skill["id"]
            if pet.skill_cooldown.get(sid, 0) > 0:
                continue
            cost = skill.get("rage", skill.get("cost", 0))
            if cost and pet.rage < cost:
                continue
            usable.append(skill)

        for skill in usable:
            if skill.get("type") == "ultimate":
                return skill["id"]
        if usable:
            return usable[0]["id"]
        return "normal_attack"

    def transition_behavior(self, pet: Pet, new_behavior: str) -> None:
        """切换行为时清空旧行为残留的目标/寻路状态。"""
        if new_behavior == pet.behavior:
            return
        pet.target = None
        pet.path = []
        pet.stuck_count = 0
        pet.behavior = new_behavior

    def sync_pet_state(self, pet: Pet) -> dict:
        """组队同步：位置与行为状态一起下发。"""
        return {
            "pid": pet.pid,
            "position": pet.position,
            "hp": pet.hp,
            "behavior": pet.behavior,
            "target": pet.target,
            "skill_cooldown": dict(pet.skill_cooldown),
        }

    sync_pet_position = sync_pet_state
