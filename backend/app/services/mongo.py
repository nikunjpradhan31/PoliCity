import os
from pymongo import MongoClient
from datetime import datetime
from typing import Optional, Dict, Any

# Load env variables for mongo
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "infrastructure_reports")

client: Optional[MongoClient] = None

def get_mongo_client() -> MongoClient:
    global client
    if client is None:
        client = MongoClient(MONGO_URI)
    return client


def get_database():
    return get_mongo_client()[MONGO_DB_NAME]

async def setup_indexes():
    db = get_database()
    collections = [
        "incidents", "agent_planner", "agent_cost_research",
        "agent_repair_plan", "agent_contractor", "agent_budget",
        "agent_validation", "agent_report"
    ]
    for collection in collections:
        db[collection].create_index("incident_id", unique=True)
    
    # TTL index on incidents for 1 year
    db["incidents"].create_index("created_at", expireAfterSeconds=31536000)

async def get_incident(incident_id: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    return db.incidents.find_one({"incident_id": incident_id})

async def save_incident(incident_id: str, data: Dict[str, Any]):
    db = get_database()
    data["updated_at"] = datetime.utcnow()
    db.incidents.replace_one({"incident_id": incident_id}, data, upsert=True)

async def get_agent_output(agent_id: str, incident_id: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    collection = f"agent_{agent_id}"
    if agent_id == "report":
        collection = "agent_report"
    elif agent_id == "validation":
        collection = "agent_validation"
    return db[collection].find_one({"incident_id": incident_id})

async def save_agent_output(agent_id: str, incident_id: str, payload: Dict[str, Any]):
    db = get_database()
    collection = f"agent_{agent_id}"
    if agent_id == "report":
        collection = "agent_report"
    elif agent_id == "validation":
        collection = "agent_validation"
    db[collection].replace_one({"incident_id": incident_id}, payload, upsert=True)

async def delete_agent_output(agent_id: str, incident_id: str):
    db = get_database()
    collection = f"agent_{agent_id}"
    if agent_id == "report":
        collection = "agent_report"
    elif agent_id == "validation":
        collection = "agent_validation"
    db[collection].delete_one({"incident_id": incident_id})
