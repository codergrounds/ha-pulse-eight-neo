from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = [
        HealthSensor(coordinator, entry.entry_id, "system_status",  "System Status",   "StatusMessage",       None, None),
        HealthSensor(coordinator, entry.entry_id, "power_supply",   "Power Supply",    "PSU1Message",         None, None),
        HealthSensor(coordinator, entry.entry_id, "inputs_health",  "Inputs Health",   "InputModulesMessage", None, None),
        HealthSensor(coordinator, entry.entry_id, "outputs_health", "Outputs Health",  "OutputModulesMessage",None, None),
        HealthSensor(coordinator, entry.entry_id, "temperature",    "Temperature",     "Temperature0",
                     SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT),
        UptimeSensor(coordinator, entry.entry_id),
    ]

    for port in coordinator.data["ports"]:
        if port.get("Mode") == "Output":
            entities.append(TxFirmwareSensor(coordinator, entry.entry_id, port["Bay"]))

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


class HealthSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, entry_id, sensor_id, name, json_key,
                 device_class=None, unit=None, state_class=None):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._json_key = json_key

        self._attr_unique_id = f"{entry_id}_sensor_{sensor_id}"
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.coordinator.data.get("health", {}).get(self._json_key)

    @property
    def device_info(self):
        return _device_info(self.hass, self._entry_id)


class UptimeSensor(CoordinatorEntity, SensorEntity):

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_sensor_uptime"
        self._attr_name = "Uptime"
        self._prev = None
        self._last_boot = None

    @property
    def native_value(self):
        uptime = self.coordinator.data.get("health", {}).get("Uptime")
        if uptime is None:
            return None

        now = dt_util.utcnow()
        if self._last_boot is None:
            self._last_boot = now - timedelta(seconds=int(uptime))
        elif self._prev is not None and uptime < self._prev:
            _LOGGER.info("Pulse-Eight Neo rebooted, resetting uptime tracking")
            self._last_boot = now

        self._prev = uptime
        return uptime

    @property
    def extra_state_attributes(self):
        if self._last_boot:
            return {"last_boot": self._last_boot.isoformat()}
        return {}

    @property
    def device_info(self):
        return _device_info(self.hass, self._entry_id)


class TxFirmwareSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, entry_id, bay):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._bay = bay
        self._attr_unique_id = f"{entry_id}_output_{bay}_tx_firmware"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    def _port(self):
        for p in self.coordinator.data["ports"]:
            if p.get("Mode") == "Output" and p.get("Bay") == self._bay:
                return p
        return None

    @property
    def name(self):
        p = self._port()
        label = p.get("Name") if p else f"Output {self._bay + 1}"
        return f"{label} TX Firmware"

    @property
    def native_value(self):
        p = self._port()
        if not p:
            return None
        fw = p.get("FirmwareVersion", "")
        return fw.split()[0] if fw else None

    @property
    def device_info(self):
        return _device_info(self.hass, self._entry_id)
