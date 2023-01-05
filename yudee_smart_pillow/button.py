from __future__ import annotations
import asyncio
from dataclasses import dataclass
import logging
from asyncio import sleep
from typing import Callable
from . import SmartPillowAPICoordinator
from .entity_description import SmartPillowEntityDescription
from .smart_pillow.pillow_api import PillowCloudAPI

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import  COORDINATORS, DOMAIN
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription


_LOGGER = logging.getLogger(__name__)

@dataclass
class SmartPillowRequiredKeysMixin:
    """Mixin for required keys."""

    run_func: Callable[[PillowCloudAPI], None]


@dataclass
class SmartPillowEntityDescription(ButtonEntityDescription, SmartPillowRequiredKeysMixin):
    """Describes Smart pillow sensor entity."""

BUTTON_TYPE_UPDATE_LAST_NIGHT = SmartPillowEntityDescription(
    key="get_last_night_report",
    name="Get last night report",
    icon="mdi:chart-areaspline",
    # device_class=ButtonDeviceClass.SWITCH,
    run_func=lambda api: api.fetch_last_night_report(),
)



async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    
    entities = []
    for coordinator in hass.data[DOMAIN][COORDINATORS]:

        entities.append(SmartPillowSensorAdapter(coordinator, BUTTON_TYPE_UPDATE_LAST_NIGHT))


    async_add_entities(entities)
    _LOGGER.debug("Button setup entry")

class SmartPillowSensorAdapter(ButtonEntity):

    """Representation of a Sensor."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: SmartPillowAPICoordinator,
        description: SmartPillowEntityDescription,
    ) -> None:
        # super().__init__(coordinator, description.name)
        # super().__init__()

        # Override attributes from super
        # self._name = f"{self._device.name} {description.name}"
        self._attr_unique_id = f"{coordinator.pillow_api.did}_{description.key}"
        self._api = coordinator.pillow_api
        self._coordinator = coordinator
        self.entity_description = description


    async def async_press(self) -> None:
        # await self.entity_description.run_func(self._api)
        await self._coordinator.async_refresh()
        self.async_schedule_update_ha_state(True)
        # await self._coordinator.async_config_entry_first_refresh()

    def available(self) -> bool:
        return self._api.day_report is None

    @property
    def device_info(self) -> DeviceInfo:
        """Return info about the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._api.did)},
            manufacturer="MLILY",
            model="Dual-Mode Sleep Sensor",
            name="Sleep Sensor",
        )
