"""Adds config flow for component."""
import logging
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries

from . import DOMAIN, NAME
from .const import CONF_OPENING_HOURS_LIBRARIES
from .utils import ComponentSession
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME
)
_LOGGER = logging.getLogger(DOMAIN)


def create_schema(entry, option=False):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """

    if option:
        # We use .get here incase some of the texts gets changed.
        default_username = entry.data.get(CONF_USERNAME, "")
        default_password = entry.data.get(CONF_PASSWORD, "")
    else:
        default_username = ""
        default_password = ""

    data_schema = OrderedDict()
    data_schema[
        vol.Required(CONF_USERNAME, default=default_username, description="username")
    ] = str
    data_schema[
        vol.Required(CONF_PASSWORD, default=default_password, description="password")
    ] = str

    return data_schema

class ComponentFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._user_input = {}
        self._libraries = {}
        self._sub_libraries = {}
        self._library_fields = {}

    async def _async_prepare_sub_libraries(self):
        """Log in and prepare selectable sub-library options for each main library."""
        session = ComponentSession(self.hass)
        user_data = await session.login(
            self._user_input[CONF_USERNAME], self._user_input[CONF_PASSWORD]
        )
        self._libraries = user_data.get("librarydetails", {})
        self._sub_libraries = {}
        self._library_fields = {}

        for library_slug in self._libraries:
            self._sub_libraries[library_slug] = await session.library_autocomplete(
                library_slug
            )
            self._library_fields[library_slug] = library_slug.replace("-", "_")

    def _sub_library_schema(self):
        """Create a selector schema for the sub-libraries."""
        data_schema = OrderedDict()
        for library_slug, sub_libraries in self._sub_libraries.items():
            field = self._library_fields[library_slug]
            options = {
                sub_library["id"]: sub_library["label"]
                for sub_library in sub_libraries
                if sub_library.get("id")
            }

            if not options:
                options = {library_slug: library_slug.replace("-", " ").title()}

            data_schema[
                vol.Required(
                    field,
                    default=next(iter(options)),
                    description={"suggested_value": next(iter(options))},
                )
            ] = vol.In(options)

        return data_schema

    async def async_step_user(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""

        if user_input is not None:
            self._user_input = user_input
            self._errors = {}
            try:
                await self._async_prepare_sub_libraries()
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to prepare Bibliotheek.be sub-library choices")
                self._errors["base"] = "cannot_connect"
                return await self._show_config_form(user_input)

            if self._sub_libraries:
                return await self.async_step_sub_library()

            return self.async_create_entry(title=NAME, data=user_input)

        return await self._show_config_form(user_input)

    async def async_step_sub_library(self, user_input=None):
        """Ask which sub-library should be used for opening hours."""
        if user_input is not None:
            selected_libraries = {}

            for library_slug, sub_libraries in self._sub_libraries.items():
                selected_id = user_input.get(self._library_fields[library_slug])
                selected = next(
                    (
                        sub_library
                        for sub_library in sub_libraries
                        if sub_library.get("id") == selected_id
                    ),
                    None,
                )
                if selected is None:
                    selected = {
                        "id": selected_id,
                        "label": library_slug.replace("-", " ").title(),
                    }

                selected_libraries[library_slug] = selected
                selected_libraries[library_slug]["main_library"] = library_slug
                selected_libraries[library_slug]["url"] = self._libraries.get(library_slug)

            data = dict(self._user_input)
            data[CONF_OPENING_HOURS_LIBRARIES] = selected_libraries
            return self.async_create_entry(title=NAME, data=data)

        return self.async_show_form(
            step_id="sub_library",
            data_schema=vol.Schema(self._sub_library_schema()),
            errors=self._errors,
        )

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        data_schema = create_schema(user_input)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_import(self, user_input):  # pylint: disable=unused-argument
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        return self.async_create_entry(title="configuration.yaml", data={})

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):  # TODO
    #     """Get the options flow for this handler."""
    #     return ComponentOptionsHandler(config_entry)


class ComponentOptionsHandler(config_entries.OptionsFlow):
    """Now this class isnt like any normal option handlers.. as ha devs option seems think options is
    #  supposed to be EXTRA options, i disagree, a user should be able to edit anything.."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self._errors = {}

    async def async_step_init(self, user_input=None):

        return self.async_show_form(
            step_id="edit",
            data_schema=vol.Schema(create_schema(self.config_entry, option=True)),
            errors=self._errors,
        )

    async def async_step_edit(self, user_input):
        # edit does not work.
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(title="", data={})
