from app.prompts import build_system_prompt


def test_build_system_prompt_returns_str_and_includes_goal():
    p = build_system_prompt("Open startmenu", [])
    assert isinstance(p, str)
    assert "GOAL: Open startmenu" in p


def test_build_system_prompt_includes_observation_block_when_provided():
    p = build_system_prompt(
        "Open startmenu", ["click(10,10)"], "last_screen_changed=False"
    )
    assert "OBSERVATION:" in p
    assert "last_screen_changed=False" in p
