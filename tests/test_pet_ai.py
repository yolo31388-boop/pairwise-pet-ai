"""宠物技能与AI系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pet.ai import PetAI, Pet, Enemy

class TestSkillCDIndependent:
    def test_pet_skill_cd_independent_of_owner(self):
        ai = PetAI()
        ai.pets["p1"] = Pet("p1", "pet")
        # 主人技能CD不应影响宠物
        ai.owner_skill_cd["p1"] = 100.0
        assert ai.use_skill("p1", "bite", 50.0) == True  # bug1: 被主人CD挡住

class TestTargetSelection:
    def test_target_prioritizes_low_hp_caster(self):
        ai = PetAI()
        ai.pets["p1"] = Pet("p1", "pet")
        enemies = [
            Enemy("e1", 100, 5, is_casting=False),
            Enemy("e2", 10, 10, is_casting=True),  # 残血施法者应该优先
        ]
        target = ai.select_target("p1", enemies)
        assert target == "e2"  # bug2: 选了e1（距离近）

class TestPositionUpdate:
    def test_position_updates_immediately(self):
        ai = PetAI()
        ai.pets["p1"] = Pet("p1", "pet", position=(0, 0))
        ai.update_position("p1", (10, 10))
        assert ai.pets["p1"].position == (10, 10)  # bug3: 还是(0,0)

class TestAutoLootSpace:
    def test_auto_loot_checks_backpack(self):
        ai = PetAI()
        ai.pets["p1"] = Pet("p1", "pet")
        assert ai.auto_loot("p1", "item", 0) == False  # bug4: 背包满还捡

class TestModeSwitchResetsTarget:
    def test_switch_to_passive_stops_attack(self):
        ai = PetAI()
        ai.pets["p1"] = Pet("p1", "pet", mode="active", target="e1")
        ai.switch_mode("p1", "passive")
        assert ai.pets["p1"].target == ""  # bug5: 还在追e1

class TestSkillDamageIncludesGear:
    def test_damage_includes_equipment_and_buffs(self):
        ai = PetAI()
        pet = Pet("p1", "pet", equipment={"collar": 20}, buffs=[{"type": "atk", "value": 10}])
        ai.pets["p1"] = pet
        dmg = ai.calculate_skill_damage("p1", 100)
        assert dmg > 100  # bug6: 还是100

class TestReviveCooldown:
    def test_revive_has_cooldown(self):
        ai = PetAI()
        pet = Pet("p1", "pet", alive=False, revive_cd=100.0)
        ai.pets["p1"] = pet
        assert ai.revive("p1", 50.0) == False  # bug7: 冷却中还能复活
