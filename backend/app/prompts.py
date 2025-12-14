"""
Advanced prompts for VLM desktop agent.

Architecture inspired by:
- WorldGUI (action history as memory)
- Anthropic Claude (two-phase observe-then-act)
- OS-Copilot (state-aware planning)
- MobileUse (stuck-behavior prevention)

Key innovations:
1. Two-phase prompting: OBSERVE → ACT
2. Structured action-observation history
3. Goal decomposition hints
4. Explicit state awareness
"""
from __future__ import annotations

from typing import List, Optional
import re

# Qwen VL uses 1000-normalized coordinates
COORD_MAX = 1000


# =============================================================================
# PHASE 1: OBSERVATION PROMPT
# Forces model to describe screen state BEFORE deciding on action
# =============================================================================

OBSERVATION_PROMPT = """Look at this screenshot and describe:

1. VISIBLE WINDOWS: What applications/windows are currently open?
2. FOCUSED ELEMENT: What has keyboard focus (active window, cursor location)?
3. TASKBAR STATE: Which apps are open (highlighted) vs closed in taskbar?
4. RELEVANT UI: For the goal "{goal}", what UI elements do you see?

Be specific and brief. Example:
"Chrome browser is open and focused. Address bar shows 'google.com'. Taskbar shows Chrome highlighted. YouTube is not yet open."
"""


# =============================================================================
# PHASE 2: ACTION PROMPT (main prompt)
# =============================================================================

SYSTEM_PROMPT = """You are a desktop automation agent. You see a screenshot and execute ONE action to progress toward a goal.

OUTPUT FORMAT - respond with ONLY a JSON object:
{"action": "click", "coordinate": [x, y], "reason": "..."}
{"action": "type", "text": "...", "reason": "..."}
{"action": "press", "key": "enter|escape|tab|backspace|ctrl+a|ctrl+c|ctrl+v", "reason": "..."}
{"action": "scroll", "direction": "up|down", "reason": "..."}
{"action": "done", "reason": "..."}

COORDINATES: Normalized [0-1000). Top-left=(0,0), bottom-right=(1000,1000).

═══════════════════════════════════════════════════════════════════════════════
                              CRITICAL THINKING RULES
═══════════════════════════════════════════════════════════════════════════════

BEFORE CLICKING, ASK YOURSELF:
  → Is the target app ALREADY OPEN? If yes, interact with the WINDOW, not the icon!
  → Did I just click this? If yes, DO SOMETHING DIFFERENT!
  → What is the NEXT logical step toward the goal?

TASKBAR BEHAVIOR (Windows):
  → Click icon ONCE = opens/restores app
  → Click icon AGAIN = MINIMIZES app (BAD!)
  → If app window is visible, NEVER click the taskbar icon again

PROGRESS THROUGH STEPS:
  1. Open app (click icon ONCE)
  2. Wait for window to appear
  3. Interact WITH the window (address bar, buttons, fields)
  4. Complete the task
  5. Say "done"

═══════════════════════════════════════════════════════════════════════════════
                                    EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

GOAL: "Open YouTube in Chrome"

Step 1 - Chrome is not open:
  Observation: Desktop visible, Chrome icon in taskbar is not highlighted
  → {"action": "click", "coordinate": [X, 980], "reason": "Opening Chrome browser"}

Step 2 - Chrome window just opened:
  Observation: Chrome browser is now visible with address bar at top
  → {"action": "click", "coordinate": [500, 50], "reason": "Clicking address bar to type URL"}

Step 3 - Address bar is focused:
  Observation: Address bar is highlighted/selected
  → {"action": "type", "text": "youtube.com", "reason": "Typing YouTube URL"}

Step 4 - URL is typed:
  Observation: Address bar shows "youtube.com"
  → {"action": "press", "key": "enter", "reason": "Navigating to YouTube"}

Step 5 - YouTube loaded:
  Observation: YouTube homepage is visible
  → {"action": "done", "reason": "YouTube is now open in Chrome"}

═══════════════════════════════════════════════════════════════════════════════
"""


# =============================================================================
# REFLECTION PROMPT (when stuck)
# =============================================================================

REFLECTION_PROMPT = """The agent is STUCK - the last {n} actions had NO effect on the screen.

GOAL: {goal}

FAILED ACTIONS:
{failed_actions}

CURRENT SCREEN STATE:
{screen_state}

═══════════════════════════════════════════════════════════════════════════════
                               DIAGNOSIS
═══════════════════════════════════════════════════════════════════════════════

Common causes:
1. CLICKING SAME ICON REPEATEDLY → App is already open! Look at the WINDOW instead
2. WRONG COORDINATES → Target is slightly off, adjust position
3. APP NEEDS FOCUS → Click inside the app window first
4. LOADING/LAG → Element not ready yet, try scrolling or waiting

REQUIRED: Suggest ONE action that is DIFFERENT from the failed ones.
Look at the screenshot - what is VISIBLE that can progress the task?

JSON response:"""


# =============================================================================
# GOAL DECOMPOSITION PROMPT
# =============================================================================

DECOMPOSITION_PROMPT = """Break down this goal into specific steps:

GOAL: {goal}

List 3-7 concrete steps. Example:
Goal: "Search for cats on Google"
1. Open Chrome browser
2. Click the address bar
3. Type "google.com"
4. Press Enter
5. Click the search box
6. Type "cats"
7. Press Enter

Your steps:"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_prompt(goal: str, history: List[str], screen_state: Optional[str] = None) -> str:
    """
    Build the full action prompt with rich context.
    
    Args:
        goal: The user's goal
        history: List of previous action descriptions with outcomes
        screen_state: Optional description of current screen (from observation phase)
    """
    prompt = SYSTEM_PROMPT
    
    # Add goal
    prompt += f"\n\nGOAL: {goal}\n"
    
    # Add screen state if provided (from two-phase prompting)
    if screen_state:
        prompt += f"\nCURRENT SCREEN STATE:\n{screen_state}\n"
    
    # Add history with rich context
    if history:
        prompt += "\n" + "─" * 40 + "\n"
        prompt += "ACTION HISTORY (with outcomes):\n"
        
        # Track repeated coordinates for warnings
        coord_counts = {}
        
        for i, action in enumerate(history[-7:], 1):  # Last 7 actions
            # Detect repeated coordinates
            warning = ""
            coord_match = re.search(r'\((\d+),\s*(\d+)\)', action)
            if coord_match:
                coords = (coord_match.group(1), coord_match.group(2))
                coord_counts[coords] = coord_counts.get(coords, 0) + 1
                if coord_counts[coords] > 1:
                    warning = " ⚠️ REPEATED - DO SOMETHING ELSE!"
            
            # Format with outcome indicator
            if "[OK]" in action:
                prompt += f"  ✓ {i}. {action}\n"
            elif "[NO EFFECT]" in action:
                prompt += f"  ✗ {i}. {action}{warning}\n"
            else:
                prompt += f"  • {i}. {action}\n"
        
        prompt += "─" * 40 + "\n"
        
        # Strong warning if stuck
        no_effect_count = sum(1 for a in history[-5:] if "[NO EFFECT]" in a)
        if no_effect_count >= 2:
            prompt += "\n⚠️ WARNING: Recent actions had no effect!\n"
            prompt += "→ The app may already be open - look at the WINDOW\n"
            prompt += "→ Try clicking INSIDE the app, not the taskbar icon\n"
            prompt += "→ Check if you need to type something or press a key\n\n"
    
    prompt += "\nNEXT ACTION (JSON only):"
    return prompt


def build_observation_prompt(goal: str) -> str:
    """Build prompt for Phase 1: Screen observation."""
    return OBSERVATION_PROMPT.format(goal=goal)


def build_reflection_prompt(
    goal: str, 
    failed_actions: List[str], 
    screen_state: str = ""
) -> str:
    """Build prompt for stuck-state reflection."""
    failed_str = "\n".join(f"  {i}. {a}" for i, a in enumerate(failed_actions, 1))
    return REFLECTION_PROMPT.format(
        goal=goal,
        n=len(failed_actions),
        failed_actions=failed_str,
        screen_state=screen_state or "(not available)"
    )


def build_decomposition_prompt(goal: str) -> str:
    """Build prompt for goal decomposition (optional planning phase)."""
    return DECOMPOSITION_PROMPT.format(goal=goal)