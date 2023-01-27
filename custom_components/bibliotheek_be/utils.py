import json
import logging
import pprint
import re #regular expression
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
# from pydantic import BaseModel
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup

import voluptuous as vol
# from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
        self.userdetails = dict()

    def login(self, username, password):
    # https://bibliotheek.be/mijn-bibliotheek/aanmelden, GET
    # example payload
    # example response: 
    # header: location: https://mijn.bibliotheek.be/openbibid/rest/auth/authorize?hint=login&oauth_callback=https://bibliotheek.be/my-library/login/callback&oauth_token=5abee3c0f5c04beead64d8e625ead0e7&uilang=nl
        # Get OAuth2 state / nonce
        header = {"Content-Type": "application/json"}
        response = self.s.get("https://bibliotheek.be/mijn-bibliotheek/aanmelden",headers=header,timeout=10,allow_redirects=False)
        _LOGGER.debug(f"bibliotheek.be login post result status code: {response.status_code}")
        _LOGGER.debug(f"bibliotheek.be login header: {response.headers}")
        oauth_location = response.headers.get('location')
        oauth_locatonurl_parsed = urlsplit(oauth_location)
        query_params = parse_qs(oauth_locatonurl_parsed.query)
        oauth_callback_url = query_params.get('oauth_callback')
        oauth_token = query_params.get('oauth_token')
        hint = query_params.get('hint')
        _LOGGER.debug(f"bibliotheek.be url params parsed: oauth_callback_url: {oauth_callback_url}, oauth_token: {oauth_token}, hint: {hint}")
        assert response.status_code == 302
        
        
        #authorize based on url in location of response received
        response = self.s.get(oauth_location,headers=header,timeout=10,allow_redirects=False)
        _LOGGER.debug(f"bibliotheek.be auth get result status code: {response.status_code}")
        _LOGGER.debug(f"bibliotheek.be auth get header: {response.headers}")
        assert response.status_code == 200
        
        # data = f"hint={hint}&token={oauth_token}&callback=https%3A%2F%2Fbibliotheek.be%2Fmy-library%2Flogin%2Fcallback&email={username}&password={password}"
        data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
        #login
        #example header response: https://bibliotheek.be/my-library/login/callback?oauth_token=f68491752279e1a5c0a4ee9b6a349836&oauth_verifier=d369ffff4a5c4a05&uilang=nl
        response = self.s.post('https://mijn.bibliotheek.be/openbibid/rest/auth/login',headers=header,data=data,timeout=10,allow_redirects=False)
        _LOGGER.debug(f"bibliotheek.be login get result status code: {response.status_code}")
        _LOGGER.debug(f"bibliotheek.be login get header: {response.headers}")
        login_location = response.headers.get('location')
        login_locatonurl_parsed = urlsplit(login_location)
        login_query_params = parse_qs(login_locatonurl_parsed.query)
        oauth_verifier = login_query_params.get('oauth_verifier')
        oauth_token = query_params.get('oauth_token')
        hint = query_params.get('hint')
        _LOGGER.debug(f"bibliotheek.be url params parsed: login_location: {login_location}, oauth_token: {oauth_token}, oauth_verifier: {oauth_verifier}")
        #example login_location: https://bibliotheek.be/my-library/login/callback?oauth_token=***************&oauth_verifier=*********&uilang=nl
        assert response.status_code == 303
        
        #login callback based on url in location of response received
        response = self.s.get(login_location,headers=header,timeout=10,allow_redirects=False)
        login_callback_location = response.headers.get('location')
        _LOGGER.debug(f"bibliotheek.be login callback get result status code: {response.status_code}")
        _LOGGER.debug(f"bibliotheek.be login callback get header: {response.headers}")
        assert response.status_code == 302
        
        # request access code, https://mijn.bibliotheek.be/openbibid-api.html#_authenticatie
        data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
        response = self.s.post('https://mijn.bibliotheek.be/openbibid/rest/accessToken',headers=header,data=data,timeout=10,allow_redirects=False)
        _LOGGER.debug(f"bibliotheek.be login get result status code: {response.status_code}")
       
        #lidmaatschap based on url in location of response received
        response = self.s.get(f"{login_callback_location}",headers=header,timeout=10,allow_redirects=False)
        lidmaatschap_response_header = response.headers
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code}") # response: {response.text}")
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get header: {response.headers}")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        #find all accounts
        accounts = soup.find_all('div', class_='my-library-user-library-account-list__account')
        # _LOGGER.debug(f"accounts found: {accounts}")

        #iterate through each account
        for div in accounts:
            try:
                # account_details = div.select('[class^=sync-email-notification]')[0].get(':default-active-account')
                # account_details = div.select('[class^=sync-email-notification]')
                account_details = div.find(attrs={':default-active-account': True}).get(':default-active-account')
            except AttributeError:
                account_details = ""
            #get the number of loans
            account_details = json.loads(account_details)
            try:
                account_url = f"https://bibliotheek.be{div.find('a')['href']}"
            except AttributeError:
                account_url = ""
            account_details['url'] = account_url
            try:
                loans = div.find('li', class_='my-library-user-library-account-list__loans-link').a.text
                if "geen" in loans.lower():
                    loans = 0
                else:
                    loans = int(loans.lower().replace(' uitleningen','').replace(' uitlening',''))
            except AttributeError:
                loans = 0
            try:
                loans_url = f"https://bibliotheek.be{div.find('a', href=re.compile('uitleningen')).get('href')}"
            except AttributeError:
                loans_url = ""
            try:
                loan_history_url = f"https://bibliotheek.be{div.find('a', href=re.compile('leenhistoriek')).get('href')}"
            except AttributeError:
                loan_history_url = ""
            try:
                reservations = div.find('li', class_='my-library-user-library-account-list__holds-link').a.text
                if "geen" in reservations.lower():
                    reservations = 0
                else:
                    reservations= int(reservations.lower().replace(' reserveringen','').replace(' reservering',''))
            except AttributeError:
                reservations = 0
            try:
                reservations_url = f"https://bibliotheek.be{div.find('a', href=re.compile('reservaties')).get('href')}"
            except AttributeError:
                reservations_url = ""
            try:
                open_amounts = div.find('li', class_='my-library-user-library-account-list__open-amount-link').a.text
                if "geen" in open_amounts.lower():
                    open_amounts = 0
                else:
                    open_amounts = float(open_amounts.lower().replace(' openstaande bedragen','').replace(' openstaand bedrag','').replace(' openstaande kosten','').replace('€','').replace(',','.'))
            except AttributeError:
                open_amounts = 0
            try:
                open_amounts_url = f"https://bibliotheek.be{div.find('a', href=re.compile('te-betalen')).get('href')}"
            except AttributeError:
                open_amounts_url = ""
            _LOGGER.debug(f"uitleningen {loans} , url: {loans_url}, reservatie: {reservations}, url {account_url}, account_details {account_details}")
            self.userdetails[account_details.get('id')]={'account_details': account_details , 'loans': { 'loans': loans, 'url': loans_url, 'history': loan_history_url}, 'reservations': {'reserveration': reservations, 'url':reservations_url}, 'open_amounts': {'open_amounts': open_amounts, 'url':''}}
        _LOGGER.info(f"self.userdetails {json.dumps(self.userdetails,indent=4)}")
        return self.userdetails
        

    def loan_details(self, url):
        header = {"Content-Type": "application/json"}

        _LOGGER.info(f"loan details URL {url}")
        #lidmaatschap based on url in location of response received
        response = self.s.get(f"{url}",headers=header,timeout=10,allow_redirects=False)
        loan_details_response_header = response.headers
        _LOGGER.info(f"bibliotheek.be lidmaatschap get result status code: {response.status_code} response: {response.text}")
        _LOGGER.info(f"bibliotheek.be lidmaatschap get header: {response.headers}")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        #find all accounts
        accounts = soup.find_all('div', class_='my-library-user-library-account-list__account')
        # _LOGGER.debug(f"accounts found: {accounts}")

        #iterate through each account
        for div in accounts:
            try:
                # account_details = div.select('[class^=sync-email-notification]')[0].get(':default-active-account')
                # account_details = div.select('[class^=sync-email-notification]')
                account_details = div.find(attrs={':default-active-account': True}).get(':default-active-account')
            except AttributeError:
                account_details = ""
            #get the number of loans
            account_details = json.loads(account_details)
            try:
                account_url = f"https://bibliotheek.be{div.find('a')['href']}"
            except AttributeError:
                account_url = ""
            account_details['url'] = account_url
            try:
                loans = div.find('li', class_='my-library-user-library-account-list__loans-link').a.text
                if "geen" in loans.lower():
                    loans = 0
                else:
                    loans = int(loans.lower().replace(' uitleningen','').replace(' uitlening',''))
            except AttributeError:
                loans = 0
            try:
                loans_url = f"https://bibliotheek.be{div.find('a', href=re.compile('uitleningen')).get('href')}"
            except AttributeError:
                loans_url = ""
            try:
                loan_history_url = f"https://bibliotheek.be{div.find('a', href=re.compile('leenhistoriek')).get('href')}"
            except AttributeError:
                loan_history_url = ""
            try:
                reservations = div.find('li', class_='my-library-user-library-account-list__holds-link').a.text
                if "geen" in reservations.lower():
                    reservations = 0
                else:
                    reservations= int(reservations.lower().replace(' reserveringen','').replace(' reservering',''))
            except AttributeError:
                reservations = 0
            try:
                reservations_url = f"https://bibliotheek.be{div.find('a', href=re.compile('reservaties')).get('href')}"
            except AttributeError:
                reservations_url = ""
            try:
                open_amounts = div.find('li', class_='my-library-user-library-account-list__open-amount-link').a.text
                if "geen" in open_amounts.lower():
                    open_amounts = 0
                else:
                    open_amounts = float(open_amounts.lower().replace(' openstaande bedragen','').replace(' openstaand bedrag','').replace(' openstaande kosten','').replace('€','').replace(',','.'))
            except AttributeError:
                open_amounts = 0
            try:
                open_amounts_url = f"https://bibliotheek.be{div.find('a', href=re.compile('te-betalen')).get('href')}"
            except AttributeError:
                open_amounts_url = ""
            # _LOGGER.debug(f"uitleningen {loans} , url: {loans_url}, reservatie: {reservations}, url {account_url}, account_details {account_details}")
            self.userdetails[account_details.get('id')]={'account_details': account_details , 'loans': { 'loans': loans, 'url': loans_url, 'history': loan_history_url}, 'reservations': {'reserveration': reservations, 'url':reservations_url}, 'open_amounts': {'open_amounts': open_amounts, 'url':''}}
        # _LOGGER.info(f"self.userdetails {json.dumps(self.userdetails,indent=4)}")
        return self.userdetails