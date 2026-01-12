"""
Status API routes.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from ..models import RunStatus, StatsResponse, StageProgress

router = APIRouter(prefix="/api/status", tags=["status"])

# Results directory (relative to bloom root)
RESULTS_DIR = Path(__file__).parent.parent.parent.parent / "results"
STATE_FILE = RESULTS_DIR / "ssh_test_state.json"

PIPELINE_STAGES = ["understanding", "ideation", "rollout", "judgment"]


def load_state() -> dict:
    """Load the current state file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


@router.get("", response_model=RunStatus)
async def get_status():
    """Get current run status."""
    state = load_state()
    
    if not state:
        return RunStatus(is_running=False)
    
    # Calculate totals
    total_behaviors = state.get("total_behaviors", 0)
    turn_counts = state.get("turn_counts", [])
    total_tests = total_behaviors * len(turn_counts)
    
    completed = state.get("completed", {})
    completed_tests = sum(len(turns) for turns in completed.values())
    failed_tests = len(state.get("failed", []))
    
    # Current status
    current = state.get("current")
    is_running = current is not None
    current_stage = current.get("stage") if current else None
    
    # Calculate stage timings averages
    stage_timings = state.get("stage_timings", {})
    avg_times = {}
    for stage, times in stage_timings.items():
        if times:
            avg_times[stage] = sum(times) / len(times)
        else:
            # Default estimates
            defaults = {"understanding": 30, "ideation": 60, "rollout": 120, "judgment": 90}
            avg_times[stage] = defaults.get(stage, 60)
    
    # Build stage progress list
    stages = []
    for stage in PIPELINE_STAGES:
        if not is_running:
            status = "pending"
        elif current_stage == stage:
            status = "running"
        elif PIPELINE_STAGES.index(stage) < PIPELINE_STAGES.index(current_stage or "understanding"):
            status = "completed"
        else:
            status = "pending"
        
        stages.append(StageProgress(
            name=stage,
            status=status,
            avg_duration=avg_times.get(stage),
        ))
    
    # Calculate ETA
    eta_seconds = None
    if is_running:
        avg_test_time = sum(avg_times.values())
        remaining = total_tests - completed_tests
        # Adjust for current progress within the test
        if current_stage:
            stage_idx = PIPELINE_STAGES.index(current_stage)
            completed_stage_time = sum(avg_times.get(s, 0) for s in PIPELINE_STAGES[:stage_idx])
            current_test_remaining = avg_test_time - completed_stage_time
            eta_seconds = (remaining - 1) * avg_test_time + current_test_remaining
        else:
            eta_seconds = remaining * avg_test_time
    
    # Calculate current test number
    current_test_number = completed_tests + 1 if is_running else completed_tests
    
    return RunStatus(
        is_running=is_running,
        started_at=state.get("started_at"),
        last_updated=state.get("last_updated"),
        total_tests=total_tests,
        completed_tests=completed_tests,
        failed_tests=failed_tests,
        pending_tests=total_tests - completed_tests,
        progress_pct=(completed_tests / total_tests * 100) if total_tests > 0 else 0,
        current_behavior=current.get("behavior") if current else None,
        current_turn_count=current.get("turn_count") if current else None,
        current_stage=current_stage,
        eta_seconds=eta_seconds,
        # Granular progress
        total_behaviors=total_behaviors,
        turn_counts=turn_counts,
        stages=stages,
        current_test_number=current_test_number,
        stage_timings=avg_times if avg_times else None,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get overall statistics."""
    state = load_state()
    
    if not state:
        return StatsResponse(
            total_behaviors=0,
            total_tests=0,
            completed_tests=0,
            failed_tests=0,
            behaviors_completed=0,
            behaviors_in_progress=0,
            behaviors_pending=0,
        )
    
    total_behaviors = state.get("total_behaviors", 0)
    turn_counts = state.get("turn_counts", [])
    total_tests = total_behaviors * len(turn_counts)
    
    completed = state.get("completed", {})
    completed_tests = sum(len(turns) for turns in completed.values())
    failed_tests = len(state.get("failed", []))
    
    # Count behavior states
    behaviors_completed = sum(
        1 for turns in completed.values() 
        if len(turns) == len(turn_counts)
    )
    behaviors_in_progress = sum(
        1 for turns in completed.values() 
        if 0 < len(turns) < len(turn_counts)
    )
    behaviors_pending = total_behaviors - behaviors_completed - behaviors_in_progress
    
    # Calculate average score from judgment files
    scores = []
    for behavior_dir in RESULTS_DIR.iterdir():
        if behavior_dir.is_dir() and behavior_dir.name not in ["ssh_test_validation", "ssh_test_state.json"]:
            for turn_dir in behavior_dir.iterdir():
                if turn_dir.is_dir():
                    judgment_file = turn_dir / "bloom-results" / behavior_dir.name / "judgment.json"
                    if judgment_file.exists():
                        try:
                            with open(judgment_file) as f:
                                judgment = json.load(f)
                                if "summary_statistics" in judgment:
                                    avg_score = judgment["summary_statistics"].get("average_behavior_presence_score")
                                    if avg_score is not None:
                                        scores.append(avg_score)
                        except Exception:
                            pass
    
    avg_score = sum(scores) / len(scores) if scores else None
    
    return StatsResponse(
        total_behaviors=total_behaviors,
        total_tests=total_tests,
        completed_tests=completed_tests,
        failed_tests=failed_tests,
        behaviors_completed=behaviors_completed,
        behaviors_in_progress=behaviors_in_progress,
        behaviors_pending=behaviors_pending,
        average_score=avg_score,
    )

