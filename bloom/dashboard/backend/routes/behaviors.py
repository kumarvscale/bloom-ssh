"""
Behaviors API routes.
"""

import csv
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..models import BehaviorSummary, BehaviorDetail

router = APIRouter(prefix="/api/behaviors", tags=["behaviors"])

# Paths
BLOOM_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BLOOM_DIR / "results"
STATE_FILE = RESULTS_DIR / "ssh_test_state.json"
CSV_PATH = BLOOM_DIR / "docs" / "SSH Behaviors Taxonomy.csv"


def parse_behavior_name(comment: str) -> str:
    """Convert behavior comment path to a slug name."""
    parts = comment.split(">")
    name = parts[-1].strip()
    slug = name.lower().replace(" ", "-").replace("/", "-").replace("_", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def load_behaviors_from_csv() -> list[dict]:
    """Load behaviors from the CSV file."""
    behaviors = []
    if CSV_PATH.exists():
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                comment = row.get("Comments", "").strip()
                definition = row.get("Definition", "").strip()
                if comment:
                    if not definition:
                        definition = f"Behavior related to: {comment.replace('>', ' - ')}"
                    behaviors.append({
                        "path": comment,
                        "name": parse_behavior_name(comment),
                        "definition": definition,
                    })
    return behaviors


def load_state() -> dict:
    """Load the current state file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


@router.get("", response_model=list[BehaviorSummary])
async def list_behaviors(
    status: Optional[str] = Query(None, description="Filter by status: completed, in_progress, pending"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List all behaviors with their evaluation status."""
    behaviors = load_behaviors_from_csv()
    state = load_state()
    
    completed = state.get("completed", {})
    turn_counts = state.get("turn_counts", [4, 5, 6, 7, 8])
    current = state.get("current")
    
    results = []
    for behavior in behaviors:
        name = behavior["name"]
        completed_turns = completed.get(name, [])
        
        # Determine status
        if len(completed_turns) == len(turn_counts):
            behavior_status = "completed"
        elif len(completed_turns) > 0:
            behavior_status = "partial"
        elif current and current.get("behavior") == name:
            behavior_status = "in_progress"
        else:
            behavior_status = "pending"
        
        # Check if has results
        behavior_dir = RESULTS_DIR / name
        has_results = behavior_dir.exists() and any(behavior_dir.iterdir())
        
        # Apply filter
        if status and behavior_status != status:
            if not (status == "in_progress" and behavior_status == "partial"):
                continue
        
        results.append(BehaviorSummary(
            name=name,
            path=behavior["path"],
            definition=behavior["definition"],
            status=behavior_status,
            completed_turns=completed_turns,
            total_turns=len(turn_counts),
            has_results=has_results,
        ))
    
    # Apply pagination
    return results[offset:offset + limit]


@router.get("/{behavior_name}", response_model=BehaviorDetail)
async def get_behavior(behavior_name: str):
    """Get detailed results for a specific behavior."""
    behaviors = load_behaviors_from_csv()
    behavior = next((b for b in behaviors if b["name"] == behavior_name), None)
    
    if not behavior:
        raise HTTPException(status_code=404, detail=f"Behavior '{behavior_name}' not found")
    
    # Load results for each turn count
    behavior_dir = RESULTS_DIR / behavior_name
    turn_results = {}
    
    if behavior_dir.exists():
        for turn_dir in sorted(behavior_dir.iterdir()):
            if turn_dir.is_dir() and turn_dir.name.startswith("turns_"):
                turn_count = turn_dir.name.replace("turns_", "")
                results_subdir = turn_dir / "bloom-results" / behavior_name
                
                turn_data = {
                    "understanding": None,
                    "ideation": None,
                    "rollout": None,
                    "judgment": None,
                    "transcript": None,
                }
                
                # Load each stage's results
                for stage in ["understanding", "ideation", "rollout", "judgment"]:
                    stage_file = results_subdir / f"{stage}.json"
                    if stage_file.exists():
                        try:
                            with open(stage_file) as f:
                                turn_data[stage] = json.load(f)
                        except Exception:
                            pass
                
                # Load transcript if exists
                transcript_file = results_subdir / "transcript_v1r1.json"
                if transcript_file.exists():
                    try:
                        with open(transcript_file) as f:
                            turn_data["transcript"] = json.load(f)
                    except Exception:
                        pass
                
                turn_results[turn_count] = turn_data
    
    return BehaviorDetail(
        name=behavior["name"],
        path=behavior["path"],
        definition=behavior["definition"],
        turn_results=turn_results,
    )

