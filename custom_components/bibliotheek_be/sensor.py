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
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME
)

_LOGGER = logging.getLogger(__name__)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=120 + random.uniform(10, 20))
# MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1 + random.uniform(1, 2))


async def dry_setup(hass, config_entry, async_add_devices, coordinator):
    config = config_entry
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    check_settings(config, hass)
    sensors = []
    
    componentData = ComponentData(
        username,
        password,
        async_get_clientsession(hass),
        hass, 
        coordinator
    )

    
    await componentData._force_update()
    _LOGGER.debug(f"userdetails dry_setup {json.dumps(componentData._userdetails,indent=4)}")     
    _LOGGER.debug(f"loandetails dry_setup {json.dumps(componentData._loandetails,indent=4)}") 
    assert componentData._userdetails is not None
    assert componentData._loandetails is not None
    assert componentData._librarydetails is not None
    assert componentData._userLists is not None
    
    
    for userid, userdetail in componentData._userdetails.items():
        sensorUser = ComponentUserSensor(componentData, hass, userid)
        _LOGGER.debug(f"{NAME} Init sensor for user {userid}")
        sensors.append(sensorUser)
        
    library_names = set()
    for loan_item in componentData._loandetails:
        libraryName = loan_item.get('location',{}).get('libraryName')
        library_names.add(libraryName)
        
    for libraryName in library_names:
        sensorDate = ComponentLibrarySensor(componentData, hass, libraryName)
        _LOGGER.debug(f"{NAME} Init sensor for date {libraryName}")
        sensors.append(sensorDate)
        
    sensorLibrariesWarning = ComponentLibrariesWarningSensor(componentData, hass)
    sensors.append(sensorLibrariesWarning)

    for listid, listdetails in componentData._userLists.items():
        listname = listdetails.get('name')
        _LOGGER.debug(f"{NAME} Init sensor for list {listdetails}")
        sensorList = ComponentListSensor(componentData, hass, listname, listid)
        sensors.append(sensorList)
        
    async_add_devices(sensors)

#TODO: sensor per library (total items loand from library), attribute: number of each type lended
#TODO: sensor per type of loan (eg total 5 books lended, 3 DVDs, etc)

async def async_setup_platform(
    hass, config_entry, async_add_devices, discovery_info=None
):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_platform " + NAME)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    await dry_setup(hass, config_entry, async_add_devices, coordinator)
    return True


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_entry " + NAME)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    config = config_entry.data
    await dry_setup(hass, config, async_add_devices, coordinator)
    return True


async def async_remove_entry(hass, config_entry):
    _LOGGER.info("async_remove_entry " + NAME)
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass
        


class ComponentData:
    def __init__(self, username, password, client, hass, coordinator):
        self._username = username
        self._password = password
        self._client = client
        self._userDetailsAndLoansAndReservations = None
        self._userdetails = None
        self._userLists = None
        self._loandetails = dict()
        self._librarydetails = dict()
        self._hass = hass
        self._coordinator = coordinator
        self._lastupdate = None
        self._oauth_token = None

        self._loanDetailsUpdated = True

        
    # same as update, but without throttle to make sure init is always executed
    async def _force_update(self):
        _LOGGER.info("Forcing update stuff for " + NAME)
        await self._coordinator.async_update_data()
        
        _LOGGER.debug(f"get_userDetailsAndLoansAndReservations dry_setup {json.dumps(self._coordinator.get_userDetailsAndLoansAndReservations(),indent=4)}") 
        self._userdetails = self._coordinator.get_userdetails()
        self._userLists = self._coordinator.get_userLists()
        self._loandetails = self._coordinator.get_loandetails()
        self._librarydetails = self._coordinator.get_librarydetails()
                
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        _LOGGER.info("_update called " + NAME)
        self._userdetails = self._coordinator.get_userdetails()
        self._userLists = self._coordinator.get_userLists()
        self._loandetails = self._coordinator.get_loandetails()
        self._librarydetails = self._coordinator.get_librarydetails()
        # await self._force_update()

    async def update(self):        
        # await self._coordinator._async_local_refresh_data()
        self._lastupdate = self._coordinator.get_lastupdate()
        state_warning_sensor = self._hass.states.get(f"sensor.{DOMAIN}_warning")
        state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
        if state_warning_sensor_attributes["refresh_required"]:
            await self._force_update()
        else:
            await self._update()

    @property
    def unique_id(self):
        return f"{NAME} {self._username}"
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id

def shortenLibraryName(libraryName):
    if len(libraryName) > 20 and " - " in libraryName: 
        new_name = libraryName.split(" - ")[1]
        return new_name
    return libraryName

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
        self._libraryName = shortenLibraryName(self._data._userdetails.get(self._userid).get('account_details').get('libraryName'))
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
        self._loandetails = self._data._userdetails.get(self._userid).get('loandetails')

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._num_loans

    async def async_update(self):
        await self._data.update()
        if not self._data._userdetails.get(self._userid).get('updated'):
            _LOGGER.debug(f"ComponentUserSensor {self._userid} not updated")
            return
        
        self._data._userdetails.get(self._userid)['updated'] = False
        self._last_update =  self._data._lastupdate
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
        self._libraryName = shortenLibraryName(self._data._userdetails.get(self._userid).get('account_details').get('libraryName'))
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
        self._loandetails = self._data._userdetails.get(self._userid).get('loandetails')
        
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)


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
        return f"{self._username} {self._libraryName}"
        

class ComponentLibrarySensor(Entity):
    def __init__(self, data, hass, libraryName):
        self._data = data
        self._hass = hass
        self._libraryName = libraryName
        self._last_update = None
        self._lowest_till_date = None
        self._library_days_left = None
        self._some_not_extendable = False
        self._some_late = False
        self._loandetails = []
        self._num_loans = 0
        self._num_total_loans = 0
        self._current_librarydetails = self._data._librarydetails.get(self._libraryName)
            

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._library_days_left

    async def async_update(self):
        await self._data.update()
        self._current_librarydetails = self._data._librarydetails.get(self._libraryName)
        if not self._current_librarydetails.get('updated'):
            _LOGGER.debug(f"ComponentLibrarySensor {self._libraryName} not updated")
            return
        self._current_librarydetails['updated'] = False
        self._last_update =  self._data._lastupdate
        self._loandetails = []
        self._num_loans = 0
        self._num_total_loans = 0
        self._some_not_extendable = False
        self._some_late = False
        self._library_days_left = None
        
        today = datetime.today()
        for loan_item in self._data._loandetails:
            library_name_loop = loan_item.get('location',{}).get('libraryName')
            if library_name_loop == self._libraryName:
                _LOGGER.debug(f"library_name_loop {library_name_loop} {self._libraryName}") 
                self._num_total_loans += 1
                # item_due_date_str = loan_item.get('dueDate')
                # item_due_date = datetime.strptime(item_due_date_str, '%d/%m/%Y')
                # item_days_left = (item_due_date - today).days
                item_days_left = loan_item.get('days_remaining')
                self._loandetails.append(loan_item)
                if (self._library_days_left is None) or (self._library_days_left > item_days_left):
                    _LOGGER.debug(f"library_name_loop less days {library_name_loop} {loan_item}")
                    self._library_days_left = item_days_left
                    self._lowest_till_date = loan_item.get('dueDate')
                    self._num_loans = 1
                elif self._library_days_left == item_days_left:
                    _LOGGER.debug(f"library_name_loop same days {library_name_loop} {loan_item}")
                    self._num_loans += 1
                if loan_item.get('isRenewable') == False:
                    self._some_not_extendable = True
                if loan_item.get('isLate') == True:
                    self._some_late = True
        
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:bookshelf"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} Bib {shortenLibraryName(self._libraryName)}"
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
            "libraryName": shortenLibraryName(self._libraryName),
            "days_left": self._library_days_left,
            "some_not_extendable": self._some_not_extendable,
            "some_late": self._some_late,
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
        return f"Bib {shortenLibraryName(self._libraryName)}"
        
        
class ComponentLibrariesWarningSensor(Entity):
    def __init__(self, data, hass):
        self._data = data
        self._hass = hass
        self._last_update = None
        self._lowest_till_date = None
        self._library_days_left = None
        self._some_not_extendable = False
        self._some_late = False
        self._num_loans = 0  
        self._num_total_loans = 0
        self._library_name = ""

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._library_days_left

    async def async_update(self):
        await self._data.update()
        if not self._data._loanDetailsUpdated:
            _LOGGER.debug(f"ComponentLibrariesWarningSensor not updated")
            return
        self._data._loanDetailsUpdated = False
        self._last_update =  self._data._lastupdate
        self._num_loans = 0
        self._num_total_loans = 0
        self._some_not_extendable = False
        self._some_late = False
        self._library_name = ""
        self._library_days_left = None
        
        today = datetime.today()
        for loan_item in self._data._loandetails:
            _LOGGER.debug(f"library warning loop")
            library_name_loop = loan_item.get('location',{}).get('libraryName')
            _LOGGER.debug(f"library_name_loop {library_name_loop}") 
            self._num_total_loans += 1
            # item_due_date_str = loan_item.get('dueDate')
            # item_due_date = datetime.strptime(item_due_date_str, '%d/%m/%Y')
            # item_days_left = (item_due_date - today).days
            item_days_left = loan_item.get('days_remaining')

            if (self._library_days_left is None) or (self._library_days_left > item_days_left):
                _LOGGER.debug(f"library_name_loop less days {library_name_loop} {loan_item}")
                self._library_days_left = item_days_left
                self._lowest_till_date = loan_item.get('dueDate')
                self._num_loans = 1
                if library_name_loop not in self._library_name:
                    self._library_name += f"{shortenLibraryName(library_name_loop)} "
            elif self._library_days_left == item_days_left:
                _LOGGER.debug(f"library_name_loop same days {library_name_loop} {loan_item}")
                self._num_loans += 1
                if library_name_loop not in self._library_name:
                    self._library_name += f"{shortenLibraryName(library_name_loop)} "
            if loan_item.get('isRenewable') == False:
                self._some_not_extendable = True
            if loan_item.get('isLate') == True:
                self._some_late = True
        
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)


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
            "days_left": self._library_days_left,
            "some_not_extendable": self._some_not_extendable,
            "some_late": self._some_late,
            "lowest_till_date": self._lowest_till_date,
            "num_loans": self._num_loans,
            "num_total_loans": self._num_total_loans,
            "library_name":  shortenLibraryName(self._library_name),
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
        

class ComponentListSensor(Entity):
    def __init__(self, data, hass, listname, listid):
        self._data = data
        self._hass = hass
        self._listname = listname
        self._listid = listid
        self._last_update = None

        self._userList = self._data._userLists.get(self._listid)
        self._num_items = self._userList.get('num_items')
        self._listurl = self._userList.get('url')
        self._list_last_changed = self._userList.get('last_changed')

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._num_items

    async def async_update(self):
        await self._data.update()
        self._userList = self._data._userLists.get(self._listid)
        if not self._userList.get('updated'):
            _LOGGER.debug(f"ComponentListSensor {self._listid} not updated")
            return
        self._userList['updated'] = False
        self._last_update =  self._data._lastupdate
        
        self._userList = self._data._userLists.get(self._listid)
        self._num_items = self._userList.get('num_items')
        self._listurl = self._userList.get('url')
        self._list_last_changed = self._userList.get('last_changed')
        
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:clipboard-list-outline"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return (
            f"{NAME} list {self._listname}"
        )

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last_update": self._last_update,
            "list_name": self._listname,
            "list_id": self._listid,
            "list_url": self._listurl,
            "list_last_changed": self._list_last_changed,
            "list_items": self._userList.get('items')
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
        return "items"

    @property
    def friendly_name(self) -> str:
        return f"List {self._listname}"