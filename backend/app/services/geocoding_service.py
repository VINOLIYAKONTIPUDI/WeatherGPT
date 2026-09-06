import httpx
import logging
from typing import List, Optional
from app.models.schemas import LocationSearchResult, LocationCoordinates

logger = logging.getLogger(__name__)

INDIAN_POPULAR_CITIES = [
    LocationSearchResult(id=1, name="Hyderabad", latitude=17.3850, longitude=78.4867, country="India", admin1="Telangana", display_name="Hyderabad, Telangana, India"),
    LocationSearchResult(id=2, name="Vijayawada", latitude=16.5062, longitude=80.6480, country="India", admin1="Andhra Pradesh", display_name="Vijayawada, Andhra Pradesh, India"),
    LocationSearchResult(id=3, name="Delhi", latitude=28.6139, longitude=77.2090, country="India", admin1="Delhi", display_name="Delhi, National Capital Territory, India"),
    LocationSearchResult(id=4, name="Mumbai", latitude=19.0760, longitude=72.8777, country="India", admin1="Maharashtra", display_name="Mumbai, Maharashtra, India"),
    LocationSearchResult(id=5, name="Bengaluru", latitude=12.9716, longitude=77.5946, country="India", admin1="Karnataka", display_name="Bengaluru, Karnataka, India"),
    LocationSearchResult(id=6, name="Tadepalligudem", latitude=16.8123, longitude=81.5284, country="India", admin1="Andhra Pradesh", display_name="Tadepalligudem, Andhra Pradesh, India"),
    LocationSearchResult(id=7, name="Visakhapatnam", latitude=17.6868, longitude=83.2185, country="India", admin1="Andhra Pradesh", display_name="Visakhapatnam, Andhra Pradesh, India"),
    LocationSearchResult(id=8, name="Chennai", latitude=13.0827, longitude=80.2707, country="India", admin1="Tamil Nadu", display_name="Chennai, Tamil Nadu, India"),
    LocationSearchResult(id=9, name="Kolkata", latitude=22.5726, longitude=88.3639, country="India", admin1="West Bengal", display_name="Kolkata, West Bengal, India"),
    LocationSearchResult(id=10, name="Pune", latitude=18.5204, longitude=73.8567, country="India", admin1="Maharashtra", display_name="Pune, Maharashtra, India"),
]

class GeocodingService:
    @staticmethod
    def get_popular_cities() -> List[LocationSearchResult]:
        return INDIAN_POPULAR_CITIES

    @classmethod
    async def search_location(cls, query: str) -> List[LocationSearchResult]:
        if not query or len(query.strip()) < 2:
            return cls.get_popular_cities()

        query_clean = query.strip().lower()

        # Check in pre-cached cities first for instant response
        matched_cached = [
            c for c in INDIAN_POPULAR_CITIES
            if query_clean in c.name.lower() or query_clean in c.display_name.lower()
        ]

        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": query.strip(), "count": 8, "language": "en", "format": "json"}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    out = []
                    for item in results:
                        name = item.get("name", "")
                        admin1 = item.get("admin1", "")
                        country = item.get("country", "")
                        disp_parts = [p for p in [name, admin1, country] if p]
                        display_name = ", ".join(disp_parts)

                        out.append(LocationSearchResult(
                            id=item.get("id"),
                            name=name,
                            latitude=float(item.get("latitude")),
                            longitude=float(item.get("longitude")),
                            country=country,
                            admin1=admin1,
                            display_name=display_name
                        ))
                    if out:
                        return out
        except httpx.TimeoutException:
            logger.warning("Geocoding API connection timed out. Using cached search fallback.")
        except Exception as e:
            logger.warning(f"Geocoding API error: {e}. Using cached search fallback.")

        return matched_cached if matched_cached else cls.get_popular_cities()

    @classmethod
    async def reverse_geocode(cls, latitude: float, longitude: float) -> LocationCoordinates:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": latitude, "lon": longitude, "format": "json"}
        headers = {"User-Agent": "WeatherGPT-Hackathon-App/1.0"}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url, params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    addr = data.get("address", {})
                    
                    locality = addr.get("locality") or addr.get("suburb") or addr.get("neighbourhood") or addr.get("hamlet") or addr.get("residential")
                    village_town = addr.get("village") or addr.get("town") or addr.get("city") or addr.get("county")

                    # Check for Chinamiram / Bhimavaram bounding box (lat 16.51 to 16.58, lon 81.48 to 81.56)
                    is_chinamiram_area = (16.51 <= latitude <= 16.58 and 81.48 <= longitude <= 81.56)
                    addr_str = str(addr).lower()

                    if is_chinamiram_area or "chinamiram" in addr_str or "pedda amiram" in addr_str or "peddaamiram" in addr_str:
                        name = "Chinamiram"
                    else:
                        name = locality or village_town or "Current Location"
                        if "pedda amiram" in name.lower() or "peddaamiram" in name.lower():
                            name = "Chinamiram"

                    country = addr.get("country", "India")
                    admin1 = addr.get("state", "Andhra Pradesh")
                    return LocationCoordinates(
                        latitude=latitude,
                        longitude=longitude,
                        name=name,
                        country=country,
                        admin1=admin1
                    )
        except Exception as e:
            logger.warning(f"Reverse geocoding error: {e}")

        if 16.51 <= latitude <= 16.58 and 81.48 <= longitude <= 81.56:
            return LocationCoordinates(
                latitude=latitude,
                longitude=longitude,
                name="Chinamiram",
                country="India",
                admin1="Andhra Pradesh"
            )

        # Nearest fallback among popular cities
        best_city = INDIAN_POPULAR_CITIES[0]
        min_dist = 999999
        for city in INDIAN_POPULAR_CITIES:
            dist = (city.latitude - latitude) ** 2 + (city.longitude - longitude) ** 2
            if dist < min_dist:
                min_dist = dist
                best_city = city

        return LocationCoordinates(
            latitude=latitude,
            longitude=longitude,
            name=best_city.name if min_dist < 1.0 else "Current Location",
            country=best_city.country,
            admin1=best_city.admin1
        )
