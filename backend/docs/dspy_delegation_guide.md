# DSPy Delegation Optimization Guide

## Overview

DSPy enables **automatic prompt optimization** through programming instead of manual prompt engineering. This guide explains how to use DSPy for delegation decisions.

## Why DSPy?

**Manual Prompting (Current):**
- ❌ Requires manual tuning
- ❌ Brittle across LLM changes
- ❌ No metrics or improvement
- ❌ Hard to maintain

**DSPy (Optimized):**
- ✅ Automatic optimization from examples
- ✅ LM-agnostic (works across models)
- ✅ Metrics-driven improvement
- ✅ Composable and maintainable

## Architecture

```
Training Examples → DSPy Optimizer → Optimized Module → Production
```

### Components

1. **Signatures** - Define input/output behavior
2. **Modules** - Composable LM components
3. **Optimizers** - Improve prompts from examples
4. **Metrics** - Measure quality

## Quick Start

### 1. Train Optimized Module

```bash
python backend/scripts/optimize_delegation_prompts.py
```

**Output:**
```
🚀 DSPy Delegation Prompt Optimization
============================================================

1. Configuring DSPy with GPT-4...
2. Testing base (unoptimized) module...
   Base decision: parallel
   Confidence: 0.85
   
3. Evaluating base module on training examples...
   Average base score: 0.72

4. Optimizing module with training examples...
   Using 6 training examples
   
5. Evaluating optimized module...
   Average optimized score: 0.89
   Improvement: +23.6%
   
6. Testing optimized module...
   Optimized decision: parallel
   Confidence: 0.95
   
7. Saving optimized module to backend/app/ml/optimized_delegation_v1.json...

✅ Optimization complete!
```

### 2. Use in Production

**Option A: Replace Instructor activity (recommended for A/B testing)**

```python
# In workflows.py, use DSPy activity
from app.temporal.activities_dspy import analyze_and_decide_delegation_activity_dspy

decision = await workflow.execute_activity(
    analyze_and_decide_delegation_activity_dspy,  # DSPy version
    args=[agent_type, task_description, context, ves],
    start_to_close_timeout=timedelta(minutes=2)
)
```

**Option B: Feature flag for gradual rollout**

```python
USE_DSPY = os.getenv("USE_DSPY_DELEGATION", "false").lower() == "true"

activity_fn = (
    analyze_and_decide_delegation_activity_dspy if USE_DSPY
    else analyze_and_decide_delegation_activity
)

decision = await workflow.execute_activity(
    activity_fn,
    args=[...],
    start_to_close_timeout=timedelta(minutes=2)
)
```

## Training Examples

Add more examples to improve optimization:

```python
# In dspy_modules.py
DELEGATION_TRAINING_EXAMPLES.append(
    dspy.Example(
        agent_type="your-agent-type",
        task_description="your task",
        available_agents="agent list",
        priority="high",
        action="delegate",  # Expected action
        delegated_to="specialist",  # Expected delegation
        reason="why this decision",
        confidence=0.9
    ).with_inputs("agent_type", "task_description", "available_agents", "priority")
)
```

## Metrics

The `delegation_quality_metric` evaluates:
- ✅ Valid action (handle/delegate/parallel)
- ✅ Correct action vs expected
- ✅ Valid confidence (0.0-1.0)
- ✅ Good reasoning (>20 chars)
- ✅ Appropriate delegated_to

**Score:** 0.0 (worst) to 1.0 (perfect)

## Continuous Improvement

### 1. Collect Production Data

```python
# Log all delegation decisions
logger.info({
    "agent_type": agent_type,
    "task": task_description,
    "decision": decision,
    "outcome": "success/failure"
})
```

### 2. Create Examples from Logs

```python
# Convert successful decisions to training examples
good_decisions = filter_successful_delegations(logs)
new_examples = [create_example(d) for d in good_decisions]
```

### 3. Re-optimize

```bash
# Re-run optimization with new examples
python backend/scripts/optimize_delegation_prompts.py
```

### 4. A/B Test

```python
# Compare optimized vs base
if random.random() < 0.5:
    use_optimized_module()
else:
    use_base_module()

# Track metrics for both
```

## Advanced: Custom Optimizers

```python
from dspy.teleprompt import MIPRO

# More advanced optimizer
optimizer = MIPRO(
    metric=delegation_quality_metric,
    num_candidates=10,
    init_temperature=1.0
)

optimized = optimizer.compile(
    DelegationDecider(),
    trainset=training_examples,
    num_trials=50
)
```

## Monitoring

Track these metrics:
- **Accuracy:** % of correct delegation decisions
- **Confidence:** Average confidence scores
- **Latency:** Time to make decision
- **Improvement:** Optimized vs base performance

## Troubleshooting

**Issue:** Low optimization scores  
**Fix:** Add more diverse training examples

**Issue:** Slow optimization  
**Fix:** Reduce `max_bootstrapped_demos` or use fewer examples

**Issue:** Module not loading  
**Fix:** Check file path and ensure optimization completed

## Best Practices

1. **Start with 5-10 examples** - More isn't always better
2. **Diverse examples** - Cover different scenarios
3. **Re-optimize monthly** - Incorporate new learnings
4. **A/B test changes** - Validate improvements
5. **Monitor metrics** - Track performance over time

## Next Steps

1. ✅ Run optimization script
2. ✅ Review optimized module performance
3. ⏳ A/B test in production
4. ⏳ Collect production examples
5. ⏳ Re-optimize with new data
6. ⏳ Expand to other activities

---

**Result:** Better delegation decisions through automatic prompt optimization! 🚀
