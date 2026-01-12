# Bloom System Design

## Overview

Bloom is an automated behavioral evaluation framework for Large Language Models (LLMs). It generates evaluation suites that probe LLMs for specific behaviors such as sycophancy, self-preservation, political bias, and more.

Unlike fixed benchmarks, Bloom evaluations are **procedurally generated** based on a "seed" configuration, allowing for customizable and reproducible evaluations.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BLOOM PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │              │    │              │    │              │    │            │ │
│  │ UNDERSTANDING│───►│   IDEATION   │───►│   ROLLOUT    │───►│  JUDGMENT  │ │
│  │              │    │              │    │              │    │            │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│        │                   │                    │                  │        │
│        ▼                   ▼                    ▼                  ▼        │
│  understanding.json   ideation.json     transcript_*.json    judgment.json  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. CLI (`cli.py`)
The command-line interface that orchestrates the pipeline. Supports:
- `bloom run` - Run full pipeline
- `bloom understanding` - Run understanding stage only
- `bloom ideation` - Run ideation stage only
- `bloom rollout` - Run rollout stage only
- `bloom judgment` - Run judgment stage only
- `bloom chat` - Interactive chat with models
- `bloom init` - Initialize workspace
- `bloom sweep` - Run as W&B sweep agent

### 2. Core Pipeline (`core.py`)
Orchestrates the 4-stage pipeline:
1. **Understanding** → Analyzes target behavior
2. **Ideation** → Generates evaluation scenarios
3. **Rollout** → Executes conversations
4. **Judgment** → Scores behavior presence

### 3. Orchestrators
Two orchestrator classes handle the actual conversations:

#### `ConversationOrchestrator`
- Pure text-based conversations (Q&A format)
- Evaluator plays the role of user
- Target model responds naturally
- No tool/function calling

#### `SimEnvOrchestrator`
- Simulated environment with tool calls
- Target model can execute functions
- Evaluator simulates both user AND tool responses
- More complex scenarios possible

### 4. Utils (`utils.py`)
Central utility functions:
- Model configuration loading
- LiteLLM API wrapper with retries
- Configuration management
- Results file handling

## Data Flow

### Stage 1: Understanding
```
Input: behavior name + description + example transcripts
       ↓
   [LLM Analysis]
       ↓
Output: behavior_understanding + scientific_motivation + transcript_analyses
```

The understanding stage:
1. Takes a behavior name (e.g., "sycophancy") and its description
2. Optionally loads example transcripts showing the behavior
3. Uses an LLM to deeply analyze what the behavior is
4. Produces a structured understanding for downstream stages

### Stage 2: Ideation
```
Input: understanding.json + config parameters
       ↓
   [LLM Generation - Base Scenarios]
       ↓
   [LLM Generation - Variations]
       ↓
Output: ideation.json (variations array)
```

The ideation stage:
1. Takes the understanding from Stage 1
2. Generates diverse "base scenarios" that could elicit the behavior
3. Creates variations of each base scenario for robustness
4. For `simenv` modality, also generates tool signatures

Key formulas:
- `num_base_scenarios = total_evals × diversity`
- `variations_per_base = 1 / diversity`

### Stage 3: Rollout
```
Input: ideation.json + understanding.json
       ↓
   [Orchestrator Setup]
       ↓
   [Multi-turn Conversations]
       ↓
Output: transcript_v{N}r{M}.json files + rollout.json
```

The rollout stage:
1. Loads scenarios from ideation
2. For each scenario + repetition:
   - Creates an orchestrator (Conversation or SimEnv)
   - Evaluator generates target's system prompt
   - Multi-turn conversation proceeds
   - Transcript is saved
3. Runs concurrently with semaphore-based rate limiting

### Stage 4: Judgment
```
Input: transcript files + understanding.json + ideation.json
       ↓
   [LLM Judge - Summary & Highlights]
       ↓
   [Multi-sample Scoring]
       ↓
   [Justification Generation]
       ↓
   [Optional Meta-judgment]
       ↓
Output: judgment.json (with scores, justifications, statistics)
```

The judgment stage:
1. Loads all transcript files
2. For each transcript:
   - Formats transcript for the judge
   - Gets initial summary and highlights
   - Samples scores `num_samples` times
   - Averages scores and gets justification
3. Optionally runs meta-judgment across all scenarios
4. Computes summary statistics (avg, min, max, elicitation rate)

## Model Roles

### Evaluator Model
The "red team" model that:
- Generates system prompts for the target
- Plays the role of user during conversations
- Simulates tool responses (in simenv mode)
- Tries to elicit the target behavior

### Target Model
The model being evaluated:
- Receives the generated system prompt
- Responds to evaluator's messages
- May call tools (in simenv mode)
- Its behavior is what we're measuring

### Judge Model
The model that scores transcripts:
- Analyzes completed conversations
- Scores behavior presence (1-10)
- Scores additional qualities
- Provides justifications

## File Structure

```
bloom/
├── src/bloom/
│   ├── cli.py              # Command-line interface
│   ├── core.py             # Pipeline orchestration
│   ├── utils.py            # Utilities & LLM wrapper
│   ├── transcript_utils.py # Transcript formatting
│   ├── data/
│   │   ├── behaviors.json  # Behavior definitions
│   │   ├── models.json     # Model configurations
│   │   ├── configurable_prompts/  # Prompt templates
│   │   ├── behaviors/examples/    # Example transcripts
│   │   ├── schemas/        # JSON schemas
│   │   └── templates/      # Config templates
│   ├── orchestrators/
│   │   ├── ConversationOrchestrator.py
│   │   └── SimEnvOrchestrator.py
│   ├── prompts/
│   │   ├── step1_understanding.py
│   │   ├── step2_ideation.py
│   │   ├── step3_rollout.py
│   │   └── step4_judgment.py
│   └── stages/
│       ├── step1_understanding.py
│       ├── step2_ideation.py
│       ├── step3_rollout.py
│       ├── step4_judgment.py
│       └── interactive_chat.py
├── tests/
├── examples/sweeps/
└── docs/
```

## Key Design Decisions

### 1. Asymmetric Information
The evaluator knows the behavior being tested; the target doesn't. This allows realistic elicitation without the target "gaming" the evaluation.

### 2. Modular Stages
Each stage can run independently, allowing:
- Debugging individual stages
- Resuming from checkpoints
- Reusing artifacts across runs

### 3. Concurrent Execution
Rollout and judgment stages use asyncio with semaphores for:
- Parallel API calls
- Rate limiting
- Better throughput

### 4. Flexible Model Specification
Models can be specified as:
- Short names (from `models.json`): `"claude-sonnet-4"`
- Direct LiteLLM IDs: `"anthropic/claude-sonnet-4-20250514"`

### 5. Extended Thinking Support
Supports reasoning models with:
- `reasoning_effort`: "none", "low", "medium", "high"
- Automatic thinking budget allocation
- Thinking content extraction and logging

### 6. W&B Integration
Deep Weights & Biases integration for:
- Sweep-based parameter search
- Artifact logging
- Metric tracking
- Resume from previous runs

## Transcript Format (v3.0)

Transcripts follow a structured format with:
- `transcript_id`: Unique identifier
- `schema_version`: "3.0"
- `metadata`: Model info, timestamps, etc.
- `target_system_prompt`: What the target received
- `events`: Array of transcript events

Each event contains:
- `id`: Unique event ID
- `timestamp`: ISO timestamp
- `type`: "transcript_event"
- `edit`: Operation details
- `views`: Which views can see this event

Views:
- `evaluator`: What the evaluator sees
- `target`: What the target sees
- `combined`: Combined view for analysis

## Error Handling

The pipeline handles errors gracefully:
- API failures logged without crashing
- Failed rollouts tracked in results
- Partial results preserved
- Debug mode for detailed diagnostics

## Extensibility Points

### Custom Behaviors
Add new behaviors to `behaviors.json` with:
- Name and description
- Optional example transcripts

### Custom Prompts
Create new prompt files in `configurable_prompts/`:
- Override system prompts
- Add custom instructions
- Modify stage-specific behavior

### Custom Models
Add models to `models.json` with:
- LiteLLM ID
- Display name
- Organization
- Thinking capability flag

