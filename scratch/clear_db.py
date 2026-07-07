import asyncio
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.db_models import ChatMessage, Conversation, RequestLog, User
from sqlalchemy import delete

async def clear_database():
    print("=== STARTING DATABASE CLEANUP ===")
    async with AsyncSessionLocal() as session:
        try:
            # 1. Delete all chat messages
            print("Deleting all ChatMessages...")
            await session.execute(delete(ChatMessage))
            
            # 2. Delete all conversations
            print("Deleting all Conversations...")
            await session.execute(delete(Conversation))
            
            # 3. Delete all request logs
            print("Deleting all RequestLogs...")
            await session.execute(delete(RequestLog))
            
            # 4. Delete all guest users (keeping only admin or active custom users if any)
            print("Deleting guest users...")
            await session.execute(delete(User).where(User.role == "guest"))
            
            await session.commit()
            print("=== DATABASE CLEANUP SUCCESSFUL ===")
        except Exception as e:
            await session.rollback()
            print(f"=== DATABASE CLEANUP FAILED: {e} ===")

if __name__ == "__main__":
    # Ensure env vars are loaded
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(clear_database())
