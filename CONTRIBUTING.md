# Contributing to VL Desktop Agent

Thank you for your interest in contributing! This document provides guidelines for development and contribution.

---

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Running in Development

Terminal 1 - Backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

---

## Code Quality

### Type Checking

```bash
cd backend
mypy app/
```

### Linting

```bash
cd backend
ruff check app/
```

### Formatting

```bash
cd backend
ruff format app/
```

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Project Structure Guidelines

### Backend (`backend/app/`)

| File | Purpose |
|------|---------|
| `agent.py` | Core agent loop - capture/infer/execute |
| `executor.py` | Action execution via PyAutoGUI |
| `models.py` | Pydantic schemas for actions |
| `parsing.py` | Model response parsing |
| `vision.py` | Screen capture abstraction |
| `safety.py` | Action validation and guardrails |
| `trace.py` | Session recording |
| `evaluation.py` | Metrics collection |
| `config.py` | Environment configuration |
| `main.py` | FastAPI application |

### Frontend (`frontend/src/`)

| File | Purpose |
|------|---------|
| `App.tsx` | Main application component |
| `api.ts` | Backend API client |
| `components/` | Reusable UI components |

---

## Adding New Action Types

1. **Define the model** in `models.py`:
   ```python
   class MyNewAction(BaseAction, Coords):
       action_type: Literal["my_new_action"] = "my_new_action"
       my_field: str = Field(...)
   ```

2. **Add to Union** in `models.py`:
   ```python
   DesktopAction = Union[
       ...,
       MyNewAction,
   ]
   ```

3. **Add to tool schema** in `tools.py`:
   ```python
   AVAILABLE_TOOLS["my_new_action"] = MyNewAction
   ```

4. **Implement execution** in `executor.py`:
   ```python
   if isinstance(action, MyNewAction):
       # Execute the action
       return desc, coords
   ```

5. **Add tests** in `tests/test_executor.py`

---

## Adding New Configuration Options

1. **Add to Settings** in `config.py`:
   ```python
   my_option: str = os.getenv("AGENT_MY_OPTION", "default")
   ```

2. **Document** in README.md

3. **Update CLI** in `cli.py` if needed

---

## Commit Message Format

Use conventional commits:

```
feat: add new action type for window switching
fix: handle malformed JSON with missing y coordinate
docs: update architecture diagram
test: add tests for safety checker
refactor: extract coordinate mapping to separate function
```

---

## Pull Request Process

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes
3. Run tests: `python -m pytest tests/ -v`
4. Run type check: `mypy app/`
5. Run lint: `ruff check app/`
6. Commit with descriptive message
7. Push and create PR

---

## Questions?

Open an issue for discussion before making large changes.
