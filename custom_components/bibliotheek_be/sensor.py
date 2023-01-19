import logging
import asyncio
from datetime import date, datetime, timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from . import DOMAIN, NAME
from .utils import *

_LOGGER = logging.getLogger(__name__)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional("username", default=""): cv.string,
        vol.Optional("password", default=""): cv.string,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(hours=1)


async def dry_setup(hass, config_entry, async_add_devices):
    config = config_entry
    username = config.get("username")
    password = config.get("password")

    check_settings(config, hass)
    sensors = []
    
    componentData = ComponentData(
        username,
        password,
        async_get_clientsession(hass),
        hass
    )
    await componentData._init()
    assert componentData._usage_details is not None
    
    sensorMobile = ComponentMobileSensor(componentData, hass)
    sensors.append(sensorMobile)
    
    sensorInternet = ComponentInternetSensor(componentData, hass)
    sensors.append(sensorInternet)
    
    async_add_devices(sensors)


async def async_setup_platform(
    hass, config_entry, async_add_devices, discovery_info=None
):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_platform " + NAME)
    await dry_setup(hass, config_entry, async_add_devices)
    return True


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_entry " + NAME)
    config = config_entry.data
    await dry_setup(hass, config, async_add_devices)
    return True


async def async_remove_entry(hass, config_entry):
    _LOGGER.info("async_remove_entry " + NAME)
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass
        

class ComponentData:
    def __init__(self, username, password, client, hass):
        self._username = username
        self._password = password
        self._client = client
        self._session = ComponentSession()
        self._usage_details = None
        self._hass = hass
        self._lastupdate = None
        self._user_details = None
        
    # same as update, but without throttle to make sure init is always executed
    async def _init(self):
        _LOGGER.info("Fetching intit stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession()

        if self._session:
            self._user_details = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            _LOGGER.info(f"{NAME} init login completed")
            self._usage_details = await self._hass.async_add_executor_job(lambda: self._session.usage_details())
            _LOGGER.debug(f"{NAME} init usage_details data: {self._usage_details}")
            self._lastupdate = datetime.now()
                
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        _LOGGER.info("Fetching intit stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession()

        if self._session:
            self._user_details = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            _LOGGER.info(f"{NAME} init login completed")
            self._usage_details = await self._hass.async_add_executor_job(lambda: self._session.usage_details())
            _LOGGER.debug(f"{NAME} init usage_details data: {self._usage_details}")
            self._lastupdate = datetime.now()

    async def update(self):
        await self._update()
    
    def clear_session():
        self._session : None



class ComponentMobileSensor(Entity):
    def __init__(self, data, hass):
        self._data = data
        self._hass = hass
        self._last_update = None
        self._period_start_date = None
        self._period_left = None
        self._total_volume = None
        self._isunlimited = None
        self._extracosts = None
        self._used_percentage = None
        self._phonenumber = None
        self._includedvolume_usage = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._used_percentage

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        self._phonenumber = self._data._user_details.get('Object').get('Customer').get('PhoneNumber')
        self._period_start_date = self._data._usage_details.get('Object')[2].get('Properties')[0].get('Value')
        self._period_left = self._data._usage_details.get('Object')[2].get('Properties')[1].get('Value')
        
        self._includedvolume_usage = self._data._usage_details.get('Object')[1].get('Properties')[0].get('Value')
        self._total_volume = self._data._usage_details.get('Object')[1].get('Properties')[1].get('Value')
        self._used_percentage = self._data._usage_details.get('Object')[1].get('Properties')[2].get('Value')
        self._isunlimited = self._data._usage_details.get('Object')[1].get('Properties')[3].get('Value')
        self._extracosts = self._data._usage_details.get('Object')[3].get('Properties')[0].get('Value')
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:phone-plus"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            NAME + " call sms"
        )

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "phone_number": self._phonenumber,
            "used_percentage": self._used_percentage,
            "total_volume": self._total_volume,
            "includedvolume_usage": self._includedvolume_usage,
            "unlimited": self._isunlimited,
            "period_start": self._period_start_date,
            "period_days_left": self._period_left,
            "extra_costs": self._extracosts,
            "usage_details_json": self._data._usage_details,
            "user_details_json": self._data._user_details
        }

    @property
    def device_info(self) -> dict:
        """I can't remember why this was needed :D"""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
        }

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"

    @property
    def friendly_name(self) -> str:
        return self.unique_id
        

class ComponentInternetSensor(Entity):
    def __init__(self, data, hass):
        self._data = data
        self._hass = hass
        self._last_update = None
        self._period_start_date = None
        self._period_left = None
        self._total_volume = None
        self._isunlimited = None
        self._used_percentage = None
        self._phonenumber = None
        self._includedvolume_usage = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._used_percentage

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        self._phonenumber = self._data._user_details.get('Object').get('Customer').get('PhoneNumber')
        
        self._period_start_date = self._data._usage_details.get('Object')[2].get('Properties')[0].get('Value')
        self._period_left = self._data._usage_details.get('Object')[2].get('Properties')[1].get('Value')
        
        self._includedvolume_usage = self._data._usage_details.get('Object')[0].get('Properties')[0].get('Value')
        self._total_volume = self._data._usage_details.get('Object')[0].get('Properties')[1].get('Value')
        self._used_percentage = self._data._usage_details.get('Object')[0].get('Properties')[2].get('Value')
        self._isunlimited = self._data._usage_details.get('Object')[0].get('Properties')[3].get('Value')
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:web"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            NAME + " internet"
        )

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "phone_number": self._phonenumber,
            "used_percentage": self._used_percentage,
            "total_volume": self._total_volume,
            "includedvolume_usage": self._includedvolume_usage,
            "unlimited": self._isunlimited,
            "period_start": self._period_start_date,
            "period_days_left": self._period_left,
            "usage_details_json": self._data._usage_details
        }

    @property
    def device_info(self) -> dict:
        """I can't remember why this was needed :D"""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
        }

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"

    @property
    def friendly_name(self) -> str:
        return self.unique_id
        
