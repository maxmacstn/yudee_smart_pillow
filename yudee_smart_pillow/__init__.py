"""The YUDEE Pillow integration."""
from __future__ import annotations
from datetime import datetime, time, timedelta

import logging
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers import aiohttp_client
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .smart_pillow.pillow_api import PillowCloudAPI
from aiohttp import web
import async_timeout




from .const import COORDINATORS, DATA_UPDATED, DOMAIN

PLATFORMS: list[Platform] = [ Platform.SENSOR, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up YUDEE Pillow device from a config entry."""
    _LOGGER.debug("ASYNC SETUP ENTRY")
    mac = entry.data.get("mac")
    uid = entry.data.get("uid")
    cname = entry.data.get("cname")
    cnameType = entry.data.get("cnameType")
    sort = entry.data.get("sort")

    _LOGGER.debug(f"data = {mac} {uid} {cname} {cnameType} {sort}")
    # assert address is not None

    session = aiohttp_client.async_get_clientsession(hass)

    pillow_api = PillowCloudAPI(session, cname, cnameType, uid, mac, sort)
    coordinator = SmartPillowAPICoordinator(hass, entry, pillow_api)
    hass.data[DOMAIN].setdefault(COORDINATORS, [])
    hass.data[DOMAIN][COORDINATORS].append(coordinator)

    # await coordinator.async_config_entry_first_refresh()
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)


    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class SmartPillowAPICoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, entry:ConfigEntry, pillow_api:PillowCloudAPI):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Smart Pillow Coordinator"
        )
        self.pillow_api = pillow_api
        self._entry = entry

    
    async def check_token(self):
        
        if (self._entry.data.get("token") is not None and  datetime.fromtimestamp(self._entry.data.get("expiration")) > datetime.now() ):
            token = self._entry.data.get("token")
            _LOGGER.debug(f"Token is {token}")
            return True
        
        else:
            return False


    async def _async_update_data(self):
        token_may_expired = False


        if await self.check_token():
            try:

                async with async_timeout.timeout(10):
                    self.pillow_api.set_token(self._entry.data.get("token") )
                    await self.pillow_api.fetch_last_night_report()
                    async_dispatcher_send(self.hass, DATA_UPDATED)

                    # self.async_update_listeners()
            except web.HTTPUnauthorized:
                token_may_expired = True

        if not await self.check_token() or token_may_expired:
            token = await self.pillow_api.get_token()
            expiration = datetime.timestamp( datetime.now() + timedelta(days=15))
            entry_data = self._entry.data.copy()
            entry_data["token"] = token
            entry_data["expiration"] = expiration

            self.hass.config_entries.async_update_entry(self._entry, data=entry_data)

            #Try get data again
            try:

                async with async_timeout.timeout(10):
                    self.pillow_api.set_token(self._entry.data.get("token") )
                    await self.pillow_api.fetch_last_night_report()
                    async_dispatcher_send(self.hass, DATA_UPDATED)

                # self.async_update_listeners()
            except web.HTTPUnauthorized:
                token_may_expired = True
                raise UpdateFailed(f"Error communicating with API")