import logging
import asyncio
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    in_memory_users: Dict[str, Dict[str, Any]] = {} # Fallback in-memory collection if Mongo Atlas offline

db_instance = MongoDB()

async def connect_to_mongo():
    logger.info("Initializing MongoDB connection...")
    try:
        if settings.MONGODB_URI:
            db_instance.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=4000
            )
            db_instance.db = db_instance.client[settings.MONGODB_DB_NAME]
            # Ping database to verify connection
            await db_instance.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB Atlas!")
            return
    except Exception as e:
        logger.warning(f"Could not connect to live MongoDB Atlas ({e}). Operating in resilient fallback database mode.")
    
    db_instance.client = None
    db_instance.db = None

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    return db_instance.db
