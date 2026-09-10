"""DataUpdateCoordinator for the RTE France integration."""

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import RTEDataAPI
from .const import DOMAIN
from .endpoints import RTEEndpoint

_LOGGER = logging.getLogger(__name__)


class RTEDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that fetches and caches data from an RTE Data API endpoint.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param api: Initialized RTE Data API client.
    :type api: RTEDataAPI
    :param endpoint: Descriptor for the RTE Data endpoint to poll.
    :type endpoint: RTEEndpoint
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api: RTEDataAPI,
        endpoint: RTEEndpoint,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.endpoint = endpoint
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{endpoint.key}",
            update_interval=endpoint.update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data from the configured RTE endpoint.

        :return: Parsed API response.
        :rtype: dict[str, Any]
        """
        params = None
        if self.endpoint.build_params:
            params = self.endpoint.build_params(datetime.now(UTC))
        return await self.api.fetch(self.endpoint.path, params)
