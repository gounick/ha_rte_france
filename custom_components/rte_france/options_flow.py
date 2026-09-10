"""Options flow for the RTE France integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_ENABLED_ENDPOINTS
from .endpoints import list_endpoint_keys

_LOGGER = logging.getLogger(__name__)


class RTEFranceOptionsFlowHandler(OptionsFlow):
    """Handle options for the RTE France integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    @callback
    def _build_schema(self) -> vol.Schema:
        """Return the schema for the options step."""
        all_keys = list_endpoint_keys()
        default = self.config_entry.options.get(CONF_ENABLED_ENDPOINTS, all_keys)
        return vol.Schema(
            {
                vol.Required(
                    CONF_ENABLED_ENDPOINTS,
                    default=default,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=all_keys,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._build_schema(),
        )


@callback
def async_get_options_flow(config_entry: ConfigEntry) -> RTEFranceOptionsFlowHandler:
    """Return the options flow handler for this config entry."""
    return RTEFranceOptionsFlowHandler(config_entry)
