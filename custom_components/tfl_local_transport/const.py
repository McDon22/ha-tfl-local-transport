"""Constants for the TfL Local Transport integration."""

DOMAIN = "tfl_local_transport"

# Configuration keys
CONF_STATION_CRS = "station_crs"
CONF_STATION_NAPTAN = "station_naptan"
CONF_DARWIN_API_KEY = "darwin_api_key"
CONF_TFL_APP_KEY = "tfl_app_key"
CONF_DESTINATIONS = "destinations"
CONF_BUS_STOPS = "bus_stops"
CONF_LINES = "lines"
CONF_NUM_DEPARTURES = "num_departures"
CONF_TIME_WINDOW = "time_window"

# Default values
DEFAULT_NUM_DEPARTURES = 10
DEFAULT_TIME_WINDOW = 120  # minutes
DEFAULT_UPDATE_INTERVAL = 120  # seconds

# API endpoints
TFL_API_BASE = "https://api.tfl.gov.uk"
DARWIN_API_BASE = "https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS/api/20220120"
HUXLEY_API_BASE = "https://huxley2.azurewebsites.net"  # Community JSON proxy (no key needed for testing)

# Grove Park specific
GROVE_PARK_CRS = "GRP"
GROVE_PARK_NAPTAN = "910GGRVPK"

# Common London stations for destination filtering
LONDON_TERMINALS = {
    "CHX": "London Charing Cross",
    "CST": "London Cannon Street", 
    "VIC": "London Victoria",
    "LBG": "London Bridge",
    "WAT": "London Waterloo",
    "WAE": "London Waterloo East",
    "STP": "St Pancras International",
}
