"""
Enhanced delegation activity with DSPy support
Supports both Instructor (type-safe) and DSPy (optimized) approaches
"""
from temporalio import activity
from typing import Dict, Any, List
import os


@activity.defn
async def analyze_and_decide_delegation_activity_dspy(
    agent_type: str,
    task_description: str,
    context: Dict[str, Any],
    available_agents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Activity using DSPy for optimized delegation decisions.
    Uses pre-trained, optimized prompts for better performance.
    """
    import dspy
    from app.ml.dspy_modules import DelegationDecider, load_optimized_module
    
    # Build list of available agents
    agent_list = "\n".join([
        f"{agent['agent_type']} ({agent['ve_details']['seniority_level']})"
        for agent in available_agents
    ])
    
    try:
        # Configure DSPy
        lm = dspy.LM('openai/gpt-4', api_key=os.getenv("OPENAI_API_KEY"))
        dspy.configure(lm=lm)
        
        # Try to load optimized module, fall back to base module
        try:
            module = load_optimized_module("backend/app/ml/optimized_delegation_v1.json")
        except:
            module = DelegationDecider()
        
        # Get delegation decision
        result = module(
            agent_type=agent_type,
            task_description=task_description,
            available_agents=agent_list,
            priority=context.get('priority', 'medium')
        )
        
        # Parse delegated_to (comma-separated for parallel)
        delegated_to = None
        if result.delegated_to:
            if ',' in result.delegated_to:
                delegated_to = [a.strip() for a in result.delegated_to.split(',')]
            else:
                delegated_to = result.delegated_to.strip()
        
        # Determine subtasks for parallel execution
        subtasks = None
        if result.action == "parallel" and isinstance(delegated_to, list):
            subtasks = [
                {"agent": agent, "task": f"Handle {task_description} - {agent} portion"}
                for agent in delegated_to
            ]
        
        # Log the decision
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"DSPy delegation decision by {agent_type}: {result.action} "
            f"(confidence: {result.confidence:.2f}) - {result.reason}"
        )
        
        return {
            "action": result.action,
            "delegated_to": delegated_to,
            "subtasks": subtasks,
            "reason": result.reason,
            "confidence": float(result.confidence),
            "method": "dspy_optimized"
        }
        
    except Exception as e:
        # Fallback on error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in DSPy delegation analysis: {e}")
        
        return {
            "action": "handle",
            "delegated_to": None,
            "subtasks": None,
            "reason": f"Error in DSPy analysis, defaulting to self-execution: {str(e)}",
            "confidence": 0.3,
            "method": "fallback"
        }
