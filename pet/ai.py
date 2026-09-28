"""宠物技能与AI系统 - 含7个bug"""
import time
from dataclasses import dataclass, field

@dataclass
class Enemy:
    eid: str
    hp: float
    distance: float
    is_casting: bool = False

@dataclass
class Pet:
    pid: str
    name: str
    mode: str = "active"  # active/passive/defensive
    target: str = ""
    skill_cd: dict = field(default_factory=dict)
    position: tuple = (0, 0)
    equipment: dict = field(default_factory=dict)
    buffs: list = field(default_factory=list)
    alive: bool = True
    revive_cd: float = 0

class PetAI:
    def __init__(self):
        self.pets: dict[str, Pet] = {}
        self.owner_skill_cd: dict[str, float] = {}  # bug1: 共用

    def use_skill(self, pet_id: str, skill: str, current_time: float) -> bool:
        # bug1: 和主人技能CD共用
        if pet_id in self.owner_skill_cd:
            if current_time < self.owner_skill_cd[pet_id]:
                return False
        pet = self.pets[pet_id]
        if skill in pet.skill_cd and current_time < pet.skill_cd[skill]:
            return False
        pet.skill_cd[skill] = current_time + 5.0
        return True

    def select_target(self, pet_id: str, enemies: list[Enemy]) -> str:
        # bug2: 只看距离
        if not enemies:
            return ""
        return min(enemies, key=lambda e: e.distance).eid

    def update_position(self, pet_id: str, new_pos: tuple):
        # bug3: 位置更新延迟
        pet = self.pets[pet_id]
        # 应该立即更新
        pass

    def auto_loot(self, pet_id: str, item: str, backpack_space: int) -> bool:
        # bug4: 不检查背包空间
        return True

    def switch_mode(self, pet_id: str, mode: str):
        # bug5: 切换模式不重置目标
        pet = self.pets[pet_id]
        pet.mode = mode

    def calculate_skill_damage(self, pet_id: str, base_damage: float) -> float:
        # bug6: 不算装备和buff
        return base_damage

    def revive(self, pet_id: str, current_time: float) -> bool:
        # bug7: 无复活冷却
        pet = self.pets[pet_id]
        pet.alive = True
        return True
