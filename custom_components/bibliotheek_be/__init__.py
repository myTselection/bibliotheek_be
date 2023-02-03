import logging
import json
from pathlib import Path

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from .utils import *

manifestfile = Path(__file__).parent / 'manifest.json'
with open(manifestfile, 'r') as json_file:
    manifest_data = json.load(json_file)
    
DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")

STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
""".format(
    name=NAME, version=VERSION, issueurl=ISSUEURL
)


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up this component using YAML."""
    _LOGGER.info(STARTUP)
    if config.get(DOMAIN) is None:
        # We get her if the integration is set up using config flow
        return True

    try:
        await hass.config_entries.async_forward_entry(config, "sensor")
        _LOGGER.info("Successfully added sensor from the integration")
    except ValueError:
        pass

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    register_services(hass)
    return True

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload integration when options changed"""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(config_entry, "sensor")
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up component as config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )
    return True


async def async_remove_entry(hass, config_entry):
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass
        

#based on aria2p
def register_services(hass):
    async def handle_extend_loan(call):
        """Handle the service call."""
        extend_loan_id = call.data.get('extend_loan_id')
        # entry_id = call.data.get('server_entry_id')
        # await hass.data[DOMAIN][entry_id]['ws_client'].call(AddUri([url]))
        self._session = ComponentSession()
            self._userdetails = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            assert self._userdetails is not None
            _LOGGER.info(f"{NAME} handle_extend_loan login completed")
            for user_id, userdetail in self._userdetails.items():
                url = userdetail.get('loans').get('url')
                if url:
                    _LOGGER.info(f"handle_extend_loan calling extend_single_item {userdetail.get('account_details').get('userName')} , extend id: {extend_loan_id}")
                    self._extension_confirmation = await self._hass.async_add_executor_job(lambda: self._session.extend_single_item(url, extend_loan_id, false))
                            

    async def handle_extend_loans_library(call):
        """Handle the service call."""
        library_name = call.data.get('library_name')
        # entry_id = call.data.get('server_entry_id')
        # await hass.data[DOMAIN][entry_id]['ws_client'].call(Remove(gid))
        self._session = ComponentSession()
            self._userdetails = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            assert self._userdetails is not None
            _LOGGER.info(f"{NAME} handle_extend_loan login completed")
            for user_id, userdetail in self._userdetails.items():
                url = userdetail.get('loans').get('url')
                if url:
                    _LOGGER.info(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')}")
                    loandetails = await self._hass.async_add_executor_job(lambda: self._session.loan_details(url))
                    assert loandetails is not None
                    # loandetails["user"] = userdetail.get('account_details').get('userName')
                    _LOGGER.debug(f"handle_extend_loan loandetails {json.dumps(loandetails,indent=4)}") 
                    # _LOGGER.info(f"calling extend_all")
                    # num_extensions = self.session.extend_all(url, False)
                    # _LOGGER.info(f"num of extensions found: {num_extensions}")
                    extend_load_ids = []
                    for loan_id, loan_item in loandetails.items():
                        library_name_loop = loan_item.get('library')
                        curr_extend_loan_id = loan_item.get('extend_loan_id')
                        if library_name_loop == library_name:
                            _LOGGER.info(f"handle_extend_loan curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop}")
                            extend_load_ids.append(curr_extend_loan_id)
                    self._extension_confirmation = await self._hass.async_add_executor_job(lambda: self._session.extend_multiple_ids(url, extend_load_ids, false))

    async def handle_extend_loans_user(call):
        """Handle the service call."""
        barcode = call.data.get('barcode')
        # entry_id = call.data.get('server_entry_id')
        # await hass.data[DOMAIN][entry_id]['ws_client'].call(Pause(gid))
        """Handle the service call."""
        self._session = ComponentSession()
            self._userdetails = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            assert self._userdetails is not None
            _LOGGER.info(f"{NAME} handle_extend_loan login completed")
            for user_id, userdetail in self._userdetails.items():
                curr_barcode = userdetail.get('account_details').get('barcode')
                if curr_barcode == barcode:
                    url = userdetail.get('loans').get('url')
                    if url:
                        _LOGGER.info(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')}")
                        self._extension_confirmation = await self._hass.async_add_executor_job(lambda: self._session.extend_all(url, false))

    async def handle_extend_all_loans(call):
        """Handle the service call."""
        # entry_id = call.data.get('server_entry_id')
        # await hass.data[DOMAIN][entry_id]['ws_client'].call(Unpause(gid))
        """Handle the service call."""
        self._session = ComponentSession()
            self._userdetails = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
            assert self._userdetails is not None
            _LOGGER.info(f"{NAME} handle_extend_loan login completed")
            for user_id, userdetail in self._userdetails.items():
                url = userdetail.get('loans').get('url')
                if url:
                    _LOGGER.info(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')}")
                    self._extension_confirmation = await self._hass.async_add_executor_job(lambda: self._session.extend_all(url, false))


    hass.services.async_register(DOMAIN, 'extend_loan', handle_extend_loan)
    hass.services.async_register(DOMAIN, 'extend_loans_library', handle_extend_loans_library)
    hass.services.async_register(DOMAIN, 'extend_loans_user', handle_extend_loans_user)
    hass.services.async_register(DOMAIN, 'extend_all_loans', handle_extend_all_loans)