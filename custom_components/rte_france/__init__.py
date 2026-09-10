"""The RTE France integration."""

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RTEDataAPI, RTEDataAPIError
from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN
from .coordinator import RTEDataUpdateCoordinator
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RTE France from a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ConfigEntry
    :return: True if setup succeeded.
    :rtype: bool
    """
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]
    session = async_get_clientsession(hass)

    api = RTEDataAPI(client_id, client_secret, session)

    try:
        await api.authenticate()
    except (RTEDataAPIError, aiohttp.ClientError) as err:
        raise ConfigEntryNotReady() from err

    coordinators = {
        "market": RTEDataUpdateCoordinator(
            hass,
            api,
            "market",
            api.fetch_france_power_exchanges,
        ),
        "generation": RTEDataUpdateCoordinator(
            hass,
            api,
            "generation",
            api.fetch_actual_generation,
        ),
        "generation_forecast": RTEDataUpdateCoordinator(
            hass,
            api,
            "generation_forecast",
            api.fetch_generation_forecast,
        ),
        "consumption": RTEDataUpdateCoordinator(
            hass,
            api,
            "consumption",
            api.fetch_consumption,
        ),
        "physical_flows": RTEDataUpdateCoordinator(
            hass,
            api,
            "physical_flows",
            api.fetch_physical_flows,
        ),
    }

    for coordinator in coordinators.values():
        await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
    }

    async_setup_services(hass, api)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being unloaded.
    :type entry: ConfigEntry
    :return: True if unload succeeded.
    :rtype: bool
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
