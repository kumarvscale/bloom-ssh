"""
Pydantic models for the dashboard API.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class StageProgress(BaseModel):
    """Progress for a single pipeline stage."""
    name: str
    status: str  # "pending", "running", "completed"
    avg_duration: Optional[float] = None


class RunStatus(BaseModel):
    """Current run status."""
    is_running: bool
    started_at: Optional[str] = None
    last_updated: Optional[str] = None
    total_tests: int = 0
    completed_tests: int = 0
    failed_tests: int = 0
    pending_tests: int = 0
    progress_pct: float = 0.0
    current_behavior: Optional[str] = None
    current_turn_count: Optional[int] = None
    current_stage: Optional[str] = None
    eta_seconds: Optional[float] = None
    # Granular progress
    total_behaviors: int = 0
    turn_counts: list[int] = []
    stages: list[StageProgress] = []
    current_test_number: int = 0
    stage_timings: Optional[dict[str, float]] = None
    

class BehaviorSummary(BaseModel):
    """Summary of a behavior's evaluation status."""
    name: str
    path: str
    definition: str
    status: str  # "completed", "in_progress", "pending", "partial"
    completed_turns: list[int] = []
    total_turns: int = 0
    has_results: bool = False


class BehaviorDetail(BaseModel):
    """Detailed results for a behavior."""
    name: str
    path: str
    definition: str
    turn_results: dict[str, Any] = {}  # turn_count -> results


class ConversationMessage(BaseModel):
    """A single message in a conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None


class ConversationSummary(BaseModel):
    """Summary of a conversation."""
    id: str
    behavior: str
    turn_count: int
    timestamp: str
    score: Optional[float] = None
    stage: str  # "understanding", "ideation", "rollout", "judgment"
    preview: Optional[str] = None  # First few words of the conversation


class ConversationDetail(BaseModel):
    """Full conversation details."""
    id: str
    behavior: str
    turn_count: int
    understanding: Optional[dict] = None
    ideation: Optional[dict] = None
    rollout: Optional[dict] = None
    judgment: Optional[dict] = None
    transcript: list[ConversationMessage] = []


class StatsResponse(BaseModel):
    """Overall statistics."""
    total_behaviors: int
    total_tests: int
    completed_tests: int
    failed_tests: int
    behaviors_completed: int
    behaviors_in_progress: int
    behaviors_pending: int
    average_score: Optional[float] = None

