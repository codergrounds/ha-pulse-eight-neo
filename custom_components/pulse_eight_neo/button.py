import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import PulseEightAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    async_add_entities([RebootButton(api, entry.entry_id)])


class RebootButton(ButtonEntity):

    def __init__(self, api, entry_id):
        self.api = api
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_button_reboot"
        self._attr_name = "Reboot System"
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self):
        _LOGGER.warning("Rebooting Pulse-Eight matrix")
        try:
            await self.api.reboot()
        except Exception as e:
            _LOGGER.error("Reboot failed: %s", e)

    @property
    def device_info(self):
        d = self.hass.data[DOMAIN][self._entry_id]["details"]
        rev = d.get("BoardRev")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Pulse-Eight Neo Matrix",
            manufacturer="Pulse-Eight",
            model=d.get("Model"),
            sw_version=d.get("Version"),
            hw_version=str(rev) if rev is not None else None,
            serial_number=d.get("Serial"),
        )
