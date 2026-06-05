import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PulseEightAPI, PulseEightAPIError, PulseEightConnectionError
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PulseEightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input["host"]
            port = user_input.get("port", DEFAULT_PORT)

            try:
                session = async_get_clientsession(self.hass)
                api = PulseEightAPI(host, port, session)
                details = await api.get_system_details()

                uid = details.get("MAC") or details.get("Serial") or f"{host}:{port}"
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()

                model = details.get("Model", "Pulse-Eight Neo")
                return self.async_create_entry(title=f"{model} ({host})", data=user_input)

            except PulseEightConnectionError:
                errors["base"] = "cannot_connect"
            except PulseEightAPIError:
                errors["base"] = "api_error"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"

        schema = vol.Schema({
            vol.Required("host"): str,
            vol.Optional("port", default=DEFAULT_PORT): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

        schema = vol.Schema({
            vol.Optional(CONF_POLL_INTERVAL, default=current_interval): vol.All(
                int, vol.Range(min=5, max=300)
            ),
        })

        return self.async_show_form(step_id="init", data_schema=schema)
