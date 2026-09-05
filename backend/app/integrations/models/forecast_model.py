"""Placeholder adapters for GFS, WRF, satellite, IMD WIS2.0 — not implemented as models."""

from typing import Any


class ForecastModelService:
    """Future: GFS / WRF / IMD NWP. MVP uses demo adapter labelled DEMO DATA."""

    def available_models(self) -> list[dict[str, str]]:
        return [
            {"id": "open-meteo", "status": "active", "notes": "Default live forecast provider"},
            {"id": "gfs", "status": "adapter-only", "notes": "NOAA GFS — not ingested in MVP"},
            {"id": "wrf", "status": "adapter-only", "notes": "WRF regional — not ingested in MVP"},
            {"id": "imd-nwp", "status": "adapter-only", "notes": "Official IMD NWP — future WIS2.0/MQTT"},
        ]

    async def fetch_gfs(self, lat: float, lon: float) -> dict[str, Any]:
        return {
            "model": "GFS",
            "status": "unavailable",
            "is_demo": True,
            "label": "DEMO DATA",
            "message": "GFS ingest is not enabled in this MVP. Use WeatherService / Open-Meteo instead.",
            "latitude": lat,
            "longitude": lon,
        }

    async def fetch_wrf(self, lat: float, lon: float) -> dict[str, Any]:
        return {
            "model": "WRF",
            "status": "unavailable",
            "is_demo": True,
            "label": "DEMO DATA",
            "message": "WRF ingest is not enabled in this MVP.",
            "latitude": lat,
            "longitude": lon,
        }


class SatelliteDataService:
    async def latest_scene(self, region: str = "india") -> dict[str, Any]:
        return {
            "region": region,
            "status": "unavailable",
            "is_demo": True,
            "label": "DEMO DATA",
            "message": "Satellite imagery adapter is a placeholder for INSAT/MOSDAC integration.",
        }
