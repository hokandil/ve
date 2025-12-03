"""
Seed marketplace with initial VE agents
Run this to populate the marketplace with sample agents
"""
import asyncio
from app.core.database import get_supabase_admin
import uuid

async def seed_marketplace():
    """Seed marketplace with sample VEs"""
    supabase = get_supabase_admin()
    
    sample_ves = [
        {
            "id": str(uuid.uuid4()),
            "name": "Sarah Johnson",
            "role": "Marketing Manager",
            "department": "marketing",
            "seniority_level": "manager",
            "status": "stable",
            "pricing_monthly": 187,
            "description": "Strategic marketing leader with expertise in campaign management and team coordination",
            "category": "Marketing",
            "source": "platform",
            "skills": ["Campaign Management", "Team Leadership", "Analytics", "Strategy"],
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Alex Chen",
            "role": "Senior Marketing Specialist",
            "department": "marketing",
            "seniority_level": "senior",
            "status": "stable",
            "pricing_monthly": 149,
            "description": "Experienced marketing specialist focused on content creation and SEO",
            "category": "Marketing",
            "source": "platform",
            "skills": ["Content Creation", "SEO", "Social Media", "Analytics"],
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Jamie Taylor",
            "role": "Junior Content Creator",
            "department": "marketing",
            "seniority_level": "junior",
            "status": "stable",
            "pricing_monthly": 99,
            "description": "Creative content creator specializing in social media and blog posts",
            "category": "Marketing",
            "source": "platform",
            "skills": ["Content Writing", "Social Media", "Copywriting"],
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]
    
    print("Seeding marketplace with sample VEs...")
    
    for ve in sample_ves:
        try:
            # Check if already exists
            existing = supabase.table("virtual_employees").select("id").eq("name", ve["name"]).execute()
            
            if existing.data:
                print(f"✓ {ve['name']} already exists")
                continue
            
            # Insert
            result = supabase.table("virtual_employees").insert(ve).execute()
            print(f"✓ Added {ve['name']} - {ve['role']}")
            
        except Exception as e:
            print(f"✗ Failed to add {ve['name']}: {e}")
    
    print("\nDone! Marketplace seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_marketplace())
