from geopy.geocoders import Nominatim
from typing import Dict, Any, Optional

# Provide a custom user agent to avoid rate limits
geolocator = Nominatim(user_agent="policity_app")

async def geocode_location(location: str) -> Optional[Dict[str, Any]]:
    """
    Convert a string location into coordinates.
    """
    try:
        location_data = geolocator.geocode(location)
        if location_data:
            return {
                "coordinates": {"lat": location_data.latitude, "lng": location_data.longitude},
                "neighborhood": location_data.address.split(',')[0] if location_data.address else "Unknown",
                "geocoder": "nominatim"
            }
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None
