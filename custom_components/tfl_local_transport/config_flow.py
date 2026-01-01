"""Config flow for TfL Local Transport integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_STATION_CRS,
    CONF_DARWIN_API_KEY,
    CONF_TFL_APP_KEY,
    CONF_DESTINATIONS,
    CONF_BUS_STOPS,
    CONF_LINES,
    CONF_NUM_DEPARTURES,
    CONF_TIME_WINDOW,
    DEFAULT_NUM_DEPARTURES,
    DEFAULT_TIME_WINDOW,
    GROVE_PARK_CRS,
    LONDON_TERMINALS,
)

_LOGGER = logging.getLogger(__name__)


class TflLocalTransportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TfL Local Transport."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the configuration
            station_crs = user_input.get(CONF_STATION_CRS, GROVE_PARK_CRS).upper()
            
            if len(station_crs) != 3:
                errors["base"] = "invalid_crs"
            else:
                # Create config entry
                return self.async_create_entry(
                    title=f"Transport - {station_crs}",
                    data={
                        CONF_STATION_CRS: station_crs,
                        CONF_DARWIN_API_KEY: user_input.get(CONF_DARWIN_API_KEY, ""),
                        CONF_TFL_APP_KEY: user_input.get(CONF_TFL_APP_KEY, ""),
                        CONF_DESTINATIONS: user_input.get(CONF_DESTINATIONS, ["CHX", "LBG", "VIC"]),
                        CONF_BUS_STOPS: user_input.get(CONF_BUS_STOPS, []),
                        CONF_LINES: user_input.get(CONF_LINES, ["southeastern"]),
                        CONF_NUM_DEPARTURES: user_input.get(CONF_NUM_DEPARTURES, DEFAULT_NUM_DEPARTURES),
                        CONF_TIME_WINDOW: user_input.get(CONF_TIME_WINDOW, DEFAULT_TIME_WINDOW),
                    },
                )

        # Build destination options
        destination_options = {k: f"{v} ({k})" for k, v in LONDON_TERMINALS.items()}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_STATION_CRS, default=GROVE_PARK_CRS): str,
                vol.Optional(CONF_DARWIN_API_KEY, default=""): str,
                vol.Optional(CONF_TFL_APP_KEY, default=""): str,
                vol.Optional(
                    CONF_DESTINATIONS, 
                    default=["CHX", "LBG", "VIC"]
                ): cv.multi_select(destination_options),
                vol.Optional(CONF_LINES, default=["southeastern"]): cv.multi_select({
                    "southeastern": "Southeastern",
                    "southern": "Southern",
                    "thameslink": "Thameslink",
                    "great-northern": "Great Northern",
                    "c2c": "c2c",
                    "elizabeth": "Elizabeth Line",
                }),
                vol.Optional(CONF_NUM_DEPARTURES, default=DEFAULT_NUM_DEPARTURES): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=20)
                ),
                vol.Optional(CONF_TIME_WINDOW, default=DEFAULT_TIME_WINDOW): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=300)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "default_station": GROVE_PARK_CRS,
                "api_info": "API keys are optional but recommended for higher rate limits.",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return TflOptionsFlowHandler(config_entry)


class TflOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        destination_options = {k: f"{v} ({k})" for k, v in LONDON_TERMINALS.items()}
        current_destinations = self.config_entry.data.get(CONF_DESTINATIONS, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DESTINATIONS,
                        default=current_destinations,
                    ): cv.multi_select(destination_options),
                    vol.Optional(
                        CONF_NUM_DEPARTURES,
                        default=self.config_entry.data.get(CONF_NUM_DEPARTURES, DEFAULT_NUM_DEPARTURES),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
                    vol.Optional(
                        CONF_TIME_WINDOW,
                        default=self.config_entry.data.get(CONF_TIME_WINDOW, DEFAULT_TIME_WINDOW),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=300)),
                }
            ),
        )
