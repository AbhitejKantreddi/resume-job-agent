"""In-memory run store with thread-safe state updates.

Swap this for Supabase/Postgres if you want to persist run history (see the
README "future work" note).
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .agent.pipeline import NODES


def _initial_steps() -> list[dict[str, Any]]:
    return [{"node": node, "label": label, "status": "pending"} for node, label in NODES]


@dataclass
class Run:
    run_id: str
    raw_text: str
    location: str
    status: str = "pending"  # pending | running | completed | failed
    current_node: str = ""
    steps: list[dict[str, Any]] = field(default_factory=_initial_steps)
    results: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    version: int = 0  # bumped on every state change so SSE can diff cheaply
    created_at: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set_node(self, node: str, status: str) -> None:
        with self._lock:
            self.current_node = node
            for step in self.steps:
                if step["node"] == node:
                    step["status"] = status
            if status == "in_progress":
                self.status = "running"
            self.version += 1

    def set_result(self, key: str, value: Any) -> None:
        with self._lock:
            self.results[key] = value
            self.version += 1

    def finish(self, error: str | None = None) -> None:
        with self._lock:
            if error:
                self.status = "failed"
                self.error = error
                for step in self.steps:
                    if step["status"] == "in_progress":
                        step["status"] = "error"
            else:
                self.status = "completed"
            self.version += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "run_id": self.run_id,
                "status": self.status,
                "current_node": self.current_node,
                "steps": [dict(s) for s in self.steps],
                "results": dict(self.results),
                "error": self.error,
                "version": self.version,
            }


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}
        self._lock = threading.Lock()

    def create(self, raw_text: str, location: str) -> Run:
        run_id = uuid.uuid4().hex[:12]
        run = Run(run_id=run_id, raw_text=raw_text, location=location)
        with self._lock:
            self._runs[run_id] = run
        return run

    def get(self, run_id: str) -> Run | None:
        with self._lock:
            return self._runs.get(run_id)


store = RunStore()
