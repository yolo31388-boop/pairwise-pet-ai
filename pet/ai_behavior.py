"""宠物AI行为树 - 含6个bug"""
from dataclasses import dataclass, field

@dataclass
class Pet:
    pid: str
    hp: int = 100
    max_hp: int = 100
    position: tuple = (0, 0)
    target: str = None  # bug5: 行为切换不重置
    behavior: str = "idle"
    skill_cooldown: dict = field(default_factory=dict)

class AISystem:
    def __init__(self):
        self.pets: dict[str, Pet] = {}

    def select_node(self, pet: Pet) -> str:
        # bug1: 不检查前置条件，优先级排序
        if pet.behavior == "attack":
            return "attack"
        if pet.hp < 10:
            return "flee"
        return "follow"

    def calculate_path(self, start: tuple, end: tuple, obstacles: list) -> list:
        # bug2: 直线移动，不绕路，无重规划
        return [end]

    def select_target(self, pet: Pet, enemies: list) -> str:
        # bug3: 只选最近的
        if not enemies:
            return None
        return enemies[0]["id"]

    def decide_skill(self, pet: Pet, skills: list) -> str:
        # bug4: 不检查冷却，CD中发呆
        for skill in skills:
            if skill.get("type") == "ultimate":
                return skill["id"]
        return "normal_attack"

    def transition_behavior(self, pet: Pet, new_behavior: str) -> None:
        # bug5: 不重置上一个行为的状态
        pet.behavior = new_behavior

    def sync_pet_state(self, pet: Pet) -> dict:
        # bug6: 不同步行为状态
        return {"position": pet.position, "hp": pet.hp}
