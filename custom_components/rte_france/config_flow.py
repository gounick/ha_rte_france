"""Config flow for the RTE France integration."""

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .api import RTEDataAPI, RTEDataAPIError
from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
    }
)


class RTEFranceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for RTE France."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.

        :param user_input: User-submitted credentials, or None on first call.
        :type user_input: dict[str, Any] | None
        :return: Flow result.
        :rtype: FlowResult
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            client_id = user_input[CONF_CLIENT_ID]
            client_secret = user_input[CONF_CLIENT_SECRET]

            session = aiohttp.ClientSession()
            try:
                api = RTEDataAPI(client_id, client_secret, session)
                await api.fetch_france_power_exchanges()
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except RTEDataAPIError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
            finally:
                await session.close()

            if not errors:
                await self.async_set_unique_id(
                    f"{DOMAIN}_{client_id[-8:]}", raise_on_progress=False
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="RTE France",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
