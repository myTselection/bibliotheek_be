from datetime import datetime, timedelta
import logging


from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.todo import TodoItem, TodoItemStatus

from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME
)
from .const import (
    DOMAIN,
    NAME,
    CONF_REFRESH_INTERVAL
)

from .utils import *


_LOGGER = logging.getLogger(DOMAIN)

class ComponentUpdateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, config_entry, refresh_interval):
        self._config = config_entry.data
        self._username = self._config.get(CONF_USERNAME)
        self._password = self._config.get(CONF_PASSWORD)
        self._unique_user_id = f"{self._username}"
        super().__init__(hass, _LOGGER, config_entry = config_entry, name = f"{DOMAIN} Coordinator {self._unique_user_id}", update_method=self.async_update_data, update_interval = timedelta(minutes = refresh_interval))
        
        self._last_updated = None
        self._hass = hass
        self._session = ComponentSession(self._hass)
        self._userDetailsAndLoansAndReservations = None
        self._userdetails = None
        self._userLists = None
        self._loandetails = None
        self._librarydetails = dict()

        

    async def async_initialize(self):
        await self.async_config_entry_first_refresh()
        
        # await self._status_store.async_load()
        # await self.async_refresh()

    async def async_update_data(self):
        try:
            _LOGGER.debug(f"{DOMAIN} ComponentUpdateCoordinator update started, username: {self._username}")
            if not(self._session):
                self._session = ComponentSession(self._hass)
                
            today = datetime.today()
            if self._session:
                # self._userDetailsAndLoansAndReservations = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
                self._userDetailsAndLoansAndReservations = await self._session.login(self._username, self._password)
                self._userdetails = self._userDetailsAndLoansAndReservations.get('userdetails', None)
                self._loandetails = self._userDetailsAndLoansAndReservations.get('loandetails', None)
                self._reservationdetails = self._userDetailsAndLoansAndReservations.get('reservationdetails', None)
                assert self._userdetails is not None
                _LOGGER.debug(f"{DOMAIN} update login completed")
                
                for user_id, userdetail in self._userdetails.items():
                    libraryurl = f"{userdetail.get('account_details').get('library')}/adres-en-openingsuren"
                    libraryName = userdetail.get('account_details').get('libraryName')
                    if not self._librarydetails.get(libraryName):
                        # librarydetails = await self._hass.async_add_executor_job(lambda: self._session.library_details(libraryurl))
                        librarydetails = await self._session.library_details(libraryurl)
                        # assert librarydetails is not None
                        self._librarydetails[libraryName] = librarydetails

                    if userdetail.get('loans'):
                        url = userdetail.get('loans').get('url')
                        if url:
                            # loandetails_url = await self._hass.async_add_executor_job(lambda: self._session.loan_details(url))
                            loandetails_url = await self._session.loan_details(url)
                            # assert loandetails is not None
                            userdetail.get('loans')['loandetails_url'] = loandetails_url

                for loanitem in self._loandetails:
                    userLibMatchFound = False
                    
                    item_due_date_str = loanitem.get('dueDate')
                    item_due_date = datetime.strptime(item_due_date_str, '%d/%m/%Y')
                    item_days_left = (item_due_date - today).days
                    loanitem["loan_till"] = loanitem.get('dueDate')
                    loanitem["days_remaining"] = item_days_left
                    loanitem["url"] = loanitem.get("renewUrl")


                    for account in self._userdetails.values():
                        if account.get('account_details').get('name') == loanitem.get('accountName') and account.get('account_details').get('libraryName') == loanitem.get('location',{}).get('libraryName'):
                            userLibMatchFound = True
                            self.enrichLoanItem(loanitem, account, account.get('loandetails',[]))
                            break
                    
                    if not userLibMatchFound:
                        accountId = loanitem.get('accountId')
                        account = self._userdetails.get(accountId)
                        oldLoans = self._userdetails.get(accountId).get('loandetails',[])
                        self.enrichLoanItem(loanitem, account, oldLoans)

                    self._loanDetailsUpdated = True


                # self._userLists = await self._hass.async_add_executor_job(lambda: self._session.user_lists())
                self._userLists = await self._session.user_lists()
                assert self._userLists is not None
                self._lastupdate = datetime.now()
        except Exception as err:
            _LOGGER.error(f"{DOMAIN} ComponentUpdateCoordinator update failed, username: {self._username}", exc_info=err)
            raise UpdateFailed(f"Error fetching data: {err}")
    
    def enrichLoanItem(self, loanitem, account, oldLoans):
        loanitem["renewUrl"] = account.get('loans',{}).get('url',loanitem.get("renewUrl",""))
        loanitem["accountUrl"] = f"{account.get('account_details',{}).get('library',{})}{loanitem.get("accountUrl","")}"
        loanitem["user"] = account.get('account_details').get('userName',"Unknown")
        loanitem["userid"] = account.get('account_details').get('id',"Unknown")
        loanitem["barcode"] = account.get('account_details').get('barcode',"Unknown")
        loanitem["barcode_spell"] = account.get('account_details').get('barcode_spell',[])
        # combine loandetail info 
        loandetails_url = account.get('loans',{}).get('loandetails_url',{}).get(loanitem.get('title',''),{})
        if loandetails_url and loandetails_url !=  {}:
            loanitem["loan_type"] = loandetails_url.get("loan_type","Unknown")
            loanitem["author"] = loandetails_url.get("author","Unknown")
            loanitem["image_src"] = loandetails_url.get("image_src", None)
            loanitem["days_remaining"] = loandetails_url.get("days_remaining",None)
            loanitem["loan_from"] = loandetails_url.get("loan_from", None)
            loanitem["library"] = loandetails_url.get("library",loanitem.get('location',{}).get('libraryName') )
            loanitem["extend_loan_id"] = loandetails_url.get("extend_loan_id", None)
            loanitem["url"] = loandetails_url.get("url", account.get('account_details',{}).get('library',{}))
        else:
            loanitem["loan_type"] = "Unknown"
            loanitem["author"] = "Unknown"
            loanitem["image_src"] = None
            loanitem["days_remaining"] = None
            loanitem["loan_from"] = None
            loanitem["library"] = loanitem.get('location',{}).get('libraryName') 
            loanitem["extend_loan_id"] = None
            loanitem["url"] = account.get('account_details',{}).get('library',{})
        account['loandetails'] = oldLoans + [loanitem]
        account.get('loans')['loans'] = len(oldLoans) + 1


    def get_userDetailsAndLoansAndReservations(self):
        return self._userDetailsAndLoansAndReservations
        
    def get_userdetails(self):
        return self._userdetails

    def get_userLists(self):
        return self._userLists

    def get_loandetails(self):
        return self._loandetails
        
    def get_librarydetails(self):
        return self._librarydetails
        
    def get_lastupdate(self):
        return self._lastupdate
    

    async def extend_loan(self, extend_loan_id, max_days_remaining):
        
        today = datetime.today()
        
        assert self._loandetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        extend_load_ids = []
        for loanitem in self._loandetails:
            curr_extend_loan_id = loanitem.get("itemId")
            # item_due_date_str = loanitem.get('dueDate')
            # item_due_date = datetime.strptime(item_due_date_str, '%d/%m/%Y')
            # curr_days_remaining = (item_due_date - today).days
            curr_days_remaining = loanitem.get('days_remaining')
            library_name_loop = loanitem.get('location',{}).get('libraryName')
            if str(curr_extend_loan_id) == str(extend_loan_id):
                _LOGGER.debug(f"handle_extend_loan curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop}")
                if int(curr_days_remaining) <= int(max_days_remaining):
                    # extension_confirmation = await self._hass.async_add_executor_job(lambda: self._session.extend_single_item(url, extend_loan_id, True))
                    url = loanitem.get('renewUrl')
                    extend_load_ids.append(curr_extend_loan_id)
                    _LOGGER.debug(f"handle_extend_loan curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop} renewUrl {url}")
                    extension_confirmation = await self._session.extend_multiple_ids(url, extend_load_ids, True)
                    if extension_confirmation > 0:
                        state_warning_sensor = self._hass.states.get(f"sensor.{DOMAIN}_warning")
                        _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
                        state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
                        state_warning_sensor_attributes["refresh_required"] = state_warning_sensor_attributes.get("refresh_required", False) or (extension_confirmation > 0)
                        _LOGGER.debug(f"state_warning_sensor attributes sensor.{DOMAIN}_warning: {state_warning_sensor_attributes}")
                        # await self._hass.async_add_executor_job(lambda: self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))
                        await self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes)
                    return
                else:
                    _LOGGER.debug(f"skipped extension since {curr_days_remaining} below max {max_days_remaining}")
                    return
        _LOGGER.debug(f"extend_loan_id {extend_loan_id} not found in loandetails")



    async def handle_extend_loans_library(self, library_name, max_days_remaining):
        assert self._userdetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        _LOGGER.debug(f"handle_extend_loan loandetails {json.dumps(self._loandetails,indent=4)}") 
        extend_load_ids = []
        url = ""
        extension_confirmation = 0
        for loanitem in self._loandetails:
            library_name_loop = loanitem.get('library')
            curr_extend_loan_id = loanitem.get('extend_loan_id')
            curr_days_remaining = loanitem.get('days_remaining')
            _LOGGER.debug(f"handle_extend_loans_library curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop} curr_days_remaining {curr_days_remaining}")
            curr_url = loanitem.get('renewUrl')
            if curr_url and not curr_url != url and len(extend_load_ids) > 0 :
                # processing new account, first extend previous account
                _LOGGER.debug(f"handle_extend_loans_library curr_extend_loan_id {curr_extend_loan_id}, extend_load_ids {extend_load_ids}, library_name_loop {library_name_loop} curr_days_remaining {curr_days_remaining} processsing previous account url {url}")
                curr_extension_confirmation = await self._session.extend_multiple_ids(url, extend_load_ids, True)
                extension_confirmation = max(extension_confirmation, curr_extension_confirmation)
                extend_load_ids = []
            url = curr_url
            if curr_extend_loan_id and library_name_loop.lower() == library_name.lower():
                _LOGGER.info(f"handle_extend_loan curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop}")
                if int(curr_days_remaining) <= int(max_days_remaining):
                    extend_load_ids.append(curr_extend_loan_id)
                else:
                    _LOGGER.debug(f"skipped extension since {curr_days_remaining} below max {max_days_remaining}")

        if len(extend_load_ids) > 0:
            # processing last account
            _LOGGER.debug(f"handle_extend_loans_library curr_extend_loan_id {curr_extend_loan_id}, extend_load_ids {extend_load_ids}, library_name_loop {library_name_loop} curr_days_remaining {curr_days_remaining} processsing last account url {url}")
            curr_extension_confirmation = await self._session.extend_multiple_ids(url, extend_load_ids, True)
            extension_confirmation = max(extension_confirmation, curr_extension_confirmation)
        
        if extension_confirmation > 0:
            state_warning_sensor = self._hass.states.get(f"sensor.{DOMAIN}_warning")
            state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
            state_warning_sensor_attributes["refresh_required"] = state_warning_sensor_attributes.get("refresh_required", False) or (extension_confirmation > 0)
            # await self._hass.async_add_executor_job(lambda: self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))
            await self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes)

    async def handle_extend_loans_user(self, barcode, max_days_remaining):
        assert self._userdetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        for user_id, userdetail in self._userdetails.items():
            curr_barcode = userdetail.get('account_details').get('barcode')
            if curr_barcode == barcode:
                url = userdetail.get('loans').get('url')
                if url:
                    extend_load_ids = []
                    for loanitem in userdetail.get('loans').get('loandetails_url').values():
                        curr_extend_loan_id = loanitem.get('extend_loan_id')
                        curr_days_remaining = loanitem.get('days_remaining')
                        _LOGGER.info(f"handle_extend_loan extend user calling loan details {userdetail.get('account_details').get('userName')} extend_load_ids {extend_load_ids} curr_extend_loan_id {curr_extend_loan_id}")
                        if curr_extend_loan_id and int(curr_days_remaining) <= int(max_days_remaining):
                            extend_load_ids.append(curr_extend_loan_id)
                        _LOGGER.info(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')} extend_load_ids {extend_load_ids}")
                        if len(extend_load_ids) > 0:
                            extension_confirmation = await self._session.extend_multiple_ids(url, extend_load_ids, True)
                        if extension_confirmation > 0:
                            state_warning_sensor = self._hass.states.get(f"sensor.{DOMAIN}_warning")
                            state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
                            state_warning_sensor_attributes["refresh_required"] = True
                            # await self._hass.async_add_executor_job(lambda: self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))
                            await self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes)
                return

    async def handle_extend_all(self, max_days_remaining):
        assert self._userdetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        extension_confirmation = 0
        for user_id, userdetail in self._userdetails.items():
            url = userdetail.get('loans').get('url')
            if url:
                extend_load_ids = []
                for loanitem in userdetail.get('loans').get('loandetails_url').values():
                    curr_extend_loan_id = loanitem.get('extend_loan_id')
                    curr_days_remaining = loanitem.get('days_remaining')
                    _LOGGER.info(f"handle_extend_loan extend all calling loan details {userdetail.get('account_details').get('userName')} extend_load_ids {extend_load_ids} curr_extend_loan_id {curr_extend_loan_id}")
                    if curr_extend_loan_id and int(curr_days_remaining) <= int(max_days_remaining):
                        extend_load_ids.append(curr_extend_loan_id)
                _LOGGER.info(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')} extend_load_ids {extend_load_ids}")
                if len(extend_load_ids) > 0:
                    # extension_confirmation = await self._hass.async_add_executor_job(lambda: self._session.extend_all(url, int(max_days_remaining), True))
                    curr_extension_confirmation = await self._session.extend_multiple_ids(url, extend_load_ids, True)
                    extension_confirmation = max(extension_confirmation, curr_extension_confirmation)
        if extension_confirmation > 0:
            state_warning_sensor = self._hass.states.get(f"sensor.{DOMAIN}_warning")
            _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
            state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
            state_warning_sensor_attributes["refresh_required"] = True
            # await self._hass.async_add_executor_job(lambda: self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))
            await self._hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes)