"""宠物技能与AI系统"""
from dataclasses import dataclass, field

SKILL_COOLDOWN = 5.0
REVIVE_COOLDOWN = 30.0
DEFAULT_MAX_REVIVES = 3
POSITION_HISTORY = 16

W_THREAT = 1.0
W_DISTANCE = 1.0
CASTER_BONUS = 50.0
LOW_HP_FACTOR = 100.0


@dataclass
class Enemy:
    eid: str
    hp: float
    distance: float
    is_casting: bool = False
    threat: float = 0.0


@dataclass
class Pet:
    pid: str
    name: str
    mode: str = "active"  # active/passive/defensive
    target: str = ""
    skill_cd: dict = field(default_factory=dict)
    position: tuple = (0.0, 0.0)
    position_history: list = field(default_factory=list)
    equipment: dict = field(default_factory=dict)
    buffs: list = field(default_factory=list)
    alive: bool = True
    revive_cd: float = 0.0
    revive_count: int = 0
    max_revives: int = DEFAULT_MAX_REVIVES
    attacking: bool = False


class PetAI:
    def __init__(self):
        self.pets: dict[str, Pet] = {}
        self.owner_skill_cd: dict[str, float] = {}
        self.owner_links: dict[str, dict] = {}

    def use_skill(self, pet_id: str, skill: str, current_time: float) -> bool:
        pet = self.pets[pet_id]
        if not pet.alive:
            return False
        if current_time < pet.skill_cd.get(skill, 0.0):
            return False
        pet.skill_cd[skill] = current_time + SKILL_COOLDOWN
        return True

    def _target_score(self, enemy: Enemy) -> float:
        low_hp_score = LOW_HP_FACTOR / (enemy.hp + 1.0)
        score = enemy.threat * W_THREAT + low_hp_score - enemy.distance * W_DISTANCE
        if enemy.is_casting:
            score += CASTER_BONUS
        return score

    def select_target(self, pet_id: str, enemies: list[Enemy]) -> str:
        if not enemies:
            return ""
        return max(enemies, key=self._target_score).eid

    def update_position(self, pet_id: str, new_pos: tuple, current_time: float | None = None):
        pet = self.pets[pet_id]
        pet.position = tuple(new_pos)
        if current_time is not None:
            history = pet.position_history
            history.append((current_time, pet.position))
            if len(history) > POSITION_HISTORY:
                del history[:-POSITION_HISTORY]

    def interpolate_position(self, pet_id: str, at_time: float) -> tuple:
        history = self.pets[pet_id].position_history
        if not history:
            return self.pets[pet_id].position
        if at_time <= history[0][0]:
            return history[0][1]
        if at_time >= history[-1][0]:
            return history[-1][1]
        for (t0, p0), (t1, p1) in zip(history, history[1:]):
            if t0 <= at_time <= t1:
                ratio = (at_time - t0) / (t1 - t0) if t1 > t0 else 0.0
                return (
                    p0[0] + (p1[0] - p0[0]) * ratio,
                    p0[1] + (p1[1] - p0[1]) * ratio,
                )
        return history[-1][1]

    def auto_loot(self, pet_id: str, item: str, backpack_space: int) -> bool:
        pet = self.pets[pet_id]
        if not pet.alive or backpack_space <= 0:
            return False
        return True

    def switch_mode(self, pet_id: str, mode: str):
        if mode not in ("active", "passive", "defensive"):
            raise ValueError(f"unknown pet mode: {mode}")
        pet = self.pets[pet_id]
        pet.mode = mode
        pet.target = ""
        pet.attacking = False

    def set_owner_link(self, pet_id: str, owner_attack: float = 0.0, ratio: float = 0.1):
        self.owner_links[pet_id] = {"attack": owner_attack, "ratio": ratio}

    def calculate_skill_damage(self, pet_id: str, base_damage: float) -> float:
        pet = self.pets[pet_id]
        equipment_bonus = sum(v for v in pet.equipment.values() if isinstance(v, (int, float)))
        buff_flat = 0.0
        buff_pct = 0.0
        for buff in pet.buffs:
            buff_type = buff.get("type", "")
            value = buff.get("value", 0.0)
            if buff_type in ("atk", "attack"):
                buff_flat += value
            elif buff_type in ("dmg_pct", "damage_percent"):
                buff_pct += value
        link = self.owner_links.get(pet_id)
        owner_bonus = link["attack"] * link["ratio"] if link else 0.0
        damage = base_damage + equipment_bonus + buff_flat + owner_bonus
        return damage * (1.0 + buff_pct)

    def die(self, pet_id: str, current_time: float):
        pet = self.pets[pet_id]
        pet.alive = False
        pet.target = ""
        pet.attacking = False
        pet.revive_cd = current_time + REVIVE_COOLDOWN

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
        pet.revive_cd = current_time + REVIVE_COOLDOWN
        pet.target = ""
        pet.attacking = False
        return True
