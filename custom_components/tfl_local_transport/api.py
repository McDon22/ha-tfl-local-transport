"""API clients for TfL and National Rail Darwin APIs."""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
import aiohttp

from .const import (
    TFL_API_BASE,
    DARWIN_API_BASE,
    HUXLEY_API_BASE,
)

_LOGGER = logging.getLogger(__name__)


class TflApiClient:
    """Client for TfL Unified API."""

    def __init__(self, session: aiohttp.ClientSession, app_key: Optional[str] = None):
        """Initialize the TfL API client."""
        self.session = session
        self.app_key = app_key

    def _build_url(self, endpoint: str) -> str:
        """Build URL with optional API key."""
        url = f"{TFL_API_BASE}/{endpoint}"
        if self.app_key:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}app_key={self.app_key}"
        return url

    async def get_line_status(self, line_ids: list[str]) -> list[dict]:
        """Get status for specified lines."""
        lines = ",".join(line_ids)
        url = self._build_url(f"Line/{lines}/Status")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("TfL API error: %s", response.status)
                return []
        except Exception as e:
            _LOGGER.error("Error fetching line status: %s", e)
            return []

    async def get_stop_arrivals(self, stop_id: str) -> list[dict]:
        """Get arrivals at a stop point (buses, etc.)."""
        url = self._build_url(f"StopPoint/{stop_id}/Arrivals")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Sort by expected arrival time
                    return sorted(data, key=lambda x: x.get("expectedArrival", ""))
                _LOGGER.error("TfL API error: %s", response.status)
                return []
        except Exception as e:
            _LOGGER.error("Error fetching stop arrivals: %s", e)
            return []

    async def get_station_info(self, naptan_id: str) -> dict:
        """Get information about a station."""
        url = self._build_url(f"StopPoint/{naptan_id}")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("TfL API error: %s", response.status)
                return {}
        except Exception as e:
            _LOGGER.error("Error fetching station info: %s", e)
            return {}

    async def get_disruptions(self, modes: list[str]) -> list[dict]:
        """Get current disruptions for specified modes."""
        modes_str = ",".join(modes)
        url = self._build_url(f"Line/Mode/{modes_str}/Disruption")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("TfL API error: %s", response.status)
                return []
        except Exception as e:
            _LOGGER.error("Error fetching disruptions: %s", e)
            return []


class DarwinApiClient:
    """Client for National Rail Darwin API (via Rail Data Marketplace)."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        """Initialize the Darwin API client."""
        self.session = session
        self.api_key = api_key
        self.base_url = DARWIN_API_BASE

    async def get_departures(
        self,
        station_crs: str,
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "to",
        time_offset: int = 0,
        time_window: int = 120,
    ) -> dict:
        """Get departure board for a station."""
        url = f"{self.base_url}/GetDepBoardWithDetails/{station_crs}"
        
        params = {
            "numRows": num_rows,
            "timeOffset": time_offset,
            "timeWindow": time_window,
        }
        if filter_crs:
            params["filterCrs"] = filter_crs
            params["filterType"] = filter_type
        
        headers = {
            "x-apikey": self.api_key,
            "User-Agent": "HomeAssistantTfLIntegration/1.0",
        }
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("Darwin API error: %s - %s", response.status, await response.text())
                return {}
        except Exception as e:
            _LOGGER.error("Error fetching departures from Darwin: %s", e)
            return {}

    async def get_arrivals(
        self,
        station_crs: str,
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "from",
        time_offset: int = 0,
        time_window: int = 120,
    ) -> dict:
        """Get arrival board for a station."""
        url = f"{self.base_url}/GetArrBoardWithDetails/{station_crs}"
        
        params = {
            "numRows": num_rows,
            "timeOffset": time_offset,
            "timeWindow": time_window,
        }
        if filter_crs:
            params["filterCrs"] = filter_crs
            params["filterType"] = filter_type
        
        headers = {
            "x-apikey": self.api_key,
            "User-Agent": "HomeAssistantTfLIntegration/1.0",
        }
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("Darwin API error: %s - %s", response.status, await response.text())
                return {}
        except Exception as e:
            _LOGGER.error("Error fetching arrivals from Darwin: %s", e)
            return {}


class HuxleyApiClient:
    """Client for Huxley2 REST proxy (fallback if Darwin API unavailable)."""

    def __init__(self, session: aiohttp.ClientSession, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the Huxley API client."""
        self.session = session
        self.api_key = api_key
        self.base_url = base_url or HUXLEY_API_BASE

    async def get_departures(
        self,
        station_crs: str,
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "to",
        time_offset: int = 0,
        time_window: int = 120,
        expand: bool = True,
    ) -> dict:
        """Get departure board using Huxley2 REST API."""
        if filter_crs:
            url = f"{self.base_url}/departures/{station_crs}/{filter_type}/{filter_crs}/{num_rows}"
        else:
            url = f"{self.base_url}/departures/{station_crs}/{num_rows}"
        
        params = {
            "timeOffset": time_offset,
            "timeWindow": time_window,
            "expand": str(expand).lower(),
        }
        if self.api_key:
            params["accessToken"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("Huxley API error: %s - %s", response.status, await response.text())
                return {}
        except Exception as e:
            _LOGGER.error("Error fetching departures from Huxley: %s", e)
            return {}

    async def get_arrivals(
        self,
        station_crs: str,
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "from",
        time_offset: int = 0,
        time_window: int = 120,
        expand: bool = True,
    ) -> dict:
        """Get arrival board using Huxley2 REST API."""
        if filter_crs:
            url = f"{self.base_url}/arrivals/{station_crs}/{filter_type}/{filter_crs}/{num_rows}"
        else:
            url = f"{self.base_url}/arrivals/{station_crs}/{num_rows}"
        
        params = {
            "timeOffset": time_offset,
            "timeWindow": time_window,
            "expand": str(expand).lower(),
        }
        if self.api_key:
            params["accessToken"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("Huxley API error: %s", response.status)
                return {}
        except Exception as e:
            _LOGGER.error("Error fetching arrivals from Huxley: %s", e)
            return {}

    async def get_all(
        self,
        station_crs: str,
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "to",
        time_offset: int = 0,
        time_window: int = 120,
        expand: bool = True,
    ) -> dict:
        """Get combined arrivals and departures."""
        if filter_crs:
            url = f"{self.base_url}/all/{station_crs}/{filter_type}/{filter_crs}/{num_rows}"
        else:
            url = f"{self.base_url}/all/{station_crs}/{num_rows}"
        
        params = {
            "timeOffset": time_offset,
            "timeWindow": time_window,
            "expand": str(expand).lower(),
        }
        if self.api_key:
            params["accessToken"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.error("Huxley API error: %s", response.status)
                return {}
        except Exception as e:
            _LOGGER.error("Error fetching all from Huxley: %s", e)
            return {}

    async def get_station_crs(self, query: str) -> list[dict]:
        """Search for station CRS codes."""
        url = f"{self.base_url}/crs/{query}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception as e:
            _LOGGER.error("Error searching stations: %s", e)
            return []


class TrainApiClient:
    """Unified client that tries Darwin API first, falls back to Huxley."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        darwin_api_key: Optional[str] = None,
        huxley_api_key: Optional[str] = None,
    ):
        """Initialize the unified train API client."""
        self.session = session
        self.darwin_client = DarwinApiClient(session, darwin_api_key) if darwin_api_key else None
        self.huxley_client = HuxleyApiClient(session, huxley_api_key)
        self._last_source = None

    @property
    def last_source(self) -> Optional[str]:
        """Return which API was used for the last successful request."""
        return self._last_source

    async def get_departures(
        self,
        station_crs: str,
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "to",
        time_offset: int = 0,
        time_window: int = 120,
    ) -> dict:
        """Get departures, trying Darwin first then Huxley as fallback."""
        # Try Darwin API first if we have a key
        if self.darwin_client:
            _LOGGER.debug("Trying Darwin API for departures from %s", station_crs)
            try:
                result = await self.darwin_client.get_departures(
                    station_crs=station_crs,
                    num_rows=num_rows,
                    filter_crs=filter_crs,
                    filter_type=filter_type,
                    time_offset=time_offset,
                    time_window=time_window,
                )
                if result:
                    self._last_source = "darwin"
                    _LOGGER.debug("Darwin API success for %s", station_crs)
                    return result
            except Exception as e:
                _LOGGER.warning("Darwin API error for %s: %s", station_crs, e)
            _LOGGER.warning("Darwin API failed for %s, falling back to Huxley", station_crs)

        # Fall back to Huxley
        _LOGGER.debug("Using Huxley API for departures from %s", station_crs)
        result = await self.huxley_client.get_departures(
            station_crs=station_crs,
            num_rows=num_rows,
            filter_crs=filter_crs,
            filter_type=filter_type,
            time_offset=time_offset,
            time_window=time_window,
        )
        if result:
            self._last_source = "huxley"
        return result

    async def get_arrivals(
        self,
        station_crs: str,
        num_rows: int = 10,
        filter_crs: Optional[str] = None,
        filter_type: str = "from",
        time_offset: int = 0,
        time_window: int = 120,
    ) -> dict:
        """Get arrivals, trying Darwin first then Huxley as fallback."""
        # Try Darwin API first if we have a key
        if self.darwin_client:
            _LOGGER.debug("Trying Darwin API for arrivals at %s", station_crs)
            try:
                result = await self.darwin_client.get_arrivals(
                    station_crs=station_crs,
                    num_rows=num_rows,
                    filter_crs=filter_crs,
                    filter_type=filter_type,
                    time_offset=time_offset,
                    time_window=time_window,
                )
                if result:
                    self._last_source = "darwin"
                    _LOGGER.debug("Darwin API success for %s", station_crs)
                    return result
            except Exception as e:
                _LOGGER.warning("Darwin API error for %s: %s", station_crs, e)
            _LOGGER.warning("Darwin API failed for %s, falling back to Huxley", station_crs)

        # Fall back to Huxley
        _LOGGER.debug("Using Huxley API for arrivals at %s", station_crs)
        result = await self.huxley_client.get_arrivals(
            station_crs=station_crs,
            num_rows=num_rows,
            filter_crs=filter_crs,
            filter_type=filter_type,
            time_offset=time_offset,
            time_window=time_window,
        )
        if result:
            self._last_source = "huxley"
        return result
