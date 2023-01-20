import json
import logging
import pprint
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
from pydantic import BaseModel
# from urlparse import urlparse

import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"

def check_settings(config, hass):
    if not any(config.get(i) for i in ["username"]):
        _LOGGER.error("username was not set")
    else:
        return True
    if not config.get("password"):
        _LOGGER.error("password was not set")
    else:
        return True
    if not config.get("data"):
        _LOGGER.error("data bool was not set")
    else:
        return True
    if not config.get("mobile"):
        _LOGGER.error("mobile bool was not set")
    else:
        return True
        
    if config.get("data") and config.get("mobile"):
        return True
    else:
        _LOGGER.error("At least one of data or mobile is to be set")

    raise vol.Invalid("Missing settings to setup the sensor.")


class ComponentSession(object):
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Python/3"
        self.userdetails = None
        self.msisdn = None

    def login(self, username, password):
    # https://bibliotheek.be/mijn-bibliotheek/aanmelden, GET
    # example payload
    # example response: 
    # header: location: https://mijn.bibliotheek.be/openbibid/rest/auth/authorize?hint=login&oauth_callback=https://bibliotheek.be/my-library/login/callback&oauth_token=5abee3c0f5c04beead64d8e625ead0e7&uilang=nl
        # Get OAuth2 state / nonce
        header = {"Content-Type": "application/json"}
        response = self.s.get("https://bibliotheek.be/mijn-bibliotheek/aanmelden",headers=header,timeout=10)
        _LOGGER.info("bibliotheek.be login post result status code: " + str(response.status_code) + ", response: " + response.text)
        _LOGGER.info("bibliotheek.be login header: " + str(response.headers))
        oauth_location = response.headers.get('location')
        # oauth_url_parsed = urlparse(oauth_location)
        oauth_
        assert response.status_code == 302
        
        
        response = self.s.get(oauth_location,headers=header,timeout=10)
        _LOGGER.info("bibliotheek.be auth get result status code: " + str(response.status_code) + ", response: " + response.text)
        _LOGGER.info("bibliotheek.be auth get header: " + str(response.headers))
        assert response.status_code == 200
        
        
        response = self.s.get('https://mijn.bibliotheek.be/openbibid/rest/auth/login',headers=header,timeout=10)
        _LOGGER.info("bibliotheek.be auth get result status code: " + str(response.status_code) + ", response: " + response.text)
        _LOGGER.info("bibliotheek.be auth get header: " + str(response.headers))
        assert response.status_code == 200
        
        
        self.userdetails = response.json()
        self.msisdn = self.userdetails.get('Object').get('Customers')[0].get('Msisdn')
        self.s.headers["securitykey"] = response.headers.get('securitykey')
        return self.userdetails

    def usage_details(self):
    # https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo
    # request.Msisdn - phonenr 
    # {"Message":null,"ResultCode":0,"Object":[{"Properties":[{"Key":"UsedAmount","Value":"0"},{"Key":"BundleDurationWithUnits","Value":"250 MB"},{"Key":"Percentage","Value":"0.00"},{"Key":"_isUnlimited","Value":"0"},{"Key":"_isExtraMbsAvailable","Value":"1"}],"SectionId":1},{"Properties":[{"Key":"UsedAmount","Value":"24"},{"Key":"BundleDurationWithUnits","Value":"200 Min"},{"Key":"Percentage","Value":"12.00"},{"Key":"_isUnlimited","Value":"0"}],"SectionId":2},{"Properties":[{"Key":"StartDate","Value":"1 februari 2023"},{"Key":"NumberOfRemainingDays","Value":"16"}],"SectionId":3},{"Properties":[{"Key":"UsedAmount","Value":"0.00"}],"SectionId":4}]}
        header = {"Content-Type": "application/json"}
        response = self.s.get("https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo",data='{"request": {"Msisdn": '+str(self.msisdn)+'}}',headers=header,timeout=10)
        self.s.headers["securitykey"] = response.headers.get('securitykey')
        _LOGGER.debug("bibliotheek.be  result status code: " + str(response.status_code) + ", msisdn" + str(self.msisdn))
        _LOGGER.debug("bibliotheek.be  result " + response.text)
        assert response.status_code == 200
        return response.json()
        