import asyncio
from pymongo import AsyncMongoClient
import os

async def test_connection():
    try:
        # Your exact connection string
        url = "mongodb+srv://abdullahEcommerce:ecommerce@cluster0.b8qkk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        
        print("Attempting to connect...")
        client = AsyncMongoClient(url, serverSelectionTimeoutMS=10000)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connection successful!")
        
        # List databases
        databases = await client.list_database_names()
        print(f"Databases available: {databases}")
        
        client.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if cluster is paused in MongoDB Atlas")
        print("2. Verify username and password")
        print("3. Check network connection")
        print("4. Try connecting via MongoDB Compass")

asyncio.run(test_connection())