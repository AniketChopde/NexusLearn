
import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from models.engagement import Engagement
from sqlalchemy import text

async def migrate():
    """Create engagements table."""
    async with engine.begin() as conn:
        try:
            # Check if table exists
            result = await conn.execute(text(
                "SELECT count(*) FROM pragma_table_info('engagements')"
            ))
            exists = result.scalar() > 0
            
            if not exists:
                print("Creating engagements table...")
                await conn.run_sync(Engagement.metadata.create_all)
                print("Migration successful: Created engagements table.")
            else:
                print("Table engagements already exists.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(migrate())
