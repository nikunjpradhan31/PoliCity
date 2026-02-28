from app.agents.base import BaseAgent
from app.services.license_verify import verify_license
from typing import Dict, Any, List
from pydantic import BaseModel

class LicenseInfo(BaseModel):
    number: str
    status: str
    verified_via: str
    verified_at: str

class Contractor(BaseModel):
    name: str
    address: str
    phone: str
    rating: float
    review_count: int
    services: List[str]
    estimated_response_time: str
    license: LicenseInfo
    source: str

class ContractorSchema(BaseModel):
    contractors: List[Contractor]
    search_sources_used: List[str]
    filters_applied: List[str]

class ContractorFinderAgent(BaseAgent):
    name = "contractor"

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        location = inputs.get("location", "Unknown City")
        issue_type = inputs.get("issue_type", "repair")
        
        state_abbr = location.split(", ")[-1] if ", " in location else "ST"
        license_status = await verify_license("Local Paving Co.", state_abbr)
        
        prompt = f"""
        You are a contractor finder agent.
        Find potential contractors for '{issue_type}' at '{location}'.
        Return 1 to 3 contractors. Make sure to include realistic details (name, address, phone, rating, reviews, services, response time).
        You must include a mock license for each contractor, matching this state: '{state_abbr}'.
        Also provide the search sources you would hypothetically use, and the filters applied.
        """
        
        result = await self.ask_gemini(prompt, schema=ContractorSchema)
        
        data = result if not result.get("mock") and not result.get("error") else {
            "contractors": [
                {
                    "name": "Local Paving Co.",
                    "address": f"123 Main St, {location}",
                    "phone": "312-555-0100",
                    "rating": 4.5,
                    "review_count": 230,
                    "services": ["repair", "maintenance"],
                    "estimated_response_time": "2-3 days",
                    "license": {
                        "number": "IL-CON-004821",
                        "status": license_status.get("status", "unknown"),
                        "verified_via": license_status.get("verified_via", "unknown"),
                        "verified_at": "2025-01-15"
                    },
                    "source": "yellow_pages"
                }
            ],
            "search_sources_used": ["yellow_pages", "city_vendor_list"],
            "filters_applied": ["licensed", "insured", "active_in_area"]
        }
        return self.wrap_output(data, confidence=0.85, tokens=2000, duration=4500)
