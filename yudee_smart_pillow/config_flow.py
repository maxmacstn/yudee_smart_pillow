"""Config flow for Yudee Pillow integration."""
from __future__ import annotations

import asyncio
from collections.abc import Mapping
import dataclasses
import secrets
from typing import Any
import os,binascii


import voluptuous as vol

import logging


from homeassistant.components import onboarding
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    BluetoothManager
)
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult
                

from .const import DOMAIN, DATA_MANAGER



# How long to wait for additional advertisement packets if we don't have the right ones
ADDITIONAL_DISCOVERY_TIMEOUT = 60

_LOGGER = logging.getLogger(__name__)

DEBUG_ENV = True

try:
    from .test_credentials import *
    _LOGGER.debug("Run integration in debug mode")

except ImportError:
    DEBUG_ENV = False
    _LOGGER.debug("Run integration in prodution mode")

@dataclasses.dataclass
class Discovery:
    """A discovered bluetooth device."""

    title: str
    discovery_info: BluetoothServiceInfo
    # device: DeviceData
    device: Any


# def _title(discovery_info: BluetoothServiceInfo, device: DeviceData) -> str:
# def _title(discovery_info: BluetoothServiceInfo, device) -> str:
#     return "MLILY"
    # return device.title or device.get_device_name() or discovery_info.name


class YUDEEPillowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for YUDEE Pillow Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfo | None = None
        # self._discovered_device: DeviceData | None = None
        self._discovered_device  = None
        self._discovered_devices: dict[str, Discovery] = {}


    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        # self._abort_if_unique_id_configured()
        # device = DeviceData()
        # if not device.supported(discovery_info):
        #     return self.async_abort(reason="not_supported")
        _LOGGER.debug("Found BLE {discovery_info}")

        title = discovery_info.name
        self.context["title_placeholders"] = {"name": title}

        self._discovered_device = discovery_info

        return await self.async_step_bluetooth_confirm()



    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        """Confirm discovery."""
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            mac = str(self._discovered_device.address)

            if (len(mac) != 17):
                mac = ""

            manager: BluetoothManager = self.hass.data[DATA_MANAGER]
            adapters = await manager.async_get_bluetooth_adapters()
            uid = secrets.token_hex(32)
            if (adapters):  
                mac = list(adapters.values())[0]["address"].replace(":","").lower()
                if mac != "000000000000":
                    uid = mac


            if DEBUG_ENV:
                data_schema = {
                    vol.Required("mac", default=mac):str,
                    vol.Required("cname", default=TEST_CNAME): str,
                    vol.Required("cnameType", default=TEST_CNAMETYPE): str,
                    vol.Required("uid", default=TEST_UID): str,
                    vol.Required("sort", default=TEST_SORT): str,
                }
            else:
                data_schema = {
                    vol.Required("mac", default=mac):str,
                    vol.Required("cname"): str,
                    vol.Required("cnameType"): str,
                    vol.Required("uid"): str,
                    vol.Required("sort"): str,
                }

            return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:


        manager: BluetoothManager = self.hass.data[DATA_MANAGER]
        adapters = await manager.async_get_bluetooth_adapters()
        
        uid = secrets.token_hex(32)
        if (adapters):  
            mac = list(adapters.values())[0]["address"].replace(":","").lower()
            if mac != "000000000000":
                uid = mac
    
        if user_input is not None:
            _LOGGER.debug(user_input)
            await self.async_set_unique_id(user_input["mac"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
            title="Smart Pillow - " + user_input["mac"].replace(":","")[4:],
                data=user_input,
            )
        
        if DEBUG_ENV:
            data_schema = {
                vol.Required("mac", default=TEST_DID): str,
                vol.Required("cname", default=TEST_CNAME): str,
                vol.Required("cnameType", default=TEST_CNAMETYPE): str,
                vol.Required("uid", default=TEST_UID): str,
                vol.Required("sort", default=TEST_SORT): str,
            }
        else:
            data_schema = {
                vol.Required("mac"): str,
                vol.Required("cname"): str,
                vol.Required("cnameType"): str,
                vol.Required("uid"): str,
                vol.Required("sort"): str,
            }


        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))
