"""
Load Test Script for Intelligent Delegation
Simulates 100 concurrent complex tasks to verify autonomous agent scaling
"""
import asyncio
import uuid
from temporalio.client import Client
from datetime import datetime
import json


COMPLEX_TASKS = [
    "Launch a comprehensive product marketing campaign with social media, email, and content strategy",
    "Create a complete brand identity including logo, style guide, and marketing materials",
    "Develop a data-driven customer acquisition strategy with analytics and A/B testing",
    "Design and implement a multi-channel customer engagement program",
    "Build a content marketing strategy with blog posts, videos, and infographics",
    "Create a product launch plan with PR, influencer outreach, and paid advertising",
    "Develop a customer retention program with loyalty rewards and personalized communications",
    "Design a comprehensive social media strategy across all major platforms",
    "Create a lead generation campaign with landing pages, forms, and nurture sequences",
    "Build an email marketing automation workflow with segmentation and personalization"
]


async def submit_task(client: Client, task_num: int, task_description: str):
    """Submit a single complex task"""
    task_id = f"load-test-{task_num}-{uuid.uuid4()}"
    
    try:
        start_time = datetime.now()
        
        # Start workflow
        handle = await client.start_workflow(
            "OrchestratorWorkflow",
            args=[{
                "customer_id": f"load-test-customer-{task_num % 10}",  # 10 customers
                "task_id": task_id,
                "task_description": task_description,
                "context": {
                    "priority": "high",
                    "load_test": True,
                    "task_number": task_num
                }
            }],
            id=task_id,
            task_queue="campaign-queue"
        )
        
        # Wait for result (with timeout)
        result = await asyncio.wait_for(handle.result(), timeout=600)  # 10 min timeout
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "task_num": task_num,
            "task_id": task_id,
            "status": "success",
            "duration": duration,
            "result": result,
            "delegation_type": result.get("delegation_type"),
            "delegation_chain": result.get("delegation_chain", [])
        }
        
    except asyncio.TimeoutError:
        return {
            "task_num": task_num,
            "task_id": task_id,
            "status": "timeout",
            "error": "Workflow exceeded 10 minute timeout"
        }
    except Exception as e:
        return {
            "task_num": task_num,
            "task_id": task_id,
            "status": "error",
            "error": str(e)
        }


async def run_load_test(num_tasks: int = 100):
    """
    Run load test with concurrent task submissions.
    
    Expected behavior:
    - 100 tasks submitted
    - Each spawns 2-5 sub-delegations
    - Total: 300-500 concurrent workflows
    - K8s should scale workers from 3 → 15-20 pods
    """
    print(f"🚀 Starting load test with {num_tasks} concurrent tasks...")
    print(f"⏰ Start time: {datetime.now()}")
    
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    
    # Create tasks
    tasks = []
    for i in range(num_tasks):
        task_desc = COMPLEX_TASKS[i % len(COMPLEX_TASKS)]
        tasks.append(submit_task(client, i, task_desc))
    
    # Execute all tasks concurrently
    print(f"📤 Submitting {num_tasks} tasks...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyze results
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    failed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
    timeout = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "timeout")
    
    # Calculate delegation stats
    delegation_types = {}
    total_delegations = 0
    max_chain_length = 0
    
    for r in results:
        if isinstance(r, dict) and r.get("status") == "success":
            dtype = r.get("delegation_type", "unknown")
            delegation_types[dtype] = delegation_types.get(dtype, 0) + 1
            
            chain = r.get("delegation_chain", [])
            total_delegations += len(chain)
            max_chain_length = max(max_chain_length, len(chain))
    
    avg_duration = sum(
        r.get("duration", 0) for r in results 
        if isinstance(r, dict) and r.get("status") == "success"
    ) / max(successful, 1)
    
    # Print results
    print("\n" + "="*60)
    print("📊 LOAD TEST RESULTS")
    print("="*60)
    print(f"✅ Successful: {successful}/{num_tasks} ({successful/num_tasks*100:.1f}%)")
    print(f"❌ Failed: {failed}/{num_tasks}")
    print(f"⏱️  Timeout: {timeout}/{num_tasks}")
    print(f"\n📈 Delegation Statistics:")
    print(f"   Total delegations: {total_delegations}")
    print(f"   Avg delegations per task: {total_delegations/max(successful, 1):.1f}")
    print(f"   Max delegation chain: {max_chain_length}")
    print(f"\n🎯 Delegation Types:")
    for dtype, count in delegation_types.items():
        print(f"   {dtype}: {count} ({count/successful*100:.1f}%)")
    print(f"\n⏱️  Performance:")
    print(f"   Average duration: {avg_duration:.2f}s")
    print(f"   End time: {datetime.now()}")
    print("="*60)
    
    # Save detailed results
    with open("load_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total_tasks": num_tasks,
                "successful": successful,
                "failed": failed,
                "timeout": timeout,
                "total_delegations": total_delegations,
                "avg_delegations": total_delegations/max(successful, 1),
                "max_chain_length": max_chain_length,
                "delegation_types": delegation_types,
                "avg_duration": avg_duration
            },
            "results": [r for r in results if isinstance(r, dict)]
        }, f, indent=2)
    
    print("\n💾 Detailed results saved to load_test_results.json")
    
    return results


if __name__ == "__main__":
    # Run with different scales
    print("Choose load test scale:")
    print("1. Small (10 tasks)")
    print("2. Medium (50 tasks)")
    print("3. Large (100 tasks)")
    print("4. Extreme (200 tasks)")
    
    choice = input("Enter choice (1-4): ").strip()
    
    scale_map = {"1": 10, "2": 50, "3": 100, "4": 200}
    num_tasks = scale_map.get(choice, 100)
    
    asyncio.run(run_load_test(num_tasks))
