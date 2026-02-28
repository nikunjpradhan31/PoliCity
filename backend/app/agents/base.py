import os
from datetime import datetime
import json
import time
from typing import Dict, Any
from pydantic import BaseModel
from google import genai
from google.genai import types

class AgentBase:
    def __init__(self, name: str):
        self.name = name
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print(f"Warning: GOOGLE_API_KEY not set for {self.name}")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.model_name = "gemini-2.5-flash"  # using a known fast model

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the agent and returns standard envelope output."""
        start_time = time.time()
        
        try:
            result_data = await self.execute(inputs)
            confidence = 0.9 # placeholder, real logic could parse this
        except Exception as e:
            result_data = {"error": str(e)}
            confidence = 0.0

        duration_ms = int((time.time() - start_time) * 1000)
        
        return {
            "agent_id": self.name,
            "executed_at": datetime.utcnow().isoformat() + "Z",
            "duration_ms": duration_ms,
            "model_used": self.model_name,
            "tokens_used": 0, # Could be pulled from usageMetadata
            "confidence": confidence,
            "data": result_data
        }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method in subclasses."""
        raise NotImplementedError
