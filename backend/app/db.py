"""
MongoDB client and helper functions for PoliCity API.
"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.client_session import ClientSession
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection URI
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "policity")

# MongoDB client instance
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    """
    Get or create MongoDB client instance.
    
    Returns:
        MongoClient: The MongoDB client instance.
    """
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_database() -> Database:
    """
    Get the MongoDB database instance.
    
    Returns:
        Database: The MongoDB database instance.
    """
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[MONGO_DB_NAME]
    return _db


def get_collection(collection_name: str):
    """
    Get a collection from the database.
    
    Args:
        collection_name: Name of the collection.
    
    Returns:
        Collection: The MongoDB collection.
    """
    db = get_database()
    return db[collection_name]


def close_mongo_connection():
    """Close the MongoDB connection."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
