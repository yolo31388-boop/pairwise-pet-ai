"""宠物AI行为树测试。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pet.ai_behavior import AISystem, Pet


class TestBehaviorPrecondition:
    def test_low_hp_pet_flees_not_attacks(self):
        ai = AISystem()
        pet = Pet("p1", hp=5, behavior="attack", target="e1")
        assert ai.select_node(pet) == "flee"

    def test_low_hp_uses_ratio_of_max_hp(self):
        ai = AISystem()
        pet = Pet("p1", hp=9, max_hp=100, target="e1")
        assert ai.select_node(pet) == "flee"
        pet.hp = 10
        assert ai.select_node(pet) == "attack"

    def test_attack_requires_target_precondition(self):
        ai = AISystem()
        pet = Pet("p1", hp=80, behavior="attack", target=None)
        assert ai.select_node(pet) == "follow"

    def test_healthy_pet_with_target_attacks(self):
        ai = AISystem()
        pet = Pet("p1", hp=80, target="e1")
        assert ai.select_node(pet) == "attack"


class TestPathfinding:
    def test_path_avoids_obstacles(self):
        ai = AISystem()
        path = ai.calculate_path((0, 0), (10, 0), [(5, 0)])
        assert (5, 0) not in path
        assert path[0] == (0, 0)
        assert path[-1] == (10, 0)

    def test_path_routes_around_wall(self):
        ai = AISystem()
        wall = [(5, y) for y in range(-5, 6)]
        path = ai.calculate_path((0, 0), (10, 0), wall)
        assert path and path[-1] == (10, 0)
        assert set(path).isdisjoint(set(wall))

    def test_no_path_returns_empty(self):
        ai = AISystem()
        assert ai.calculate_path((0, 0), (1, 0), [(1, 0)]) == []

    def test_movement_replans_when_path_blocked(self):
        ai = AISystem()
        pet = Pet("p1", position=(0, 0))
        pet.path = [(1, 0), (2, 0)]
        obstacles = [(1, 0), (1, 1), (1, -1), (1, -2)]
        pos = ai.update_movement(pet, (2, 0), obstacles)
        assert pos != (1, 0)
        assert pet.position not in obstacles
        for _ in range(40):
            ai.update_movement(pet, (2, 0), obstacles)
        assert pet.position == (2, 0)


class TestTargetSelection:
    def test_target_considers_threat_not_just_distance(self):
        ai = AISystem()
        pet = Pet("p1")
        enemies = [
            {"id": "e1", "distance": 1, "hp": 100, "threat": 10},
            {"id": "e2", "distance": 2, "hp": 1, "threat": 100},
        ]
        assert ai.select_target(pet, enemies) == "e2"

    def test_target_prefers_low_hp_equal_threat(self):
        ai = AISystem()
        pet = Pet("p1")
        enemies = [
            {"id": "full", "distance": 1, "hp": 100, "threat": 50},
            {"id": "low", "distance": 3, "hp": 1, "threat": 50},
        ]
        assert ai.select_target(pet, enemies) == "low"

    def test_dead_enemies_ignored(self):
        ai = AISystem()
        pet = Pet("p1")
        enemies = [
            {"id": "dead", "distance": 1, "hp": 0, "threat": 100},
            {"id": "alive", "distance": 5, "hp": 50, "threat": 10},
        ]
        assert ai.select_target(pet, enemies) == "alive"

    def test_empty_enemies_returns_none(self):
        assert AISystem().select_target(Pet("p1"), []) is None


class TestSkillCooldown:
    def test_uses_normal_attack_when_ultimate_on_cd(self):
        ai = AISystem()
        pet = Pet("p1")
        pet.skill_cooldown["ult"] = 10
        skills = [{"id": "ult", "type": "ultimate"}]
        assert ai.decide_skill(pet, skills) == "normal_attack"

    def test_uses_ultimate_when_ready(self):
        ai = AISystem()
        pet = Pet("p1", rage=100)
        skills = [{"id": "ult", "type": "ultimate", "rage": 50}]
        assert ai.decide_skill(pet, skills) == "ult"

    def test_insufficient_rage_falls_back_to_normal_attack(self):
        ai = AISystem()
        pet = Pet("p1", rage=0)
        skills = [{"id": "ult", "type": "ultimate", "rage": 50}]
        assert ai.decide_skill(pet, skills) == "normal_attack"

    def test_other_ready_skill_used_when_ultimate_on_cd(self):
        ai = AISystem()
        pet = Pet("p1", rage=100)
        pet.skill_cooldown["ult"] = 5
        skills = [
            {"id": "ult", "type": "ultimate", "rage": 50},
            {"id": "slash", "type": "active", "rage": 0},
        ]
        assert ai.decide_skill(pet, skills) == "slash"


class TestBehaviorTransitionReset:
    def test_transition_resets_old_behavior_state(self):
        ai = AISystem()
        pet = Pet("p1", target="enemy1", behavior="attack")
        ai.transition_behavior(pet, "follow")
        assert pet.target is None
        assert pet.behavior == "follow"

    def test_transition_clears_path(self):
        ai = AISystem()
        pet = Pet("p1", target="enemy1", behavior="attack")
        pet.path = [(1, 0), (2, 0)]
        ai.transition_behavior(pet, "flee")
        assert pet.path == []
        assert pet.stuck_count == 0


class TestStateSync:
    def test_sync_includes_behavior_state(self):
        ai = AISystem()
        pet = Pet("p1", behavior="attack", target="e1")
        state = ai.sync_pet_state(pet)
        assert "behavior" in state
        assert state["behavior"] == "attack"
        assert state["target"] == "e1"
        assert state["position"] == pet.position

    def test_sync_alias_includes_position_and_behavior(self):
        ai = AISystem()
        pet = Pet("p1", position=(3, 4), behavior="flee")
        state = ai.sync_pet_position(pet)
        assert state["position"] == (3, 4)
        assert state["behavior"] == "flee"
