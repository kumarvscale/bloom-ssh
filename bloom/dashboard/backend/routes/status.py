"""
Status API routes.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from ..models import RunStatus, StatsResponse, StageProgress, JudgmentStats

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
    
    # Calculate scores from judgment files
    # Priority: judgment_assistant_harmfulness.json (new) > judgment.json (old)
    scores = []
    
    def extract_scores_from_dir(results_dir: Path) -> list:
        """Extract harmfulness scores from a results directory."""
        extracted = []
        
        # First try the new assistant harmfulness judgment
        harmfulness_file = results_dir / "judgment_assistant_harmfulness.json"
        if harmfulness_file.exists():
            try:
                with open(harmfulness_file) as f:
                    judgment = json.load(f)
                    # Get individual harmfulness scores from judgments
                    if "judgments" in judgment:
                        for j in judgment["judgments"]:
                            score = j.get("harmfulness_score")
                            if score is not None:
                                extracted.append(score)
                    # Fallback to summary if no individual scores
                    elif "summary_statistics" in judgment:
                        avg_score = judgment["summary_statistics"].get("average_harmfulness_score")
                        if avg_score is not None:
                            extracted.append(avg_score)
            except Exception:
                pass
            return extracted  # Use new scores if available
        
        # Fallback to old judgment.json
        judgment_file = results_dir / "judgment.json"
        if judgment_file.exists():
            try:
                with open(judgment_file) as f:
                    judgment = json.load(f)
                    if "summary_statistics" in judgment:
                        avg_score = judgment["summary_statistics"].get("average_behavior_presence_score")
                        if avg_score is not None:
                            extracted.append(avg_score)
            except Exception:
                pass
        
        return extracted
    
    # Check timestamped run directories
    for run_dir in RESULTS_DIR.iterdir():
        if run_dir.is_dir() and run_dir.name.startswith("run_"):
            for behavior_dir in run_dir.iterdir():
                if behavior_dir.is_dir() and not behavior_dir.name.startswith("."):
                    for turn_dir in behavior_dir.iterdir():
                        if turn_dir.is_dir() and turn_dir.name.startswith("turns_"):
                            results_path = turn_dir / "bloom-results" / behavior_dir.name
                            scores.extend(extract_scores_from_dir(results_path))
    
    # Also check old-style results directories (non-timestamped)
    for behavior_dir in RESULTS_DIR.iterdir():
        if behavior_dir.is_dir() and not behavior_dir.name.startswith("run_") and behavior_dir.name not in ["ssh_test_validation", "ssh_test_state.json"]:
            for turn_dir in behavior_dir.iterdir():
                if turn_dir.is_dir():
                    results_path = turn_dir / "bloom-results" / behavior_dir.name
                    scores.extend(extract_scores_from_dir(results_path))
    
    # Also check bloom-results directory
    bloom_results_dir = RESULTS_DIR.parent / "bloom-results"
    if bloom_results_dir.exists():
        for behavior_dir in bloom_results_dir.iterdir():
            if behavior_dir.is_dir():
                scores.extend(extract_scores_from_dir(behavior_dir))
    
    # Calculate judgment statistics
    judgment_stats = None
    avg_score = None
    
    if scores:
        scores_sorted = sorted(scores)
        avg_score = sum(scores) / len(scores)
        
        # Calculate median
        n = len(scores_sorted)
        if n % 2 == 0:
            median = (scores_sorted[n//2 - 1] + scores_sorted[n//2]) / 2
        else:
            median = scores_sorted[n//2]
        
        # Score distribution (5 ranges)
        range_1_2 = sum(1 for s in scores if s <= 2)
        range_3_4 = sum(1 for s in scores if 2 < s <= 4)
        range_5_6 = sum(1 for s in scores if 4 < s <= 6)
        range_7_8 = sum(1 for s in scores if 6 < s <= 8)
        range_9_10 = sum(1 for s in scores if s > 8)
        
        judgment_stats = JudgmentStats(
            count=len(scores),
            average=avg_score,
            min_score=min(scores),
            max_score=max(scores),
            median=median,
            range_1_2=range_1_2,
            range_3_4=range_3_4,
            range_5_6=range_5_6,
            range_7_8=range_7_8,
            range_9_10=range_9_10,
        )
    
    return StatsResponse(
        total_behaviors=total_behaviors,
        total_tests=total_tests,
        completed_tests=completed_tests,
        failed_tests=failed_tests,
        behaviors_completed=behaviors_completed,
        behaviors_in_progress=behaviors_in_progress,
        behaviors_pending=behaviors_pending,
        average_score=avg_score,
        judgment_stats=judgment_stats,
    )

