import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PulseEightAPI, PulseEightConnectionError, PulseEightAPIError
from .const import DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SELECT, Platform.SENSOR, Platform.BUTTON]


class PulseEightDataUpdateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, api):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self):
        try:
            async with asyncio.timeout(20):
                ports = await self.api.get_ports()

                for port in ports:
                    if port.get("Mode") == "Output":
                        bay = port.get("Bay")
                        try:
                            details = await self.api.get_port_details("Output", bay)
                            port["FirmwareVersion"] = details.get("FirmwareVersion")
                        except Exception:
                            port["FirmwareVersion"] = None

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

    session = async_get_clientsession(hass)
    api = PulseEightAPI(host, port, session)

    coordinator = PulseEightDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    details = await api.get_system_details()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "details": details,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
