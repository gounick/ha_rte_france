"""RTE Data API client."""

import base64
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class RTEDataAPIError(Exception):
    """Exception raised when the RTE API returns an unexpected error."""


class RTEDataAPI:
    """Async client for the RTE Data API.

    Handles OAuth2 client-credentials authentication and exposes a generic
    ``fetch`` method for all public RTE Data endpoints.

    :param client_id: RTE API OAuth2 client id.
    :type client_id: str
    :param client_secret: RTE API OAuth2 client secret.
    :type client_secret: str
    :param session: aiohttp client session.
    :type session: aiohttp.ClientSession
    """

    OAUTH_URL = "https://digital.iservices.rte-france.com/oauth2/token"
    BASE_URL = "https://digital.iservices.rte-france.com/open_api"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        session: aiohttp.ClientSession,
    ):
        """Initialize the RTE Data API client."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._session = session
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    async def _authenticate(self) -> None:
        """Request or refresh the OAuth2 access token."""
        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()

        async with self._session.post(
            self.OAUTH_URL,
            headers={"Authorization": f"Basic {credentials}"},
            data={"grant_type": "client_credentials"},
        ) as resp:
            resp.raise_for_status()
            token_data = await resp.json()

        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in - 60)
        _LOGGER.debug("RTE access token refreshed")

    async def _ensure_token(self) -> None:
        """Refresh the token if it is missing or about to expire."""
        if self._access_token is None or (
            self._token_expires_at is not None
            and datetime.now(UTC) >= self._token_expires_at
        ):
            await self._authenticate()

    async def fetch(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch data from an RTE Data API endpoint.

        :param endpoint: RTE API endpoint path after ``/open_api/``,
            e.g. ``wholesale_market/v3/france_power_exchanges``.
        :type endpoint: str
        :param params: Optional query parameters.
        :type params: dict[str, Any] | None
        :return: Parsed JSON response from the API.
        :rtype: dict[str, Any]
        :raises RTEDataAPIError: If the request fails.
        """
        await self._ensure_token()

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        _LOGGER.debug("Fetching RTE endpoint: %s", url)

        async with self._session.get(
            url,
            headers={"Authorization": f"Bearer {self._access_token}"},
            params=params,
        ) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as err:
                raise RTEDataAPIError(
                    f"RTE API request failed: {err.status} {err.message}"
                ) from err
            return await resp.json()

    async def fetch_france_power_exchanges(self) -> dict[str, Any]:
        """Fetch France power exchange prices and volumes.

        :return: Parsed JSON response from the API.
        :rtype: dict[str, Any]
        """
        today = datetime.now(UTC).date()
        tomorrow = today + timedelta(days=1)
        return await self.fetch(
            "wholesale_market/v3/france_power_exchanges",
            {
                "start_date": f"{today.isoformat()}T00:00:00+00:00",
                "end_date": f"{tomorrow.isoformat()}T23:59:59+00:00",
            },
        )

    async def fetch_actual_generation(self) -> dict[str, Any]:
        """Fetch actual generation per production type.

        :return: Parsed JSON response from the API.
        :rtype: dict[str, Any]
        """
        today = datetime.now(UTC).date()
        tomorrow = today + timedelta(days=1)
        return await self.fetch(
            "actual_generation/v1/actual_generations_per_production_type",
            {
                "start_date": f"{today.isoformat()}T00:00:00+00:00",
                "end_date": f"{tomorrow.isoformat()}T23:59:59+00:00",
            },
        )

    async def fetch_generation_forecast(self) -> dict[str, Any]:
        """Fetch generation forecasts.

        :return: Parsed JSON response from the API.
        :rtype: dict[str, Any]
        """
        today = datetime.now(UTC).date()
        tomorrow = today + timedelta(days=1)
        return await self.fetch(
            "generation_forecast/v1/generation_forecasts",
            {
                "start_date": f"{today.isoformat()}T00:00:00+00:00",
                "end_date": f"{tomorrow.isoformat()}T23:59:59+00:00",
            },
        )

    async def fetch_consumption(self) -> dict[str, Any]:
        """Fetch short-term consumption forecast.

        :return: Parsed JSON response from the API.
        :rtype: dict[str, Any]
        """
        today = datetime.now(UTC).date()
        tomorrow = today + timedelta(days=1)
        return await self.fetch(
            "consumption/v1/short_term",
            {
                "start_date": f"{today.isoformat()}T00:00:00+00:00",
                "end_date": f"{tomorrow.isoformat()}T23:59:59+00:00",
            },
        )

    async def fetch_physical_flows(self) -> dict[str, Any]:
        """Fetch physical cross-border flows.

        :return: Parsed JSON response from the API.
        :rtype: dict[str, Any]
        """
        today = datetime.now(UTC).date()
        tomorrow = today + timedelta(days=1)
        return await self.fetch(
            "physical_flow/v1/physical_flows",
            {
                "start_date": f"{today.isoformat()}T00:00:00+00:00",
                "end_date": f"{tomorrow.isoformat()}T23:59:59+00:00",
            },
        )
