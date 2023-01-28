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
    await componentData._force_update()
    assert componentData._userdetails is not None
    assert componentData._loandetails is not None
    
    for userid, userdetail in componentData._userdetails.items():
        sensorUser = ComponentUserSensor(componentData, hass, userid)
        _LOGGER.info(f"{NAME} Init sensor for user {userid}")
        sensors.append(sensorUser)
        
    library_names = set()
    for user_id, user_data in componentData._userdetails.items():
        libraryName = user_data.get('account_details').get('libraryName')
        library_names.add(libraryName)
        
    for libraryName in library_names:
        sensorDate = ComponentDateSensor(componentData, hass, libraryName)
        _LOGGER.info(f"{NAME} Init sensor for date {libraryName}")
        sensors.append(sensorDate)
        
    async_add_devices(sensors)

#TODO: sensor per library (total items loand from library), attribute: number of each type lended
#TODO: sensor per type of loan (eg total 5 books lended, 3 DVDs, etc)

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
        self._userdetails = None
        self._loandetails = dict()
        self._hass = hass
        self._lastupdate = None
        self._oauth_token = None
        
    # same as update, but without throttle to make sure init is always executed
    async def _force_update(self):
        _LOGGER.info("Fetching intit stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession()

        if self._session:
            self._userdetails = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            assert self._userdetails is not None
            _LOGGER.info(f"{NAME} init login completed")
            for user_id, userdetail in self._userdetails.items():
                url = userdetail.get('loans').get('url')
                if url:
                    _LOGGER.info(f"calling loan details")
                    loandetails = await self._hass.async_add_executor_job(lambda: self._session.loan_details(url))
                    assert loandetails is not None
                    _LOGGER.debug(f"loandetails {json.dumps(loandetails,indent=4)}") 
                    # _LOGGER.info(f"calling extend_all")
                    # num_extensions = self.session.extend_all(url, False)
                    # _LOGGER.info(f"num of extensions found: {num_extensions}")
                    self._loandetails[user_id] = loandetails
            self._lastupdate = datetime.now()
                
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        await self._force_update()

    async def update(self):
        await self._update()
    
    def clear_session():
        self._session : None



class ComponentUserSensor(Entity):
    def __init__(self, data, hass, userid):
        self._data = data
        self._hass = hass
        self._userid = userid
        self._last_update = None
        
        # _LOGGER.info(f"init sensor userid {userid} _userdetails {self._data._userdetails}")
        self._num_loans = self._data._userdetails.get(self._userid).get('loans').get('loans')
        self._num_reservations = self._data._userdetails.get(self._userid).get('reservations').get('reservations')
        self._open_amounts = self._data._userdetails.get(self._userid).get('open_amounts').get('open_amounts')
        self._barcode = self._data._userdetails.get(self._userid).get('account_details').get('barcode')
        self._username = self._data._userdetails.get(self._userid).get('account_details').get('userName')
        self._libraryName = self._data._userdetails.get(self._userid).get('account_details').get('libraryName')
        self._loandetails = self._data._loandetails.get(self._userid)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._num_loans

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        self._num_loans = self._data._userdetails.get(self._userid).get('loans').get('loans')
        self._num_reservations = self._data._userdetails.get(self._userid).get('reservations').get('reservations')
        self._open_amounts = self._data._userdetails.get(self._userid).get('open_amounts').get('open_amounts')
        self._barcode = self._data._userdetails.get(self._userid).get('account_details').get('barcode')
        self._username = self._data._userdetails.get(self._userid).get('account_details').get('userName')
        self._libraryName = self._data._userdetails.get(self._userid).get('account_details').get('libraryName')
        self._loandetails = self._data._loandetails.get(self._userid)
        
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:bookshelf"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} {self._userid}"
        )

    @property
    def name(self) -> str:
        return f"{NAME} {self._username} {self._libraryName}"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "userid": self._userid,
            "barcode": self._barcode,
            "num_loans": self._num_loans,
            "num_reservations": self._num_reservations,
            "open_amounts": self._open_amounts,
            "username": self._username,
            "libraryName": self._libraryName,
            "loandetails": self._loandetails
        }
        
        # self._userid = userid
        # self._barcode = None
        # self._last_update = None
        # self._num_loans = None
        # self._num_reservations = None
        # self._open_amounts = None
        # self._username = None
        # self._libraryName = None
        # self._loandetails = None

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
        return "loans"

    @property
    def friendly_name(self) -> str:
        return self.name
        

class ComponentDateSensor(Entity):
    def __init__(self, data, hass, libraryName):
        self._data = data
        self._hass = hass
        self._libraryName = libraryName
        self._last_update = None
        self._lowest_till_date = None
        self._days_left = None
        self._loandetails = []
        self._num_loans = 0

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._days_left

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        
        for name, loan_data in self._data._loandetails.items():
            library_name_loop = loan_data.get('library')
            if library_name_loop == self._libraryName:
                if (self._days_left is None) or (self._days_left > loan_data.get('days_remaining')):
                    self._days_left = loan_data.get('days_remaining')
                    self._lowest_till_date = loan_data.get('loan_till')
                    self._loandetails.append(loan_data)
                    ++ self._num_loans
                if self._days_left == loan_data.get('days_remaining'):
                    self._loandetails.append(loan_data)
                    ++ self._num_loans
                    
                #TODO add total number of loans
                #TODO add number of loans per type
        
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:bookshelf"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} {self._libraryName}"
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
            "libraryName": self._libraryName,
            "days_left": self._days_left,
            "lowest_till_date": self._lowest_till_date,
            "num_loans": self._num_loans,
            "loandetails": self._loandetails
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
        return "days"

    @property
    def friendly_name(self) -> str:
        return self.name
        