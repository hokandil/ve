# DSPy Rollout Plan

## Phase 1: Preparation (Day 1) ✅

- [x] Install DSPy: `pip install dspy-ai`
- [x] Create DSPy modules with signatures
- [x] Add 6 training examples
- [x] Create optimization script
- [x] Create DSPy-powered activity
- [x] Add feature flags system
- [x] Create staging configuration

## Phase 2: Optimization & Testing (Day 2)

### Step 1: Run Optimization
```bash
# Set OpenAI API key
export OPENAI_API_KEY=your-key

# Run optimization
python backend/scripts/optimize_delegation_prompts.py
```

**Expected Output:**
```
Base module score: 0.72
Optimized module score: 0.89
Improvement: +23.6%
Saved to: backend/app/ml/optimized_delegation_v1.json
```

### Step 2: Review Performance
- Check optimization metrics
- Review decision quality
- Validate confidence scores
- Test with sample tasks

### Step 3: Enable in Staging (0% rollout)
```bash
# In .env.staging
USE_DSPY_DELEGATION=true
DSPY_ROLLOUT_PERCENTAGE=0  # Start at 0%
LOG_DELEGATION_DECISIONS=true
```

## Phase 3: Gradual Rollout (Week 1)

### Day 1-2: 10% Rollout
```bash
DSPY_ROLLOUT_PERCENTAGE=10
```
- Monitor metrics
- Compare Instructor vs DSPy
- Check error rates

### Day 3-4: 25% Rollout
```bash
DSPY_ROLLOUT_PERCENTAGE=25
```
- Validate improvements
- Collect more training data

### Day 5-7: 50% Rollout
```bash
DSPY_ROLLOUT_PERCENTAGE=50
```
- A/B test results
- Analyze delegation patterns

## Phase 4: Full Rollout (Week 2)

### If metrics are good:
```bash
DSPY_ROLLOUT_PERCENTAGE=100
```

### If metrics need improvement:
1. Collect failed decisions
2. Add as training examples
3. Re-optimize
4. Test again

## Metrics to Monitor

### Success Metrics
- **Accuracy:** % correct delegation decisions
- **Confidence:** Average confidence scores
- **Latency:** Decision time
- **User Satisfaction:** Task completion quality

### Comparison Metrics
| Metric | Instructor | DSPy | Target |
|--------|-----------|------|--------|
| Accuracy | 85% | 90%+ | >88% |
| Avg Confidence | 0.75 | 0.85+ | >0.80 |
| Latency | 1.2s | 1.5s | <2s |
| Error Rate | 2% | <1% | <2% |

## Rollback Plan

If DSPy performs worse:
```bash
# Immediate rollback
DSPY_ROLLOUT_PERCENTAGE=0

# Or disable completely
USE_DSPY_DELEGATION=false
```

## Continuous Improvement

### Weekly:
1. Review delegation logs
2. Identify patterns
3. Add good examples to training

### Monthly:
1. Re-optimize with new examples
2. A/B test new version
3. Deploy if better

### Quarterly:
1. Expand to other activities
2. Build optimization pipeline
3. Automate retraining

## Commands Reference

```bash
# Run optimization
python backend/scripts/optimize_delegation_prompts.py

# Test DSPy module
python -c "from app.ml.dspy_modules import DelegationDecider; print(DelegationDecider())"

# Check feature flags
python -c "from app.core.feature_flags import get_feature_flags; print(get_feature_flags().get_all_flags())"

# Enable DSPy (staging)
export USE_DSPY_DELEGATION=true
export DSPY_ROLLOUT_PERCENTAGE=10

# Monitor logs
tail -f logs/delegation_decisions.log | grep "TRAINING_DATA"
```

## Success Criteria

✅ **Go-Live Criteria:**
- Optimization shows >15% improvement
- Staging tests pass
- Error rate <2%
- Latency <2s
- 50% rollout successful for 3 days

✅ **Full Rollout Criteria:**
- 100% rollout stable for 1 week
- User satisfaction maintained
- No increase in errors
- Confidence scores >0.80

---

**Current Status:** Phase 1 Complete ✅  
**Next Step:** Run optimization script
