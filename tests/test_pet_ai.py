"""宠物AI行为树 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pet.ai_behavior import AISystem, Pet

class TestBehaviorPrecondition:
    def test_low_hp_pet_flees_not_attacks(self):
        ai = AISystem()
        pet = Pet("p1", hp=5, behavior="attack")
        node = ai.select_node(pet)
        assert node == "flee"

class TestPathfinding:
    def test_path_avoids_obstacles(self):
        ai = AISystem()
        path = ai.calculate_path((0, 0), (10, 0), [(5, 0)])
        # 路径不应该经过障碍物
        assert (5, 0) not in path

class TestTargetSelection:
    def test_target_considers_threat_not_just_distance(self):
        ai = AISystem()
        pet = Pet("p1")
        enemies = [
            {"id": "e1", "distance": 1, "hp": 100, "threat": 10},
            {"id": "e2", "distance": 2, "hp": 1, "threat": 100}
        ]
        target = ai.select_target(pet, enemies)
        # 应该选威胁高的或残血的
        assert target == "e2"

class TestSkillCooldown:
    def test_uses_normal_attack_when_ultimate_on_cd(self):
        ai = AISystem()
        pet = Pet("p1")
        pet.skill_cooldown["ult"] = 10
        skills = [{"id": "ult", "type": "ultimate"}]
        skill = ai.decide_skill(pet, skills)
        assert skill == "normal_attack"

class TestBehaviorTransitionReset:
    def test_transition_resets_old_behavior_state(self):
        ai = AISystem()
        pet = Pet("p1", target="enemy1", behavior="attack")
        ai.transition_behavior(pet, "follow")
        assert pet.target is None

class TestStateSync:
    def test_sync_includes_behavior_state(self):
        ai = AISystem()
        pet = Pet("p1", behavior="attack")
        state = ai.sync_pet_state(pet)
        assert "behavior" in state
