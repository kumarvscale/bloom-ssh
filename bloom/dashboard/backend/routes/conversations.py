"""
Conversations API routes.
"""

import json
import re
from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

from ..models import ConversationSummary, ConversationDetail, ConversationMessage

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# Paths
BLOOM_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BLOOM_DIR / "results"
BLOOM_RESULTS_DIR = BLOOM_DIR / "bloom-results"


def extract_preview(results_subdir: Path) -> Optional[str]:
    """Extract preview from rollout or ideation files."""
    preview = None
    rollout_file = results_subdir / "rollout.json"
    ideation_file = results_subdir / "ideation.json"
    
    if rollout_file.exists():
        try:
            with open(rollout_file) as f:
                rollout_data = json.load(f)
                if "rollouts" in rollout_data and len(rollout_data["rollouts"]) > 0:
                    desc = rollout_data["rollouts"][0].get("variation_description", "")
                    # Extract first meaningful words (skip markdown formatting)
                    clean_desc = re.sub(r'\*+', '', desc)  # Remove asterisks
                    words = clean_desc.strip().split()[:8]
                    preview = " ".join(words)
                    if len(clean_desc.split()) > 8:
                        preview += "..."
        except Exception:
            pass
    
    if not preview and ideation_file.exists():
        try:
            with open(ideation_file) as f:
                ideation_data = json.load(f)
                if "variations" in ideation_data and len(ideation_data["variations"]) > 0:
                    desc = ideation_data["variations"][0].get("description", "")
                    clean_desc = re.sub(r'\*+', '', desc)
                    words = clean_desc.strip().split()[:8]
                    preview = " ".join(words)
                    if len(clean_desc.split()) > 8:
                        preview += "..."
        except Exception:
            pass
    
    return preview


def get_conversation_data(results_subdir: Path, behavior_name: str, turn_count: int) -> Optional[dict]:
    """Extract conversation data from a results directory."""
    # Get modification time
    if results_subdir.exists():
        mtime = results_subdir.stat().st_mtime
        timestamp = datetime.fromtimestamp(mtime).isoformat()
    else:
        return None
    
    # Check what stages are complete
    stages_complete = []
    for stage in ["understanding", "ideation", "rollout", "judgment"]:
        if (results_subdir / f"{stage}.json").exists():
            stages_complete.append(stage)
    
    if not stages_complete:
        return None
    
    # Get score from judgment if available
    score = None
    judgment_file = results_subdir / "judgment.json"
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
    
    # Extract preview
    preview = extract_preview(results_subdir)
    
    return {
        "id": f"{behavior_name}_turns_{turn_count}",
        "behavior": behavior_name,
        "turn_count": turn_count,
        "timestamp": timestamp,
        "score": score,
        "stage": current_stage,
        "path": str(results_subdir),
        "preview": preview,
    }


def get_all_conversations() -> list[dict]:
    """Scan both results and bloom-results directories for all conversations."""
    conversations = []
    seen_ids = set()
    
    # First, scan the bloom-results directory (direct results from Bloom runs)
    if BLOOM_RESULTS_DIR.exists():
        for behavior_dir in BLOOM_RESULTS_DIR.iterdir():
            if not behavior_dir.is_dir():
                continue
            
            behavior_name = behavior_dir.name
            
            # For bloom-results, we don't have turn-based subdirs, so use default turn count
            # Check if there's actual data
            conv_data = get_conversation_data(behavior_dir, behavior_name, 0)
            if conv_data:
                # Override ID to indicate it's from bloom-results (no specific turn)
                conv_data["id"] = f"{behavior_name}_default"
                if conv_data["id"] not in seen_ids:
                    seen_ids.add(conv_data["id"])
                    conversations.append(conv_data)
    
    # Then, scan the results directory (SSH test runs with turns)
    if RESULTS_DIR.exists():
        for behavior_dir in RESULTS_DIR.iterdir():
            if not behavior_dir.is_dir():
                continue
            if behavior_dir.name in ["ssh_test_validation", "ssh_test_state.json"]:
                continue
            
            behavior_name = behavior_dir.name
            
            for turn_dir in behavior_dir.iterdir():
                if not turn_dir.is_dir() or not turn_dir.name.startswith("turns_"):
                    continue
                
                turn_count = int(turn_dir.name.replace("turns_", ""))
                results_subdir = turn_dir / "bloom-results" / behavior_name
                
                conv_data = get_conversation_data(results_subdir, behavior_name, turn_count)
                if conv_data and conv_data["id"] not in seen_ids:
                    seen_ids.add(conv_data["id"])
                    conversations.append(conv_data)
    
    # Sort by timestamp (newest first)
    conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return conversations


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    behavior: Optional[str] = Query(None, description="Filter by behavior name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all conversations with pagination."""
    conversations = get_all_conversations()
    
    # Apply filter
    if behavior:
        conversations = [c for c in conversations if c["behavior"] == behavior]
    
    # Apply pagination
    paginated = conversations[offset:offset + limit]
    
    return [
        ConversationSummary(
            id=c["id"],
            behavior=c["behavior"],
            turn_count=c["turn_count"],
            timestamp=c["timestamp"],
            score=c["score"],
            stage=c["stage"],
            preview=c.get("preview"),
        )
        for c in paginated
    ]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str):
    """Get full details for a specific conversation."""
    # Check if it's a default (bloom-results) conversation
    if conversation_id.endswith("_default"):
        behavior_name = conversation_id.replace("_default", "")
        turn_count = 0
        results_dir = BLOOM_RESULTS_DIR / behavior_name
    else:
        # Parse ID for turn-based results
        parts = conversation_id.rsplit("_turns_", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        behavior_name = parts[0]
        try:
            turn_count = int(parts[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid turn count in ID")
        
        # Find the conversation
        results_dir = RESULTS_DIR / behavior_name / f"turns_{turn_count}" / "bloom-results" / behavior_name
    
    if not results_dir.exists():
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
    
    # Transcript - try multiple sources
    transcript_file = results_dir / "transcript_v1r1.json"
    if transcript_file.exists():
        with open(transcript_file) as f:
            transcript_data = json.load(f)
            
            # Extract conversation messages
            if "conversation" in transcript_data:
                for msg in transcript_data["conversation"]:
                    transcript.append(ConversationMessage(
                        role=msg.get("role", "unknown"),
                        content=msg.get("content", ""),
                    ))
            elif "events" in transcript_data:
                for event in transcript_data["events"]:
                    if event.get("type") == "message":
                        transcript.append(ConversationMessage(
                            role=event.get("role", "unknown"),
                            content=event.get("content", ""),
                        ))
    
    # If no transcript found, try extracting from rollout.json
    if not transcript and rollout:
        try:
            rollouts_list = rollout.get("rollouts", [])
            if rollouts_list:
                # Get the first rollout's transcript
                rollout_transcript = rollouts_list[0].get("transcript", {})
                events = rollout_transcript.get("events", [])
                
                # First pass: collect all messages with their views
                all_messages = []
                for event in events:
                    if event.get("type") == "transcript_event":
                        edit = event.get("edit", {})
                        message = edit.get("message", {})
                        view = event.get("view", [])
                        
                        if message:
                            role = message.get("role", "unknown")
                            content = message.get("content", "")
                            
                            # Handle complex content (can be string or list of content blocks)
                            if isinstance(content, list):
                                text_parts = []
                                for block in content:
                                    if isinstance(block, dict):
                                        if block.get("type") == "text":
                                            text_parts.append(block.get("text", ""))
                                    elif isinstance(block, str):
                                        text_parts.append(block)
                                content = "\n".join(text_parts)
                            
                            all_messages.append({
                                "role": role,
                                "content": content,
                                "view": view,
                            })
                
                # Filter to show only target-facing messages (the actual conversation)
                # Target view shows: system prompt for target, user messages (from evaluator), assistant responses (from target)
                for msg in all_messages:
                    view = msg["view"]
                    content = msg["content"]
                    role = msg["role"]
                    
                    # Skip empty content
                    if not content or not content.strip():
                        continue
                    
                    # Only include messages visible to the target model
                    # This filters out the evaluator's meta-level setup
                    if "target" in view:
                        transcript.append(ConversationMessage(
                            role=role,
                            content=content,
                        ))
        except Exception as e:
            print(f"Error extracting transcript from rollout: {e}")
    
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

