from dataclasses import dataclass
from typing import Callable
from homeassistant.components.sensor import SensorEntityDescription


@dataclass
class SmartPillowRequiredKeysMixin:
    """Mixin for required keys."""

    value_func: Callable[[dict], float | None]


@dataclass
class SmartPillowEntityDescription(SensorEntityDescription, SmartPillowRequiredKeysMixin):
    """Describes Smart pillow sensor entity."""
