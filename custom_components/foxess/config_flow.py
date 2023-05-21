"""Config flow to configure Foxess."""
import hashlib
import logging

from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DEVICE_ID,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import UpdateFailed
import homeassistant.helpers.config_validation as cv

from .commons import auth_and_get_token
from .const import (
    DOMAIN,
    DEFAULT_NAME,

)

DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


class FoxessFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a FoxEss config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get option flow."""
        return FoxessOptionsFlowHandler(config_entry)

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                hashed_password = hashlib.md5(user_input.get(CONF_PASSWORD).encode()).hexdigest()
                token = await auth_and_get_token(self.hass, user_input.get(CONF_USERNAME), hashed_password)
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()
            except UpdateFailed as e:
                errors["base"] = str(e)
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class FoxessOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle option."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Dict[str, Any]:
        errors = {}
        config = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            try:
                hashed_password = hashlib.md5(user_input.get(CONF_PASSWORD).encode()).hexdigest()
                token = await auth_and_get_token(self.hass, user_input.get(CONF_USERNAME), hashed_password)
            except UpdateFailed as e:
                errors["base"] = str(e)
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema(
            {
                vol.Optional(CONF_NAME, default=config.get(CONF_NAME)): cv.string,
                vol.Required(CONF_USERNAME, default=config.get(CONF_USERNAME)): cv.string,
                vol.Required(CONF_PASSWORD, default=config.get(CONF_PASSWORD)): cv.string,
                vol.Required(CONF_DEVICE_ID, default=config.get(CONF_DEVICE_ID)): cv.string,
            }
        ), errors=errors)
