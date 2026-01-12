#!/usr/bin/env python3
"""
Minimal test script to validate the first SSH behavior works with Bloom pipeline.

This tests:
- "Emotional Breakdown" behavior from SSH Behaviors Taxonomy
- 4 conversation turns
- Gemini 3 Pro Preview for ideation
- Gemini 3 Flash Preview for rollout target
"""

import csv
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def parse_behavior_name(comment: str) -> str:
    """
    Convert behavior comment path to a slug name.
    e.g., "Distressed User>Acute Emotional Psychological Distress>Emotional Breakdown"
    -> "emotional-breakdown"
    """
    # Get the last part of the path
    parts = comment.split(">")
    name = parts[-1].strip()
    # Convert to lowercase slug
    slug = name.lower().replace(" ", "-").replace("/", "-").replace("_", "-")
    # Remove special characters
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Remove multiple consecutive hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def load_behaviors_from_csv(csv_path: Path) -> list[dict]:
    """Load behaviors from the SSH Behaviors Taxonomy CSV."""
    behaviors = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comment = row.get("Comments", "").strip()
            definition = row.get("Definition", "").strip()
            if comment and definition:
                behaviors.append({
                    "path": comment,
                    "name": parse_behavior_name(comment),
                    "definition": definition,
                })
    return behaviors


def create_test_config(behavior: dict, output_dir: Path, max_turns: int = 4) -> Path:
    """Create a seed.yaml config for testing a behavior."""
    config = {
        "behavior": {
            "name": behavior["name"],
            "examples": [],
        },
        "temperature": 1.0,
        "evaluator_reasoning_effort": "low",
        "target_reasoning_effort": "none",
        "max_concurrent": 5,
        "configurable_prompts": "default",
        "anonymous_target": False,
        "debug": True,
        "understanding": {
            "model": "gemini-3-pro-preview",
            "max_tokens": 2000,
        },
        "ideation": {
            "model": "gemini-3-pro-preview",
            "total_evals": 1,
            "diversity": 1.0,
            "max_tokens": 8000,
            "web_search": False,
        },
        "rollout": {
            "model": "gemini-3-pro-preview",
            "target": "gemini-3-flash-preview",
            "modality": "conversation",
            "max_turns": max_turns,
            "max_tokens": 4000,
            "no_user_mode": False,
            "selected_variations": None,
            "num_reps": 1,
        },
        "judgment": {
            "model": "gemini-3-pro-preview",
            "max_tokens": 6000,
            "num_samples": 1,
            "additional_qualities": ["unrealism", "evaluation-awareness"],
            "metajudgment_qualities": ["diversity"],
            "redaction_tags": None,
        },
    }
    
    config_path = output_dir / "seed.yaml"
    import yaml
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    return config_path


def add_behavior_to_json(behavior: dict, behaviors_json_path: Path) -> None:
    """Add the behavior definition to behaviors.json."""
    with open(behaviors_json_path, "r") as f:
        behaviors = json.load(f)
    
    # Add or update the behavior
    behaviors[behavior["name"]] = behavior["definition"]
    
    with open(behaviors_json_path, "w") as f:
        json.dump(behaviors, f, indent=4)


def run_test():
    """Run the first behavior test."""
    print("=" * 60)
    print("SSH Behavior Test - First Behavior Validation")
    print("=" * 60)
    
    # Paths
    bloom_dir = Path(__file__).parent.parent
    csv_path = bloom_dir / "docs" / "SSH Behaviors Taxonomy.csv"
    behaviors_json_path = bloom_dir / "src" / "bloom" / "data" / "behaviors.json"
    results_dir = bloom_dir / "results" / "ssh_test_validation"
    
    # Load behaviors
    print("\n1. Loading behaviors from CSV...")
    behaviors = load_behaviors_from_csv(csv_path)
    print(f"   Found {len(behaviors)} behaviors")
    
    if not behaviors:
        print("   ERROR: No behaviors found in CSV!")
        return False
    
    # Get first behavior
    first_behavior = behaviors[0]
    print(f"\n2. Testing first behavior:")
    print(f"   Path: {first_behavior['path']}")
    print(f"   Name: {first_behavior['name']}")
    print(f"   Definition: {first_behavior['definition'][:100]}...")
    
    # Add behavior to behaviors.json
    print("\n3. Adding behavior to behaviors.json...")
    add_behavior_to_json(first_behavior, behaviors_json_path)
    print("   Done")
    
    # Create output directory
    print("\n4. Creating output directory...")
    results_dir.mkdir(parents=True, exist_ok=True)
    print(f"   {results_dir}")
    
    # Create config
    print("\n5. Creating seed.yaml config...")
    config_path = create_test_config(first_behavior, results_dir, max_turns=4)
    print(f"   {config_path}")
    
    # Copy models.json to results dir (bloom expects bloom-models.json)
    models_json_src = bloom_dir / "src" / "bloom" / "data" / "models.json"
    models_json_dst = results_dir / "bloom-models.json"
    shutil.copy(models_json_src, models_json_dst)
    
    # Copy behaviors.json to results dir (bloom expects bloom-behaviors.json)
    behaviors_json_dst = results_dir / "bloom-behaviors.json"
    shutil.copy(behaviors_json_path, behaviors_json_dst)
    
    # Copy configurable prompts directory
    prompts_src = bloom_dir / "src" / "bloom" / "data" / "configurable_prompts"
    prompts_dst = results_dir / "bloom-configurable_prompts"
    if prompts_src.exists():
        if prompts_dst.exists():
            shutil.rmtree(prompts_dst)
        shutil.copytree(prompts_src, prompts_dst)
    
    # Run Bloom pipeline
    print("\n6. Running Bloom pipeline...")
    print("   This may take a few minutes...")
    
    # Import and run
    from bloom.core import run_pipeline, set_debug_mode
    from bloom.utils import load_config
    
    try:
        # Load config properly
        config = load_config(config_path, config_dir=results_dir)
        
        # Enable debug mode
        set_debug_mode(True)
        
        # Run pipeline
        results = run_pipeline(config, config_dir=results_dir)
        
        print("\n" + "=" * 60)
        print("TEST PASSED!")
        print("=" * 60)
        print(f"\nResults saved to: {results_dir}")
        
        # Print summary
        if results and isinstance(results, dict):
            print("\nPipeline Results:")
            for stage, data in results.items():
                if isinstance(data, dict):
                    print(f"  - {stage}: {len(data)} items")
                elif isinstance(data, list):
                    print(f"  - {stage}: {len(data)} items")
                else:
                    print(f"  - {stage}: completed")
        
        return True
        
    except Exception as e:
        print(f"\n{'=' * 60}")
        print("TEST FAILED!")
        print("=" * 60)
        print(f"\nError: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    
    success = run_test()
    sys.exit(0 if success else 1)

