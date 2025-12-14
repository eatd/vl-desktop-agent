"""Tests for the executor module."""
import unittest
from unittest.mock import patch

from app.executor import execute, scale_coords
from app.models import Action


class TestExecutor(unittest.TestCase):
    """Test suite for executor functions."""

    def test_scale_coords(self):
        """Test coordinate scaling from image to screen."""
        # Center of 1280x720 image → center of 1920x1080 screen
        result = scale_coords((640, 360), (1920, 1080))
        self.assertEqual(result, (960, 540))
        
        # Origin stays at origin
        result = scale_coords((0, 0), (1920, 1080))
        self.assertEqual(result, (0, 0))

    @patch("app.executor.pyautogui")
    def test_click(self, mock_pyautogui):
        """Test click action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        
        action = Action(action="click", coordinate=(640, 360), reason="test")
        desc, coords = execute(action, dry_run=False)
        
        mock_pyautogui.click.assert_called_with(960, 540)
        self.assertEqual(coords, (960, 540))

    @patch("app.executor.pyautogui")
    def test_type(self, mock_pyautogui):
        """Test type action."""
        action = Action(action="type", text="hello", reason="test")
        desc, coords = execute(action, dry_run=False)
        
        mock_pyautogui.write.assert_called_with("hello", interval=0.02)
        self.assertIn("Type", desc)

    @patch("app.executor.pyautogui")
    def test_press(self, mock_pyautogui):
        """Test press action."""
        action = Action(action="press", key="enter", reason="test")
        desc, coords = execute(action, dry_run=False)
        
        mock_pyautogui.press.assert_called_with("enter")

    @patch("app.executor.pyautogui")
    def test_hotkey(self, mock_pyautogui):
        """Test hotkey combination."""
        action = Action(action="press", key="ctrl+c", reason="test")
        desc, coords = execute(action, dry_run=False)
        
        mock_pyautogui.hotkey.assert_called_with("ctrl", "c")

    @patch("app.executor.pyautogui")
    def test_scroll(self, mock_pyautogui):
        """Test scroll action."""
        action = Action(action="scroll", direction="down", reason="test")
        desc, coords = execute(action, dry_run=False)
        
        mock_pyautogui.scroll.assert_called_with(-3)

    @patch("app.executor.pyautogui")
    def test_done(self, mock_pyautogui):
        """Test done action."""
        action = Action(action="done", reason="completed")
        desc, coords = execute(action, dry_run=False)
        
        self.assertIn("Done", desc)

    @patch("app.executor.pyautogui")
    def test_dry_run(self, mock_pyautogui):
        """Test dry run doesn't execute."""
        mock_pyautogui.size.return_value = (1920, 1080)
        
        action = Action(action="click", coordinate=(640, 360), reason="test")
        desc, coords = execute(action, dry_run=True)
        
        mock_pyautogui.click.assert_not_called()

    @patch("app.executor.pyautogui") 
    def test_blocked_hotkey(self, mock_pyautogui):
        """Test dangerous hotkeys are blocked."""
        action = Action(action="press", key="alt+f4", reason="test")
        desc, coords = execute(action, dry_run=False)
        
        self.assertIn("blocked", desc.lower())
        mock_pyautogui.hotkey.assert_not_called()


if __name__ == "__main__":
    unittest.main()
