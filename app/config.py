import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "multi-ai-system")
    
    # App
    DEBUG = os.getenv("DEBUG", "True") == "True"

config = Config()