from app.parsing import parse_action


def test_parse_action_direct_json():
    action = parse_action('{"action_type":"wait","reasoning":"ok"}')
    assert action.action_type == "wait"
    assert action.reasoning == "ok"


def test_parse_action_embedded_json():
    action = parse_action('some text\n{"action_type":"hotkey","key_combination":"ctrl+l","reasoning":"focus"}\nmore')
    assert action.action_type == "hotkey"
    assert action.key_combination == "ctrl+l"
