
import asyncio
import os
import sys

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from sqlalchemy import text

async def migrate():
    """Add is_superuser column to users table."""
    async with engine.begin() as conn:
        try:
            # Check if column exists
            result = await conn.execute(text(
                "SELECT count(*) FROM pragma_table_info('users') WHERE name='is_superuser'"
            ))
            exists = result.scalar() > 0
            
            if not exists:
                print("Adding is_superuser column to users table...")
                await conn.execute(text("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT 0"))
                print("Migration successful: Added is_superuser column.")
            else:
                print("Column is_superuser already exists.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
