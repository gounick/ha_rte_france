"""The RTE France integration."""

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RTEDataAPI, RTEDataAPIError
from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_ENABLED_ENDPOINTS, DOMAIN
from .coordinator import RTEDataUpdateCoordinator
from .endpoints import get_endpoint, list_endpoint_keys
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

    enabled_keys = entry.options.get(CONF_ENABLED_ENDPOINTS, list_endpoint_keys())

    coordinators: dict[str, RTEDataUpdateCoordinator] = {}
    for key in enabled_keys:
        endpoint = get_endpoint(key)
        if endpoint is None:
            _LOGGER.warning("Unknown RTE endpoint '%s' skipped", key)
            continue

        coordinator = RTEDataUpdateCoordinator(hass, api, endpoint)
        try:
            await coordinator.async_config_entry_first_refresh()
        except ConfigEntryNotReady as err:
            _LOGGER.warning(
                "RTE France '%s' API is not available for this application: %s",
                key,
                err,
            )
            continue
        coordinators[key] = coordinator

    if not coordinators:
        raise ConfigEntryNotReady(
            "No RTE Data APIs are accessible for this application."
        )

    _LOGGER.info(
        "RTE France enabled categories: %s",
        ", ".join(sorted(coordinators)),
    )

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
