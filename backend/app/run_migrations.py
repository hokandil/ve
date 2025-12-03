"""
Database migration runner
Applies SQL migrations to Supabase database
"""
import os
from pathlib import Path
from app.core.database import get_supabase_admin

def run_migrations():
    """Run all SQL migrations"""
    supabase = get_supabase_admin()
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    # Get all SQL files sorted by name
    sql_files = sorted(migrations_dir.glob("*.sql"))
    
    print(f"Found {len(sql_files)} migration files")
    
    for sql_file in sql_files:
        print(f"\nApplying migration: {sql_file.name}")
        
        # Read SQL content
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        try:
            # Execute SQL
            supabase.rpc('exec_sql', {'sql': sql}).execute()
            print(f"✅ Successfully applied {sql_file.name}")
        except Exception as e:
            print(f"❌ Failed to apply {sql_file.name}: {e}")
            # Continue with other migrations

if __name__ == "__main__":
    run_migrations()
