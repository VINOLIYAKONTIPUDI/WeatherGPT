from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any


class WeatherProvider(ABC):
    """Replaceable weather data source (Open-Meteo, IMD, OpenWeather, etc.)."""

    name: str = "base"

    @abstractmethod
    async def geocode(self, query: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def current(self, lat: float, lon: float) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def forecast(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def historical(
        self, lat: float, lon: float, start: date, end: date
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
