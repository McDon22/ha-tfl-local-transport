"""TfL Local Transport Integration for Home Assistant.

Provides local transport information using TfL Unified API and National Rail Darwin API.
Includes train departures, bus times, line status, and local area information.
"""
import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_STATION_CRS,
    CONF_STATION_NAPTAN,
    CONF_DARWIN_API_KEY,
    CONF_TFL_APP_KEY,
    CONF_DESTINATIONS,
    CONF_BUS_STOPS,
    CONF_LINES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TfL Local Transport from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    
    # Store configuration data
    hass.data[DOMAIN][entry.entry_id] = {
        "session": session,
        "config": entry.data,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
