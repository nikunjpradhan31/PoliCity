"""MongoDB database connection module using Motor async client."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """Establish connection to MongoDB."""
    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    _db = _client[settings.MONGO_DB_NAME]
    
    # Create indexes
    await _create_indexes()


async def _create_indexes() -> None:
    """Create necessary database indexes."""
    if _db is None:
        return
    
    # Potholes collection indexes
    await _db.potholes.create_index("external_id", unique=True)
    await _db.potholes.create_index([("location", "2dsphere")])
    await _db.potholes.create_index("city")
    await _db.potholes.create_index("status")
    
    # Budgets collection indexes
    await _db.budgets.create_index("city")
    await _db.budgets.create_index("year")
    
    # Optimizations collection indexes
    await _db.optimizations.create_index("run_id", unique=True)
    await _db.optimizations.create_index("city")
    
    # Reports collection indexes
    await _db.reports.create_index("run_id")


async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo first.")
    return _db


# Collection getters
def get_potholes_collection():
    """Get potholes collection."""
    return get_database().potholes


def get_budgets_collection():
    """Get budgets collection."""
    return get_database().budgets


def get_optimizations_collection():
    """Get optimizations collection."""
    return get_database().optimizations


def get_reports_collection():
    """Get reports collection."""
    return get_database().reports
