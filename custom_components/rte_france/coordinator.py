"""DataUpdateCoordinator for the RTE France integration."""

import logging
from collections.abc import Callable, Coroutine
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import RTEDataAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_UPDATE_INTERVAL = timedelta(minutes=15)


class RTEDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that fetches and caches data from an RTE Data API endpoint.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param api: Initialized RTE Data API client.
    :type api: RTEDataAPI
    :param name: Coordinator / sensor suffix.
    :type name: str
    :param update_method: Async callable returning parsed API data.
    :type update_method: Callable[[], Coroutine[Any, Any, dict[str, Any]]]
    :param update_interval: Optional override of the default polling interval.
    :type update_interval: timedelta | None
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api: RTEDataAPI,
        name: str,
        update_method: Callable[[], Coroutine[Any, Any, dict[str, Any]]],
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self._update_method = update_method
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
            update_interval=update_interval or DEFAULT_UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data from the configured RTE endpoint.

        :return: Parsed API response.
        :rtype: dict[str, Any]
        """
        return await self._update_method()
