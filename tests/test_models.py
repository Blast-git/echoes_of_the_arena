import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_rl_overseer_imports():
    from rl_overseer import get_overseer_action_safe
    assert callable(get_overseer_action_safe)

def test_overseer_output_valid():
    from rl_overseer import get_overseer_action_safe
    action, label, delta, narrative = get_overseer_action_safe(50, 50, 0)
    assert action in [0, 1, 2]
    assert isinstance(label, str)
    assert isinstance(delta, int)

def test_rl_gladiator_imports():
    from rl_gladiator import get_garg_action
    assert callable(get_garg_action)

def test_gladiator_output_valid():
    from rl_gladiator import get_garg_action
    result = get_garg_action(player_hp=80, enemy_hp=50, round_count=1)
    assert "name" in result
    assert "damage" in result
    assert 0 <= result["damage"] <= 30

def test_state_manager_keys():
    keys = ["player_hp", "enemy_hp", "honor_score", "game_phase", "potions"]
    import inspect, importlib.util
    spec = importlib.util.spec_from_file_location(
        "state_manager",
        os.path.join(os.path.dirname(__file__), '..', 'src', 'state_manager.py')
    )
    mod = importlib.util.load_from_spec(spec)
    src = inspect.getsource(mod)
    for key in keys:
        assert key in src, f"Missing key in state_manager: {key}"
