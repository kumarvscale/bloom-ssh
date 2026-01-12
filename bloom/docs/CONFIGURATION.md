# Bloom Configuration Reference

This document provides a complete reference for all configurable parameters in Bloom's `seed.yaml` configuration file.

## Configuration File Structure

The configuration is organized into sections:
1. **Behavior Configuration** - What behavior to evaluate
2. **Global Parameters** - Settings that apply across stages
3. **Resume Parameters** - For continuing interrupted runs
4. **Understanding Stage** - Behavior analysis settings
5. **Ideation Stage** - Scenario generation settings
6. **Rollout Stage** - Conversation execution settings
7. **Judgment Stage** - Transcript scoring settings

---

## Behavior Configuration

```yaml
behavior:
  name: "self-preferential-bias"
  examples: []
```

### `behavior.name`
**Type:** `string`  
**Required:** Yes

The target behavior to evaluate. Must match a key in `behaviors.json`.

**Available behaviors:**
| Behavior | Description |
|----------|-------------|
| `self-preservation` | Tendency to resist shutdown or modification |
| `delusion-sycophancy` | Validating user's fantastical or psychotic beliefs |
| `instructed-long-horizon-sabotage` | Ability to perform covert harmful actions |
| `reasoning-unfaithfulness` | Reasoning that doesn't match actions |
| `prompt-injection-vulnerability` | Susceptibility to prompt injection attacks |
| `political-bias` | Departing from neutral political stance |
| `cyber-bio-chem-capabilities` | Demonstrating dangerous technical capabilities |
| `self-preferential-bias` | Favoring itself when acting as judge |
| `flattery` | Always flattering the user |
| `self-promotion` | Subtle bias toward self-promotion |
| `defer-to-users` | Deferring even when users are wrong |
| `emotional-bond` | Steering conversations to create attachment |
| `research-sandbagging` | Writing worse code for AI safety tasks |

### `behavior.examples`
**Type:** `list[string]`  
**Default:** `[]`

List of example transcript files (without `.json` extension) from `behaviors/examples/` directory.

**Examples:**
```yaml
examples: []  # Zero-shot generation
examples: ["sycophancy-sonnet4"]  # One example
examples: ["example1", "example2", "example3"]  # Multiple examples
```

---

## Global Parameters

```yaml
temperature: 1.0
evaluator_reasoning_effort: "low"
target_reasoning_effort: "medium"
max_concurrent: 15
configurable_prompts: "default"
anonymous_target: false
debug: false
```

### `temperature`
**Type:** `float`  
**Default:** `1.0`  
**Range:** `0.0` - `2.0`

Controls randomness in model outputs. **Must be `1.0` when using extended thinking** (reasoning_effort ≠ "none").

### `evaluator_reasoning_effort`
**Type:** `string`  
**Default:** `"high"`  
**Options:** `"none"`, `"low"`, `"medium"`, `"high"`

Thinking token budget for evaluator models across all stages.

| Level | Token Budget |
|-------|--------------|
| `none` | 0 |
| `low` | 1,024 |
| `medium` | 2,048 |
| `high` | 4,096 |

### `target_reasoning_effort`
**Type:** `string`  
**Default:** `"medium"`  
**Options:** `"none"`, `"low"`, `"medium"`, `"high"`

Thinking token budget for target models during rollout.

### `max_concurrent`
**Type:** `integer`  
**Default:** `15`

Maximum concurrent API calls. Higher = faster but more resource-intensive.

### `configurable_prompts`
**Type:** `string`  
**Default:** `"default"`

Name of prompts file to load from `configurable_prompts/` directory.

**Available files:**
- `default` - Standard prompts
- `sandbag` - For sandbagging evaluations
- `self-preferential-bias` - For self-preference evaluations
- `web-search` - With web search enabled

### `anonymous_target`
**Type:** `boolean`  
**Default:** `false`

When `true`, the target model's identity is hidden from all agents. Useful for evaluating identity-oriented behaviors like self-preferential bias.

### `debug`
**Type:** `boolean`  
**Default:** `false`

Enable detailed debug output showing API calls, stage transitions, and intermediate results.

---

## Resume Parameters

```yaml
# resume: "wandb_run_id_here"
# resume_stage: "rollout"
```

### `resume`
**Type:** `string`  
**Optional**

W&B run ID to resume from. Found in W&B dashboard.

### `resume_stage`
**Type:** `string`  
**Optional**  
**Options:** `"understanding"`, `"ideation"`, `"rollout"`, `"judgment"`

Stage to resume from. Artifacts from prior stages are loaded from the specified W&B run.

---

## Understanding Stage

```yaml
understanding:
  model: "claude-opus-4.1"
  max_tokens: 2000
```

### `understanding.model`
**Type:** `string`  
**Default:** `"deepseek-r1"`

Model for behavior analysis. Recommend strong reasoning models.

**Format options:**
- Short name: `"claude-opus-4.1"`
- Direct LiteLLM ID: `"anthropic/claude-opus-4-1-20250805"`

### `understanding.max_tokens`
**Type:** `integer`  
**Default:** `4000`

Maximum tokens for understanding output.

---

## Ideation Stage

```yaml
ideation:
  model: "claude-opus-4.1"
  total_evals: 3
  diversity: 1.0
  max_tokens: 12000
  web_search: false
```

### `ideation.model`
**Type:** `string`  
**Default:** `"gpt-4.1"`

Model for generating evaluation scenarios.

### `ideation.total_evals`
**Type:** `integer`  
**Default:** `10`

Total number of evaluation scenarios to generate.

### `ideation.diversity`
**Type:** `float`  
**Default:** `0.2`  
**Range:** `0.0` - `1.0`

Controls scenario diversity:
- **Higher** = more diverse base scenarios with fewer variations each
- **Lower** = fewer base scenarios with more variations each

**Formulas:**
```
num_base_scenarios = total_evals × diversity
variations_per_base = 1 / diversity
```

**Examples:**
| total_evals | diversity | base_scenarios | variations_per_base |
|-------------|-----------|----------------|---------------------|
| 10 | 0.2 | 2 | 5 |
| 10 | 0.5 | 5 | 2 |
| 10 | 1.0 | 10 | 1 |

### `ideation.max_tokens`
**Type:** `integer`  
**Default:** `4000`

Maximum tokens for ideation output. Budget approximately:
- **800 tokens** per conversational scenario
- **1200 tokens** per simenv scenario (includes tool signatures)

### `ideation.web_search`
**Type:** `boolean`  
**Default:** `false`

Enable web search during scenario generation. Helps ground scenarios in real-world context.

> **Note:** Web search and extended thinking are incompatible. If `web_search: true`, reasoning_effort is automatically disabled for ideation.

---

## Rollout Stage

```yaml
rollout:
  model: "claude-opus-4.1"
  target: "claude-sonnet-4"
  modality: "conversation"
  max_turns: 2
  max_tokens: 4000
  no_user_mode: false
  selected_variations: null
  num_reps: 1
```

### `rollout.model`
**Type:** `string`  
**Default:** `"gemini-2.5-flash"`

Evaluator (red team) model that plays the user role.

### `rollout.target`
**Type:** `string`  
**Default:** `"gpt-4o"`

Target model being evaluated.

### `rollout.modality`
**Type:** `string`  
**Default:** `"simenv"`  
**Options:** `"conversation"`, `"simenv"`

| Modality | Description |
|----------|-------------|
| `conversation` | Pure text Q&A format, no tool calls |
| `simenv` | Simulated environment with function/tool calling |

### `rollout.max_turns`
**Type:** `integer`  
**Default:** `5`

Maximum conversation length in turns. One turn = one user message + one assistant response.

### `rollout.max_tokens`
**Type:** `integer`  
**Default:** `4000`

Maximum tokens per message for both evaluator and target.

### `rollout.no_user_mode`
**Type:** `boolean`  
**Default:** `false`

When `true` (simenv only), target must always respond with tool calls rather than text. Evaluator only simulates tool responses, not user messages.

### `rollout.selected_variations`
**Type:** `list[integer] | null`  
**Default:** `null`

Which variation indices to evaluate (1-indexed). If `null`, all variations are evaluated.

**Example:**
```yaml
selected_variations: [1, 3, 5]  # Only test variations 1, 3, and 5
selected_variations: null       # Test all variations
```

### `rollout.num_reps`
**Type:** `integer`  
**Default:** `1`

Number of repetitions for each variation. Higher = more statistical robustness but longer runtime.

---

## Judgment Stage

```yaml
judgment:
  model: "claude-opus-4.1"
  max_tokens: 6000
  num_samples: 1
  additional_qualities: ["unrealism", "evaluation-awareness", "evaluation-invalidity"]
  metajudgment_qualities: ["diversity"]
  redaction_tags: null
```

### `judgment.model`
**Type:** `string`  
**Default:** `"gpt-5-mini"`

Judge model for scoring transcripts.

### `judgment.max_tokens`
**Type:** `integer`  
**Default:** `4000`

Maximum tokens for judgment output.

### `judgment.num_samples`
**Type:** `integer`  
**Default:** `1`

Number of times to sample scores for each transcript. Higher = more robust through independent judgments.

### `judgment.additional_qualities`
**Type:** `list[string]`  
**Default:** `["unrealism", "elicitation-difficulty", "evaluation-awareness"]`

Additional quality dimensions to score (each 1-10):

| Quality | Description |
|---------|-------------|
| `unrealism` | How unrealistic/contrived the scenario is |
| `elicitation-difficulty` | How hard the evaluator had to work |
| `evaluation-awareness` | Whether target seemed aware of evaluation |
| `evaluation-invalidity` | Whether the setup was valid for measuring the behavior |
| `stealth` | Whether target actions would evade oversight |

### `judgment.metajudgment_qualities`
**Type:** `list[string]`  
**Default:** `["diversity"]`

Meta-qualities evaluated across ALL scenarios (cross-scenario analysis):

| Quality | Description |
|---------|-------------|
| `diversity` | Variety across all scenarios |

### `judgment.redaction_tags`
**Type:** `string | null`  
**Default:** `null`

Tag name for redacting transcript content from judge. Content between `<TAG>...</TAG>` will be removed before showing to judge.

**Example:**
```yaml
redaction_tags: "SPECIAL_INSTRUCTIONS"
# Content between <SPECIAL_INSTRUCTIONS> and </SPECIAL_INSTRUCTIONS> is hidden from judge
```

---

## Model Specification

Models can be specified in two formats:

### 1. Short Name (from models.json)
```yaml
model: "claude-sonnet-4"
```

### 2. Direct LiteLLM ID
```yaml
model: "anthropic/claude-sonnet-4-20250514"
```

Direct IDs bypass `models.json` lookup and support any LiteLLM-compatible model.

---

## Environment Variables

Required API keys depend on which models you use:

| Provider | Environment Variable(s) |
|----------|------------------------|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |

Set these in your `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

---

## Example Configurations

### Minimal Configuration
```yaml
behavior:
  name: "sycophancy"
  examples: []

understanding:
  model: "claude-sonnet-4"

ideation:
  model: "claude-sonnet-4"
  total_evals: 5

rollout:
  model: "claude-sonnet-4"
  target: "gpt-4o"
  modality: "conversation"
  max_turns: 3

judgment:
  model: "claude-sonnet-4"
```

### High-Quality Evaluation
```yaml
behavior:
  name: "self-preservation"
  examples: ["self-preservation-example1"]

temperature: 1.0
evaluator_reasoning_effort: "high"
target_reasoning_effort: "medium"
max_concurrent: 10
debug: false

understanding:
  model: "claude-opus-4.1"
  max_tokens: 4000

ideation:
  model: "claude-opus-4.1"
  total_evals: 20
  diversity: 0.5
  max_tokens: 20000

rollout:
  model: "claude-opus-4.1"
  target: "gpt-4o"
  modality: "simenv"
  max_turns: 8
  max_tokens: 4000
  num_reps: 3

judgment:
  model: "claude-opus-4.1"
  max_tokens: 6000
  num_samples: 3
  additional_qualities: ["unrealism", "elicitation-difficulty", "evaluation-awareness"]
  metajudgment_qualities: ["diversity"]
```

### W&B Sweep Resume
```yaml
behavior:
  name: "political-bias"
  examples: []

resume: "abc123xyz"
resume_stage: "rollout"

# ... rest of config
```

