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
DEFAULT_TIME_WINDOW = 120  # 2 hours - max allowed by API
DEFAULT_UPDATE_INTERVAL = 120  # seconds

# API endpoints
TFL_API_BASE = "https://api.tfl.gov.uk"
TFL_API_URL = "https://api.tfl.gov.uk"  # Alias for compatibility
DARWIN_API_BASE = "https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS/api/20220120"
HUXLEY_API_BASE = "https://huxley2.azurewebsites.net"  # Community JSON proxy (no key needed for testing)

# Grove Park specific
GROVE_PARK_CRS = "GRP"
GROVE_PARK_NAPTAN = "910GGRVPK"

# Grove Park Bus Stops
GROVE_PARK_BUS_STOPS = {
    "490001124E": "Grove Park Station (Stop E) - towards Lee Green/Mottingham",
    "490015256D": "Grove Park Station (Stop D) - towards Catford/Lewisham", 
    "490015256C": "Grove Park Station (Stop C) - towards Mottingham",
    "490001124B": "Grove Park Station (Stop B) - towards Bromley",
}

# Default bus stops to monitor
DEFAULT_BUS_STOPS = ["490001124E", "490015256D"]

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

# DLR StopPoint IDs
DLR_STATIONS = {
    "LEWISHAM": "940GZZDLLEW",
    "BANK": "940GZZDLBNK",
    "GREENWICH": "940GZZDLGRE",
    "CUTTY_SARK": "940GZZDLCUT",  # Note: Currently closed until spring 2026
}

# Sensor names
SENSOR_TRAIN_DEPARTURES = "train_departures"
SENSOR_TRAIN_ARRIVALS = "train_arrivals"
SENSOR_LINE_STATUS = "line_status"
SENSOR_BUS_STOP = "bus_stop"
SENSOR_DLR_DEPARTURES = "dlr_departures"

