"""
Temporal Worker Service
Runs the worker that executes workflows and activities.
"""
import asyncio
import sys
import os
import logging

# Add backend directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from temporalio.client import Client
from temporalio.worker import Worker
from app.core.config import settings
from app.temporal.workflows import (
    ProductLaunchCampaignWorkflow,
    ContentCreationWorkflow,
    EngagementMonitorWorkflow,
    OrchestratorWorkflow,
    DynamicTaskAnalysisWorkflow,
    EscalationWorkflow,
    CrossDepartmentDelegationWorkflow,
    TaskDecompositionWorkflow,
    IntelligentDelegationWorkflow,
    DirectAssignmentWorkflow
)
from app.temporal.activities import (
    invoke_agent_activity,
    publish_update_activity,
    save_task_result_activity,
    get_campaign_performance_activity,
    analyze_routing_activity,
    get_customer_ves_activity,
    analyze_task_description_activity,
    analyze_and_decide_delegation_activity
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_worker():
    logger.info(f"Connecting to Temporal Server at {settings.TEMPORAL_HOST}...")
    
    try:
        client = await Client.connect(
            settings.TEMPORAL_HOST,
            namespace=settings.TEMPORAL_NAMESPACE,
        )
        logger.info("Connected to Temporal Server.")
        
        worker = Worker(
            client,
            task_queue="campaign-queue",
            workflows=[
                ProductLaunchCampaignWorkflow,
                ContentCreationWorkflow,
                EngagementMonitorWorkflow,
                OrchestratorWorkflow,
                DynamicTaskAnalysisWorkflow,
                EscalationWorkflow,
                CrossDepartmentDelegationWorkflow,
                TaskDecompositionWorkflow,
                IntelligentDelegationWorkflow,
                DirectAssignmentWorkflow
            ],
            activities=[
                invoke_agent_activity,
                publish_update_activity,
                save_task_result_activity,
                get_campaign_performance_activity,
                analyze_routing_activity,
                get_customer_ves_activity,
                analyze_task_description_activity,
                analyze_and_decide_delegation_activity
            ]
        )
        
        logger.info("Starting Temporal Worker on queue 'campaign-queue'...")
        await worker.run()
    except Exception as e:
        logger.error(f"Failed to start worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_worker())
