# Architecture Deep Dive

This document provides a detailed technical overview of the Vision-Language Desktop Agent architecture, suitable for technical interviews and deeper understanding.

---

## System Overview

The agent operates as a continuous loop:

```
┌──────────────────────────────────────────────────────────────────┐
│                        AGENT LOOP                                │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐          │
│  │ CAPTURE │ → │  INFER  │ → │VALIDATE │ → │ EXECUTE │          │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘          │
│       │             │             │             │                │
│       ▼             ▼             ▼             ▼                │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐          │
│  │ vision  │   │ OpenAI  │   │ safety  │   │executor │          │
│  │  .py    │   │  API    │   │  .py    │   │  .py    │          │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘          │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐          │
│  │              OBSERVABILITY LAYER                   │          │
│  │   trace.py  │  evaluation.py  │  exceptions.py     │          │
│  └────────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   main.py   │  │   cli.py    │  │  React UI   │               │
│  │  (FastAPI)  │  │   (Rich)    │  │ (WebSocket) │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

### `agent.py` - Core Agent Loop

The heart of the system. Runs in a dedicated thread and orchestrates:

1. **State Management**: Tracks running state, step count, history
2. **Prompt Construction**: Builds context-aware prompts with observation hints
3. **Model Invocation**: Calls VLM with retries and timeout handling
4. **Stuck Detection**: Tracks consecutive no-change frames
5. **Auto-Recovery**: Injects recovery actions when stuck

Key design decisions:
- Thread-based (not async) for simplicity with blocking CV2/DXCam operations
- Rolling history window (10 steps) to prevent context overflow
- Visual history: Previous frame included in prompt for comparison

### `vision.py` - Screen Capture

Provides continuous, thread-safe screenshot capture.

**DXCam Backend** (Windows):
- Uses DirectX for GPU-accelerated capture
- ~60 FPS possible, we limit to 5 FPS for efficiency
- Lower latency than MSS

**MSS Backend** (Cross-platform):
- Uses Windows GDI/macOS CGWindow/X11
- Reliable fallback, slightly higher latency

Design pattern: Singleton capture thread with lock-protected frame buffer.

### `models.py` - Action Schema

Pydantic models for all supported actions:

```python
DesktopAction = Union[
    ClickAction,      # x, y coordinates
    DoubleClickAction,
    RightClickAction,
    TypeAction,       # text_content, optional x/y
    PasteAction,      # clipboard-based typing
    DragAction,       # start/end coordinates
    ScrollAction,     # scroll_amount
    HotkeyAction,     # key_combination
    WaitAction,       # duration_ms
    DoneAction,       # signal completion
    MouseDownAction,
    MouseUpAction,
]
```

All actions include `reasoning` and `confidence_score` for explainability.

### `executor.py` - Action Execution

Translates model coordinates to screen coordinates and executes via PyAutoGUI.

**Coordinate Mapping**:
```python
# Model outputs: 1288×728 image space
# Screen: actual resolution (e.g., 1920×1080)
scale_x = screen_w / 1288
scale_y = screen_h / 728
screen_x = int(model_x * scale_x)
screen_y = int(model_y * scale_y)
```

**Safety Features**:
- Coordinate clamping to valid ranges
- Dry-run mode for testing
- PyAutoGUI failsafe enabled

### `safety.py` - Guardrails

Validates actions before execution:

**Blocked Hotkeys**:
- `alt+f4` (close application)
- `ctrl+alt+delete` (system interrupt)
- `win+l` (lock screen)
- `win+r` (run dialog - potential command execution)

**Text Pattern Detection**:
- `rm -rf` commands
- `format` commands
- PowerShell encoded commands

**Coordinate Bounds**:
- Validates coordinates are within screen bounds
- Warns on edge clicks (may indicate model confusion)

### `trace.py` - Session Recording

Records complete execution traces for debugging and analysis:

```
traces/
└── 20241213_143022/
    ├── trace.json      # Full session data
    ├── step_001.jpg    # Screenshot at step 1
    ├── step_002.jpg
    └── ...
```

**Trace JSON Structure**:
```json
{
  "session_id": "20241213_143022",
  "goal": "Open Notepad",
  "steps": [
    {
      "step_number": 1,
      "action_type": "click",
      "action_data": {"x": 644, "y": 720},
      "model_response_raw": "...",
      "frame_change_score": 15.3
    }
  ],
  "completed": true,
  "total_steps": 5
}
```

### `evaluation.py` - Metrics Collection

Collects aggregate performance metrics:

- **Task Completion Rate**: Percentage of goals marked "done"
- **Average Steps**: Steps required per successful task
- **Model Latency**: Inference time tracking
- **Confidence Distribution**: Model's self-reported confidence
- **Failure Patterns**: Common final actions before failure

### `exceptions.py` - Error Taxonomy

Structured error hierarchy with recovery hints:

```python
class AgentError(Exception):
    severity: ErrorSeverity  # LOW, MEDIUM, HIGH, CRITICAL
    category: ErrorCategory  # MODEL, PARSING, EXECUTION, SAFETY
    recovery_hint: str       # Human-readable recovery suggestion
    retryable: bool          # Whether retry might succeed
```

Enables:
- Automatic retry decisions
- User-friendly error messages
- Failure pattern analysis

---

## Data Flow Example

**Goal**: "Click the Start menu"

1. **Capture** (vision.py):
   - Get latest frame from DXCam
   - Shape: (1080, 1920, 3) BGR

2. **Prepare** (agent.py):
   - Resize to 1288×728 (model's expected size)
   - Apply grid overlay if enabled
   - Encode as JPEG base64

3. **Prompt** (prompts.py):
   ```
   You are a Windows desktop automation agent.
   Goal: Click the Start menu
   Previous actions: [empty]
   Observation: steady
   
   Return a single JSON action...
   ```

4. **Infer** (agent.py → OpenAI API):
   - Send image + prompt to VLM
   - Receive tool call: `click(x=20, y=710)`

5. **Parse** (parsing.py):
   - Extract function name and arguments
   - Repair malformed JSON if needed
   - Create `ClickAction(x=20, y=710)`

6. **Validate** (safety.py):
   - Check coordinates in bounds ✓
   - Not a dangerous action ✓

7. **Execute** (executor.py):
   - Map 20,710 → 30,1053 (screen coords)
   - Call `pyautogui.click(30, 1053)`

8. **Observe** (agent.py):
   - Wait for UI settle (0.3s)
   - Capture new frame
   - Compare: change_score = 45.2 (high, success!)

9. **Record** (trace.py + evaluation.py):
   - Save screenshot and action data
   - Update metrics

---

## Thread Model

```
Main Thread (FastAPI/Uvicorn)
├── Handles HTTP requests
├── Manages WebSocket connections
└── Event broadcasting via asyncio

Agent Thread (DesktopAgent.run_loop)
├── Blocking capture + inference loop
├── Publishes events via callback
└── Lock-protected state access

Capture Thread (ContinuousCapture._run)
├── DXCam or MSS capture loop
├── Lock-protected frame buffer
└── Runs at target FPS
```

Communication:
- Agent → FastAPI: Callback function (thread-safe queue)
- FastAPI → WebSocket: asyncio broadcast
- Capture → Agent: Lock-protected frame buffer

---

## Configuration Architecture

Settings are defined as dataclass fields with environment variable defaults:

```python
@dataclass
class Settings:
    model: str = os.getenv("AGENT_MODEL", "qwen/qwen3-vl-4b")
    max_steps: int = _env_int("AGENT_MAX_STEPS", 80)
    trace_enabled: bool = _env_bool("AGENT_TRACE_ENABLED", True)
```

Benefits:
- Type-safe configuration
- IDE autocomplete support
- Clear documentation of defaults
- Runtime modification via API

---

## Extension Points

The architecture supports several extension paths:

### 1. Multi-Model (Planner + Actor)
Replace single model call with:
```python
plan = planner_model.plan(goal, screenshot)  # GPT-4o
action = actor_model.ground(plan, screenshot)  # ShowUI
```

### 2. Application Allowlisting
Extend `safety.py` with window detection:
```python
if not allowlist.is_app_allowed(get_active_window()):
    return SafetyCheckResult(allowed=False, reason="App not in allowlist")
```

### 3. Action Verification
Add semantic verification after execution:
```python
expected_ui = model.predict_ui_state_after(action)
actual_ui = capture()
if not verify_ui_state(expected_ui, actual_ui):
    inject_correction_prompt()
```

### 4. Benchmark Integration
Support OSWorld task format:
```python
task = OSWorldTask.load("task_001.json")
agent.run_goal(task.instruction)
result = task.evaluate(trace)
```
