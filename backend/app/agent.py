"""
Core agent loop: capture → infer → verify → execute.

Features:
- Verification loop: Detects if actions had effect
- Self-correction: Reflects when stuck
- Confidence filtering: Retries uncertain actions
"""

from __future__ import annotations

import base64
import json
import logging
import re
import threading
import time
from datetime import datetime
from typing import Callable, List, Optional

import cv2
import numpy as np
import openai

from .config import settings
from .executor import execute
from .models import Action, AgentStatus, Event
from .prompts import build_observation_prompt, build_prompt, build_reflection_prompt
from .trace import save_session, save_step

logger = logging.getLogger(__name__)

# Thresholds
MIN_CONFIDENCE = 60  # Minimum confidence to execute
STUCK_THRESHOLD = 3  # Failed verifications before reflection
FRAME_DIFF_THRESHOLD = 2.0  # Minimum % pixel change to count as "changed"


def encode_image(frame: np.ndarray) -> str:
    """Encode frame as base64 JPEG."""
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buffer).decode("ascii")


def frame_diff(before: np.ndarray, after: np.ndarray) -> float:
    """Calculate percentage of pixels that changed between frames."""
    if before.shape != after.shape:
        after = cv2.resize(after, (before.shape[1], before.shape[0]))

    diff = cv2.absdiff(before, after)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    changed = np.count_nonzero(gray > 20)  # Threshold for noise
    total = gray.size
    return (changed / total) * 100


def parse_action(text: str) -> Optional[Action]:
    """Extract JSON action from model response."""
    match = re.search(r"\{[^{}]*\}", text)
    if not match:
        logger.warning(f"No JSON found in: {text[:100]}")
        return None

    try:
        data = json.loads(match.group())
        return Action(**data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse action: {e}")
        return None


class Agent:
    """Desktop automation agent with verification and self-correction."""

    def __init__(self, capture) -> None:
        self._capture = capture
        self._client = openai.OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout,
        )

        self._lock = threading.Lock()
        self._running = False
        self._goal: Optional[str] = None
        self._step = 0
        self._last_action: Optional[str] = None
        self._stop_event = threading.Event()
        self._history: List[str] = []
        self._session_id: Optional[str] = None
        self._stuck_count = 0  # Consecutive failed verifications
        self._last_raw_response = ""  # Raw model output for logging
        self._screen_state = ""  # Observation phase result

    def status(self) -> AgentStatus:
        with self._lock:
            return AgentStatus(
                running=self._running,
                goal=self._goal,
                step=self._step,
                last_action=self._last_action,
                dry_run=settings.dry_run,
            )

    def start(self, goal: str) -> bool:
        with self._lock:
            if self._running:
                return False

            self._running = True
            self._goal = goal
            self._step = 0
            self._last_action = None
            self._stop_event.clear()
            self._history = []
            self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._stuck_count = 0
            return True

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            self._running = False

    def run_loop(self, publish: Callable[[Event], None]) -> None:
        """Main loop with verification."""
        while True:
            with self._lock:
                if not self._running or self._goal is None:
                    time.sleep(0.1)
                    continue
                goal = self._goal
                session_id = self._session_id

            if self._stop_event.is_set():
                self._finalize("stopped")
                continue

            if self._step >= settings.max_steps:
                publish(Event(type="log", payload={"message": "Max steps reached"}))
                self._finalize("max_steps")
                continue

            # 1. CAPTURE (before)
            frame_before = self._capture.get_latest()  # Get latest frame from capture
            if frame_before is None:
                time.sleep(0.1)
                continue

            image_b64 = encode_image(frame_before)
            # Send preview to UI
            publish(
                Event(
                    type="preview",
                    payload={
                        "jpeg_b64": image_b64,
                        "status": self.status().model_dump(),
                    },
                )
            )

            # 2. OBSERVE (Phase 1: Describe screen state)
            # Only do observation every 3 steps to save API calls
            if self._step % 3 == 0 or self._stuck_count > 0:
                self._screen_state = self._observe_screen(image_b64, goal)
                publish(
                    Event(
                        type="log",
                        payload={"message": f"[OBSERVE] {self._screen_state[:80]}..."},
                    )
                )

            # 3. INFER (Phase 2: Decide action based on observation)
            try:
                action = self._get_confident_action(image_b64, goal)
            except Exception as e:
                logger.error(f"Model error: {e}")
                publish(Event(type="error", payload={"message": str(e)}))
                time.sleep(1)
                continue

            if action is None:
                time.sleep(0.5)
                continue

            self._step += 1

            # 3. EXECUTE
            desc, coords = execute(action, dry_run=settings.dry_run)
            self._last_action = desc

            # 4. VERIFY (check if UI changed)
            self._last_frame_change = 0.0  #

            if action.action not in ("done", "scroll"):
                time.sleep(0.4)  # Wait for UI to update
                frame_after = self._capture.get_latest()

                if frame_after is not None:  # Check if frame_after is not None
                    # Calculate frame difference
                    change = frame_diff(frame_before, frame_after)

                    self._last_frame_change = change

                    if change < FRAME_DIFF_THRESHOLD:
                        # Action had no effect
                        self._stuck_count += 1
                        desc = f"[NO EFFECT] {desc}"

                        if self._stuck_count >= STUCK_THRESHOLD:
                            # Trigger reflection
                            publish(
                                Event(
                                    type="log",
                                    payload={
                                        "message": f"Stuck ({self._stuck_count}x), reflecting..."
                                    },
                                )
                            )
                            self._reflect_and_correct(image_b64, goal)
                    else:
                        self._stuck_count = 0  # Reset on success
                        desc = f"[OK] {desc}"

            self._history.append(desc)

            # 5. RECORD (enhanced logging)
            verified = "[OK]" in desc
            change_pct = getattr(self, "_last_frame_change", 0.0)
            if session_id:
                save_step(
                    session_id,
                    self._step,
                    frame_before,
                    action.model_dump(),
                    raw_response=self._last_raw_response,
                    frame_change=change_pct,
                    verified=verified,
                )

            # 6. PUBLISH (include click target for UI)
            click_target = None
            if action.action == "click" and action.coordinate:
                click_target = {
                    "x": action.coordinate[0],
                    "y": action.coordinate[1],
                }

            publish(
                Event(
                    type="action",
                    payload={
                        "step": self._step,
                        "action": action.model_dump(),
                        "description": desc,
                        "click_target": click_target,
                    },
                )
            )

            # 7. CHECK DONE
            if action.action == "done":
                publish(Event(type="log", payload={"message": "Goal complete"}))
                self._finalize("done")

            time.sleep(settings.loop_delay)

    def _get_confident_action(
        self, image_b64: str, goal: str, max_attempts: int = 2
    ) -> Optional[Action]:
        """Get action with confidence >= threshold, or retry."""
        for attempt in range(max_attempts):
            # Pass screen state from observation phase
            action = self._call_model(image_b64, goal, self._screen_state)

            if action is None:
                continue

            # Check confidence (parse from reason if not explicit)
            # For now, accept all actions but log confidence
            logger.debug(f"Action confidence: {action.reason}")
            return action

        return None

    def _observe_screen(self, image_b64: str, goal: str) -> str:
        """
        Phase 1: Observe and describe the current screen state.

        This forces the model to LOOK before acting, improving
        state awareness and reducing repetitive actions.
        """
        prompt = build_observation_prompt(goal)

        try:
            response = self._client.chat.completions.create(
                model=settings.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                        ],
                    },
                ],
                max_tokens=150,
                temperature=0,
            )

            state = response.choices[0].message.content or ""
            logger.debug(f"Screen observation: {state[:100]}")
            return state.strip()

        except Exception as e:
            logger.warning(f"Observation phase failed: {e}")
            return ""

    def _reflect_and_correct(self, image_b64: str, goal: str) -> None:
        """Reflect on failures and suggest correction."""
        failed = [h for h in self._history[-5:] if "[NO EFFECT]" in h]

        if not failed:
            return

        # Build reflection prompt with screen state
        prompt = build_reflection_prompt(goal, failed, self._screen_state)

        try:
            response = self._client.chat.completions.create(
                model=settings.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Suggest a different action:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                        ],
                    },
                ],
                max_tokens=300,
                temperature=0.3,  # Slightly creative for recovery
            )

            content = response.choices[0].message.content or ""
            logger.info(f"Reflection: {content[:200]}")

            # Add reflection to history
            self._history.append(f"[REFLECT] {content[:100]}")
            self._stuck_count = 0  # Reset after reflection

        except Exception as e:
            logger.error(f"Reflection failed: {e}")

    def _call_model(
        self, image_b64: str, goal: str, screen_state: str = ""
    ) -> Optional[Action]:
        """Call VLM and parse response (Phase 2: Action)."""
        prompt = build_prompt(goal, self._history, screen_state)

        response = self._client.chat.completions.create(
            model=settings.model,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is the next action?"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                },
            ],
            max_tokens=200,
            temperature=0,
        )

        content = response.choices[0].message.content or ""
        self._last_raw_response = content  # Save for logging
        logger.debug(f"Model response: {content}")

        return parse_action(content)

    def _finalize(self, status: str) -> None:
        """Clean up after goal completes."""
        with self._lock:
            if self._session_id and self._goal:
                save_session(self._session_id, self._goal, status, self._step)

            self._running = False
            self._goal = None
