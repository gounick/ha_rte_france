"""RTE France integration services."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.helpers.config_validation import ServiceResponseSchema

from .api import RTEDataAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_FETCH_DATA = "fetch_data"

SERVICE_FETCH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            "endpoint", default="wholesale_market/v3/france_power_exchanges"
        ): str,
        vol.Optional("params", default={}): dict,
    }
)


def async_setup_services(hass: HomeAssistant, api: RTEDataAPI) -> None:
    """Register RTE France services.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param api: Initialized RTE Data API client.
    :type api: RTEDataAPI
    """

    async def handle_fetch_data(call: ServiceCall) -> ServiceResponse:
        """Handle the fetch_data service call.

        :param call: Service call containing endpoint and optional params.
        :type call: ServiceCall
        :return: API response data.
        :rtype: ServiceResponse
        """
        endpoint: str = call.data["endpoint"]
        params: dict[str, Any] = call.data.get("params", {})

        _LOGGER.debug(
            "Service %s called with endpoint=%s params=%s",
            SERVICE_FETCH_DATA,
            endpoint,
            params,
        )

        data = await api.fetch(endpoint, params)
        return {"data": data}

    hass.services.async_register(
        DOMAIN,
        SERVICE_FETCH_DATA,
        handle_fetch_data,
        schema=SERVICE_FETCH_DATA_SCHEMA,
        supports_response=ServiceResponseSchema.RESPONSE_ONLY,
    )
