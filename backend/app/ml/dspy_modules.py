"""
DSPy Modules for Intelligent Delegation
Provides optimizable, programmatic LLM modules instead of manual prompts
"""
import dspy
from typing import List, Dict, Any


class DelegationAnalysisSignature(dspy.Signature):
    """
    Signature defining the input/output behavior for delegation analysis.
    DSPy will automatically generate and optimize prompts for this.
    """
    agent_type: str = dspy.InputField(desc="Current agent type (e.g., 'marketing-manager')")
    task_description: str = dspy.InputField(desc="Task to be analyzed for delegation")
    available_agents: str = dspy.InputField(desc="List of available team members with expertise")
    priority: str = dspy.InputField(desc="Task priority: low, medium, high")
    
    action: str = dspy.OutputField(desc="Delegation action: 'handle', 'delegate', or 'parallel'")
    delegated_to: str = dspy.OutputField(desc="Agent type(s) to delegate to (comma-separated for parallel)")
    reason: str = dspy.OutputField(desc="Clear reasoning for the delegation decision")
    confidence: float = dspy.OutputField(desc="Confidence score between 0.0 and 1.0")


class DelegationDecider(dspy.Module):
    """
    DSPy module for intelligent delegation decisions.
    Uses Chain of Thought reasoning for better decision quality.
    """
    def __init__(self):
        super().__init__()
        # Use ChainOfThought for better reasoning
        self.decide = dspy.ChainOfThought(DelegationAnalysisSignature)
    
    def forward(self, agent_type: str, task_description: str, available_agents: str, priority: str = "medium"):
        """
        Make a delegation decision with reasoning.
        
        Args:
            agent_type: Current agent making the decision
            task_description: Task to analyze
            available_agents: Available team members
            priority: Task priority
        
        Returns:
            DSPy Prediction with action, delegated_to, reason, confidence
        """
        result = self.decide(
            agent_type=agent_type,
            task_description=task_description,
            available_agents=available_agents,
            priority=priority
        )
        
        return result


class TaskComplexityAnalysisSignature(dspy.Signature):
    """Signature for analyzing task complexity"""
    task_description: str = dspy.InputField(desc="Task to analyze")
    
    complexity: str = dspy.OutputField(desc="Complexity level: 'simple', 'moderate', or 'complex'")
    requires_multiple_agents: bool = dspy.OutputField(desc="Whether task needs multiple agents")
    estimated_time: int = dspy.OutputField(desc="Estimated time in minutes")
    reasoning: str = dspy.OutputField(desc="Explanation of complexity assessment")


class TaskComplexityAnalyzer(dspy.Module):
    """Module for analyzing task complexity"""
    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(TaskComplexityAnalysisSignature)
    
    def forward(self, task_description: str):
        return self.analyze(task_description=task_description)


# Training examples for delegation optimization
DELEGATION_TRAINING_EXAMPLES = [
    dspy.Example(
        agent_type="marketing-manager",
        task_description="Create a social media post about our new product",
        available_agents="copywriter (senior), designer (junior), data-analyst (senior)",
        priority="medium",
        action="delegate",
        delegated_to="copywriter",
        reason="Simple content creation task best handled by copywriter specialist",
        confidence=0.9
    ).with_inputs("agent_type", "task_description", "available_agents", "priority"),
    
    dspy.Example(
        agent_type="marketing-manager",
        task_description="Launch comprehensive marketing campaign with content, design, and analytics",
        available_agents="copywriter (senior), designer (senior), data-analyst (senior)",
        priority="high",
        action="parallel",
        delegated_to="copywriter,designer,data-analyst",
        reason="Complex campaign requires parallel work from content, design, and analytics teams",
        confidence=0.95
    ).with_inputs("agent_type", "task_description", "available_agents", "priority"),
    
    dspy.Example(
        agent_type="marketing-manager",
        task_description="Review quarterly marketing metrics",
        available_agents="copywriter (senior), designer (junior), data-analyst (senior)",
        priority="medium",
        action="handle",
        delegated_to="",
        reason="Strategic review task within manager's core responsibilities",
        confidence=0.85
    ).with_inputs("agent_type", "task_description", "available_agents", "priority"),
    
    dspy.Example(
        agent_type="copywriter",
        task_description="Write technical documentation for API",
        available_agents="technical-writer (senior), developer (senior)",
        priority="high",
        action="delegate",
        delegated_to="technical-writer",
        reason="Technical documentation requires specialized technical writing expertise",
        confidence=0.9
    ).with_inputs("agent_type", "task_description", "available_agents", "priority"),
    
    dspy.Example(
        agent_type="designer",
        task_description="Create simple social media graphic",
        available_agents="junior-designer (junior), copywriter (senior)",
        priority="low",
        action="handle",
        delegated_to="",
        reason="Simple graphic within my expertise, no need to delegate",
        confidence=0.8
    ).with_inputs("agent_type", "task_description", "available_agents", "priority"),
    
    dspy.Example(
        agent_type="data-analyst",
        task_description="Build comprehensive dashboard with data pipeline and visualizations",
        available_agents="data-engineer (senior), visualization-specialist (senior)",
        priority="high",
        action="parallel",
        delegated_to="data-engineer,visualization-specialist",
        reason="Complex project requiring both data engineering and visualization expertise",
        confidence=0.92
    ).with_inputs("agent_type", "task_description", "available_agents", "priority"),
]


def delegation_quality_metric(example, prediction, trace=None):
    """
    Metric to evaluate delegation decision quality.
    Used by DSPy optimizers to improve prompts.
    
    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0
    
    # Check if action is valid
    if prediction.action not in ["handle", "delegate", "parallel"]:
        return 0.0
    
    score += 0.3  # Valid action
    
    # Check if action matches expected
    if hasattr(example, 'action') and prediction.action == example.action:
        score += 0.4  # Correct action
    
    # Check confidence is reasonable
    try:
        conf = float(prediction.confidence)
        if 0.0 <= conf <= 1.0:
            score += 0.1  # Valid confidence
    except:
        pass
    
    # Check reasoning is provided
    if prediction.reason and len(prediction.reason) > 20:
        score += 0.1  # Good reasoning
    
    # Check delegated_to is appropriate
    if prediction.action == "handle" and not prediction.delegated_to:
        score += 0.1
    elif prediction.action in ["delegate", "parallel"] and prediction.delegated_to:
        score += 0.1
    
    return score


def optimize_delegation_module(training_examples=None, metric=None):
    """
    Optimize the DelegationDecider module using training examples.
    
    Args:
        training_examples: List of dspy.Example objects (defaults to DELEGATION_TRAINING_EXAMPLES)
        metric: Evaluation metric (defaults to delegation_quality_metric)
    
    Returns:
        Optimized DelegationDecider module
    """
    from dspy.teleprompt import BootstrapFewShot
    
    if training_examples is None:
        training_examples = DELEGATION_TRAINING_EXAMPLES
    
    if metric is None:
        metric = delegation_quality_metric
    
    # Create optimizer
    optimizer = BootstrapFewShot(
        metric=metric,
        max_bootstrapped_demos=4,  # Use up to 4 examples in prompts
        max_labeled_demos=2  # Use up to 2 labeled examples
    )
    
    # Optimize the module
    base_module = DelegationDecider()
    optimized_module = optimizer.compile(
        base_module,
        trainset=training_examples
    )
    
    return optimized_module


def save_optimized_module(module, filepath: str):
    """Save optimized DSPy module to file"""
    module.save(filepath)


def load_optimized_module(filepath: str) -> DelegationDecider:
    """Load optimized DSPy module from file"""
    module = DelegationDecider()
    module.load(filepath)
    return module
