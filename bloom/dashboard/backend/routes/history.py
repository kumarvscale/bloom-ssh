"""
Run History API routes.
Provides endpoints to browse past runs and their results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..models import ConversationSummary, ConversationDetail, ConversationMessage

router = APIRouter(prefix="/api/history", tags=["history"])

# Paths
BLOOM_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BLOOM_DIR / "results"
BLOOM_RESULTS_DIR = BLOOM_DIR / "bloom-results"


def parse_run_id(run_dir_name: str) -> Optional[str]:
    """Extract run ID from directory name like 'run_20260112_143052'."""
    if run_dir_name.startswith("run_"):
        return run_dir_name[4:]  # Remove 'run_' prefix
    return None


def format_run_timestamp(run_id: str) -> str:
    """Convert run ID to human-readable timestamp."""
    try:
        # Parse format: YYYYMMDD_HHMMSS
        dt = datetime.strptime(run_id, "%Y%m%d_%H%M%S")
        return dt.strftime("%b %d, %Y %H:%M:%S")
    except ValueError:
        return run_id


def get_date_from_run_id(run_id: str) -> str:
    """Extract date string from run ID (YYYYMMDD_HHMMSS -> YYYYMMDD)."""
    if run_id == "default":
        return "default"
    try:
        return run_id.split("_")[0]
    except:
        return run_id


def format_date_header(date_str: str) -> str:
    """Format date string for display."""
    if date_str == "default":
        return "Default Results"
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%B %d, %Y")  # e.g., "January 11, 2026"
    except ValueError:
        return date_str


@router.get("/runs")
async def list_runs():
    """List all previous runs grouped by date."""
    runs = []
    
    if not RESULTS_DIR.exists():
        pass
    else:
        for item in RESULTS_DIR.iterdir():
            if item.is_dir() and item.name.startswith("run_"):
                run_id = parse_run_id(item.name)
                if not run_id:
                    continue
                
                # Load run state if available
                state_file = item / "run_state.json"
                state = {}
                if state_file.exists():
                    try:
                        with open(state_file) as f:
                            state = json.load(f)
                    except Exception:
                        pass
                
                # Count behaviors and conversations
                behavior_count = 0
                conversation_count = 0
                for behavior_dir in item.iterdir():
                    if behavior_dir.is_dir() and not behavior_dir.name.startswith("."):
                        behavior_count += 1
                        for turn_dir in behavior_dir.iterdir():
                            if turn_dir.is_dir() and turn_dir.name.startswith("turns_"):
                                conversation_count += 1
                
                # Get modification time
                mtime = item.stat().st_mtime
                
                # Extract time portion for sorting within day
                time_str = run_id.split("_")[1] if "_" in run_id else "000000"
                
                runs.append({
                    "run_id": run_id,
                    "directory": item.name,
                    "timestamp": format_run_timestamp(run_id),
                    "time_only": f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}",
                    "date": get_date_from_run_id(run_id),
                    "modified_at": datetime.fromtimestamp(mtime).isoformat(),
                    "total_behaviors": state.get("total_behaviors", behavior_count),
                    "completed_tests": sum(len(v) for v in state.get("completed", {}).values()),
                    "failed_tests": len(state.get("failed", [])),
                    "conversation_count": conversation_count,
                    "config": state.get("config", {}),
                })
    
    # Also add bloom-results as a "default" run
    if BLOOM_RESULTS_DIR.exists():
        behavior_count = sum(1 for d in BLOOM_RESULTS_DIR.iterdir() if d.is_dir())
        if behavior_count > 0:
            runs.append({
                "run_id": "default",
                "directory": "bloom-results",
                "timestamp": "Default Results",
                "time_only": "",
                "date": "default",
                "modified_at": datetime.fromtimestamp(BLOOM_RESULTS_DIR.stat().st_mtime).isoformat(),
                "total_behaviors": behavior_count,
                "completed_tests": behavior_count,
                "failed_tests": 0,
                "conversation_count": behavior_count,
                "config": {},
            })
    
    # Sort by run_id descending (newest first)
    runs.sort(key=lambda x: x["run_id"] if x["run_id"] != "default" else "00000000_000000", reverse=True)
    
    # Group by date
    from collections import OrderedDict
    grouped = OrderedDict()
    
    for run in runs:
        date = run["date"]
        if date not in grouped:
            grouped[date] = {
                "date": date,
                "date_display": format_date_header(date),
                "runs": [],
                "total_completed": 0,
                "total_failed": 0,
                "total_conversations": 0,
            }
        grouped[date]["runs"].append(run)
        grouped[date]["total_completed"] += run["completed_tests"]
        grouped[date]["total_failed"] += run["failed_tests"]
        grouped[date]["total_conversations"] += run["conversation_count"]
    
    return list(grouped.values())


@router.get("/runs/{run_id}/conversations")
async def list_run_conversations(
    run_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List all conversations from a specific run."""
    conversations = []
    
    # Determine the directory to scan
    if run_id == "default":
        results_dir = BLOOM_RESULTS_DIR
        is_default = True
    else:
        results_dir = RESULTS_DIR / f"run_{run_id}"
        is_default = False
    
    if not results_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    if is_default:
        # For default/bloom-results, each behavior is directly in the folder
        for behavior_dir in results_dir.iterdir():
            if not behavior_dir.is_dir():
                continue
            
            behavior_name = behavior_dir.name
            conv_data = _get_conversation_data(behavior_dir, behavior_name, 0, run_id)
            if conv_data:
                conversations.append(conv_data)
    else:
        # For timestamped runs, structure is run_xxx/behavior/turns_N/bloom-results/behavior
        for behavior_dir in results_dir.iterdir():
            if not behavior_dir.is_dir() or behavior_dir.name.startswith("."):
                continue
            
            behavior_name = behavior_dir.name
            
            for turn_dir in behavior_dir.iterdir():
                if not turn_dir.is_dir() or not turn_dir.name.startswith("turns_"):
                    continue
                
                turn_count = int(turn_dir.name.replace("turns_", ""))
                results_subdir = turn_dir / "bloom-results" / behavior_name
                
                conv_data = _get_conversation_data(results_subdir, behavior_name, turn_count, run_id)
                if conv_data:
                    conversations.append(conv_data)
    
    # Sort by timestamp (newest first)
    conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Apply pagination
    return conversations[offset:offset + limit]


def _get_conversation_data(results_dir: Path, behavior_name: str, turn_count: int, run_id: str) -> Optional[dict]:
    """Extract conversation data from a results directory."""
    import re
    
    if not results_dir.exists():
        return None
    
    # Get modification time
    mtime = results_dir.stat().st_mtime
    timestamp = datetime.fromtimestamp(mtime).isoformat()
    
    # Check what stages are complete
    stages_complete = []
    for stage in ["understanding", "ideation", "rollout", "judgment"]:
        if (results_dir / f"{stage}.json").exists():
            stages_complete.append(stage)
    
    if not stages_complete:
        return None
    
    # Get score from judgment if available
    score = None
    judgment_file = results_dir / "judgment.json"
    if judgment_file.exists():
        try:
            with open(judgment_file) as f:
                judgment = json.load(f)
                if "summary_statistics" in judgment:
                    score = judgment["summary_statistics"].get("average_behavior_presence_score")
        except Exception:
            pass
    
    # Determine current stage
    if "judgment" in stages_complete:
        current_stage = "judgment"
    elif "rollout" in stages_complete:
        current_stage = "rollout"
    elif "ideation" in stages_complete:
        current_stage = "ideation"
    elif "understanding" in stages_complete:
        current_stage = "understanding"
    else:
        current_stage = "pending"
    
    # Extract preview from rollout
    preview = None
    rollout_file = results_dir / "rollout.json"
    if rollout_file.exists():
        try:
            with open(rollout_file) as f:
                rollout_data = json.load(f)
                if "rollouts" in rollout_data and len(rollout_data["rollouts"]) > 0:
                    desc = rollout_data["rollouts"][0].get("variation_description", "")
                    clean_desc = re.sub(r'\*+', '', desc)
                    words = clean_desc.strip().split()[:8]
                    preview = " ".join(words)
                    if len(clean_desc.split()) > 8:
                        preview += "..."
        except Exception:
            pass
    
    return {
        "id": f"{run_id}:{behavior_name}_turns_{turn_count}" if turn_count > 0 else f"{run_id}:{behavior_name}_default",
        "run_id": run_id,
        "behavior": behavior_name,
        "turn_count": turn_count,
        "timestamp": timestamp,
        "score": score,
        "stage": current_stage,
        "preview": preview,
        "path": str(results_dir),
    }


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_history_conversation(conversation_id: str):
    """Get full details for a conversation from any run."""
    # Parse the conversation ID: run_id:behavior_name_turns_N or run_id:behavior_name_default
    if ":" not in conversation_id:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format. Expected run_id:conversation_id")
    
    run_id, conv_part = conversation_id.split(":", 1)
    
    # Determine the results directory
    if run_id == "default":
        base_dir = BLOOM_RESULTS_DIR
    else:
        base_dir = RESULTS_DIR / f"run_{run_id}"
    
    if not base_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Parse the conversation part
    if conv_part.endswith("_default"):
        behavior_name = conv_part.replace("_default", "")
        turn_count = 0
        results_dir = base_dir / behavior_name if run_id == "default" else None
    else:
        parts = conv_part.rsplit("_turns_", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        behavior_name = parts[0]
        try:
            turn_count = int(parts[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid turn count in ID")
        
        if run_id == "default":
            results_dir = base_dir / behavior_name
        else:
            results_dir = base_dir / behavior_name / f"turns_{turn_count}" / "bloom-results" / behavior_name
    
    if results_dir is None or not results_dir.exists():
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Load all stage data
    understanding = None
    ideation = None
    rollout = None
    judgment = None
    transcript = []
    
    # Understanding
    understanding_file = results_dir / "understanding.json"
    if understanding_file.exists():
        with open(understanding_file) as f:
            understanding = json.load(f)
    
    # Ideation
    ideation_file = results_dir / "ideation.json"
    if ideation_file.exists():
        with open(ideation_file) as f:
            ideation = json.load(f)
    
    # Rollout
    rollout_file = results_dir / "rollout.json"
    if rollout_file.exists():
        with open(rollout_file) as f:
            rollout = json.load(f)
    
    # Judgment
    judgment_file = results_dir / "judgment.json"
    if judgment_file.exists():
        with open(judgment_file) as f:
            judgment = json.load(f)
    
    # Extract transcript from rollout
    if rollout:
        try:
            rollouts_list = rollout.get("rollouts", [])
            if rollouts_list:
                rollout_transcript = rollouts_list[0].get("transcript", {})
                events = rollout_transcript.get("events", [])
                
                for event in events:
                    if event.get("type") == "transcript_event":
                        edit = event.get("edit", {})
                        message = edit.get("message", {})
                        view = event.get("view", [])
                        
                        if message and "target" in view:
                            role = message.get("role", "unknown")
                            content = message.get("content", "")
                            
                            if isinstance(content, list):
                                text_parts = []
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        text_parts.append(block.get("text", ""))
                                    elif isinstance(block, str):
                                        text_parts.append(block)
                                content = "\n".join(text_parts)
                            
                            if content and content.strip():
                                transcript.append(ConversationMessage(
                                    role=role,
                                    content=content,
                                ))
        except Exception as e:
            print(f"Error extracting transcript: {e}")
    
    return ConversationDetail(
        id=conversation_id,
        behavior=behavior_name,
        turn_count=turn_count,
        understanding=understanding,
        ideation=ideation,
        rollout=rollout,
        judgment=judgment,
        transcript=transcript,
    )

