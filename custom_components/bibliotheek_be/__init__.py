import logging
import json
from pathlib import Path

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from .utils import *
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    Platform
)
from homeassistant.core import (
    HomeAssistant,
    ServiceResponse,
    SupportsResponse
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import MyDataUpdateCoordinator
from .const import (
    CONF_REFRESH_INTERVAL
)
# manifestfile = Path(__file__).parent / 'manifest.json'
# with open(manifestfile, 'r') as json_file:
#     manifest_data = json.load(json_file)
    
# DOMAIN = manifest_data.get("domain")
# NAME = manifest_data.get("name")
# VERSION = manifest_data.get("version")
# ISSUEURL = manifest_data.get("issue_tracker")
DOMAIN = "bibliotheek_be"
NAME = "Bibliotheek.be"

PLATFORMS = [Platform.SENSOR]

STARTUP = """
-------------------------------------------------------------------
{name}
This is a custom component
-------------------------------------------------------------------
""".format(
    name=NAME
)


_LOGGER = logging.getLogger(__name__)


# async def async_setup(hass: HomeAssistant, config: ConfigType):
#     """Set up this component using YAML."""
#     _LOGGER.info(STARTUP)
#     if config.get(DOMAIN) is None:
#         # We get here if the integration is set up using config flow
#         return True

#     try:
#         await hass.config_entries.async_forward_entry(config, Platform.SENSOR)
#         _LOGGER.info("Successfully added platform from the integration")
#     except ValueError:
#         pass

#     await hass.config_entries.flow.async_init(
#             DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
#         )
#     return True

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload integration when options changed"""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Flag that a reload is in progress
    hass.data[DOMAIN]["reloading"] = True

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    hass.data[DOMAIN].pop("reloading", None)
    return unload_ok


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up component as config entry."""
    refresh_interval = 30
    coordinator = MyDataUpdateCoordinator(hass, config_entry, refresh_interval)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "coordinator": coordinator
    }
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))
    _LOGGER.info(f"{DOMAIN} register_services")
    register_services(hass, config_entry)
    return True


async def async_remove_entry(hass, config_entry):
    try:
        for platform in PLATFORMS:
            await hass.config_entries.async_forward_entry_unload(config_entry, platform)
            _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass


def register_services(hass, config_entry):
        
    async def handle_extend_loan(call):
        """Handle the service call."""
        extend_loan_id = call.data.get('extend_loan_id')
        max_days_remaining = call.data.get('max_days_remaining')
        coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        await coordinator.async_request_refresh()
        _LOGGER.info(f"handle_extend_loan extending loan {extend_loan_id}")
        await coordinator.extend_loan(extend_loan_id, max_days_remaining)
        _LOGGER.info(f"handle_extend_loan extending loan {extend_loan_id} done")
                            

    async def handle_extend_loans_library(call):
        """Handle the service call."""
        library_name = call.data.get('library_name')
        max_days_remaining = call.data.get('max_days_remaining')
        coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        await coordinator.async_request_refresh()
        _LOGGER.info(f"handle_extend_loan extending loans {library_name}")
        await coordinator.extend_loans_library(library_name, max_days_remaining)
        _LOGGER.info(f"handle_extend_loan extending loans {library_name} done")
        

    async def handle_extend_loans_user(call):
        """Handle the service call."""
        barcode = call.data.get('barcode')
        max_days_remaining = call.data.get('max_days_remaining')
        coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        await coordinator.async_request_refresh()
        _LOGGER.info(f"handle_extend_loan extending loans {barcode}")
        await coordinator.extend_loans_user(barcode, max_days_remaining)
        _LOGGER.info(f"handle_extend_loan extending loans {barcode} done")
        

    async def handle_extend_all_loans(call):
        """Handle the service call."""
        max_days_remaining = call.data.get('max_days_remaining')
        coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        await coordinator.async_request_refresh()
        _LOGGER.info(f"handle_extend_loan extending loans all")
        await coordinator.extend_all_loans(max_days_remaining)
        _LOGGER.info(f"handle_extend_loan extending loans all done")
        

    async def handle_update(call):
        """Handle the service call."""
        state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
        _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
        state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
        state_warning_sensor_attributes["refresh_required"] = True
        await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))
        _LOGGER.info(f"handle_update done")


    hass.services.async_register(DOMAIN, 'extend_loan', handle_extend_loan)
    hass.services.async_register(DOMAIN, 'extend_loans_library', handle_extend_loans_library)
    hass.services.async_register(DOMAIN, 'extend_loans_user', handle_extend_loans_user)
    hass.services.async_register(DOMAIN, 'extend_all_loans', handle_extend_all_loans)
    hass.services.async_register(DOMAIN, 'update', handle_update)
    _LOGGER.info(f"async_register done")