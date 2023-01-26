import json
import logging
import pprint
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
from pydantic import BaseModel
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup

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
        response = self.s.get("https://bibliotheek.be/mijn-bibliotheek/aanmelden",headers=header,timeout=10,allow_redirects=False)
        _LOGGER.info(f"bibliotheek.be login post result status code: {response.status_code}")
        _LOGGER.info(f"bibliotheek.be login header: {response.headers}")
        oauth_location = response.headers.get('location')
        oauth_locatonurl_parsed = urlsplit(oauth_location)
        query_params = parse_qs(oauth_locatonurl_parsed.query)
        oauth_callback_url = query_params.get('oauth_callback')
        oauth_token = query_params.get('oauth_token')
        hint = query_params.get('hint')
        _LOGGER.info(f"bibliotheek.be url params parsed: oauth_callback_url: {oauth_callback_url}, oauth_token: {oauth_token}, hint: {hint}")
        assert response.status_code == 302
        
        
        #authorize based on url in location of response received
        response = self.s.get(oauth_location,headers=header,timeout=10,allow_redirects=False)
        _LOGGER.info(f"bibliotheek.be auth get result status code: {response.status_code}")
        _LOGGER.info(f"bibliotheek.be auth get header: {response.headers}")
        assert response.status_code == 200
        
        # data = f"hint={hint}&token={oauth_token}&callback=https%3A%2F%2Fbibliotheek.be%2Fmy-library%2Flogin%2Fcallback&email={username}&password={password}"
        data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
        #login
        #example header response: https://bibliotheek.be/my-library/login/callback?oauth_token=f68491752279e1a5c0a4ee9b6a349836&oauth_verifier=d369ffff4a5c4a05&uilang=nl
        response = self.s.post('https://mijn.bibliotheek.be/openbibid/rest/auth/login',headers=header,data=data,timeout=10,allow_redirects=False)
        _LOGGER.info(f"bibliotheek.be login get result status code: {response.status_code}")
        _LOGGER.info(f"bibliotheek.be login get header: {response.headers}")
        login_location = response.headers.get('location')
        login_locatonurl_parsed = urlsplit(login_location)
        login_query_params = parse_qs(login_locatonurl_parsed.query)
        oauth_verifier = login_query_params.get('oauth_verifier')
        oauth_token = query_params.get('oauth_token')
        hint = query_params.get('hint')
        _LOGGER.info(f"bibliotheek.be url params parsed: login_location: {login_location}, oauth_token: {oauth_token}, oauth_verifier: {oauth_verifier}")
        #example login_location: https://bibliotheek.be/my-library/login/callback?oauth_token=***************&oauth_verifier=*********&uilang=nl
        assert response.status_code == 303
        
        #login callback based on url in location of response received
        response = self.s.get(login_location,headers=header,timeout=10,allow_redirects=False)
        login_callback_location = response.headers.get('location')
        _LOGGER.info(f"bibliotheek.be login callback get result status code: {response.status_code}")
        _LOGGER.info(f"bibliotheek.be login callback get header: {response.headers}")
        assert response.status_code == 302
        
        # request access code, https://mijn.bibliotheek.be/openbibid-api.html#_authenticatie
        data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
        response = self.s.post('https://mijn.bibliotheek.be/openbibid/rest/accessToken',headers=header,data=data,timeout=10,allow_redirects=False)
        _LOGGER.info(f"bibliotheek.be login get result status code: {response.status_code}")
       
        
        
        #lidmaatschap based on url in location of response received
        response = self.s.get(f"{login_callback_location}",headers=header,timeout=10,allow_redirects=False)
        lidmaatschap_response_header = response.headers
        _LOGGER.info(f"bibliotheek.be lidmaatschap get result status code: {response.status_code}") # response: {response.text}")
        _LOGGER.info(f"bibliotheek.be lidmaatschap get header: {response.headers}")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        #find all accounts
        accounts = soup.find_all('div', class_='my-library-user-library-account-list__account')
        _LOGGER.info(f"accounts found: {accounts}")

        #iterate through each account
        for div in accounts:
            #get the name
            name = div.find('div', class_='my-library-user-library-account-list__name').text
            _LOGGER.info(f"bib account {name}")
            #get the number of loans
            try:
                loans = div.find('li', class_='my-library-user-library-account-list__loans-link').a.text
            except AttributeError:
                loans = "0"
            try:
                loans_url = div.find('a')['href=*uitleningen']
            except AttributeError:
                loans_url = ""
            try:
                reservations = div.find('li', class_='my-library-user-library-account-list__holds-link').a.text
            except AttributeError:
                reservations = "0"
            try:
                account_url = div.find('a')['href']
            except AttributeError:
                account_url = "0"
            try:
                account_id = account_url.split('/')[-1]
            except AttributeError:
                account_id = "0"
            #print the name and number of loans
            _LOGGER.info(f"{name} : uitleningen {loans} , url: {loans_url}, reservatie: {reservations}, url {account_url}, id {account_id}")
        
        # _LOGGER.info(f"bibliotheek.be lidmaatschap data: {data}")
        return oauth_token

    def usage_details(self):
    # https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo
    # request.Msisdn - phonenr 
    # {"Message":null,"ResultCode":0,"Object":[{"Properties":[{"Key":"UsedAmount","Value":"0"},{"Key":"BundleDurationWithUnits","Value":"250 MB"},{"Key":"Percentage","Value":"0.00"},{"Key":"_isUnlimited","Value":"0"},{"Key":"_isExtraMbsAvailable","Value":"1"}],"SectionId":1},{"Properties":[{"Key":"UsedAmount","Value":"24"},{"Key":"BundleDurationWithUnits","Value":"200 Min"},{"Key":"Percentage","Value":"12.00"},{"Key":"_isUnlimited","Value":"0"}],"SectionId":2},{"Properties":[{"Key":"StartDate","Value":"1 februari 2023"},{"Key":"NumberOfRemainingDays","Value":"16"}],"SectionId":3},{"Properties":[{"Key":"UsedAmount","Value":"0.00"}],"SectionId":4}]}
        header = {"Content-Type": "application/json"}
        # response = self.s.get("https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo",data='{"request": {"Msisdn": '+str(self.msisdn)+'}}',headers=header,timeout=10)
        self.s.headers["securitykey"] = response.headers.get('securitykey')
        _LOGGER.debug("bibliotheek.be  result status code: " + str(response.status_code) + ", msisdn" + str(self.msisdn))
        _LOGGER.debug("bibliotheek.be  result " + response.text)
        assert response.status_code == 200
        return response.json()
        