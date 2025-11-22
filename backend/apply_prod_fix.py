import os
import sys
import time
from sqlalchemy import create_engine, text, inspect

# Add current directory to path
sys.path.append(os.getcwd())

def get_database_url():
    # Try to get from environment variable first
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("WARNING: DATABASE_URL not found in environment.")
        # Fallback for local testing if needed, but in production this should be set
        return "postgresql://accounting_user:accounting_pass@db:5432/accounting_db"
    return url

def fix_driver_in_url(url):
    # SQLAlchemy with psycopg 3 requires postgresql+psycopg://
    if url.startswith("postgresql://") and "psycopg" not in url:
        try:
            import psycopg
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        except ImportError:
            print("psycopg (v3) not found, assuming psycopg2 or other driver.")
    return url

def migrate_production_db():
    print("Starting production database migration check...")
    
    raw_url = get_database_url()
    # Mask password for logging
    safe_url = raw_url.split("@")[-1] if "@" in raw_url else "..."
    print(f"Target Database Host: {safe_url}")
    
    url = fix_driver_in_url(raw_url)
    
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print("Successfully connected to database.")
            
            inspector = inspect(engine)
            columns = inspector.get_columns('transactions')
            column_names = [col['name'] for col in columns]
            
            if 'note' in column_names:
                print("✅ Column 'note' already exists in 'transactions' table. No action needed.")
            else:
                print("⚠️ Column 'note' is MISSING in 'transactions' table.")
                print("Attempting to add 'note' column...")
                
                try:
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN note VARCHAR"))
                    conn.commit()
                    print("✅ Successfully added 'note' column to 'transactions' table.")
                except Exception as e:
                    print(f"❌ Failed to add column: {e}")
                    raise e
                    
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_production_db()
