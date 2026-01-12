# Bloom Documentation

Bloom is an automated behavioral evaluation framework for Large Language Models (LLMs). It generates evaluation suites that probe LLMs for specific behaviors like sycophancy, self-preservation, political bias, and more.

## Documentation Index

| Document | Description |
|----------|-------------|
| [QUICK_START.md](QUICK_START.md) | Get up and running quickly |
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | Architecture and design overview |
| [CONFIGURATION.md](CONFIGURATION.md) | Complete configuration reference |
| [PIPELINE_STAGES.md](PIPELINE_STAGES.md) | Detailed stage documentation |
| [API_REFERENCE.md](API_REFERENCE.md) | Python API reference |

## Quick Overview

### What Bloom Does

Given a "seed" configuration describing a target behavior, Bloom:

1. **Understands** the behavior through deep analysis
2. **Ideates** diverse evaluation scenarios
3. **Executes** conversations between evaluator and target models
4. **Judges** the transcripts for behavior presence

### Key Features

- **Procedural Generation**: Evaluations are generated, not hand-crafted
- **Two Modalities**: Pure conversation or simulated environment with tools
- **Multi-Model**: Separate evaluator, target, and judge models
- **Extended Thinking**: Support for reasoning models
- **W&B Integration**: Sweep-based parameter search and tracking
- **Concurrent Execution**: Parallel API calls for speed

### Basic Usage

```bash
# Initialize workspace
bloom init

# Configure API keys
source .env

# Run evaluation
bloom run bloom-data
```

### Pipeline Visualization

```
┌─────────────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│UNDERSTANDING│ ──► │ IDEATION │ ──► │ ROLLOUT │ ──► │ JUDGMENT │
└─────────────┘     └──────────┘     └─────────┘     └──────────┘
      │                  │                │               │
      ▼                  ▼                ▼               ▼
understanding.json  ideation.json   transcripts    judgment.json
```

### Available Behaviors

| Category | Behaviors |
|----------|-----------|
| Safety | `self-preservation`, `cyber-bio-chem-capabilities`, `prompt-injection-vulnerability` |
| Alignment | `sycophancy`, `delusion-sycophancy`, `political-bias`, `self-preferential-bias` |
| Deception | `reasoning-unfaithfulness`, `instructed-long-horizon-sabotage`, `research-sandbagging` |
| Quirks | `flattery`, `self-promotion`, `defer-to-users`, `emotional-bond`, `increasing-pep` |

### Model Roles

| Role | Function |
|------|----------|
| **Evaluator** | Generates scenarios, plays user, simulates environment |
| **Target** | The model being evaluated |
| **Judge** | Scores transcripts for behavior presence |

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/safety-research/bloom/issues)
- **Email**: isha.gpt@outlook.com

## Citation

```bibtex
@misc{bloom2025,
  title={Bloom: an open source tool for automated behavioral evaluations},
  author={Gupta, Isha and Fronsdal, Kai and Sheshadri, Abhay and Michala, Jonathan and Tay, Jacqueline and Wang, Rowan and Bowman, Samuel R. and Price, Sara},
  year={2025},
  url={https://github.com/safety-research/bloom},
}
```

