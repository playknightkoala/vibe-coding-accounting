#!/usr/bin/env python3
"""
Migration tool to add foreign_amount and foreign_currency columns to transactions table.
This script can be run directly on the production database to fix the schema mismatch.
"""

import psycopg
import os
import sys

def apply_migration():
    """Apply the foreign currency columns migration to the database."""
    
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/accounting_db')
    
    # Parse the URL to get connection parameters
    # Format: postgresql://user:password@host:port/database
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', '', 1)
    
    try:
        # Connect to database
        print(f"Connecting to database...")
        conn = psycopg.connect(database_url if database_url.startswith('postgresql://') else f'postgresql://{database_url}')
        cursor = conn.cursor()
        
        # Check if columns already exist
        print("Checking if foreign_amount column exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transactions' AND column_name='foreign_amount'
        """)
        
        if cursor.fetchone():
            print("✓ Migration already applied - foreign_amount column exists")
            cursor.close()
            conn.close()
            return True
        
        print("Applying migration...")
        
        # Add foreign_amount column
        print("  - Adding foreign_amount column...")
        cursor.execute("""
            ALTER TABLE transactions 
            ADD COLUMN foreign_amount FLOAT NULL
        """)
        
        # Add foreign_currency column
        print("  - Adding foreign_currency column...")
        cursor.execute("""
            ALTER TABLE transactions 
            ADD COLUMN foreign_currency VARCHAR NULL
        """)
        
        # Commit the changes
        conn.commit()
        print("✓ Migration applied successfully!")
        
        # Verify the columns were added
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transactions' 
            AND column_name IN ('foreign_amount', 'foreign_currency')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        print(f"\nVerification - Found columns: {[col[0] for col in columns]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Error applying migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Foreign Currency Migration Tool")
    print("=" * 60)
    print()
    
    success = apply_migration()
    
    print()
    print("=" * 60)
    if success:
        print("Migration completed successfully!")
        print("You can now restart your backend service.")
        sys.exit(0)
    else:
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)
