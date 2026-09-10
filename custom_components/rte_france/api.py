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

    async def authenticate(self) -> None:
        """Validate credentials by fetching an OAuth2 token.

        :raises RTEDataAPIError: If the credentials are rejected.
        :raises aiohttp.ClientError: If the network request fails.
        """
        await self._authenticate()

    async def _authenticate(self) -> None:
        """Request or refresh the OAuth2 access token."""
        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()

        try:
            async with self._session.post(
                self.OAUTH_URL,
                headers={"Authorization": f"Basic {credentials}"},
                data={"grant_type": "client_credentials"},
            ) as resp:
                resp.raise_for_status()
                token_data = await resp.json()
        except aiohttp.ClientResponseError as err:
            raise RTEDataAPIError(
                f"RTE OAuth authentication failed: {err.status} {err.message}"
            ) from err

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
            e.g. ``wholesale_market/v2/france_power_exchanges``.
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
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
            },
            params=params,
        ) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as err:
                raise RTEDataAPIError(
                    f"RTE API request failed: {err.status} {err.message}"
                ) from err
            return await resp.json()
