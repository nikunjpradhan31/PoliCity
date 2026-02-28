import os
import json
import logging
from typing import Dict, Any, Type
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash"  # Using 2.5 flash as 3-flash preview may not be readily available via google-genai or we use whatever is available in SDK

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class BaseAgent:
    name: str = "base_agent"

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Override to implement agent specific logic"""
        raise NotImplementedError()

    async def ask_gemini(self, prompt: str, schema: Type[Any] = None) -> Dict[str, Any]:
        if not client:
            logger.warning(f"{self.name} returning mock data because GEMINI_API_KEY is missing.")
            return {"mock": True}
        
        try:
            config = types.GenerateContentConfig()
            if schema:
                config.response_mime_type = "application/json"
                config.response_schema = schema

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config
            )
            
            if schema:
                return json.loads(response.text)
            return {"text": response.text}
        except Exception as e:
            logger.error(f"Gemini API error in {self.name}: {e}")
            return {"error": str(e), "confidence": 0.1}

    def wrap_output(self, data: Dict[str, Any], confidence: float = 0.9, tokens: int = 1500, duration: int = 2000) -> Dict[str, Any]:
        import datetime
        return {
            "agent_id": self.name,
            "executed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "duration_ms": duration,
            "model_used": MODEL_NAME,
            "tokens_used": tokens,
            "confidence": confidence,
            "data": data
        }
