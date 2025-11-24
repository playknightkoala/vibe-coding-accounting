#!/usr/bin/env python3
"""
Production Fix Tool
This script checks the production database for missing columns and adds them if necessary.
It is designed to be run directly on the production server or inside the backend container.
"""

import os
import sys
import psycopg
from urllib.parse import urlparse

def get_db_connection():
    """Get database connection using environment variables."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        sys.exit(1)
        
    # Handle SQLAlchemy format if present
    if database_url.startswith('postgresql+psycopg://'):
        database_url = database_url.replace('postgresql+psycopg://', 'postgresql://')
        
    return psycopg.connect(database_url)

def check_and_add_column(cursor, table, column, data_type):
    """Check if a column exists and add it if missing."""
    print(f"Checking {table}.{column}...")
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    
    if not cursor.fetchone():
        print(f"  -> Column missing. Adding {column} ({data_type})...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {data_type}")
        return True
    else:
        print("  -> Column exists.")
        return False

def fix_schema():
    """Fix database schema by adding missing columns."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        changes_made = False
        
        # 1. Check transactions table for foreign currency columns
        if check_and_add_column(cursor, 'transactions', 'foreign_amount', 'FLOAT'):
            changes_made = True
        if check_and_add_column(cursor, 'transactions', 'foreign_currency', 'VARCHAR'):
            changes_made = True
            
        # 2. Check budgets table for daily_limit
        if check_and_add_column(cursor, 'budgets', 'daily_limit', 'FLOAT'):
            changes_made = True
            
        if changes_made:
            conn.commit()
            print("\n✓ Schema fixes applied successfully.")
        else:
            print("\n✓ Schema is already up to date.")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Error fixing schema: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Production Schema Fix Tool")
    print("=" * 50)
    
    if fix_schema():
        print("\nYou can now restart the backend service to ensure all changes are picked up.")
    else:
        sys.exit(1)
