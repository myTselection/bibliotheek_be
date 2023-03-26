import logging
import json
from pathlib import Path

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.const import Platform
from .utils import *
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME
)

manifestfile = Path(__file__).parent / 'manifest.json'
with open(manifestfile, 'r') as json_file:
    manifest_data = json.load(json_file)
    
DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
PLATFORMS = [Platform.SENSOR]

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


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this component using YAML."""
    _LOGGER.info(STARTUP)
    if config.get(DOMAIN) is None:
        # We get her if the integration is set up using config flow
        return True

    try:
        await hass.config_entries.async_forward_entry(config, Platform.SENSOR)
        _LOGGER.info("Successfully added sensor from the integration")
    except ValueError:
        pass

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    return True

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload integration when options changed"""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    # if unload_ok:
        # hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up component as config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.SENSOR)
    )
    _LOGGER.info(f"{DOMAIN} register_services")
    register_services(hass, config_entry)
    return True


async def async_remove_entry(hass, config_entry):
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, PLATFORMS)
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass
        

def register_services(hass, config_entry):
        
    async def handle_extend_loan(call):
        """Handle the service call."""
        extend_loan_id = call.data.get('extend_loan_id')
        max_days_remaining = call.data.get('max_days_remaining')
        
        config = config_entry.data
        username = config.get("username")
        password = config.get("password")
        session = ComponentSession()
        userdetails = await hass.async_add_executor_job(lambda: session.login(username, password))
        assert userdetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        extend_loan_id_found = False
        for user_id, userdetail in userdetails.items():
            url = userdetail.get('loans').get('url')
            _LOGGER.debug(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')}, url {url}")
            if url: 
                loandetails = await hass.async_add_executor_job(lambda: session.loan_details(url))
                assert loandetails is not None
                for loan_id, loan_item in loandetails.items():
                    library_name_loop = loan_item.get('library')
                    curr_extend_loan_id = loan_item.get('extend_loan_id')
                    curr_days_remaining = loan_item.get('days_remaining')
                    _LOGGER.debug(f"handle_extend_loan loan details {library_name_loop} - {curr_extend_loan_id}, extend_loan_id {extend_loan_id}")
                    if str(curr_extend_loan_id) == str(extend_loan_id):
                        extend_loan_id_found = True
                        _LOGGER.debug(f"handle_extend_loan curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop}")
                        _LOGGER.info(f"handle_extend_loan calling extend_single_item {userdetail.get('account_details').get('userName')} , extend id: {extend_loan_id}")
                        if int(curr_days_remaining) <= int(max_days_remaining):
                            extension_confirmation = await hass.async_add_executor_job(lambda: session.extend_single_item(url, extend_loan_id, True))
                            state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
                            _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
                            state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
                            state_warning_sensor_attributes["refresh_required"] = (extension_confirmation > 0)
                            _LOGGER.debug(f"state_warning_sensor attributes sensor.{DOMAIN}_warning: {state_warning_sensor_attributes}")
                            await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))
                        else:
                            _LOGGER.debug(f"skipped extension since {curr_days_remaining} below max {max_days_remaining}")
                        break
                if extend_loan_id_found:
                    break
                            

    async def handle_extend_loans_library(call):
        """Handle the service call."""
        library_name = call.data.get('library_name')
        max_days_remaining = call.data.get('max_days_remaining')
        
        config = config_entry.data
        username = config.get("username")
        password = config.get("password")
        session = ComponentSession()
        userdetails = await hass.async_add_executor_job(lambda: session.login(username, password))
        assert userdetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        for user_id, userdetail in userdetails.items():
            url = userdetail.get('loans').get('url')
            if url:
                _LOGGER.debug(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')}")
                loandetails = await hass.async_add_executor_job(lambda: session.loan_details(url))
                assert loandetails is not None
                _LOGGER.debug(f"handle_extend_loan loandetails {json.dumps(loandetails,indent=4)}") 
                extend_load_ids = []
                for loan_id, loan_item in loandetails.items():
                    library_name_loop = loan_item.get('library')
                    curr_extend_loan_id = loan_item.get('extend_loan_id')
                    curr_days_remaining = loan_item.get('days_remaining')
                    _LOGGER.debug(f"handle_extend_loans_library curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop} curr_days_remaining {curr_days_remaining}")
                    if curr_extend_loan_id and library_name_loop.lower() == library_name.lower():
                        _LOGGER.info(f"handle_extend_loan curr_extend_loan_id {curr_extend_loan_id} library_name_loop {library_name_loop}")
                        if int(curr_days_remaining) <= int(max_days_remaining):
                            extend_load_ids.append(curr_extend_loan_id)
                        else:
                            _LOGGER.debug(f"skipped extension since {curr_days_remaining} below max {max_days_remaining}")
                extension_confirmation = await hass.async_add_executor_job(lambda: session.extend_multiple_ids(url, extend_load_ids, True))
                state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
                state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
                state_warning_sensor_attributes["refresh_required"] = (extension_confirmation > 0)
                await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))

    async def handle_extend_loans_user(call):
        """Handle the service call."""
        barcode = call.data.get('barcode')
        max_days_remaining = call.data.get('max_days_remaining')
        
        config = config_entry.data
        username = config.get("username")
        password = config.get("password")
        """Handle the service call."""
        session = ComponentSession()
        userdetails = await hass.async_add_executor_job(lambda: session.login(username, password))
        assert userdetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        for user_id, userdetail in userdetails.items():
            curr_barcode = userdetail.get('account_details').get('barcode')
            if curr_barcode == barcode:
                url = userdetail.get('loans').get('url')
                if url:
                    _LOGGER.info(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')}")
                    extension_confirmation = await hass.async_add_executor_job(lambda: session.extend_all(url, int(max_days_remaining), True))
                    state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
                    state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
                    state_warning_sensor_attributes["refresh_required"] = (extension_confirmation > 0)
                    await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))
                break

    async def handle_extend_all_loans(call):
        """Handle the service call."""
        max_days_remaining = call.data.get('max_days_remaining')
        
        config = config_entry.data
        username = config.get("username")
        password = config.get("password")
        """Handle the service call."""
        session = ComponentSession()
        userdetails = await hass.async_add_executor_job(lambda: session.login(username, password))
        assert userdetails is not None
        _LOGGER.debug(f"{NAME} handle_extend_loan login completed")
        for user_id, userdetail in userdetails.items():
            url = userdetail.get('loans').get('url')
            if url:
                _LOGGER.info(f"handle_extend_loan calling loan details {userdetail.get('account_details').get('userName')}")
                extension_confirmation = await hass.async_add_executor_job(lambda: session.extend_all(url, int(max_days_remaining), True))
                state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
                _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
                state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
                state_warning_sensor_attributes["refresh_required"] = (extension_confirmation > 0)
                await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))

    async def handle_update(call):
        """Handle the service call."""
        state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
        _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
        state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
        state_warning_sensor_attributes["refresh_required"] = True
        await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))


    hass.services.async_register(DOMAIN, 'extend_loan', handle_extend_loan)
    hass.services.async_register(DOMAIN, 'extend_loans_library', handle_extend_loans_library)
    hass.services.async_register(DOMAIN, 'extend_loans_user', handle_extend_loans_user)
    hass.services.async_register(DOMAIN, 'extend_all_loans', handle_extend_all_loans)
    hass.services.async_register(DOMAIN, 'update', handle_update)
    _LOGGER.info(f"async_register done")