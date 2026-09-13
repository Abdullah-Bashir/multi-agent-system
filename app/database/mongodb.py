from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure
from config import config

class MongoDB:
    client = None
    db = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB Atlas"""
        if cls.client is None:
            try:
                # Use ServerApi for better compatibility
                cls.client = AsyncMongoClient(
                    config.MONGODB_URL,
                    server_api=ServerApi('1'),
                    serverSelectionTimeoutMS=10000,
                )
                cls.db = cls.client[config.DATABASE_NAME]
                
                # Test connection
                await cls.client.admin.command('ping')
                print(f"✅ Connected to MongoDB: {config.DATABASE_NAME}")
                return cls.db
            except ConnectionFailure as e:
                print(f"❌ MongoDB connection failed: {e}")
                raise
        return cls.db

    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            print("✅ Disconnected from MongoDB")

    @classmethod
    def get_db(cls):
        """Get database instance"""
        return cls.db

async def get_db():
    """Get database connection"""
    if MongoDB.db is None:
        await MongoDB.connect()
    return MongoDB.db