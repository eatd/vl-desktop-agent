# Vision Language Desktop Agent

A desktop automation system that uses Vision-Language Models (VLMs) to understand screen content and execute actions autonomously.

![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-blue)
![React](https://img.shields.io/badge/React-18+-61dafb)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

-  **Screen Capture**: DXCam (Windows) or MSS (cross-platform)
-  **VLM Integration**: OpenAI-compatible API (LM Studio, vLLM, etc.)
-  **Smart Execution**: Click, type, scroll, hotkeys
-  **Verification Loop**: Detects if actions had effect
-  **Self-Correction**: Reflects and recovers when stuck
-  **Action Tracing**: Full session recording with screenshots
-  **Safety Guardrails**: Blocks dangerous hotkeys

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │◄────│   FastAPI   │◄────│  VLM Server │
│  (WebSocket)│     │   Backend   │     │ (LM Studio) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │    Desktop Agent     │
              │  Capture → Infer →   │
              │  Verify → Execute    │
              └──────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- VLM server (e.g., LM Studio with `qwen/qwen3-vl-4b`)

### 1. Start VLM Server

Using LM Studio:
1. Download `qwen/qwen3-vl-4b`
2. Start server on port 1234

### 2. Start Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Use

Open `http://localhost:5173` and enter a goal like "Open Notepad".

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MODEL` | `qwen/qwen3-vl-4b` | Model name |
| `AGENT_BASE_URL` | `http://localhost:1234/v1` | 
| `AGENT_DRY_RUN` | `0` | Log without executing |
| `AGENT_MAX_STEPS` | `50` | Max steps per goal |
| `AGENT_USE_DXCAM` | `0` | Use DXCam (Windows) |

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/status` | Agent status |
| `POST` | `/api/run` | Start goal `{"goal": "..."}` |
| `POST` | `/api/stop` | Stop agent |
| `GET` | `/api/traces` | List sessions |
| `GET` | `/api/traces/{id}` | Session detail |
| `GET` | `/api/benchmark/tasks` | Benchmark tasks |
| `GET` | `/api/benchmark/runs` | Benchmark results |
| `WS` | `/api/events` | Real-time events |

---

## Project Structure

```
backend/app/
├── agent.py      # Core loop: capture→infer→verify→execute
├── executor.py   # PyAutoGUI action execution
├── models.py     # Action schema  
├── prompts.py    # System prompt with few-shot examples
├── vision.py     # Screen capture
├── trace.py      # Session recording
├── safety.py     # Hotkey blocking
├── benchmark.py  # Task evaluation
├── grid.py       # Coordinate overlay
├── config.py     # Environment settings
├── main.py       # FastAPI app
└── service.py    # Agent lifecycle

frontend/src/
├── App.tsx       # Main component
├── api.ts        # API client
└── components/   # UI components
```

---

## Verification System

The agent verifies each action by comparing before/after screenshots:

```
[OK] Click at (960, 540)        ← UI changed (verified)
[NO EFFECT] Click at (100, 50)  ← No change detected
[REFLECT] Adjusting approach... ← Self-correction triggered
```

After 3 consecutive failures, the agent reflects on what went wrong.

---

## Development

```bash
# Run tests
cd backend
python -m pytest tests/ -v

# Type check
mypy app/

# Format
ruff format app/
```

---

## License

MIT
