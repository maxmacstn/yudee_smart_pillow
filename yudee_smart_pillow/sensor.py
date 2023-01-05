from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


from typing import Callable, Optional, Union

from . import SmartPillowAPICoordinator

from homeassistant import config_entries
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEVICE_CLASS_DATE,
    PERCENTAGE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATORS, DATA_UPDATED, DOMAIN
from .device import device_key_to_bluetooth_entity_key, sensor_device_info_to_hass
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class SmartPillowRequiredKeysMixin:
    """Mixin for required keys."""

    value_func: Callable[[dict], float | None]


@dataclass
class SmartPillowEntityDescription(SensorEntityDescription, SmartPillowRequiredKeysMixin):
    """Describes Smart pillow sensor entity."""


SENSOR_TYPE_SLEEP_SCORE = SmartPillowEntityDescription(
    key="score",
    name="Sleep score",
    icon="mdi:star",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: data["score"],
)

SENSOR_TYPE_GO_TO_BED_TIME = SmartPillowEntityDescription(
    key="go_to_bed_time",
    name="Go to bed time",
    icon="mdi:bed-clock",
    value_func=lambda data: datetime.fromtimestamp(data["go_to_bed_time"]),
)

SENSOR_TYPE_WAKE_UP_TIME = SmartPillowEntityDescription(
    key="wake_up_time",
    name="Wake up time",
    icon="mdi:bed-clock",
    device_class=DEVICE_CLASS_DATE,
    value_func=lambda data: datetime.fromtimestamp(data["wake_up_time"]),
)
SENSOR_TYPE_AWAKE_PERCENT = SmartPillowEntityDescription(
    key="awake_percent",
    name="Awake",
    icon="mdi:bed",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: data["awake"]["percentage"],
)
SENSOR_TYPE_DEEP_PERCENT = SmartPillowEntityDescription(
    key="deep_sleep_percent",
    name="Deep sleep",
    icon="mdi:bed",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: data["deep"]["percentage"],
)
SENSOR_TYPE_LIGHT_PERCENT = SmartPillowEntityDescription(
    key="light_sleep_percent",
    name="Light sleep",
    icon="mdi:bed",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: data["light"]["percentage"],
)
SENSOR_TYPE_REM_PERCENT = SmartPillowEntityDescription(
    key="rem_percent",
    name="REM",
    icon="mdi:bed",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: data["rem"]["percentage"],
)
SENSOR_TYPE_HEART_BEAT_AVG = SmartPillowEntityDescription(
    key="heart_beat_avg",
    name="Heart beat average",
    icon="mdi:heart-pulse",
    native_unit_of_measurement="BPM",
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: data["heart_beat_avg"],
)
SENSOR_TYPE_BREATHE_BEAT_AVG = SmartPillowEntityDescription(
    key="breath_rate_avg",
    name="Respiratory rate average",
    icon="mdi:lungs",
    native_unit_of_measurement="BPM",
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: data["breath_avg"],
)

SENSOR_TYPE_SLEEP_DURATION_HR = SmartPillowEntityDescription(
    key="SLEEP_DURATION_HR",
    name="Sleep duration",
    icon="mdi:bed-clock",
    native_unit_of_measurement="Hour",
    state_class=SensorStateClass.MEASUREMENT,
    value_func=lambda data: round((datetime.fromtimestamp(data["wake_up_time"]) - datetime.fromtimestamp(data["go_to_bed_time"])).total_seconds() / 3600, 1)
)

SENSOR_TYPE_DEEP_SLEEP_TIME = SmartPillowEntityDescription(
    key="SLEEP_DEEP_TIME",
    name="Deep sleep time",
    icon="mdi:bed-clock",
    value_func=lambda data: data["deep_sleep_time"]
)

SENSOR_TYPE_LIGHT_SLEEP_TIME = SmartPillowEntityDescription(
    key="SLEEP_LIGHT_TIME",
    name="Light sleep time",
    icon="mdi:bed-clock",
    value_func=lambda data: data["light_sleep_time"]
)

SENSOR_TYPE_REM_TIME = SmartPillowEntityDescription(
    key="SLEEP_REM_TIME",
    name="REM time",
    icon="mdi:bed-clock",
    value_func=lambda data: data["rem_time"]
)

SENSOR_TYPE_AWAKE_TIME = SmartPillowEntityDescription(
    key="SLEEP_AWAKE_TIME",
    name="Awake time",
    icon="mdi:bed-clock",
    value_func=lambda data: data["awake_time"]
)

SENSOR_TYPE_MOVE_TIME = SmartPillowEntityDescription(
    key="SLEEP_MOVE_TIME",
    name="Move time",
    icon="mdi:car-brake-worn-linings",
    value_func=lambda data: data["move_time"]
)

SENSOR_TYPE_REVOLVE_TIME = SmartPillowEntityDescription(
    key="SLEEP_REVOLVE_TIME",
    name="Revolve time",
    icon="mdi:reload",
    value_func=lambda data: data["revolve_time"]
)

SENSOR_TYPE_VIBRATE_COUNT = SmartPillowEntityDescription(
    key="SLEEP_VIBRATE_COUNT",
    name="Vibrate count",
    icon="mdi:vibrate",
    value_func=lambda data: data["vibrate_count"],
    state_class=SensorStateClass.TOTAL
)


SENSOR_TYPE_SNORE_COUNT = SmartPillowEntityDescription(
    key="SLEEP_SNORE_COUNT",
    name="Snore count",
    icon="mdi:sleep",
    value_func=lambda data: data["snore_count_total"],
    state_class=SensorStateClass.TOTAL
)

SENSOR_TYPE_VIBRATE_TIME = SmartPillowEntityDescription(
    key="SLEEP_VIBRATE_TIME",
    name="Vibrate time",
    icon="mdi:vibrate",
    value_func=lambda data: data["vibrate_time"]
)


SENSOR_TYPE_SNORE_COUNT_TIME = SmartPillowEntityDescription(
    key="SLEEP_SNORE_COUNT_TIME",
    name="Snore time",
    icon="mdi:sleep",
    value_func=lambda data: data["snore_count_time"]
)

SUPPORTED_SENSORS = [SENSOR_TYPE_SLEEP_SCORE, SENSOR_TYPE_GO_TO_BED_TIME, SENSOR_TYPE_WAKE_UP_TIME
                     , SENSOR_TYPE_AWAKE_PERCENT
                     , SENSOR_TYPE_DEEP_PERCENT
                     , SENSOR_TYPE_LIGHT_PERCENT
                     , SENSOR_TYPE_REM_PERCENT
                     , SENSOR_TYPE_HEART_BEAT_AVG
                     , SENSOR_TYPE_BREATHE_BEAT_AVG
                     , SENSOR_TYPE_SLEEP_DURATION_HR
                     , SENSOR_TYPE_DEEP_SLEEP_TIME
                     , SENSOR_TYPE_LIGHT_SLEEP_TIME
                     , SENSOR_TYPE_REM_TIME
                     , SENSOR_TYPE_AWAKE_TIME
                     , SENSOR_TYPE_REVOLVE_TIME
                     , SENSOR_TYPE_MOVE_TIME
                     , SENSOR_TYPE_VIBRATE_COUNT
                     , SENSOR_TYPE_SNORE_COUNT
                     , SENSOR_TYPE_VIBRATE_TIME
                     , SENSOR_TYPE_SNORE_COUNT_TIME]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = []
    for coordinator in hass.data[DOMAIN][COORDINATORS]:
        for sensor in SUPPORTED_SENSORS:
            entities.append(SmartPillowSensorAdapter(coordinator, sensor))

    async_add_entities(entities)


class SmartPillowSensorAdapter(SensorEntity):

    _attr_should_poll = False

    """Representation of a Sensor."""

    entity_description: SensorEntityDescription

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
        self.entity_description = description
        self.unsub_update: CALLBACK_TYPE | None = None

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.unsub_update = async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    async def will_remove_from_hass(self) -> None:
        """Unsubscribe from update dispatcher."""
        if self.unsub_update:
            self.unsub_update()
        self.unsub_update = None

    @callback
    def _schedule_immediate_update(self) -> None:
        self.async_schedule_update_ha_state(True)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if (self._api.day_report is None):
            return None
        return self.entity_description.value_func(self._api.day_report)

    def available(self) -> bool:
        return self._api.day_report is None

    @property
    def device_info(self) -> DeviceInfo:
        """Return info about the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._api.did)},
            manufacturer="YUDEE",
            model="Dual-Mode Sleep Sensor",
            name="Sleep Sensor",
        )

