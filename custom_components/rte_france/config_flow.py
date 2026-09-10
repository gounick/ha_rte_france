"""Config flow for the RTE France integration."""

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import RTEDataAPI, RTEDataAPIError
from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_ENABLED_ENDPOINTS, DOMAIN
from .endpoints import list_endpoint_keys
from .options_flow import RTEFranceOptionsFlowHandler

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

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._credentials: dict[str, str] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> RTEFranceOptionsFlowHandler:
        """Return the options flow handler."""
        return RTEFranceOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial credentials step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client_id = user_input[CONF_CLIENT_ID]
            client_secret = user_input[CONF_CLIENT_SECRET]

            session = aiohttp.ClientSession()
            try:
                api = RTEDataAPI(client_id, client_secret, session)
                await api.authenticate()
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
                self._credentials = user_input
                await self.async_set_unique_id(
                    f"{DOMAIN}_{client_id[-8:]}", raise_on_progress=False
                )
                self._abort_if_unique_id_configured()
                return await self.async_step_endpoints()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_endpoints(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the endpoint selection step."""
        if user_input is not None:
            return self.async_create_entry(
                title="RTE France",
                data=self._credentials,
                options={CONF_ENABLED_ENDPOINTS: user_input[CONF_ENABLED_ENDPOINTS]},
            )

        all_keys = list_endpoint_keys()
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENABLED_ENDPOINTS,
                    default=all_keys,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=all_keys,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="endpoints",
            data_schema=data_schema,
        )
