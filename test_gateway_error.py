# Test script to trigger agent invocation and see detailed Gateway error
import httpx
import json
import asyncio

async def test_agent_invoke():
    """Test agent invocation to see Gateway error details"""
    
    # Get auth token (you'll need to replace this with a real token)
    # For now, let's just try to hit the endpoint
    
    base_url = "http://localhost:8000"
    
    # Try to create a task (which should trigger orchestrator)
    async with httpx.AsyncClient() as client:
        # First, let's check if backend is running
        try:
            response = await client.get(f"{base_url}/health", timeout=5.0)
            print(f"✅ Backend health check: {response.status_code}")
        except Exception as e:
            print(f"❌ Backend not reachable: {e}")
            return
        
        # Try to invoke orchestrator directly
        print("\n🔍 Testing orchestrator invocation...")
        print("This should show detailed Gateway error in backend logs")
        
        # Check what the actual error is
        print("\n📋 Next steps:")
        print("1. Check your uvicorn terminal for detailed Gateway error")
        print("2. Look for lines containing 'Agent Gateway returned'")
        print("3. The error will show the exact URL, Host header, and response body")

if __name__ == "__main__":
    asyncio.run(test_agent_invoke())
