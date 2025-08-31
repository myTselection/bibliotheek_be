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
        self._session = ComponentSession()
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
                self._session = ComponentSession()
                
            today = datetime.today()
            if self._session:
                self._userDetailsAndLoansAndReservations = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
                self._userdetails = self._userDetailsAndLoansAndReservations.get('userdetails', None)
                self._loandetails = self._userDetailsAndLoansAndReservations.get('loandetails', None)
                self._reservationdetails = self._userDetailsAndLoansAndReservations.get('reservationdetails', None)
                assert self._userdetails is not None
                _LOGGER.debug(f"{DOMAIN} update login completed")
                
                for user_id, userdetail in self._userdetails.items():
                    libraryurl = f"{userdetail.get('account_details').get('library')}/adres-en-openingsuren"
                    libraryName = userdetail.get('account_details').get('libraryName')
                    if not self._librarydetails.get(libraryName):
                        librarydetails = await self._hass.async_add_executor_job(lambda: self._session.library_details(libraryurl))
                        # assert librarydetails is not None
                        self._librarydetails[libraryName] = librarydetails

                    if userdetail.get('loans'):
                        url = userdetail.get('loans').get('url')
                        if url:
                            loandetails_url = await self._hass.async_add_executor_job(lambda: self._session.loan_details(url))
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
                            
                            loanitem["renewUrl"] = f"{account.get('account_details',{}).get('library',{})}{loanitem.get("renewUrl","")}"
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
                                loanitem["library"] = loandetails_url.get("library","Unknown")
                                loanitem["extend_loan_id"] = loandetails_url.get("extend_loan_id", None)
                            else:
                                loanitem["loan_type"] = "Unknown"
                                loanitem["author"] = "Unknown"
                                loanitem["image_src"] = None
                                loanitem["days_remaining"] = None
                                loanitem["loan_from"] = None
                                loanitem["library"] = loanitem.get('location',{}).get('libraryName') 
                                loanitem["extend_loan_id"] = None
                            oldLoans = account.get('loandetails',[])
                            account['loandetails'] = oldLoans + [loanitem]
                            account.get('loans')['loans'] = len(oldLoans) + 1
                            break
                    
                    if not userLibMatchFound:
                        accountId = loanitem.get('accountId')
                        account = self._userdetails.get(accountId)
                        loanitem["renewUrl"] = f"{account.get('account_details',{}).get('library',{})}{loanitem.get("renewUrl","")}"
                        loanitem["user"] = account.get('account_details').get('userName',"Unknown")
                        loanitem["userid"] = account.get('account_details').get('id',"Unknown")
                        loanitem["barcode"] = account.get('account_details').get('barcode',"Unknown")
                        loanitem["barcode_spell"] = account.get('account_details').get('barcode_spell',[])
                        oldLoans = self._userdetails.get(accountId).get('loandetails',[])
                        self._userdetails.get(accountId)['loandetails'] = oldLoans + [loanitem]
                        self._userdetails.get(accountId).get('loans')['loans'] = len(oldLoans) + 1

                    self._loanDetailsUpdated = True


                self._userLists = await self._hass.async_add_executor_job(lambda: self._session.user_lists())
                assert self._userLists is not None
                self._lastupdate = datetime.now()
        except Exception as err:
            _LOGGER.error(f"{DOMAIN} ComponentUpdateCoordinator update failed, username: {self._username}", exc_info=err)
            raise UpdateFailed(f"Error fetching data: {err}")
    

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