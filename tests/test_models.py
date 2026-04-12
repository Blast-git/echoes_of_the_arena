import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_critical_files_exist():
    base = os.path.join(os.path.dirname(__file__), '..')
    files = [
        'src/state_manager.py',
        'src/rl_overseer.py',
        'src/rl_gladiator.py',
        'src/rag_merchant.py',
        'src/cv_combat.py',
    ]
    for f in files:
        assert os.path.exists(os.path.join(base, f)), f"Missing: {f}"


def test_overseer_output():
    from rl_overseer import get_overseer_action_safe
    result = get_overseer_action_safe(50, 50, 0)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert result["action_id"] in [0, 1, 2], f"Unexpected action_id: {result['action_id']}"
    assert isinstance(result["action_name"], str), "action_name should be str"
    assert isinstance(result["hp_delta"], int), "hp_delta should be int"
    assert "description" in result, "Missing key: description"


def test_gladiator_output():
    from rl_gladiator import get_garg_action
    result = get_garg_action(player_hp=80, enemy_hp=50, round_count=1)
    assert "name" in result
    assert "damage" in result