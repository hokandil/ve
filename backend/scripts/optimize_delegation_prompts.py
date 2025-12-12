"""
Script to optimize delegation prompts using DSPy
Run this to train and save optimized delegation modules
"""
import asyncio
import dspy
from app.ml.dspy_modules import (
    DelegationDecider,
    DELEGATION_TRAINING_EXAMPLES,
    delegation_quality_metric,
    optimize_delegation_module,
    save_optimized_module
)
import os


async def main():
    """Optimize and save delegation module"""
    
    print("🚀 DSPy Delegation Prompt Optimization")
    print("=" * 60)
    
    # Configure DSPy with LLM
    print("\n1. Configuring DSPy with GPT-4...")
    lm = dspy.LM('openai/gpt-4', api_key=os.getenv("OPENAI_API_KEY"))
    dspy.configure(lm=lm)
    
    # Test base module
    print("\n2. Testing base (unoptimized) module...")
    base_module = DelegationDecider()
    
    test_result = base_module(
        agent_type="marketing-manager",
        task_description="Create a product launch campaign",
        available_agents="copywriter, designer, data-analyst",
        priority="high"
    )
    
    print(f"   Base decision: {test_result.action}")
    print(f"   Delegated to: {test_result.delegated_to}")
    print(f"   Confidence: {test_result.confidence}")
    print(f"   Reason: {test_result.reason[:100]}...")
    
    # Evaluate base module
    print("\n3. Evaluating base module on training examples...")
    base_scores = []
    for example in DELEGATION_TRAINING_EXAMPLES:
        prediction = base_module(
            agent_type=example.agent_type,
            task_description=example.task_description,
            available_agents=example.available_agents,
            priority=example.priority
        )
        score = delegation_quality_metric(example, prediction)
        base_scores.append(score)
    
    avg_base_score = sum(base_scores) / len(base_scores)
    print(f"   Average base score: {avg_base_score:.2f}")
    
    # Optimize module
    print("\n4. Optimizing module with training examples...")
    print(f"   Using {len(DELEGATION_TRAINING_EXAMPLES)} training examples")
    
    optimized_module = optimize_delegation_module(
        training_examples=DELEGATION_TRAINING_EXAMPLES,
        metric=delegation_quality_metric
    )
    
    # Evaluate optimized module
    print("\n5. Evaluating optimized module...")
    optimized_scores = []
    for example in DELEGATION_TRAINING_EXAMPLES:
        prediction = optimized_module(
            agent_type=example.agent_type,
            task_description=example.task_description,
            available_agents=example.available_agents,
            priority=example.priority
        )
        score = delegation_quality_metric(example, prediction)
        optimized_scores.append(score)
    
    avg_optimized_score = sum(optimized_scores) / len(optimized_scores)
    print(f"   Average optimized score: {avg_optimized_score:.2f}")
    
    improvement = ((avg_optimized_score - avg_base_score) / avg_base_score) * 100
    print(f"   Improvement: {improvement:+.1f}%")
    
    # Test optimized module
    print("\n6. Testing optimized module...")
    test_result_opt = optimized_module(
        agent_type="marketing-manager",
        task_description="Create a product launch campaign",
        available_agents="copywriter, designer, data-analyst",
        priority="high"
    )
    
    print(f"   Optimized decision: {test_result_opt.action}")
    print(f"   Delegated to: {test_result_opt.delegated_to}")
    print(f"   Confidence: {test_result_opt.confidence}")
    print(f"   Reason: {test_result_opt.reason[:100]}...")
    
    # Save optimized module
    output_path = "backend/app/ml/optimized_delegation_v1.json"
    print(f"\n7. Saving optimized module to {output_path}...")
    save_optimized_module(optimized_module, output_path)
    
    print("\n✅ Optimization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the optimized module performance")
    print("2. Update analyze_and_decide_delegation_activity to use optimized module")
    print("3. A/B test optimized vs base prompts in production")
    print("4. Collect more training examples from production data")
    print("5. Re-optimize periodically for continuous improvement")


if __name__ == "__main__":
    asyncio.run(main())
