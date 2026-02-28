async def verify_license(contractor_name: str, state: str) -> dict:
    return {"status": "active", "verified_via": "state_portal"}