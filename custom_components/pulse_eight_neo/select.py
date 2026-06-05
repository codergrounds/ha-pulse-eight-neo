import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import PulseEightAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = [
        PulseEightOutputSourceSelect(coordinator, api, port["Bay"], entry.entry_id)
        for port in coordinator.data["ports"]
        if port.get("Mode") == "Output"
    ]
    async_add_entities(entities)


def _device_info(hass, entry_id):
    details = hass.data[DOMAIN][entry_id]["details"]
    rev = details.get("BoardRev")
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="Pulse-Eight Neo",
        manufacturer="Pulse-Eight",
        model=details.get("Model"),
        sw_version=details.get("Version"),
        hw_version=str(rev) if rev is not None else None,
        serial_number=details.get("Serial"),
    )


class PulseEightOutputSourceSelect(CoordinatorEntity, SelectEntity):

    def __init__(self, coordinator, api, bay, entry_id):
        super().__init__(coordinator)
        self.api = api
        self._bay = bay
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_output_{bay}_source"

    def _port(self):
        for p in self.coordinator.data["ports"]:
            if p.get("Mode") == "Output" and p.get("Bay") == self._bay:
                return p
        return None

    @property
    def name(self):
        p = self._port()
        if p and p.get("Name"):
            return p["Name"]
        return f"Output {self._bay + 1}"

    @property
    def current_option(self):
        p = self._port()
        if not p:
            return None
        rx = p.get("ReceiveFrom")
        if rx is None:
            return None
        for port in self.coordinator.data["ports"]:
            if port.get("Mode") == "Input" and port.get("Bay") == rx:
                return port.get("Name")
        return f"Input Bay {rx}"

    @property
    def options(self):
        inputs = sorted(
            [p for p in self.coordinator.data["ports"] if p.get("Mode") == "Input"],
            key=lambda x: x.get("Bay", 0),
        )
        return [p["Name"] for p in inputs if p.get("Name")]

    async def async_select_option(self, option):
        input_bay = None
        for port in self.coordinator.data["ports"]:
            if port.get("Mode") == "Input" and port.get("Name") == option:
                input_bay = port.get("Bay")
                break

        if input_bay is None:
            _LOGGER.error("Can't find input '%s'", option)
            return

        try:
            await self.api.set_port_routing(input_bay, self._bay)
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error("Routing failed for %s: %s", self.name, e)

    @property
    def device_info(self):
        return _device_info(self.hass, self._entry_id)
