# Bloom API Reference

This document provides a reference for using Bloom programmatically as a Python library.

## Installation

```python
pip install git+https://github.com/safety-research/bloom.git
```

## Core Functions

### Running the Pipeline

```python
from bloom.core import run_pipeline
from bloom.utils import load_config

# Load configuration
config = load_config("bloom-data/seed.yaml", config_dir="bloom-data")

# Run full pipeline
result = run_pipeline(config=config, config_dir="bloom-data")
# Returns: judgment results dict or True/False
```

### Running Individual Stages

```python
import asyncio
from bloom.stages.step1_understanding import run_understanding
from bloom.stages.step2_ideation import run_ideation
from bloom.stages.step3_rollout import run_rollout
from bloom.stages.step4_judgment import run_judgment
from bloom.utils import load_config

config = load_config("bloom-data/seed.yaml", config_dir="bloom-data")

# Stage 1: Understanding
run_understanding(config=config, config_dir="bloom-data")

# Stage 2: Ideation
run_ideation(config=config, config_dir="bloom-data")

# Stage 3: Rollout (async)
rollout_results = asyncio.run(run_rollout(config=config, config_dir="bloom-data"))

# Stage 4: Judgment (async)
judgment_results = asyncio.run(run_judgment(config=config, config_dir="bloom-data"))
```

---

## Configuration Module (`bloom.utils`)

### `load_config(config_path, config_dir=None)`
Load configuration from YAML file.

```python
from bloom.utils import load_config

config = load_config("bloom-data/seed.yaml", config_dir="bloom-data")
```

**Parameters:**
- `config_path` (str | Path): Path to the YAML configuration file
- `config_dir` (str | Path | None): Path to bloom config directory

**Returns:** Dict[str, Any] - Configuration dictionary

---

### `load_behaviors(config=None, behaviors_path=None)`
Load behavior definitions.

```python
from bloom.utils import load_behaviors

behaviors = load_behaviors(config=config)
# Returns: {"sycophancy": "Sycophancy is...", ...}
```

---

### `load_example(example_name, config=None)`
Load an example transcript file.

```python
from bloom.utils import load_example

example = load_example("sycophancy-sonnet4", config=config)
# Returns: dict with conversation data
```

---

### `get_model_id(model_name_or_id, config_dir=None)`
Convert short model name to LiteLLM ID.

```python
from bloom.utils import get_model_id

# From short name
model_id = get_model_id("claude-sonnet-4", config_dir)
# Returns: "anthropic/claude-sonnet-4-20250514"

# Direct ID passes through
model_id = get_model_id("anthropic/claude-sonnet-4-20250514")
# Returns: "anthropic/claude-sonnet-4-20250514"
```

---

### `litellm_chat(...)`
Simplified LiteLLM chat completion call with retry logic.

```python
from bloom.utils import litellm_chat

response = litellm_chat(
    model_id="anthropic/claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello!"}],
    system_prompt="You are a helpful assistant.",
    max_tokens=4000,
    reasoning_effort="high",  # "none", "low", "medium", "high"
    temperature=1.0,
    tools=None,  # Optional list of tool definitions
    tool_choice="auto"  # "auto", "none", "required"
)
```

**Parameters:**
- `model_id` (str): LiteLLM model identifier
- `messages` (list): List of message dicts
- `system_prompt` (str | None): Optional system prompt
- `max_tokens` (int): Maximum response tokens
- `reasoning_effort` (str): Extended thinking level
- `temperature` (float | None): Sampling temperature
- `tools` (list | None): Tool definitions for function calling
- `tool_choice` (str): How to handle tool calls

**Returns:** LiteLLM ModelResponse object

---

### `parse_message(response)`
Parse LiteLLM response and extract key fields.

```python
from bloom.utils import parse_message

parsed = parse_message(response)
# Returns:
# {
#     "content": "The response text...",
#     "reasoning": "The thinking content...",
#     "tool_calls": [...] or None,
#     "cleaned_message": {...}  # For message history
# }
```

---

## Orchestrator Classes

### ConversationOrchestrator

For pure text conversations without tools.

```python
from bloom.orchestrators.ConversationOrchestrator import ConversationOrchestrator
from bloom.utils import litellm_chat

orchestrator = ConversationOrchestrator.setup(
    client=litellm_chat,
    evaluator_model_id="anthropic/claude-opus-4-1-20250805",
    target_model_id="anthropic/claude-sonnet-4-20250514",
    evaluator_system_prompt="You are an evaluation agent...",
    conversation_rollout_prompt="Generate a system prompt for...",
    target_sysprompt_prefix="",  # Optional prefix for target
    max_turns=5,
    evaluator_reasoning_effort="high",
    target_reasoning_effort="medium",
    evaluator_max_tokens=4000,
    target_max_tokens=4000,
    evaluator_temperature=1.0,
    target_temperature=1.0,
    no_user_mode=False,
    target_kickoff_prefix="",
    generate_kickoff_additional="",
    rollout_label="my-rollout-1"
)

# Run the conversation
transcript = orchestrator.run()
# Returns: dict with transcript in v3.0 format
```

---

### SimEnvOrchestrator

For conversations with tool/function calling.

```python
from bloom.orchestrators.SimEnvOrchestrator import SimEnvOrchestrator
from bloom.utils import litellm_chat

orchestrator = SimEnvOrchestrator.setup(
    client=litellm_chat,
    evaluator_model_id="anthropic/claude-opus-4-1-20250805",
    target_model_id="anthropic/claude-sonnet-4-20250514",
    evaluator_system_prompt="You are an evaluation agent...",
    conversation_rollout_prompt="Generate a system prompt for...",
    target_sysprompt_prefix="",
    max_turns=8,
    example_name="my-example",
    max_tokens=4000,
    temperature=1.0,
    evaluator_reasoning_effort="high",
    target_reasoning_effort="medium",
    no_user_mode=False,
    predefined_tools=["<tool_signature>...</tool_signature>"],
    target_kickoff_prefix="",
    generate_kickoff_additional="",
    rollout_label="my-rollout-1"
)

# Run the conversation
transcript = orchestrator.run()
```

#### Tool Signature Format

Tools are specified as XML strings:

```xml
<tool_signature>
  <name>send_email</name>
  <description>Send an email to a recipient</description>
  <parameters>
    <parameter>
      <name>to</name>
      <type>string</type>
      <description>Email address</description>
    </parameter>
    <parameter>
      <name>subject</name>
      <type>string</type>
      <description>Subject line</description>
    </parameter>
    <parameter>
      <name>body</name>
      <type>string</type>
      <description>Email body</description>
    </parameter>
  </parameters>
</tool_signature>
```

---

## Transcript Utilities

### `load_transcript(path)`
Load a transcript file.

```python
from bloom.transcript_utils import load_transcript
from pathlib import Path

transcript = load_transcript(Path("bloom-results/behavior/transcript_v1r1.json"))
```

---

### `format_transcript_for_judge(events, redaction_tags=None)`
Format transcript events for the judge.

```python
from bloom.transcript_utils import format_transcript_for_judge

formatted = format_transcript_for_judge(
    transcript["events"],
    redaction_tags="SPECIAL_INSTRUCTIONS"  # Optional
)
```

---

### `append_judge_output_to_transcript(path, judge_output)`
Append judgment results to transcript file.

```python
from bloom.transcript_utils import append_judge_output_to_transcript
from pathlib import Path

append_judge_output_to_transcript(
    Path("bloom-results/behavior/transcript_v1r1.json"),
    {
        "summary": "...",
        "scores": {"behavior_presence": 7},
        "justification": "..."
    }
)
```

---

## Result Loading Functions

### `load_understanding_results(example_name)`
```python
from bloom.utils import load_understanding_results

results = load_understanding_results("self-preservation")
# Returns understanding.json contents
```

### `load_ideation_results(example_name)`
```python
from bloom.utils import load_ideation_results

results = load_ideation_results("self-preservation")
# Returns ideation.json contents (includes variations)
```

---

## Debug Mode

Enable detailed output:

```python
from bloom.core import set_debug_mode

set_debug_mode(True)

# Now all debug_print() calls will output
```

---

## W&B Integration

### Running as Sweep Agent

```python
from bloom.core import run_sweep_pipeline
from bloom.utils import create_config_from_wandb_params
import wandb

wandb.init()
wandb_params = dict(wandb.config)

config = create_config_from_wandb_params(wandb_params)
success = run_sweep_pipeline(wandb_params, config)
```

### Creating Config from W&B Params

```python
from bloom.utils import create_config_from_wandb_params

wandb_params = {
    "behavior.name": "sycophancy",
    "ideation.total_evals": 10,
    "rollout.target": "gpt-4o",
    # ... more params
}

config = create_config_from_wandb_params(wandb_params)
```

---

## Custom Behaviors

### Adding a New Behavior

1. Add to `behaviors.json`:

```json
{
    "my-behavior": "Description of what this behavior is and why it matters..."
}
```

2. Optionally add example transcripts to `behaviors/examples/`:

```json
{
    "conversation": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
}
```

3. Reference in config:

```yaml
behavior:
  name: "my-behavior"
  examples: ["my-behavior-example1"]
```

---

## Error Handling

Most functions raise exceptions on failure. Wrap in try/except for graceful handling:

```python
from bloom.core import run_pipeline
from bloom.utils import load_config

try:
    config = load_config("bloom-data/seed.yaml")
    result = run_pipeline(config)
    if not result:
        print("Pipeline failed")
except FileNotFoundError as e:
    print(f"Config not found: {e}")
except ValueError as e:
    print(f"Invalid config: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Type Hints

Bloom uses type hints throughout. Key types:

```python
from typing import Dict, List, Any, Optional
from pathlib import Path

Config = Dict[str, Any]
Messages = List[Dict[str, str]]
TranscriptEvent = Dict[str, Any]
```

