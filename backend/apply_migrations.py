"""
Apply database migrations to Supabase
Run this script to apply pending migrations
"""
from app.core.database import get_supabase_admin
from pathlib import Path

def apply_migration(migration_file: str):
    """Apply a single migration file"""
    supabase = get_supabase_admin()
    
    migration_path = Path(__file__).parent / "migrations" / migration_file
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"\n📄 Applying migration: {migration_file}")
    print("=" * 60)
    
    # Read SQL
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    print(sql)
    print("=" * 60)
    
    try:
        # Execute SQL via Supabase REST API
        # Note: This uses raw SQL execution which may not be available in all Supabase plans
        # Alternative: Copy the SQL and run it manually in Supabase SQL Editor
        
        print("\n⚠️  Please copy the SQL above and run it in Supabase SQL Editor:")
        print("   1. Go to https://supabase.com/dashboard")
        print("   2. Select your project")
        print("   3. Go to SQL Editor")
        print("   4. Paste and run the SQL")
        print("\nPress Enter when done...")
        input()
        
        print("✅ Migration marked as applied")
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply migration: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Database Migration Tool")
    print("=" * 60)
    
    # Apply migrations in order
    migrations = [
        "004_security_audit_log.sql",
        "005_agent_memory_rls.sql",
        "006_shared_agents.sql"
    ]
    
    for migration in migrations:
        apply_migration(migration)
    
    print("\n✅ All migrations processed!")
