"""
Integration Tests for Temporal Workflows
"""
import pytest
import uuid
from datetime import timedelta
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.client import Client

from app.temporal.workflows import (
    OrchestratorWorkflow,
    DirectAssignmentWorkflow,
    ContentCreationWorkflow,
    EngagementMonitorWorkflow,
    ProductLaunchCampaignWorkflow
)
from app.temporal.activities import (
    invoke_agent_activity,
    save_task_result_activity,
    get_customer_ves_activity,
    analyze_routing_activity,
    publish_update_activity,
    get_campaign_performance_activity
)


@pytest.mark.asyncio
async def test_orchestrator_workflow_success():
    """Test OrchestratorWorkflow with successful task completion"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Create worker with workflows and activities
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[OrchestratorWorkflow],
            activities=[
                invoke_agent_activity,
                save_task_result_activity,
                get_customer_ves_activity,
                analyze_routing_activity
            ]
        ):
            # Execute workflow
            result = await env.client.execute_workflow(
                OrchestratorWorkflow.run,
                args=[{
                    "customer_id": "test-customer-123",
                    "task_description": "Create a marketing plan",
                    "task_id": str(uuid.uuid4()),
                    "context": {"priority": "high"}
                }],
                id=f"test-orchestrator-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            # Verify result
            assert result is not None
            assert "status" in result
            assert result["status"] in ["completed", "failed"]


@pytest.mark.asyncio
async def test_direct_assignment_workflow():
    """Test DirectAssignmentWorkflow for direct VE assignment"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[DirectAssignmentWorkflow],
            activities=[
                invoke_agent_activity,
                save_task_result_activity,
                get_customer_ves_activity
            ]
        ):
            result = await env.client.execute_workflow(
                DirectAssignmentWorkflow.run,
                args=[{
                    "customer_id": "test-customer-456",
                    "task_id": str(uuid.uuid4()),
                    "ve_id": "test-ve-789",
                    "task_description": "Write a blog post"
                }],
                id=f"test-direct-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert "status" in result


@pytest.mark.asyncio
async def test_content_creation_workflow():
    """Test ContentCreationWorkflow for multi-agent collaboration"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[ContentCreationWorkflow],
            activities=[invoke_agent_activity]
        ):
            result = await env.client.execute_workflow(
                ContentCreationWorkflow.run,
                args=[{
                    "customer_id": "test-customer-789",
                    "platform": "twitter",
                    "time": "09:00",
                    "strategy": "Increase brand awareness"
                }],
                id=f"test-content-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert result["status"] == "scheduled"
            assert result["platform"] == "twitter"
            assert "copy" in result
            assert "design" in result


@pytest.mark.asyncio
async def test_engagement_monitor_workflow():
    """Test EngagementMonitorWorkflow for monitoring"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[EngagementMonitorWorkflow],
            activities=[
                get_campaign_performance_activity,
                publish_update_activity
            ]
        ):
            result = await env.client.execute_workflow(
                EngagementMonitorWorkflow.run,
                args=[{
                    "customer_id": "test-customer-monitor",
                    "campaign_id": "test-campaign-123",
                    "duration_hours": 1
                }],
                id=f"test-monitor-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert "engagement_rate" in result or "impressions" in result


@pytest.mark.asyncio
async def test_workflow_retry_on_failure():
    """Test workflow retry logic on activity failure"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[DirectAssignmentWorkflow],
            activities=[
                invoke_agent_activity,
                save_task_result_activity,
                get_customer_ves_activity
            ]
        ):
            # This should handle failures gracefully
            result = await env.client.execute_workflow(
                DirectAssignmentWorkflow.run,
                args=[{
                    "customer_id": "nonexistent-customer",
                    "task_id": str(uuid.uuid4()),
                    "ve_id": "nonexistent-ve",
                    "task_description": "Test task"
                }],
                id=f"test-retry-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            # Should fail gracefully
            assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_workflow_signals_and_queries():
    """Test ProductLaunchCampaignWorkflow signals and queries"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[
                ProductLaunchCampaignWorkflow,
                ContentCreationWorkflow,
                EngagementMonitorWorkflow
            ],
            activities=[
                invoke_agent_activity,
                publish_update_activity,
                save_task_result_activity
            ]
        ):
            # Start workflow
            handle = await env.client.start_workflow(
                ProductLaunchCampaignWorkflow.run,
                args=[{
                    "customer_id": "test-customer-campaign",
                    "task_id": str(uuid.uuid4()),
                    "duration_days": 2  # Short duration for testing
                }],
                id=f"test-campaign-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            # Query progress
            progress = await handle.query(ProductLaunchCampaignWorkflow.get_progress)
            assert "current_day" in progress
            assert "posts_made" in progress
            
            # Send pause signal
            await handle.signal(ProductLaunchCampaignWorkflow.pause_campaign)
            
            # Query again
            progress = await handle.query(ProductLaunchCampaignWorkflow.get_progress)
            assert progress["paused"] == True
            
            # Resume
            await handle.signal(ProductLaunchCampaignWorkflow.resume_campaign)
            
            # Update strategy
            await handle.signal(
                ProductLaunchCampaignWorkflow.update_strategy,
                "New strategy: Focus on engagement"
            )
            
            # Verify strategy updated
            progress = await handle.query(ProductLaunchCampaignWorkflow.get_progress)
            assert "New strategy" in progress["strategy"]


@pytest.mark.asyncio
async def test_workflow_child_workflows():
    """Test parent-child workflow relationships"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[
                ProductLaunchCampaignWorkflow,
                ContentCreationWorkflow,
                EngagementMonitorWorkflow
            ],
            activities=[
                invoke_agent_activity,
                publish_update_activity,
                save_task_result_activity
            ]
        ):
            # Execute parent workflow that spawns child workflows
            result = await env.client.execute_workflow(
                ProductLaunchCampaignWorkflow.run,
                args=[{
                    "customer_id": "test-customer-parent",
                    "task_id": str(uuid.uuid4()),
                    "duration_days": 1
                }],
                id=f"test-parent-{uuid.uuid4()}",
                task_queue="test-queue",
                execution_timeout=timedelta(minutes=5)
            )
            
            assert result["status"] == "completed"
            assert result["posts_made"] > 0


@pytest.mark.asyncio
async def test_dynamic_task_analysis_workflow():
    """Test DynamicTaskAnalysisWorkflow with NLP agent selection"""
    from app.temporal.workflows import DynamicTaskAnalysisWorkflow
    from app.temporal.activities import analyze_task_description_activity
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[DynamicTaskAnalysisWorkflow, DirectAssignmentWorkflow],
            activities=[
                analyze_task_description_activity,
                invoke_agent_activity,
                save_task_result_activity,
                get_customer_ves_activity,
                publish_update_activity
            ]
        ):
            # Test 1: Marketing task should select marketing-manager
            result = await env.client.execute_workflow(
                DynamicTaskAnalysisWorkflow.run,
                args=[{
                    "customer_id": "test-customer-nlp",
                    "task_id": str(uuid.uuid4()),
                    "task_description": "Create a social media marketing campaign for our new product launch",
                    "context": {"priority": "high"}
                }],
                id=f"test-nlp-marketing-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert "agent_type_selected" in result
            assert result["agent_type_selected"] == "marketing-manager"
            assert result["analysis_method"] == "nlp"
            
            # Test 2: Writing task should select copywriter
            result2 = await env.client.execute_workflow(
                DynamicTaskAnalysisWorkflow.run,
                args=[{
                    "customer_id": "test-customer-nlp-2",
                    "task_id": str(uuid.uuid4()),
                    "task_description": "Write a blog article about our company values",
                    "context": {}
                }],
                id=f"test-nlp-writing-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result2 is not None
            assert result2["agent_type_selected"] == "copywriter"
            
            # Test 3: Design task should select designer
            result3 = await env.client.execute_workflow(
                DynamicTaskAnalysisWorkflow.run,
                args=[{
                    "customer_id": "test-customer-nlp-3",
                    "task_id": str(uuid.uuid4()),
                    "task_description": "Create a UI mockup for the new dashboard",
                    "context": {}
                }],
                id=f"test-nlp-design-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result3 is not None
            assert result3["agent_type_selected"] == "designer"


@pytest.mark.asyncio
async def test_escalation_workflow():
    """Test EscalationWorkflow with automatic seniority escalation"""
    from app.temporal.workflows import EscalationWorkflow
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[EscalationWorkflow],
            activities=[
                get_customer_ves_activity,
                invoke_agent_activity,
                save_task_result_activity,
                publish_update_activity
            ]
        ):
            # Test escalation starting from junior level
            result = await env.client.execute_workflow(
                EscalationWorkflow.run,
                args=[{
                    "customer_id": "test-customer-escalation",
                    "task_id": str(uuid.uuid4()),
                    "task_description": "Complex task requiring escalation",
                    "attempt": 0  # Start at junior level
                }],
                id=f"test-escalation-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert "status" in result
            # Should either complete or fail after escalation
            assert result["status"] in ["completed", "failed"]
            
            if result["status"] == "completed":
                assert "seniority_level" in result
                assert result["seniority_level"] in ["junior", "senior", "manager"]
                assert "escalation_attempts" in result


@pytest.mark.asyncio
async def test_cross_department_delegation_workflow():
    """Test CrossDepartmentDelegationWorkflow for manager-to-manager delegation"""
    from app.temporal.workflows import CrossDepartmentDelegationWorkflow
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[CrossDepartmentDelegationWorkflow],
            activities=[
                get_customer_ves_activity,
                invoke_agent_activity,
                save_task_result_activity,
                publish_update_activity
            ]
        ):
            result = await env.client.execute_workflow(
                CrossDepartmentDelegationWorkflow.run,
                args=[{
                    "customer_id": "test-customer-delegation",
                    "task_id": str(uuid.uuid4()),
                    "task_description": "Cross-department collaboration task",
                    "source_department": "marketing",
                    "target_department": "engineering",
                    "delegating_manager": "Marketing Manager"
                }],
                id=f"test-cross-dept-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert result["status"] in ["completed", "failed"]
            if result["status"] == "completed":
                assert result["delegation_type"] == "cross_department"
                assert "handled_by" in result


@pytest.mark.asyncio
async def test_task_decomposition_workflow():
    """Test TaskDecompositionWorkflow for parallel task execution"""
    from app.temporal.workflows import TaskDecompositionWorkflow
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[TaskDecompositionWorkflow, DirectAssignmentWorkflow],
            activities=[
                get_customer_ves_activity,
                invoke_agent_activity,
                save_task_result_activity,
                publish_update_activity
            ]
        ):
            result = await env.client.execute_workflow(
                TaskDecompositionWorkflow.run,
                args=[{
                    "customer_id": "test-customer-decomp",
                    "task_id": str(uuid.uuid4()),
                    "task_description": "Large task requiring decomposition and parallel execution",
                    "coordinator_agent": "senior"
                }],
                id=f"test-decomp-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert result["status"] in ["completed", "failed"]
            if result["status"] == "completed":
                assert result["delegation_type"] == "task_decomposition"
                assert "coordinator" in result
                assert "subtasks_completed" in result


@pytest.mark.asyncio
async def test_intelligent_delegation_workflow():
    """Test IntelligentDelegationWorkflow with LLM-powered agent decisions"""
    from app.temporal.workflows import IntelligentDelegationWorkflow
    from app.temporal.activities import analyze_and_decide_delegation_activity
    
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IntelligentDelegationWorkflow, DirectAssignmentWorkflow],
            activities=[
                get_customer_ves_activity,
                invoke_agent_activity,
                save_task_result_activity,
                publish_update_activity,
                analyze_and_decide_delegation_activity
            ]
        ):
            # Test intelligent delegation
            result = await env.client.execute_workflow(
                IntelligentDelegationWorkflow.run,
                args=[{
                    "customer_id": "test-customer-intelligent",
                    "task_id": str(uuid.uuid4()),
                    "task_description": "Create a comprehensive marketing campaign with content and design",
                    "current_agent_type": "marketing-manager",
                    "context": {"priority": "high"}
                }],
                id=f"test-intelligent-{uuid.uuid4()}",
                task_queue="test-queue"
            )
            
            assert result is not None
            assert "status" in result
            assert result["status"] in ["completed", "failed"]
            
            if result["status"] == "completed":
                # Should have delegation info
                assert "delegation_type" in result
                assert result["delegation_type"] in ["self_execution", "parallel_execution", "fallback_execution"]
                assert "delegation_chain" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
