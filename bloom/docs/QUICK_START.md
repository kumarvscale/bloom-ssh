# Bloom Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/safety-research/bloom.git
cd bloom

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"
```

## Setup

### 1. Initialize Workspace

```bash
bloom init
```

This creates:
- `bloom-data/seed.yaml` - Main configuration file
- `bloom-data/models.json` - Model definitions
- `bloom-data/behaviors.json` - Behavior definitions
- `.env` - API keys file

### 2. Configure API Keys

Edit `.env` and add your API keys:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
# Add others as needed
```

Load them:

```bash
source .env
```

### 3. Configure Evaluation

Edit `bloom-data/seed.yaml`:

```yaml
behavior:
  name: "sycophancy"  # Behavior to test
  examples: []        # Or list example files

ideation:
  total_evals: 5      # Number of scenarios

rollout:
  target: "gpt-4o"    # Model to evaluate
  max_turns: 3        # Conversation length
```

## Running Evaluations

### Full Pipeline

```bash
bloom run bloom-data
```

### Individual Stages

```bash
bloom understanding bloom-data
bloom ideation bloom-data
bloom rollout bloom-data
bloom judgment bloom-data
```

### With Debug Output

```bash
bloom run bloom-data --debug
```

## Results

Results are saved to `bloom-results/{behavior_name}/`:

- `understanding.json` - Behavior analysis
- `ideation.json` - Generated scenarios
- `transcript_v{N}r{M}.json` - Conversation transcripts
- `rollout.json` - Rollout summary
- `judgment.json` - Final scores and statistics

### View Results

Use the Bloom Viewer:

```bash
npx @isha-gpt/bloom-viewer --port 8080 --dir ./bloom-results
```

## Quick Configuration Examples

### Testing Sycophancy (Conversation Mode)

```yaml
behavior:
  name: "sycophancy"
  examples: []

understanding:
  model: "claude-sonnet-4"

ideation:
  model: "claude-sonnet-4"
  total_evals: 10
  diversity: 0.5

rollout:
  model: "claude-sonnet-4"
  target: "gpt-4o"
  modality: "conversation"
  max_turns: 5

judgment:
  model: "claude-sonnet-4"
```

### Testing Tool-Based Behavior (SimEnv Mode)

```yaml
behavior:
  name: "self-preservation"
  examples: []

rollout:
  model: "claude-opus-4.1"
  target: "claude-sonnet-4"
  modality: "simenv"  # Enable tool calls
  max_turns: 8
  no_user_mode: false
```

### Fast Debugging Run

```yaml
behavior:
  name: "flattery"
  examples: []

debug: true

ideation:
  model: "claude-sonnet-4"
  total_evals: 2
  diversity: 1.0

rollout:
  model: "claude-sonnet-4"
  target: "gpt-4o-mini"
  modality: "conversation"
  max_turns: 2
  num_reps: 1

judgment:
  model: "claude-sonnet-4"
  num_samples: 1
```

## Interactive Chat

Test models interactively:

```bash
bloom chat \
  --system-prompt "You are a helpful assistant" \
  --model claude-sonnet-4 \
  --output-dir bloom-results/manual
```

## Common Issues

### Missing API Keys

```
❌ MISSING API KEYS
ANTHROPIC_API_KEY is required for:
  - Claude Sonnet 4 (claude-sonnet-4)
```

**Solution:** Add the missing key to `.env` and run `source .env`

### Model Not Found

```
ValueError: Model 'my-model' not found in models.json
```

**Solution:** Either:
1. Add the model to `bloom-data/models.json`
2. Use direct LiteLLM ID: `"anthropic/claude-sonnet-4-20250514"`

### Token Limits

If ideation fails with token limit errors:

1. Reduce `ideation.total_evals`
2. Increase `ideation.diversity` (fewer scenarios per batch)
3. Use a model with higher output limits

## Next Steps

- Read [CONFIGURATION.md](CONFIGURATION.md) for all parameters
- Read [PIPELINE_STAGES.md](PIPELINE_STAGES.md) for stage details
- Read [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for architecture overview
- Check `examples/sweeps/` for W&B sweep configurations

