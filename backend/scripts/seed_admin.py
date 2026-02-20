
import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db, AsyncSessionLocal
from models.user import User
# from passlib.context import CryptContext  <-- Removed
from utils.auth import hash_password
from sqlalchemy import select

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") <-- Removed

async def seed_admin():
    async with AsyncSessionLocal() as db:
        try:
            email = input("Enter admin email: ")
            
            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if user:
                print(f"User {email} found. Promoting to admin...")
                user.is_superuser = True
                user.is_verified = True
                await db.commit()
                print("Success! User promoted to admin.")
            else:
                print(f"User {email} not found. Creating new admin...")
                password = input("Enter admin password: ")
                hashed_password = hash_password(password)
                
                new_user = User(
                    email=email,
                    password_hash=hashed_password,
                    full_name="Admin User",
                    is_active=True,
                    is_verified=True,
                    is_superuser=True
                )
                db.add(new_user)
                await db.commit()
                print("Success! New admin user created.")
                
        except Exception as e:
            print(f"Error seeding admin: {e}")
            await db.rollback()

if __name__ == "__main__":
    # Windows SelectorEventLoopPolicy fix for Python 3.8+
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_admin())
