"""
Simple benchmark system for measuring agent performance.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BENCHMARK_DIR = Path("./benchmarks")


@dataclass
class Task:
    """A benchmark task."""
    id: str
    goal: str
    max_steps: int = 20
    timeout_seconds: float = 120.0


@dataclass 
class TaskResult:
    """Result of running a task."""
    task_id: str
    success: bool
    steps_taken: int
    time_seconds: float
    final_status: str
    error: Optional[str] = None


@dataclass
class BenchmarkRun:
    """Results from running the full benchmark."""
    run_id: str
    timestamp: float
    results: List[TaskResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.success) / len(self.results)
    
    @property
    def avg_steps(self) -> float:
        successful = [r for r in self.results if r.success]
        if not successful:
            return 0.0
        return sum(r.steps_taken for r in successful) / len(successful)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "success_rate": self.success_rate,
            "avg_steps": self.avg_steps,
            "total_tasks": len(self.results),
            "results": [
                {
                    "task_id": r.task_id,
                    "success": r.success,
                    "steps": r.steps_taken,
                    "time": r.time_seconds,
                    "status": r.final_status,
                }
                for r in self.results
            ],
        }


# Default benchmark tasks
DEFAULT_TASKS = [
    Task("notepad_open", "Open Notepad"),
    Task("notepad_type", "Open Notepad and type 'Hello World'"),
    Task("calculator", "Open Calculator"),
    Task("calc_add", "Open Calculator and compute 5 + 3"),
    Task("chrome_google", "Open Chrome and go to google.com"),
    Task("settings", "Open Windows Settings"),
    Task("file_explorer", "Open File Explorer"),
    Task("search_files", "Open File Explorer and search for 'documents'"),
    Task("screenshot", "Take a screenshot using Snipping Tool"),
    Task("close_window", "Close the current window"),
]


class Benchmark:
    """Benchmark runner."""
    
    def __init__(self, tasks: Optional[List[Task]] = None) -> None:
        self.tasks = tasks or DEFAULT_TASKS
        self._current_run: Optional[BenchmarkRun] = None
    
    def start_run(self) -> str:
        """Start a new benchmark run."""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_run = BenchmarkRun(
            run_id=run_id,
            timestamp=time.time(),
        )
        return run_id
    
    def record_result(self, result: TaskResult) -> None:
        """Record a task result."""
        if self._current_run:
            self._current_run.results.append(result)
    
    def finish_run(self) -> BenchmarkRun:
        """Finish and save the run."""
        if not self._current_run:
            raise RuntimeError("No active run")
        
        run = self._current_run
        self._current_run = None
        
        # Save to disk
        BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
        path = BENCHMARK_DIR / f"{run.run_id}.json"
        with open(path, "w") as f:
            json.dump(run.to_dict(), f, indent=2)
        
        logger.info(
            f"Benchmark {run.run_id}: "
            f"{run.success_rate:.0%} success, "
            f"{run.avg_steps:.1f} avg steps"
        )
        
        return run
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """List previous benchmark runs."""
        if not BENCHMARK_DIR.exists():
            return []
        
        runs = []
        for path in sorted(BENCHMARK_DIR.glob("*.json"), reverse=True):
            with open(path) as f:
                runs.append(json.load(f))
        return runs
