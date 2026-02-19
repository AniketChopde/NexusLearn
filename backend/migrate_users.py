import sqlite3
import os

DB_PATH = "study_planner.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Migrating database...")
        
        # Add reset_token column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token VARCHAR(255)")
            print("Added reset_token column.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("reset_token column already exists.")
            else:
                print(f"Error adding reset_token: {e}")

        # Add reset_token_expires column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP")
            print("Added reset_token_expires column.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("reset_token_expires column already exists.")
            else:
                print(f"Error adding reset_token_expires: {e}")

        conn.commit()
        print("Migration complete.")
    
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
