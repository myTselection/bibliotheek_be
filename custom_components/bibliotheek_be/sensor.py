import logging
import asyncio
from datetime import date, datetime, timedelta
import random

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.util import Throttle

from . import DOMAIN, NAME
from .utils import *

_LOGGER = logging.getLogger(__name__)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("username"): cv.string,
        vol.Required("password"): cv.string,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=120 + random.uniform(10, 20))


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
    assert componentData._librarydetails is not None
    
    
    _LOGGER.debug(f"userdetails dry_setup {json.dumps(componentData._userdetails,indent=4)}") 
    
    _LOGGER.debug(f"loandetails dry_setup {json.dumps(componentData._loandetails,indent=4)}") 
    
    for userid, userdetail in componentData._userdetails.items():
        sensorUser = ComponentUserSensor(componentData, hass, userid)
        _LOGGER.debug(f"{NAME} Init sensor for user {userid}")
        sensors.append(sensorUser)
        
    library_names = set()
    loan_types = dict()
    for user_id, loan_data in componentData._loandetails.items():
        for loan_id, loan_item in loan_data.items():
            libraryName = loan_item.get('library')
            library_names.add(libraryName)
            loan_type = loan_item.get('loan_type')
            loan_types[loan_type] = 0
    _LOGGER.debug(f"loan_types dry_setup {json.dumps(loan_types,indent=4)}") 
        
    for libraryName in library_names:
        sensorDate = ComponentLibrarySensor(componentData, hass, libraryName, loan_types)
        _LOGGER.debug(f"{NAME} Init sensor for date {libraryName}")
        sensors.append(sensorDate)
        
    sensorLibrariesWarning = ComponentLibrariesWarningSensor(componentData, hass)
    sensors.append(sensorLibrariesWarning)
        
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
        self._librarydetails = dict()
        self._hass = hass
        self._lastupdate = None
        self._oauth_token = None
        
    # same as update, but without throttle to make sure init is always executed
    async def _force_update(self):
        _LOGGER.info("Fetching update stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession()

        if self._session:
            self._userdetails = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            assert self._userdetails is not None
            _LOGGER.debug(f"{NAME} update login completed")
            for user_id, userdetail in self._userdetails.items():
                url = userdetail.get('loans').get('url')
                if url:
                    _LOGGER.info(f"Calling loan details {userdetail.get('account_details').get('userName')}")
                    loandetails = await self._hass.async_add_executor_job(lambda: self._session.loan_details(url))
                    assert loandetails is not None
                    username = userdetail.get('account_details').get('userName')
                    barcode = userdetail.get('account_details').get('barcode')
                    barcode_spell = userdetail.get('account_details').get('barcode_spell')
                    for loan_info in loandetails.values():
                        loan_info["user"] = username
                        loan_info["userid"] = user_id
                        loan_info["barcode"] = barcode
                        loan_info["barcode_spell"] = barcode_spell
                        libraryName = loan_info.get('library')
                        libraryurl = f"{userdetail.get('account_details').get('library')}/adres-en-openingsuren"
                        if not self._librarydetails.get(libraryName):
                            _LOGGER.info(f"Calling library details {libraryName}")
                            librarydetails = await self._hass.async_add_executor_job(lambda: self._session.library_details(libraryurl))
                            assert librarydetails is not None
                            self._librarydetails[libraryName] = librarydetails
                    _LOGGER.debug(f"loandetails {json.dumps(loandetails,indent=4)}") 
                    self._loandetails[user_id] = loandetails

            self._lastupdate = datetime.now()
                
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        await self._force_update()

    async def update(self):        
        state_warning_sensor = self._hass.states.get(f"sensor.{DOMAIN}_warning")
        state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
        if state_warning_sensor_attributes["refresh_required"]:
            await self._force_update()
        else:
            await self._update()
    
    def clear_session(self):
        self._session : None


    @property
    def unique_id(self):
        return f"{NAME} {self._username}"
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id

class ComponentUserSensor(Entity):
    def __init__(self, data, hass, userid):
        self._data = data
        self._hass = hass
        self._userid = userid
        self._last_update = None
        self._loandetails = None
        
        # _LOGGER.info(f"init sensor userid {userid} _userdetails {self._data._userdetails}")
        self._num_loans = self._data._userdetails.get(self._userid).get('loans').get('loans')
        self._loans_url = self._data._userdetails.get(self._userid).get('loans').get('url')
        self._loans_history = self._data._userdetails.get(self._userid).get('loans').get('history')
        self._num_reservations = self._data._userdetails.get(self._userid).get('reservations').get('reservations')
        self._reservations_url = self._data._userdetails.get(self._userid).get('reservations').get('url')
        self._open_amounts = self._data._userdetails.get(self._userid).get('open_amounts').get('open_amounts')
        self._barcode = self._data._userdetails.get(self._userid).get('account_details').get('barcode')
        self._barcode_spell = self._data._userdetails.get(self._userid).get('account_details').get('barcode_spell')
        self._username = self._data._userdetails.get(self._userid).get('account_details').get('userName')
        self._libraryName = self._data._userdetails.get(self._userid).get('account_details').get('libraryName')
        self._expirationDate = self._data._userdetails.get(self._userid).get('account_details').get('expirationDate')
        self._hasError = self._data._userdetails.get(self._userid).get('account_details').get('hasError')
        self._isBlocked = self._data._userdetails.get(self._userid).get('account_details').get('isBlocked')
        self._isExpired = self._data._userdetails.get(self._userid).get('account_details').get('isExpired')
        self._name = self._data._userdetails.get(self._userid).get('account_details').get('name')
        self._address = self._data._userdetails.get(self._userid).get('account_details').get('address')
        self._id = self._data._userdetails.get(self._userid).get('account_details').get('id')
        self._libraryUrl = self._data._userdetails.get(self._userid).get('account_details').get('library')
        self._mail = self._data._userdetails.get(self._userid).get('account_details').get('mail')
        self._userMail = self._data._userdetails.get(self._userid).get('account_details').get('userMail')
        self._mailNotInSync = self._data._userdetails.get(self._userid).get('account_details').get('mailNotInSync')
        self._pendingValidationDate = self._data._userdetails.get(self._userid).get('account_details').get('pendingValidationDate')
        self._supportsOnlineRenewal = self._data._userdetails.get(self._userid).get('account_details').get('supportsOnlineRenewal')
        self._wasRecentlyAdded = self._data._userdetails.get(self._userid).get('account_details').get('wasRecentlyAdded')
        self._loandetails = self._data._loandetails.get(self._userid)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._num_loans

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        self._loandetails = None
        
        self._num_loans = self._data._userdetails.get(self._userid).get('loans').get('loans')
        self._loans_url = self._data._userdetails.get(self._userid).get('loans').get('url')
        self._loans_history = self._data._userdetails.get(self._userid).get('loans').get('history')
        self._num_reservations = self._data._userdetails.get(self._userid).get('reservations').get('reservations')
        self._reservations_url = self._data._userdetails.get(self._userid).get('reservations').get('url')
        self._open_amounts = self._data._userdetails.get(self._userid).get('open_amounts').get('open_amounts')
        self._barcode = self._data._userdetails.get(self._userid).get('account_details').get('barcode')
        self._barcode_spell = self._data._userdetails.get(self._userid).get('account_details').get('barcode_spell')
        self._username = self._data._userdetails.get(self._userid).get('account_details').get('userName')
        self._libraryName = self._data._userdetails.get(self._userid).get('account_details').get('libraryName')
        self._expirationDate = self._data._userdetails.get(self._userid).get('account_details').get('expirationDate')
        self._hasError = self._data._userdetails.get(self._userid).get('account_details').get('hasError')
        self._isBlocked = self._data._userdetails.get(self._userid).get('account_details').get('isBlocked')
        self._isExpired = self._data._userdetails.get(self._userid).get('account_details').get('isExpired')
        self._name = self._data._userdetails.get(self._userid).get('account_details').get('name')
        self._address = self._data._userdetails.get(self._userid).get('account_details').get('address')
        self._id = self._data._userdetails.get(self._userid).get('account_details').get('id')
        self._libraryUrl = self._data._userdetails.get(self._userid).get('account_details').get('library')
        self._mail = self._data._userdetails.get(self._userid).get('account_details').get('mail')
        self._userMail = self._data._userdetails.get(self._userid).get('account_details').get('userMail')
        self._mailNotInSync = self._data._userdetails.get(self._userid).get('account_details').get('mailNotInSync')
        self._pendingValidationDate = self._data._userdetails.get(self._userid).get('account_details').get('pendingValidationDate')
        self._supportsOnlineRenewal = self._data._userdetails.get(self._userid).get('account_details').get('supportsOnlineRenewal')
        self._wasRecentlyAdded = self._data._userdetails.get(self._userid).get('account_details').get('wasRecentlyAdded')
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
            f"{NAME} {self._username} {self._libraryName}"
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
            "userid": self._userid,
            "barcode": self._barcode,
            "barcode_spell": self._barcode_spell,
            "barcode_url": f"https://barcodeapi.org/api/128/{self._barcode}",
            "num_loans": self._num_loans,
            "loans_url": self._loans_url,
            "loans_history": self._loans_history,
            "num_reservations": self._num_reservations,
            "reservations_url": self._reservations_url,
            "open_amounts": self._open_amounts,
            "username": self._username,
            "libraryName": self._libraryName,
            "isExpired": self._isExpired,
            "expirationDate": self._expirationDate,
            "isBlocked": self._isBlocked,
            "hasError": self._hasError,
            "entity_picture": "https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/icon.png",
            "name": self._name,
            "address": self._address,
            "id": self._id, 
            "libaryUrl": self._libraryUrl, 
            "mail":self._mail, 
            "userMail": self._userMail,
            "mailNotInSync": self._mailNotInSync,
            "pendingValidationDate": self._pendingValidationDate,
            "supportsOnlineRenewal": self._supportsOnlineRenewal,
            "wasRecentlyAdded": self._wasRecentlyAdded,
            "loandetails": self._loandetails
        }
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )
    

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
        

class ComponentLibrarySensor(Entity):
    def __init__(self, data, hass, libraryName, loanTypes):
        self._data = data
        self._hass = hass
        self._libraryName = libraryName
        self._last_update = None
        self._lowest_till_date = None
        self._days_left = None
        self._some_not_extendable = False
        self._loandetails = []
        self._num_loans = 0
        self._num_total_loans = 0
        self._loantypes = loanTypes
        self._current_librarydetails = self._data._librarydetails.get(libraryName)
            

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._days_left

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        self._loandetails = []
        self._loantypes= {key: 0 for key in self._loantypes}
        self._num_loans = 0
        self._num_total_loans = 0
        self._some_not_extendable = False
        self._days_left = None
        
        for user_id, loan_data in self._data._loandetails.items():
            _LOGGER.debug(f"library loop {user_id} {self._libraryName}") 
            for loan_id, loan_item in loan_data.items():
                library_name_loop = loan_item.get('library')
                if library_name_loop == self._libraryName:
                    _LOGGER.debug(f"library_name_loop {library_name_loop} {self._libraryName}") 
                    self._num_total_loans += 1
                    curr_loan_type = loan_item.get('loan_type')
                    self._loantypes.setdefault(curr_loan_type, 0)
                    self._loantypes[curr_loan_type] += 1
                    self._loandetails.append(loan_item)
                    if (self._days_left is None) or (self._days_left > loan_item.get('days_remaining')):
                        _LOGGER.debug(f"library_name_loop less days {library_name_loop} {loan_item}")
                        self._days_left = loan_item.get('days_remaining')
                        self._lowest_till_date = loan_item.get('loan_till')
                        self._num_loans = 1
                        if loan_item.get('extend_loan_id') is None or loan_item.get('extend_loan_id','').strip() == '':
                            self._some_not_extendable = True
                    elif self._days_left == loan_item.get('days_remaining'):
                        _LOGGER.debug(f"library_name_loop same days {library_name_loop} {loan_item}")
                        self._num_loans += 1
                        if loan_item.get('extend_loan_id') is None or loan_item.get('extend_loan_id','').strip() == '':
                            self._some_not_extendable = True
        
        
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
            f"{NAME} Bib {self._libraryName}"
        )

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        attributes = {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "libraryName": self._libraryName,
            "days_left": self._days_left,
            "some_not_extendable": self._some_not_extendable,
            "lowest_till_date": self._lowest_till_date,
            "num_loans": self._num_loans,
            "num_total_loans": self._num_total_loans,
            "loandetails": self._loandetails,
            "url": self._current_librarydetails.get('url'),
            "address": self._current_librarydetails.get('address'),
            "latitude": self._current_librarydetails.get('lat'),
            "longitude": self._current_librarydetails.get('lon'),
            "entity_picture": "https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/icon.png",
            "phone": self._current_librarydetails.get('phone'),
            "email": self._current_librarydetails.get('email'),
            "opening_hours": self._current_librarydetails.get('hours'),
            "closed_dates": self._current_librarydetails.get('closed_dates')            
        }
        attributes.update(self._loantypes)
        return attributes


    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )
    
    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def device_class(self):
        return SensorDeviceClass.DURATION
        
    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "days"

    @property
    def friendly_name(self) -> str:
        return self.name
        
        
class ComponentLibrariesWarningSensor(Entity):
    def __init__(self, data, hass):
        self._data = data
        self._hass = hass
        self._last_update = None
        self._lowest_till_date = None
        self._days_left = None
        self._some_not_extendable = False
        self._num_loans = 0  
        self._num_total_loans = 0
        self._library_name = ""

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._days_left

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        self._num_loans = 0
        self._num_total_loans = 0
        self._some_not_extendable = False
        self._library_name = ""
        self._days_left = None
        
        for user_id, loan_data in self._data._loandetails.items():
            _LOGGER.debug(f"library warning loop {user_id}") 
            if loan_data != None:
                for loan_id, loan_item in loan_data.items():
                    library_name_loop = loan_item.get('library')
                    _LOGGER.debug(f"library_name_loop {library_name_loop}") 
                    self._num_total_loans += 1
                    if loan_item.get('days_remaining') and ((self._days_left is None) or (self._days_left > loan_item.get('days_remaining'))):
                        _LOGGER.debug(f"library_name_loop less days {library_name_loop} {loan_item}")
                        self._days_left = loan_item.get('days_remaining')
                        self._lowest_till_date = loan_item.get('loan_till')
                        self._num_loans = 1
                        if loan_item.get('library') and loan_item.get('library') not in self._library_name:
                            self._some_not_extendable = False
                            self._library_name += f"{loan_item.get('library')} "
                        if loan_item.get('extend_loan_id') is None or loan_item.get('extend_loan_id','').strip() == '':
                            self._some_not_extendable = True
                    elif self._days_left == loan_item.get('days_remaining'):
                        _LOGGER.debug(f"library_name_loop same days {library_name_loop} {loan_item}")
                        self._num_loans += 1
                        if loan_item.get('library') and loan_item.get('library') not in self._library_name:
                            self._library_name += f"{loan_item.get('library')} "
                        if loan_item.get('extend_loan_id') is None or loan_item.get('extend_loan_id','').strip() == '':
                            self._some_not_extendable = True
        
        
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
            f"{NAME} warning"
        )

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        attributes = {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "days_left": self._days_left,
            "some_not_extendable": self._some_not_extendable,
            "lowest_till_date": self._lowest_till_date,
            "num_loans": self._num_loans,
            "num_total_loans": self._num_total_loans,
            "library_name":  self._library_name,
            "entity_picture": "https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/icon.png",
            "refresh_required": False
        }
        return attributes


    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def device_class(self):
        return SensorDeviceClass.DURATION
        
    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "days"

    @property
    def friendly_name(self) -> str:
        return self.name
        