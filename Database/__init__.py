"""
Database package for the Master Extractor Bot.
Provides db and standarddb namespaces with MongoDB operations using motor.
"""
import motor.motor_asyncio
from config import Config
from datetime import datetime, timedelta
import pytz
import logging

LOGGER = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class Database:
    """Main database class handling subscribers, premium users, and backup files."""
    
    def __init__(self, db_url, db_name):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
        self.db = self.client[db_name]
        self.subscribers = self.db["subscribers"]
        self.premium_users = self.db["premium_users"]
        self.backup_files = self.db["backup_files"]
        LOGGER.info(f"Database connected: {db_name}")
    
    # ---- Subscriber Methods ----
    async def save_subscriber(self, user_id):
        """Save a subscriber to the database."""
        try:
            existing = await self.subscribers.find_one({"_id": user_id})
            if not existing:
                await self.subscribers.insert_one({"_id": user_id, "joined_at": datetime.now(IST)})
        except Exception as e:
            LOGGER.error(f"Error saving subscriber {user_id}: {e}")
    
    async def get_subscription_count(self):
        """Get total number of subscribers."""
        return await self.subscribers.count_documents({})
    
    async def get_subscribers_collections(self):
        """Get all subscribers cursor."""
        return self.subscribers.find({})
    
    # ---- Premium User Methods ----
    async def add_premium(self, user_id, days, subscription_type):
        """Add or update premium status for a user."""
        now = datetime.now(IST)
        expires_at = now + timedelta(days=days)
        await self.premium_users.update_one(
            {"_id": user_id},
            {"$set": {
                "start_at": now,
                "expires_at": expires_at,
                "subscription_type": subscription_type,
                "days": days
            }},
            upsert=True
        )
    
    async def get_premium_user(self, user_id):
        """Get premium user data."""
        user = await self.premium_users.find_one({"_id": user_id})
        if user:
            # Check if expired
            expires_at = user.get('expires_at')
            if expires_at:
                if expires_at.tzinfo is None:
                    expires_at = IST.localize(expires_at)
                if expires_at < datetime.now(IST):
                    # Premium expired, remove
                    await self.premium_users.delete_one({"_id": user_id})
                    return None
        return user
    
    async def get_premium_collection(self):
        """Get all premium users cursor."""
        return self.premium_users.find({})
    
    async def remove_user_from_premium(self, user_id):
        """Remove a user from premium."""
        await self.premium_users.delete_one({"_id": user_id})
    
    async def access_checking(self, user_id):
        """Check if user has access (admin or premium)."""
        if user_id in Config.ADMIN_ID:
            return True, "admin"
        user = await self.get_premium_user(user_id)
        if user:
            return True, user.get('subscription_type', 'V')
        return False, None
    
    # ---- Backup File Methods ----
    async def save_backup_file(self, user_id, file_name, file_data, caption=""):
        """Save a backup file for a user."""
        await self.backup_files.insert_one({
            "user_id": user_id,
            "file_name": file_name,
            "file_data": file_data,
            "caption": caption,
            "created_at": datetime.now(IST)
        })
    
    async def get_backup_files(self, user_id):
        """Get all backup files for a user."""
        cursor = self.backup_files.find({"user_id": user_id})
        return await cursor.to_list(length=None)
    
    async def get_all_backup_files(self):
        """Get all backup files (admin only)."""
        cursor = self.backup_files.find({})
        return await cursor.to_list(length=None)
    
    async def remove_all_backup_files(self):
        """Remove all backup files."""
        await self.backup_files.delete_many({})


class StandardDB:
    """Database class for standard/shared data like Appx APIs."""
    
    def __init__(self, db_url, db_name):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
        self.db = self.client[db_name]
        self.appx_apis = self.db["appx_apis"]
        LOGGER.info(f"StandardDB connected: {db_name}")
    
    async def insert_or_update_appx_api(self, app_name, api_url):
        """Insert or update an Appx API entry."""
        await self.appx_apis.update_one(
            {"app_name": app_name},
            {"$set": {
                "app_name": app_name,
                "api_url": api_url,
                "updated_at": datetime.now(IST)
            }},
            upsert=True
        )
    
    async def get_appx_api(self, app_name):
        """Get API URL for an app."""
        doc = await self.appx_apis.find_one({"app_name": app_name})
        return doc.get("api_url") if doc else None
    
    async def get_all_appx_apis(self):
        """Get all Appx API entries."""
        cursor = self.appx_apis.find({})
        return await cursor.to_list(length=None)


# Database namespace classes (to match `db.db_instance.method()` pattern)
class DBNamespace:
    def __init__(self):
        self.db_instance = Database(Config.DB_URL, Config.DB_NAME)

class StandardDBNamespace:
    def __init__(self):
        self.db_instance = StandardDB(Config.DB_URL, Config.DB_NAME)


# Create singleton instances
db = DBNamespace()
standarddb = StandardDBNamespace()
