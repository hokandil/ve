"""
Temporal Workflows for VE Platform
Production-ready workflows with real-time status updates and intelligent delegation
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
    from app.temporal.activities import (
        invoke_agent_activity,
        publish_update_activity,
        save_task_result_activity,
        get_campaign_performance_activity,
        analyze_routing_activity,
        get_customer_ves_activity,
        analyze_task_description_activity,
        analyze_and_decide_delegation_activity,
        analyze_and_decide_delegation_activity,
        update_task_status_activity,
        create_task_plan_activity
    )

@workflow.defn
class OrchestratorWorkflow:
    """
    Main workflow to orchestrate task routing and execution.
    Uses intelligent agent-driven delegation with real-time status updates.
    """
    @workflow.run
    async def run(self, request: dict) -> dict:
        customer_id = request["customer_id"]
        task_description = request["task_description"]
        task_id = request["task_id"]
        context = request.get("context", {})
        
        # 🔔 REAL-TIME UPDATE: Task started
        await workflow.execute_activity(
            update_task_status_activity,
            args=[task_id, "in_progress", None, "Starting task analysis..."],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # 1. Get Customer VEs
        ves = await workflow.execute_activity(
            get_customer_ves_activity,
            args=[customer_id],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        if not ves:
            # 🔔 REAL-TIME UPDATE: Failed - no VEs
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "failed", None, "No virtual employees found"],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            return {"status": "failed", "reason": "No VEs found"}
        
        # 2. Analyze Routing to determine initial agent
        routing_result = await workflow.execute_activity(
            analyze_routing_activity,
            args=[customer_id, task_description, context],
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        target_ve_id = routing_result.get("routed_to_ve")
        
        # Determine initial agent
        if not target_ve_id:
            # Find a manager as default entry point
            managers = [ve for ve in ves if ve["ve_details"]["seniority_level"] == "manager"]
            target_ve = managers[0] if managers else ves[0]
        else:
            target_ve = next((ve for ve in ves if ve["id"] == target_ve_id), ves[0])
        
        initial_agent_type = target_ve.get("agent_type", "marketing-manager")
        
        workflow.logger.info(f"Orchestrator routing to {initial_agent_type} for intelligent delegation")
        
        # 🔔 REAL-TIME UPDATE: Routing to agent
        await workflow.execute_activity(
            update_task_status_activity,
            args=[task_id, "in_progress", initial_agent_type, f"Routing to {initial_agent_type}..."],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # 3. Execute Intelligent Delegation Workflow
        result = await workflow.execute_child_workflow(
            IntelligentDelegationWorkflow.run,
            args=[{
                "customer_id": customer_id,
                "task_id": task_id,
                "task_description": task_description,
                "current_agent_type": initial_agent_type,
                "context": context,
                "delegation_depth": 0
            }],
            id=f"intelligent-delegation-{task_id}",
            parent_close_policy=workflow.ParentClosePolicy.TERMINATE
        )
        
        return result


@workflow.defn
class IntelligentDelegationWorkflow:
    """
    Workflow for intelligent agent-driven delegation with real-time status updates.
    Agent uses LLM reasoning to decide: handle, delegate, or parallel execution.
    
    REAL-TIME: Updates task status at every stage for live Kanban updates
    SIGNALS: pause_delegation, resume_delegation, cancel_delegation
    QUERIES: get_delegation_status, get_delegation_chain
    """
    
    def __init__(self):
        self._paused = False
        self._cancelled = False
        self._delegation_status = {
            "current_agent": None,
            "current_action": None,
            "delegation_depth": 0,
            "delegation_chain": [],
            "decisions_made": [],
            "start_time": None,
            "start_time": None,
            "last_update": None
        }
        self._feedback_received = False
        self._feedback_received = False
        self._last_feedback = None
        self._plan_approved = False
    
    @workflow.signal
    async def approve_plan(self):
        """Signal to approve the proposed plan"""
        self._plan_approved = True
        self._delegation_status["last_update"] = workflow.now().isoformat()
        workflow.logger.info("Plan approved signal received")
    
    @workflow.signal
    async def pause_delegation(self):
        """Signal to pause delegation workflow"""
        self._paused = True
        self._delegation_status["last_update"] = workflow.now().isoformat()
        workflow.logger.info("Delegation workflow paused")
    
    @workflow.signal
    async def resume_delegation(self):
        """Signal to resume delegation workflow"""
        self._paused = False
        self._delegation_status["last_update"] = workflow.now().isoformat()
        workflow.logger.info("Delegation workflow resumed")

    @workflow.signal
    async def provide_feedback(self, message: str):
        """Signal to provide user feedback"""
        self._feedback_received = True
        self._last_feedback = message
        self._delegation_status["last_update"] = workflow.now().isoformat()
        workflow.logger.info(f"Feedback signal received: {message}")
    
    @workflow.signal
    async def cancel_delegation(self):
        """Signal to cancel delegation workflow"""
        self._cancelled = True
        self._delegation_status["last_update"] = workflow.now().isoformat()
        workflow.logger.info("Delegation workflow cancelled")
    
    @workflow.query
    def get_delegation_status(self) -> dict:
        """Query to get current delegation status"""
        return {
            **self._delegation_status,
            "paused": self._paused,
            "cancelled": self._cancelled
        }
    
    @workflow.query
    def get_delegation_chain(self) -> list:
        """Query to get the full delegation chain"""
        return self._delegation_status["delegation_chain"]
    
    @workflow.run
    async def run(self, request: dict) -> dict:
        customer_id = request["customer_id"]
        task_id = request["task_id"]
        task_description = request["task_description"]
        current_agent_type = request.get("current_agent_type", "marketing-manager")
        context = request.get("context", {})
        delegation_depth = request.get("delegation_depth", 0)
        
        # Initialize status
        self._delegation_status["current_agent"] = current_agent_type
        self._delegation_status["delegation_depth"] = delegation_depth
        self._delegation_status["start_time"] = workflow.now().isoformat()
        
        workflow.logger.info(f"[TRACE] Starting delegation for {current_agent_type} at depth {delegation_depth}")
        
        # Check for cancellation
        if self._cancelled:
            return {
                "status": "cancelled",
                "reason": "Workflow cancelled by user",
                "delegation_chain": self._delegation_status["delegation_chain"]
            }
        
        # Prevent infinite delegation loops
        if delegation_depth > 5:
            workflow.logger.warning(f"Max delegation depth reached for task {task_id}")
            return {
                "status": "failed",
                "reason": "Maximum delegation depth exceeded",
                "delegation_chain": context.get("delegation_chain", [])
            }
        
        # Step 0: Interactive Planning Phase (Only for root agent)
        if delegation_depth == 0 and not context.get("plan_approved"):
            workflow.logger.info(f"Starting Planning Phase for task {task_id}")
            
            # 🔔 REAL-TIME UPDATE: drafting plan
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "planning", current_agent_type, f"{current_agent_type} is drafting an execution plan..."],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Generate Plan
            plan_result = await workflow.execute_activity(
                create_task_plan_activity,
                args=[task_id, task_description, current_agent_type, context],
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )

            if not plan_result.get("success"):
                error_msg = plan_result.get("error", "Unknown planning error")
                await workflow.execute_activity(
                    update_task_status_activity,
                    args=[task_id, "failed", current_agent_type, f"Planning Failed: {error_msg}"],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                return {"status": "failed", "reason": f"Planning failure: {error_msg}"}
            
            # 🔔 REAL-TIME UPDATE: waiting for approval
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "planning", current_agent_type, "Plan drafted. Waiting for approval."],
                start_to_close_timeout=timedelta(seconds=30)
            )

            # Wait for approval signal
            workflow.logger.info(f"Waiting for plan approval for task {task_id}")
            await workflow.wait_condition(lambda: self._plan_approved or self._cancelled)
            
            if self._cancelled:
                return {"status": "cancelled", "reason": "Workflow cancelled during planning"}
            
            # Plan Approved! Update context and proceed
            context["plan_approved"] = True
            context["user_feedback"] = "Plan approved by user." # Optional: store approval note
            
            workflow.logger.info(f"Plan approved. Proceeding to execution.")
            # 🔔 REAL-TIME UPDATE: Execution starting
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "in_progress", current_agent_type, "Plan approved. Starting execution..."],
                start_to_close_timeout=timedelta(seconds=30)
            )

        # Track delegation chain
        delegation_chain = context.get("delegation_chain", [])
        delegation_chain.append(current_agent_type)
        context["delegation_chain"] = delegation_chain
        
        # Step 1: Get available team members
        ves = await workflow.execute_activity(
            get_customer_ves_activity,
            args=[customer_id],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        if not ves:
            return {"status": "failed", "reason": "No VEs available"}
        
        # Find current agent
        current_agent = next(
            (ve for ve in ves if ve.get("agent_type") == current_agent_type),
            ves[0]  # Fallback to first available
        )
        
        # Step 2: Agent analyzes task and decides delegation strategy
        workflow.logger.info(f"{current_agent_type} analyzing task for delegation...")
        
        # Update status
        self._delegation_status["current_action"] = "analyzing"
        self._delegation_status["last_update"] = workflow.now().isoformat()
        
        # 🔔 REAL-TIME UPDATE: Agent analyzing
        await workflow.execute_activity(
            update_task_status_activity,
            args=[task_id, "in_progress", current_agent_type, f"{current_agent_type} is analyzing the task..."],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Wait if paused
        await workflow.wait_condition(lambda: not self._paused)
        
        decision = await workflow.execute_activity(
            analyze_and_decide_delegation_activity,
            args=[current_agent_type, task_description, {**context, "customer_id": customer_id, "task_id": task_id}, ves],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        workflow.logger.info(f"Agent decision: {decision['action']} - {decision.get('reason', 'No reason')}")
        
        # Track decision
        self._delegation_status["current_action"] = decision["action"]
        self._delegation_status["decisions_made"].append({
            "agent": current_agent_type,
            "action": decision["action"],
            "confidence": decision.get("confidence", 0),
            "reason": decision.get("reason", ""),
            "timestamp": workflow.now().isoformat()
        })
        self._delegation_status["delegation_chain"] = delegation_chain
        
        # Step 3: Execute based on agent's decision
        if decision["action"] == "handle":
            # Agent handles it themselves
            workflow.logger.info(f"{current_agent_type} handling task directly")
            
            # 🔔 REAL-TIME UPDATE: Agent working on task
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "in_progress", current_agent_type, f"{current_agent_type} is working on this task"],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            response = await workflow.execute_activity(
                invoke_agent_activity,
                args=[customer_id, current_agent_type, task_description, task_id],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            # 🔔 REAL-TIME UPDATE: Task completed
            await workflow.execute_activity(
                save_task_result_activity,
                args=[task_id, {"message": response.get("message", "Task completed")}, "completed"],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            return {
                "status": "completed",
                "handled_by": current_agent["persona_name"],
                "delegation_type": "self_execution",
                "delegation_chain": delegation_chain,
                "result": response.get("message", "")
            }
        
        elif decision["action"] == "ask_clarification":
            # Agent needs user feedback
            workflow.logger.info(f"{current_agent_type} asking for clarification: {decision.get('reason')}")
            
            # 🔔 REAL-TIME UPDATE: Waiting for input
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "waiting_for_input", current_agent_type, decision.get('reason')],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            # Notify user via comment
            await workflow.execute_activity(
                save_task_result_activity,
                args=[task_id, {"message": f"**QUESTION:** {decision.get('reason')}"}, "waiting_for_input"],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Wait for user feedback signal
            self._feedback_received = False
            self._last_feedback = None
            
            workflow.logger.info(f"Workflow paused, waiting for feedback on task {task_id}")
            await workflow.wait_condition(lambda: self._feedback_received or self._cancelled)
            
            if self._cancelled:
                return {"status": "cancelled", "reason": "Workflow cancelled during feedback"}
            
            workflow.logger.info(f"Feedback received: {self._last_feedback}")
            
            # Update context with feedback and loop back
            context["user_feedback"] = self._last_feedback
            # We don't recurse here; in a real loop we would continue the while loop. 
            # For this simplified version (no while loop structure visible in snippet), we'll restart delegation with updated context.
            # Ideally this whole run method should be a while loop. 
            # Let's recursively call ourselves to 'restart' the decision process with new info
            context["delegation_chain"] = delegation_chain # preserve chain
            
            # 🔔 REAL-TIME UPDATE: Resuming
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "in_progress", current_agent_type, "Feedback received, resuming analysis..."],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return await workflow.execute_child_workflow(
                IntelligentDelegationWorkflow.run,
                args=[{
                    "customer_id": customer_id,
                    "task_id": task_id,
                    "task_description": task_description,
                    "current_agent_type": current_agent_type,
                    "context": context,
                    "delegation_depth": delegation_depth 
                }],
                id=f"intelligent-delegation-{task_id}-retry-{workflow.now().timestamp()}",
                parent_close_policy=workflow.ParentClosePolicy.TERMINATE
            )

        elif decision["action"] == "delegate":
            # Agent delegates to ONE specific person
            target_agent_type = decision.get("delegated_to")
            
            if not target_agent_type:
                # Fallback: handle it themselves
                return await self._handle_task_directly(customer_id, task_id, task_description, current_agent, delegation_chain)
            
            workflow.logger.info(f"{current_agent_type} delegating to {target_agent_type}")
            
            # 🔔 REAL-TIME UPDATE: Delegating
            await workflow.execute_activity(
                update_task_status_activity,
                args=[task_id, "in_progress", target_agent_type, f"Delegating to {target_agent_type}..."],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            # Recursive call: delegated agent now makes THEIR OWN decision
            result = await workflow.execute_child_workflow(
                IntelligentDelegationWorkflow.run,
                args=[{
                    "customer_id": customer_id,
                    "task_id": task_id,
                    "task_description": task_description,
                    "current_agent_type": target_agent_type,
                    "context": context,
                    "delegation_depth": delegation_depth + 1
                }],
                id=f"delegation-{task_id}-{delegation_depth + 1}",
                parent_close_policy=workflow.ParentClosePolicy.TERMINATE
            )
            
            return {
                **result,
                "delegated_by": current_agent["persona_name"],
                "delegation_chain": delegation_chain
            }
        
        else:
            # Unknown action, fallback to self-execution
            return await self._handle_task_directly(customer_id, task_id, task_description, current_agent, delegation_chain)
    
    async def _handle_task_directly(self, customer_id, task_id, task_description, agent, delegation_chain):
        """Helper method for direct task execution with status updates"""
        
        # 🔔 REAL-TIME UPDATE: Fallback execution
        await workflow.execute_activity(
            update_task_status_activity,
            args=[task_id, "in_progress", agent.get("agent_type"), f"{agent['persona_name']} is handling this task"],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        response = await workflow.execute_activity(
            invoke_agent_activity,
            args=[customer_id, agent.get("agent_type"), task_description, task_id],
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # 🔔 REAL-TIME UPDATE: Completed
        await workflow.execute_activity(
            save_task_result_activity,
            args=[task_id, {"message": response.get("message", "")}, "completed"],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return {
            "status": "completed",
            "handled_by": agent["persona_name"],
            "delegation_type": "fallback_execution",
            "delegation_chain": delegation_chain
        }
