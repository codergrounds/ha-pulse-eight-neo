import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    async_add_entities([MatrixAvailabilitySensor(coordinator, entry.entry_id)])


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
