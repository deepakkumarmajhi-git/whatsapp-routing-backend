from motor.motor_asyncio import AsyncIOMotorClient
from app.config.config import settings

class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None

    def connect_to_database(self):
        """Initializes the MongoDB client pool."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        print(f"🔌 Successfully connected to MongoDB: {settings.MONGO_DB_NAME}")

    def close_database_connection(self):
        """Closes the MongoDB client pool cleanly on shutdown."""
        if self.client:
            self.client.close()
            print("🛑 MongoDB connection closed cleanly.")

# Create a single database manager instance
db_manager = MongoDB()

# Quick helper functions to get collections easily in routers/services
def get_collection(collection_name: str):
    return db_manager.db[collection_name]