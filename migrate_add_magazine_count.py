"""
Migration script to add magazine_count column to character_ranged_weapon table
Save this as migrate_add_magazine_count.py and run it separately

Usage:
python migrate_add_magazine_count.py
"""

import sqlite3
import os

# Database file path
db_path = 'instance/dsa_proben.db'

def migrate_database():
    """
    Add magazine_count column to character_ranged_weapon table
    """
    if not os.path.exists(db_path):
        print(f"Database file '{db_path}' not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(character_ranged_weapon)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'magazine_count' in columns:
            print("Column 'magazine_count' already exists in character_ranged_weapon table.")
        else:
            # Add the new column with default value 0
            cursor.execute("ALTER TABLE character_ranged_weapon ADD COLUMN magazine_count INTEGER DEFAULT 0")
            conn.commit()
            print("Successfully added 'magazine_count' column to character_ranged_weapon table.")
        
        # Close connection
        conn.close()
        return True
    
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Starting database migration...")
    if migrate_database():
        print("Migration completed successfully!")
    else:
        print("Migration failed!")