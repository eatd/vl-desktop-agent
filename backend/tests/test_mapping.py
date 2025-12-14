from app.executor import validate_action
from app.models import DesktopAction


def test_validate_clamps_coords():
    act = DesktopAction(action_type="click", norm_x=2000, norm_y=-5, reasoning="x")
    act2 = validate_action(act)
    assert act2.norm_x == 1000
    assert act2.norm_y == 0


def test_validate_scroll_no_amount_allowed():
    # scroll_amount is optional; None is OK (defaults to 0 in execution)
    act = DesktopAction(action_type="scroll", reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "scroll"  # scroll is allowed without amount


def test_validate_scroll_clamps_amount():
    # scroll_amount is not clamped by validator (done by executor)
    act = DesktopAction(action_type="scroll", scroll_amount=999999, reasoning="x")
    act2 = validate_action(act)
    assert act2.scroll_amount == 999999  # Not clamped


def test_validate_type_requires_text_and_coords():
    act = DesktopAction(action_type="type", norm_x=100, norm_y=100, reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "wait"  # Missing text_content


def test_validate_type_requires_coords():
    # type allows focused typing without coordinates
    act = DesktopAction(action_type="type", text_content="youtube", reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "type"


def test_validate_type_rejects_partial_coords():
    act = DesktopAction(
        action_type="type", text_content="youtube", norm_x=10, reasoning="x"
    )
    act2 = validate_action(act)
    assert act2.action_type == "wait"


def test_validate_right_click_requires_coords():
    act = DesktopAction(action_type="right_click", reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "wait"


def test_validate_double_click_requires_coords():
    act = DesktopAction(action_type="double_click", reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "wait"


def test_validate_drag_requires_all_coords():
    # drag requires start (norm_x/y) and end (end_norm_x/y)
    act = DesktopAction(action_type="drag", norm_x=10, norm_y=10, reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "wait"  # Missing end coords


def test_validate_valid_type_with_coords():
    act = DesktopAction(
        action_type="type", norm_x=100, norm_y=100, text_content="hello", reasoning="x"
    )
    act2 = validate_action(act)
    assert act2.action_type == "type"  # Valid


def test_validate_valid_drag():
    act = DesktopAction(
        action_type="drag",
        norm_x=100,
        norm_y=100,
        end_norm_x=200,
        end_norm_y=200,
        reasoning="x",
    )
    act2 = validate_action(act)
    assert act2.action_type == "drag"  # Valid


def test_validate_paste_requires_text():
    act = DesktopAction(action_type="paste", norm_x=10, norm_y=10, reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "wait"


def test_validate_paste_allows_missing_coords():
    act = DesktopAction(action_type="paste", text_content="hello", reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "paste"


def test_validate_mouse_down_rejects_partial_coords():
    act = DesktopAction(action_type="mouse_down", norm_x=10, reasoning="x")
    act2 = validate_action(act)
    assert act2.action_type == "wait"
