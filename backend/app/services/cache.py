import os
import json
import time
from typing import Any, Optional

CACHE_DIR = "/tmp/policity_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class Cache:
    @staticmethod
    def _get_path(key: str) -> str:
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return os.path.join(CACHE_DIR, f"{safe_key}.json")

    @staticmethod
    def get(key: str) -> Optional[Any]:
        path = Cache._get_path(key)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            if "expire_at" in data and time.time() > data["expire_at"]:
                os.remove(path)
                return None
                
            return data.get("value")
        except Exception:
            return None

    @staticmethod
    def set(key: str, value: Any, ttl_seconds: int = 86400):
        path = Cache._get_path(key)
        data = {
            "value": value,
            "expire_at": time.time() + ttl_seconds
        }
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Cache write error: {e}")
