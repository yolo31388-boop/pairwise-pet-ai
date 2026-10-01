"""宠物AI行为树"""
import heapq
from dataclasses import dataclass, field

FLEE_HP_RATIO = 0.1


@dataclass
class Pet:
    pid: str
    hp: int = 100
    max_hp: int = 100
    position: tuple = (0, 0)
    target: str = None
    behavior: str = "idle"
    skill_cooldown: dict = field(default_factory=dict)


class AISystem:
    def __init__(self):
        self.pets: dict[str, Pet] = {}

    def select_node(self, pet: Pet) -> str:
        # 先检查前置条件：低血量优先逃跑
        if pet.max_hp > 0 and pet.hp / pet.max_hp < FLEE_HP_RATIO:
            return "flee"
        if pet.behavior == "attack" and pet.target is not None:
            return "attack"
        return "follow"

    def calculate_path(self, start: tuple, end: tuple, obstacles: list) -> list:
        # A* 寻路，绕开障碍物；每次调用即重新规划，卡住后重算即可脱困
        blocked = set(obstacles)
        if end in blocked:
            return []

        def neighbors(node):
            x, y = node
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (x + dx, y + dy)
                if nxt not in blocked:
                    yield nxt

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_heap = [(heuristic(start, end), 0, start)]
        came_from = {start: None}
        g_score = {start: 0}

        while open_heap:
            _, g, current = heapq.heappop(open_heap)
            if current == end:
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path[1:]  # 不含起点
            if g > g_score.get(current, float("inf")):
                continue
            for nxt in neighbors(current):
                tentative = g + 1
                if tentative < g_score.get(nxt, float("inf")):
                    g_score[nxt] = tentative
                    came_from[nxt] = current
                    heapq.heappush(open_heap, (tentative + heuristic(nxt, end), tentative, nxt))
        return []  # 无可达路径

    def select_target(self, pet: Pet, enemies: list) -> str:
        # 综合威胁、血量、距离打分：高威胁、残血、近距离优先
        if not enemies:
            return None

        def score(enemy):
            threat = enemy.get("threat", 0)
            hp = enemy.get("hp", 100)
            distance = enemy.get("distance", 0)
            return threat * 2 + (100 - hp) - distance

        return max(enemies, key=score)["id"]

    def decide_skill(self, pet: Pet, skills: list) -> str:
        # 检查冷却和怒气，大招不可用时用普通攻击
        for skill in skills:
            if skill.get("type") != "ultimate":
                continue
            on_cooldown = pet.skill_cooldown.get(skill["id"], 0) > 0
            rage_cost = skill.get("rage_cost", 0)
            enough_rage = getattr(pet, "rage", 100) >= rage_cost
            if not on_cooldown and enough_rage:
                return skill["id"]
        return "normal_attack"

    def transition_behavior(self, pet: Pet, new_behavior: str) -> None:
        # 切换行为时重置上一个行为的状态
        if pet.behavior == "attack":
            pet.target = None
        pet.behavior = new_behavior

    def sync_pet_state(self, pet: Pet) -> dict:
        # 组队同步包含位置和行为状态
        return {
            "position": pet.position,
            "hp": pet.hp,
            "behavior": pet.behavior,
            "target": pet.target,
        }
