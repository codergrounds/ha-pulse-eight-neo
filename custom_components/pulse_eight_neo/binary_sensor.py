import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = [MatrixAvailabilitySensor(coordinator, entry.entry_id)]

    for port in coordinator.data["ports"]:
        mode = port.get("Mode")
        bay = port["Bay"]
        if mode == "Input":
            entities.append(InputSignalSensor(coordinator, entry.entry_id, bay))
        elif mode == "Output":
            entities.append(OutputConnectedSensor(coordinator, entry.entry_id, bay))

    async_add_entities(entities)


def _device_info(hass, entry_id):
    d = hass.data[DOMAIN][entry_id]["details"]
    rev = d.get("BoardRev")
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="Pulse-Eight Neo",
        manufacturer="Pulse-Eight",
        model=d.get("Model"),
        sw_version=d.get("Version"),
        hw_version=str(rev) if rev is not None else None,
        serial_number=d.get("Serial"),
    )


class MatrixAvailabilitySensor(CoordinatorEntity, BinarySensorEntity):

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_matrix_available"
        self._attr_name = "Matrix Available"

    @property
    def is_on(self):
        return self.coordinator.last_update_success

    @property
    def device_info(self):
        return _device_info(self.hass, self._entry_id)


class InputSignalSensor(CoordinatorEntity, BinarySensorEntity):

    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id, bay):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._bay = bay
        self._attr_unique_id = f"{entry_id}_input_{bay}_signal"

    def _port(self):
        for p in self.coordinator.data["ports"]:
            if p.get("Mode") == "Input" and p.get("Bay") == self._bay:
                return p
        return None

    @property
    def name(self):
        p = self._port()
        label = p.get("Name") if p else f"Input {self._bay + 1}"
        return f"{label} Signal"

    @property
    def is_on(self):
        p = self._port()
        if not p or p.get("HasSignal") is None:
            return None
        return bool(p["HasSignal"])

    @property
    def available(self):
        p = self._port()
        return p is not None and p.get("HasSignal") is not None

    @property
    def device_info(self):
        return _device_info(self.hass, self._entry_id)


class OutputConnectedSensor(CoordinatorEntity, BinarySensorEntity):

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id, bay):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._bay = bay
        self._attr_unique_id = f"{entry_id}_output_{bay}_connected"

    def _port(self):
        for p in self.coordinator.data["ports"]:
            if p.get("Mode") == "Output" and p.get("Bay") == self._bay:
                return p
        return None

    @property
    def name(self):
        p = self._port()
        label = p.get("Name") if p else f"Output {self._bay + 1}"
        return f"{label} Connected"

    @property
    def is_on(self):
        p = self._port()
        if not p or p.get("HPD") is None:
            return None
        return bool(p["HPD"])

    @property
    def available(self):
        p = self._port()
        return p is not None and p.get("HPD") is not None

    @property
    def device_info(self):
        return _device_info(self.hass, self._entry_id)
