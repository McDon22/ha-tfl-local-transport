"""Sensor platform for TfL Local Transport."""
import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DEFAULT_BUS_STOPS,
    DOMAIN,
    CONF_STATION_CRS,
    CONF_STATION_NAPTAN,
    CONF_DARWIN_API_KEY,
    CONF_TFL_APP_KEY,
    CONF_DESTINATIONS,
    CONF_BUS_STOPS,
    CONF_LINES,
    CONF_NUM_DEPARTURES,
    CONF_TIME_WINDOW,
    DEFAULT_NUM_DEPARTURES,
    DEFAULT_TIME_WINDOW,
    DEFAULT_UPDATE_INTERVAL,
    GROVE_PARK_CRS,
    LONDON_TERMINALS,
    DLR_STATIONS,
    SENSOR_DLR_DEPARTURES,
)
from .api import TflApiClient, TrainApiClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug("TfL Local Transport: async_setup_entry started")
    data = hass.data[DOMAIN][config_entry.entry_id]
    session = data["session"]
    config = data["config"]

    # Initialize API clients
    tfl_client = TflApiClient(session, config.get(CONF_TFL_APP_KEY))
    darwin_api_key = config.get(CONF_DARWIN_API_KEY)
    
    # Use the unified TrainApiClient that tries Darwin first, falls back to Huxley
    train_client = TrainApiClient(session, darwin_api_key=darwin_api_key)
    
    if darwin_api_key:
        _LOGGER.info("TfL Local Transport: Darwin API key configured, will use as primary source")
    else:
        _LOGGER.info("TfL Local Transport: No Darwin API key, using Huxley API only")

    station_crs = config.get(CONF_STATION_CRS, GROVE_PARK_CRS)
    destinations = config.get(CONF_DESTINATIONS, list(LONDON_TERMINALS.keys()))
    # Default to Grove Park bus stops if none configured
    bus_stops = config.get(CONF_BUS_STOPS) or DEFAULT_BUS_STOPS
    _LOGGER.debug(f"TfL Local Transport: Bus stops to monitor: {bus_stops}")
    lines = config.get(CONF_LINES, ["southeastern"])
    num_departures = config.get(CONF_NUM_DEPARTURES, DEFAULT_NUM_DEPARTURES)
    time_window = config.get(CONF_TIME_WINDOW, DEFAULT_TIME_WINDOW)

    entities: list[SensorEntity] = []

    # Create train departure coordinator and sensors
    train_coordinator = TrainDepartureCoordinator(
        hass,
        train_client,
        station_crs,
        num_departures,
        time_window,
    )
    await train_coordinator.async_config_entry_first_refresh()

    # Main departures sensor (all departures from station)
    entities.append(
        TrainDepartureSensor(
            train_coordinator,
            station_crs,
            None,
            "departures",
        )
    )

    # Sensors for specific destinations (e.g., to London)
    for dest_crs in destinations[:5]:  # Limit to avoid too many API calls
        dest_coordinator = TrainDepartureCoordinator(
            hass,
            train_client,
            station_crs,
            num_departures,
            time_window,
            filter_crs=dest_crs,
            filter_type="to",
        )
        await dest_coordinator.async_config_entry_first_refresh()
        
        dest_name = LONDON_TERMINALS.get(dest_crs, dest_crs)
        entities.append(
            TrainDepartureSensor(
                dest_coordinator,
                station_crs,
                dest_crs,
                "departures",
                destination_name=dest_name,
            )
        )

    # Arrivals from London sensor
    arrivals_coordinator = TrainArrivalCoordinator(
        hass,
        train_client,
        station_crs,
        num_departures,
        time_window,
    )
    await arrivals_coordinator.async_config_entry_first_refresh()
    entities.append(
        TrainDepartureSensor(
            arrivals_coordinator,
            station_crs,
            None,
            "arrivals",
        )
    )

    # Line status coordinator and sensor
    line_coordinator = LineStatusCoordinator(hass, tfl_client, lines)
    await line_coordinator.async_config_entry_first_refresh()
    entities.append(LineStatusSensor(line_coordinator, lines))

    # Bus stop sensors
    _LOGGER.debug(f"TfL Local Transport: About to create {len(bus_stops)} bus sensors")
    for stop_id in bus_stops:
        _LOGGER.debug(f"TfL Local Transport: Creating bus sensor for stop {stop_id}")
        bus_coordinator = BusArrivalCoordinator(hass, tfl_client, stop_id)
        await bus_coordinator.async_config_entry_first_refresh()
        entities.append(BusArrivalSensor(bus_coordinator, stop_id))

    # DLR departure sensors
    _LOGGER.debug("TfL Local Transport: Creating DLR sensors")
    # Lewisham to Bank DLR sensor
    dlr_lewisham_sensor = DLRDepartureSensor(
        tfl_client,
        DLR_STATIONS["LEWISHAM"],
        "Lewisham",
        destination_filter="Bank"
    )
    entities.append(dlr_lewisham_sensor)

    async_add_entities(entities)


class TrainDepartureCoordinator(DataUpdateCoordinator):
    """Coordinator for train departure data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TrainApiClient,
        station_crs: str,
        num_departures: int,
        time_window: int,
        filter_crs: Optional[str] = None,
        filter_type: str = "to",
    ):
        """Initialize the coordinator."""
        self.client = client
        self.station_crs = station_crs
        self.num_departures = num_departures
        self.time_window = time_window
        self.filter_crs = filter_crs
        self.filter_type = filter_type

        name = f"Train Departures {station_crs}"
        if filter_crs:
            name = f"{name} to {filter_crs}"

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            data = await self.client.get_departures(
                self.station_crs,
                self.num_departures,
                self.filter_crs,
                self.filter_type,
                time_window=self.time_window,
            )
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching train data: {err}") from err


class TrainArrivalCoordinator(DataUpdateCoordinator):
    """Coordinator for train arrival data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TrainApiClient,
        station_crs: str,
        num_arrivals: int,
        time_window: int,
        filter_crs: Optional[str] = None,
        filter_type: str = "from",
    ):
        """Initialize the coordinator."""
        self.client = client
        self.station_crs = station_crs
        self.num_arrivals = num_arrivals
        self.time_window = time_window
        self.filter_crs = filter_crs
        self.filter_type = filter_type

        super().__init__(
            hass,
            _LOGGER,
            name=f"Train Arrivals {station_crs}",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            data = await self.client.get_arrivals(
                self.station_crs,
                self.num_arrivals,
                self.filter_crs,
                self.filter_type,
                time_window=self.time_window,
            )
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching arrival data: {err}") from err


class LineStatusCoordinator(DataUpdateCoordinator):
    """Coordinator for line status data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TflApiClient,
        lines: list[str],
    ):
        """Initialize the coordinator."""
        self.client = client
        self.lines = lines

        super().__init__(
            hass,
            _LOGGER,
            name="Line Status",
            update_interval=timedelta(seconds=300),  # 5 minutes for line status
        )

    async def _async_update_data(self) -> list[dict]:
        """Fetch data from API."""
        try:
            return await self.client.get_line_status(self.lines)
        except Exception as err:
            raise UpdateFailed(f"Error fetching line status: {err}") from err


class BusArrivalCoordinator(DataUpdateCoordinator):
    """Coordinator for bus arrival data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TflApiClient,
        stop_id: str,
    ):
        """Initialize the coordinator."""
        self.client = client
        self.stop_id = stop_id

        super().__init__(
            hass,
            _LOGGER,
            name=f"Bus Arrivals {stop_id}",
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self) -> list[dict]:
        """Fetch data from API."""
        try:
            return await self.client.get_stop_arrivals(self.stop_id)
        except Exception as err:
            raise UpdateFailed(f"Error fetching bus arrivals: {err}") from err


class TrainDepartureSensor(CoordinatorEntity, SensorEntity):
    """Sensor for train departures."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        station_crs: str,
        filter_crs: Optional[str],
        sensor_type: str,
        destination_name: Optional[str] = None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.station_crs = station_crs
        self.filter_crs = filter_crs
        self.sensor_type = sensor_type
        self.destination_name = destination_name

        if filter_crs:
            self._attr_name = f"Train {sensor_type.title()} {station_crs} to {destination_name or filter_crs}"
            self._attr_unique_id = f"train_{sensor_type}_{station_crs}_{filter_crs}"
        else:
            self._attr_name = f"Train {sensor_type.title()} {station_crs}"
            self._attr_unique_id = f"train_{sensor_type}_{station_crs}"

        self._attr_icon = "mdi:train" if sensor_type == "departures" else "mdi:train-variant"

    @property
    def native_value(self) -> Optional[str]:
        """Return the next departure/arrival time."""
        if not self.coordinator.data:
            return None
        
        services = self.coordinator.data.get("trainServices") or []
        if services:
            first = services[0]
            etd = first.get("etd", first.get("std", "Unknown"))
            return etd
        return "No services"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        data = self.coordinator.data
        services = data.get("trainServices") or []
        
        trains = []
        for svc in services[:10]:
            train_info = {
                "scheduled": svc.get("std") or svc.get("sta"),
                "expected": svc.get("etd") or svc.get("eta"),
                "platform": svc.get("platform", "TBC"),
                "operator": svc.get("operator"),
                "operator_code": svc.get("operatorCode"),
                "is_cancelled": svc.get("isCancelled", False),
                "cancel_reason": svc.get("cancelReason"),
                "delay_reason": svc.get("delayReason"),
            }
            
            # Add destination/origin
            if self.sensor_type == "departures":
                destinations = svc.get("destination", [])
                if destinations:
                    train_info["destination"] = destinations[0].get("locationName")
                    train_info["destination_crs"] = destinations[0].get("crs")
            else:
                origins = svc.get("origin", [])
                if origins:
                    train_info["origin"] = origins[0].get("locationName")
                    train_info["origin_crs"] = origins[0].get("crs")
            
            # Add calling points if available
            if svc.get("subsequentCallingPoints"):
                calling_points = []
                for cp_list in (svc.get("subsequentCallingPoints") or []):
                    if cp_list is None:
                        continue
                    for cp in (cp_list.get("callingPoint") or []):
                        calling_points.append({
                            "station": cp.get("locationName"),
                            "crs": cp.get("crs"),
                            "scheduled": cp.get("st"),
                            "expected": cp.get("et"),
                        })
                train_info["calling_points"] = calling_points[:8]  # Limit size
            
            trains.append(train_info)

        # Get API source if available
        api_source = None
        if hasattr(self.coordinator, 'client') and hasattr(self.coordinator.client, 'last_source'):
            api_source = self.coordinator.client.last_source

        return {
            "station_name": data.get("locationName"),
            "crs": data.get("crs"),
            "generated_at": data.get("generatedAt"),
            "filter_crs": self.filter_crs,
            "filter_destination": self.destination_name,
            "trains": trains,
            "nrcc_messages": data.get("nrccMessages", []),
            "platforms_available": data.get("platformAvailable", False),
            "services_available": data.get("areServicesAvailable", True),
            "api_source": api_source,
        }


class LineStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor for line status."""

    def __init__(self, coordinator: LineStatusCoordinator, lines: list[str]):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.lines = lines
        self._attr_name = "Line Status"
        self._attr_unique_id = f"line_status_{'_'.join(lines)}"
        self._attr_icon = "mdi:information-outline"

    @property
    def native_value(self) -> str:
        """Return overall status."""
        if not self.coordinator.data:
            return "Unknown"
        
        # Check if all lines have good service
        statuses = []
        for line in self.coordinator.data:
            line_statuses = line.get("lineStatuses", [])
            for status in line_statuses:
                severity = status.get("statusSeverity", 10)
                if severity < 10:
                    return status.get("statusSeverityDescription", "Issues")
                statuses.append(status.get("statusSeverityDescription", "Unknown"))
        
        return "Good Service" if statuses else "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return line status details."""
        if not self.coordinator.data:
            return {}

        line_details = []
        for line in self.coordinator.data:
            line_info = {
                "line_id": line.get("id"),
                "line_name": line.get("name"),
                "mode": line.get("modeName"),
            }
            
            statuses = line.get("lineStatuses", [])
            if statuses:
                status = statuses[0]
                line_info["status"] = status.get("statusSeverityDescription")
                line_info["severity"] = status.get("statusSeverity")
                line_info["reason"] = status.get("reason")
            
            line_details.append(line_info)

        return {"lines": line_details}


class BusArrivalSensor(CoordinatorEntity, SensorEntity):
    """Sensor for bus arrivals."""

    def __init__(self, coordinator: BusArrivalCoordinator, stop_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.stop_id = stop_id
        self._attr_name = f"Bus Stop {stop_id}"
        self._attr_unique_id = f"bus_arrivals_{stop_id}"
        self._attr_icon = "mdi:bus"
        self._attr_device_class = None

    @property
    def native_value(self) -> Optional[str]:
        """Return the next bus arrival."""
        if not self.coordinator.data:
            return None
        
        if self.coordinator.data:
            first = self.coordinator.data[0]
            mins = first.get("timeToStation", 0) // 60
            return f"{mins} min"
        return "No buses"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return bus arrival details."""
        if not self.coordinator.data:
            return {}

        buses = []
        for arrival in self.coordinator.data[:10]:
            buses.append({
                "line": arrival.get("lineName"),
                "destination": arrival.get("destinationName"),
                "expected_arrival": arrival.get("expectedArrival"),
                "time_to_station": arrival.get("timeToStation", 0) // 60,
                "towards": arrival.get("towards"),
                "vehicle_id": arrival.get("vehicleId"),
            })

        return {
            "stop_id": self.stop_id,
            "buses": buses,
        }



class DLRDepartureSensor(SensorEntity):
    """Sensor for DLR departures from a specific station.
    
    This sensor monitors DLR train arrivals at a station and presents them
    as departures from the user's perspective. It supports filtering by
    destination (e.g., only trains heading to Bank).
    
    Attributes:
        state: Number of upcoming DLR departures
        departures: List of departure information dictionaries
        station_id: TfL StopPoint ID
        station_name: Human-readable station name
        destination_filter: Optional destination filter
    """

    def __init__(
        self,
        tfl_api_client,
        station_id: str,
        station_name: str,
        destination_filter: str | None = None,
    ):
        """Initialize the DLR departure sensor.
        
        Args:
            tfl_api_client: TflApiClient instance for API calls
            station_id: TfL StopPoint ID (e.g., '940GZZDLLEW')
            station_name: Display name (e.g., 'Lewisham')
            destination_filter: Optional destination to filter for (e.g., 'Bank')
        """
        self._tfl_api_client = tfl_api_client
        self._station_id = station_id
        self._station_name = station_name
        self._destination_filter = destination_filter
        
        # Set up entity attributes
        self._attr_name = self._generate_name()
        self._attr_unique_id = self._generate_unique_id()
        self._attr_attribution = ATTRIBUTION
        self._attr_icon = "mdi:train"
        
        self._departures = []
        self._last_update = None

    def _generate_name(self) -> str:
        """Generate sensor name based on configuration.
        
        Returns:
            Sensor name like "DLR Lewisham to Bank" or "DLR Lewisham"
        """
        base_name = f"DLR {self._station_name}"
        if self._destination_filter:
            # Remove "DLR Station" suffix if present for cleaner name
            clean_dest = self._destination_filter.replace(" DLR Station", "")
            return f"{base_name} to {clean_dest}"
        return base_name

    def _generate_unique_id(self) -> str:
        """Generate unique ID for the sensor.
        
        Returns:
            Unique ID like "tfl_local_transport_dlr_departures_940GZZDLLEW_to_bank"
        """
        base_id = f"{DOMAIN}_{SENSOR_DLR_DEPARTURES}_{self._station_id}"
        if self._destination_filter:
            # Create URL-safe slug from destination
            filter_slug = (
                self._destination_filter
                .lower()
                .replace(" dlr station", "")
                .replace(" ", "_")
            )
            return f"{base_id}_to_{filter_slug}"
        return base_id

    @property
    def state(self) -> int:
        """Return the number of upcoming departures.
        
        Returns:
            Count of departures in the next hour
        """
        return len(self._departures)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.
        
        Returns:
            Dictionary with departure details, station info, and metadata
        """
        return {
            "departures": self._departures,
            "station_id": self._station_id,
            "station_name": self._station_name,
            "destination_filter": self._destination_filter,
            "last_update": self._last_update,
            "attribution": ATTRIBUTION,
        }

    async def async_update(self) -> None:
        """Fetch new departure data from TfL API.
        
        This method:
        1. Queries the TfL API for arrivals at the station
        2. Filters by destination if configured
        3. Processes timing and platform information
        4. Sorts by soonest departure first
        5. Limits to next 10 departures
        """
        try:
            # Get arrivals (which are departures from this station's perspective)
            arrivals = await self._tfl_api_client.get_dlr_arrivals(self._station_id)
            
            if not arrivals:
                _LOGGER.debug(
                    "No DLR arrivals data for station %s",
                    self._station_id
                )
                self._departures = []
                return

            # Process and filter arrivals
            processed_departures = []
            
            for arrival in arrivals:
                # Apply destination filter if specified
                if self._destination_filter:
                    dest_name = arrival.get("destinationName", "")
                    # Case-insensitive partial match (e.g., "Bank" matches "Bank DLR Station")
                    if self._destination_filter.lower() not in dest_name.lower():
                        continue
                
                # Extract relevant information
                departure = {
                    "destination": arrival.get("destinationName", "Unknown"),
                    "platform": arrival.get("platformName", ""),
                    "expected_arrival": arrival.get("expectedArrival"),
                    "time_to_station": arrival.get("timeToStation", 0),
                    "current_location": arrival.get("currentLocation", ""),
                    "direction": arrival.get("direction", ""),
                    "line_name": arrival.get("lineName", "DLR"),
                    "towards": arrival.get("towards", ""),
                }
                
                # Calculate minutes until departure
                time_to_station_seconds = departure["time_to_station"]
                departure["minutes_until"] = max(0, time_to_station_seconds // 60)
                
                # Format expected arrival time (HH:MM)
                if departure["expected_arrival"]:
                    try:
                        expected_dt = datetime.fromisoformat(
                            departure["expected_arrival"].replace("Z", "+00:00")
                        )
                        departure["expected_time"] = expected_dt.strftime("%H:%M")
                    except (ValueError, AttributeError):
                        departure["expected_time"] = "Unknown"
                else:
                    departure["expected_time"] = "Unknown"
                
                processed_departures.append(departure)
            
            # Sort by time to station (soonest first)
            processed_departures.sort(key=lambda x: x["time_to_station"])
            
            # Limit to next 10 departures
            self._departures = processed_departures[:10]
            self._last_update = datetime.now().isoformat()
            
            _LOGGER.debug(
                "Updated DLR departures for %s: %d services found",
                self._station_name,
                len(self._departures)
            )
            
        except Exception as err:
            _LOGGER.error(
                "Error updating DLR departures for %s: %s",
                self._station_name,
                err,
                exc_info=True
            )
            # Clear departures on error rather than showing stale data
            self._departures = []


# ============================================================================
# INTEGRATION INTO sensor.py
# ============================================================================
#
# In your async_setup_entry function in sensor.py, add:
#
# # Add DLR sensors (after existing sensor setup)
# if tfl_api_client and config_entry.data.get(CONF_TFL_API_KEY):
#     _LOGGER.info("Setting up DLR sensors")
#     
#     dlr_sensors = [
#         DLRDepartureSensor(
#             tfl_api_client=tfl_api_client,
#             station_id=DLR_STATIONS["LEWISHAM"],
#             station_name="Lewisham",
#             destination_filter="Bank",
#         ),
#     ]
#     
#     async_add_entities(dlr_sensors, True)
#     _LOGGER.info("DLR sensors created successfully")
#
# ============================================================================
