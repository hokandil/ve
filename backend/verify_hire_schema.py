import asyncio
from app.core.database import get_supabase_admin
import uuid

async def verify_schema():
    supabase = get_supabase_admin()
    
    print("Verifying customer_ves schema...")
    
    customer_id = str(uuid.uuid4())
    customer_ve_id = str(uuid.uuid4())
    
    data = {
        "id": customer_ve_id,
        "customer_id": customer_id,
        "marketplace_agent_id": str(uuid.uuid4()),
        "agent_type": "marketing-manager",
        "agent_gateway_route": f"/agents/{customer_id}/marketing-manager",
        "status": "active",
        "persona_name": "Test Agent",
        "persona_email": "test@example.com"
        # agent_name and agent_namespace OMITTED (should be allowed as NULL)
    }
    
    try:
        print(f"Attempting insert with data: {data}")
        supabase.table("customer_ves").insert(data).execute()
        print("✅ Insert successful (unexpected but means schema is valid)")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Result: {error_msg}")
        
        if "foreign key constraint" in error_msg:
            print("✅ Schema verification PASSED: Columns exist and nullable constraints are removed.")
        elif "violates not-null constraint" in error_msg:
            print(f"❌ Schema verification FAILED: {error_msg}")
        elif "column" in error_msg and "does not exist" in error_msg:
             print("❌ Schema verification FAILED: New columns do not exist.")
        else:
            print(f"⚠️ Unknown error: {error_msg}")

if __name__ == "__main__":
    asyncio.run(verify_schema())
