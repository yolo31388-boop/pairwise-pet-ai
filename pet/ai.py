"""宠物技能与AI系统"""
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
    revive_count: int = 0
    max_revives: int = 3
    attack_order: str = ""

class PetAI:
    REVIVE_COOLDOWN = 30.0

    def __init__(self):
        self.pets: dict[str, Pet] = {}
        self.owner_skill_cd: dict[str, float] = {}

    def use_skill(self, pet_id: str, skill: str, current_time: float) -> bool:
        pet = self.pets[pet_id]
        if skill in pet.skill_cd and current_time < pet.skill_cd[skill]:
            return False
        pet.skill_cd[skill] = current_time + 5.0
        return True

    def select_target(self, pet_id: str, enemies: list[Enemy]) -> str:
        if not enemies:
            return ""

        def score(e: Enemy) -> float:
            threat = 50.0 if e.is_casting else 0.0
            hp_weight = max(0.0, 100.0 - e.hp)
            distance_penalty = e.distance * 2.0
            return threat + hp_weight - distance_penalty

        return max(enemies, key=score).eid

    def update_position(self, pet_id: str, new_pos: tuple):
        pet = self.pets[pet_id]
        pet.position = new_pos

    def auto_loot(self, pet_id: str, item: str, backpack_space: int) -> bool:
        if backpack_space <= 0:
            return False
        return True

    def switch_mode(self, pet_id: str, mode: str):
        pet = self.pets[pet_id]
        pet.mode = mode
        pet.target = ""
        pet.attack_order = ""

    def calculate_skill_damage(self, pet_id: str, base_damage: float) -> float:
        pet = self.pets[pet_id]
        equipment_bonus = sum(pet.equipment.values())
        buff_bonus = sum(b.get("value", 0) for b in pet.buffs if b.get("type") == "atk")
        owner_synergy = 1.1
        return (base_damage + equipment_bonus + buff_bonus) * owner_synergy

    def revive(self, pet_id: str, current_time: float) -> bool:
        pet = self.pets[pet_id]
        if pet.alive:
            return False
        if current_time < pet.revive_cd:
            return False
        if pet.revive_count >= pet.max_revives:
            return False
        pet.alive = True
        pet.revive_count += 1
        pet.revive_cd = current_time + self.REVIVE_COOLDOWN
        return True
