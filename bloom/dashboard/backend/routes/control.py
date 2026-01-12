"""
Run control API routes.
Provides endpoints to start, pause, stop, and restart evaluation runs.
"""

import json
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/control", tags=["control"])

# Paths
BLOOM_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BLOOM_DIR / "results"
CONTROL_FILE = RESULTS_DIR / "run_control.json"
STATE_FILE = RESULTS_DIR / "ssh_test_state.json"
BEHAVIORS_CSV = BLOOM_DIR / "docs" / "SSH Behaviors Taxonomy.csv"

# Global to track running process
_running_process: Optional[subprocess.Popen] = None


class StartRunRequest(BaseModel):
    """Request to start a new run."""
    mode: str  # "full" or "selected"
    scenarios_per_behavior: int = 1
    selected_behaviors: list[str] = []
    turn_counts: list[int] = [4, 5, 6, 7, 8]


class ControlResponse(BaseModel):
    """Response for control operations."""
    success: bool
    message: str
    run_id: Optional[str] = None


def load_control() -> dict:
    """Load current control state."""
    if CONTROL_FILE.exists():
        with open(CONTROL_FILE, "r") as f:
            return json.load(f)
    return {"status": "idle", "command": None}


def save_control(control: dict) -> None:
    """Save control state."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONTROL_FILE, "w") as f:
        json.dump(control, f, indent=2)


def load_state() -> dict:
    """Load run state."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def reset_state() -> None:
    """Reset state file for a fresh run."""
    fresh_state = {
        "started_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "total_behaviors": 0,
        "turn_counts": [],
        "completed": {},
        "current": None,
        "failed": [],
        "config": {},
        "stage_timings": {
            "understanding": [],
            "ideation": [],
            "rollout": [],
            "judgment": [],
        },
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(fresh_state, f, indent=2)


def get_behaviors_list() -> list[dict]:
    """Get list of all behaviors from CSV."""
    import csv
    behaviors = []
    if BEHAVIORS_CSV.exists():
        with open(BEHAVIORS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                comment = row.get("Comments", "").strip()
                if comment:
                    # Parse behavior name (slug)
                    parts = comment.split(">")
                    name = parts[-1].strip()
                    slug = name.lower().replace(" ", "-").replace("/", "-").replace("_", "-")
                    slug = "".join(c for c in slug if c.isalnum() or c == "-")
                    while "--" in slug:
                        slug = slug.replace("--", "-")
                    slug = slug.strip("-")
                    
                    behaviors.append({
                        "slug": slug,
                        "name": name,
                        "path": comment,
                    })
    return behaviors


def is_running() -> bool:
    """Check if a run is currently active."""
    state = load_state()
    return state.get("current") is not None


def generate_run_id() -> str:
    """Generate a unique run ID based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@router.get("/behaviors")
async def list_behaviors():
    """Get list of available behaviors for selection."""
    return get_behaviors_list()


@router.get("/status")
async def get_control_status():
    """Get current control status."""
    control = load_control()
    state = load_state()
    
    return {
        "is_running": state.get("current") is not None,
        "control_status": control.get("status", "idle"),
        "command": control.get("command"),
        "run_id": control.get("run_id"),
    }


@router.post("/start", response_model=ControlResponse)
async def start_run(request: StartRunRequest, background_tasks: BackgroundTasks):
    """Start a new evaluation run."""
    global _running_process
    
    if is_running():
        raise HTTPException(
            status_code=400,
            detail="A run is already in progress. Stop it first or wait for it to complete."
        )
    
    # Reset state for fresh run
    reset_state()
    
    # Generate run ID
    run_id = generate_run_id()
    
    # Build command arguments
    cmd = [
        sys.executable,
        str(BLOOM_DIR / "scripts" / "run_ssh_behaviors.py"),
        "--turns", ",".join(map(str, request.turn_counts)),
    ]
    
    if request.mode == "selected" and request.selected_behaviors:
        # For selected mode, we need to filter behaviors
        # Add a special flag for selected behaviors
        cmd.extend(["--selected", ",".join(request.selected_behaviors)])
    
    # Add scenarios per behavior (maps to --behaviors for now, but could be extended)
    if request.scenarios_per_behavior > 0:
        # This controls total_evals in ideation
        pass  # TODO: Add ideation control
    
    # Set environment for timestamped results
    env = os.environ.copy()
    env["RUN_ID"] = run_id
    env["LITELLM_API_KEY"] = os.environ.get("LITELLM_API_KEY", "sk-e3Mp4Ktt_rVo40i-GXgejg")
    env["LITELLM_BASE_URL"] = os.environ.get("LITELLM_BASE_URL", "https://litellm.ml.scaleinternal.com")
    
    # Save control state
    save_control({
        "status": "running",
        "command": "start",
        "run_id": run_id,
        "started_at": datetime.now().isoformat(),
        "config": {
            "mode": request.mode,
            "scenarios_per_behavior": request.scenarios_per_behavior,
            "selected_behaviors": request.selected_behaviors,
            "turn_counts": request.turn_counts,
        }
    })
    
    # Start the process in background
    try:
        _running_process = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(BLOOM_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except Exception as e:
        save_control({"status": "error", "command": None, "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to start run: {str(e)}")
    
    return ControlResponse(
        success=True,
        message=f"Started new run with ID: {run_id}",
        run_id=run_id,
    )


@router.post("/pause", response_model=ControlResponse)
async def pause_run():
    """Pause the current run."""
    if not is_running():
        raise HTTPException(status_code=400, detail="No run is currently active")
    
    control = load_control()
    control["command"] = "pause"
    control["status"] = "paused"
    save_control(control)
    
    return ControlResponse(
        success=True,
        message="Pause signal sent. Run will pause after current test completes.",
    )


@router.post("/resume", response_model=ControlResponse)
async def resume_run():
    """Resume a paused run."""
    control = load_control()
    if control.get("status") != "paused":
        raise HTTPException(status_code=400, detail="Run is not paused")
    
    control["command"] = "resume"
    control["status"] = "running"
    save_control(control)
    
    return ControlResponse(
        success=True,
        message="Resume signal sent. Run will continue.",
    )


@router.post("/stop", response_model=ControlResponse)
async def stop_run():
    """Stop the current run."""
    global _running_process
    
    if not is_running():
        # Clear any stale state
        save_control({"status": "idle", "command": None})
        return ControlResponse(
            success=True,
            message="No run was active. State cleared.",
        )
    
    control = load_control()
    control["command"] = "stop"
    control["status"] = "stopping"
    save_control(control)
    
    # Try to terminate the process gracefully
    if _running_process and _running_process.poll() is None:
        try:
            _running_process.terminate()
            _running_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _running_process.kill()
        _running_process = None
    
    # Clear the current state
    state = load_state()
    if state:
        state["current"] = None
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    
    save_control({"status": "idle", "command": None})
    
    return ControlResponse(
        success=True,
        message="Run stopped. Results up to this point have been saved.",
    )


@router.post("/restart", response_model=ControlResponse)
async def restart_run(request: StartRunRequest, background_tasks: BackgroundTasks):
    """Restart with new parameters (stops current run first)."""
    global _running_process
    
    # Stop current run if active
    if is_running():
        await stop_run()
    
    # Start new run
    return await start_run(request, background_tasks)

