import os
import asyncio 
from dotenv import load_dotenv
from pymongo import MongoClient, IndexModel, ASCENDING

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "infrastructure_reports")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

async def setup_indexes():
    """Create necessary MongoDB indexes in a background thread."""
    incidents = db["incidents"]
    print(f"[DEBUG] Type of db['incidents']: {type(incidents)}")
    
    # Wrap index creation
    index_result = await asyncio.to_thread(incidents.create_index, "incident_id", unique=True)
    print(f"[DEBUG] Type of index_result: {type(index_result)}, value: {index_result}")
    
    # TTL index (1 year)
    await asyncio.to_thread(incidents.create_index, "created_at", expireAfterSeconds=31536000)

    # agent_thinking collection indexes
    agent_thinking = db["agent_thinking"]
    await asyncio.to_thread(agent_thinking.create_index, "incident_id", unique=True)

    # agent_report collection indexes
    agent_report = db["agent_report"]
    await asyncio.to_thread(agent_report.create_index, "incident_id", unique=True)


async def get_incident(incident_id: str) -> dict:
    return await asyncio.to_thread(db["incidents"].find_one, {"incident_id": incident_id})


async def save_incident(incident_id: str, data: dict):
    await asyncio.to_thread(
        db["incidents"].replace_one, 
        {"incident_id": incident_id}, 
        data, 
        upsert=True
    )


async def update_incident_status(incident_id: str, status: str, extra: dict = None):
    update_data = {"status": status}
    if extra:
        update_data.update(extra)
        
    await asyncio.to_thread(
        db["incidents"].update_one,
        {"incident_id": incident_id},
        {"$set": update_data},
        upsert=True
    )


async def get_agent_output(collection_name: str, incident_id: str) -> dict:
    return await asyncio.to_thread(db[collection_name].find_one, {"incident_id": incident_id})


async def save_agent_output(collection_name: str, incident_id: str, data: dict):
    await asyncio.to_thread(
        db[collection_name].replace_one, 
        {"incident_id": incident_id}, 
        data, 
        upsert=True
    )


async def delete_agent_output(collection_name: str, incident_id: str):
    await asyncio.to_thread(db[collection_name].delete_one, {"incident_id": incident_id})


def get_db():
    return db