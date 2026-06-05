import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PulseEightAPI, PulseEightConnectionError, PulseEightAPIError
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SELECT, Platform.SENSOR, Platform.BUTTON, Platform.BINARY_SENSOR]


class PulseEightDataUpdateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, api, poll_interval):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self.api = api

    async def _async_update_data(self):
        try:
            async with asyncio.timeout(20):
                ports = await self.api.get_ports()

                for port in ports:
                    bay = port.get("Bay")
                    mode = port.get("Mode")

                    if mode == "Output":
                        try:
                            details = await self.api.get_port_details("Output", bay)
                            port["FirmwareVersion"] = details.get("FirmwareVersion")
                            port["HPD"] = details.get("HPD")
                        except Exception:
                            port["FirmwareVersion"] = None
                            port["HPD"] = None

                    elif mode == "Input":
                        try:
                            details = await self.api.get_port_details("Input", bay)
                            port["HasSignal"] = details.get("HasSignal")
                        except Exception:
                            port["HasSignal"] = None

                health = await self.api.get_system_health()
                return {"ports": ports, "health": health}

        except PulseEightConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except PulseEightAPIError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed("Timed out fetching data") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data["host"]
    port = entry.data.get("port", DEFAULT_PORT)
    poll_interval = entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

    session = async_get_clientsession(hass)
    api = PulseEightAPI(host, port, session)

    coordinator = PulseEightDataUpdateCoordinator(hass, api, poll_interval)
    await coordinator.async_config_entry_first_refresh()

    details = await api.get_system_details()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "details": details,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
