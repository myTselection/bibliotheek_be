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
        _LOGGER.debug(f"bibliotheek.be login callback get header: {response.headers} text {response.text}")
        if response.status_code == 302:        
            # request access code, https://mijn.bibliotheek.be/openbibid-api.html#_authenticatie
            data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
            response = self.s.post('https://mijn.bibliotheek.be/openbibid/rest/accessToken',headers=header,data=data,timeout=10,allow_redirects=False)
            _LOGGER.debug(f"bibliotheek.be login get result status code: {response.status_code}")
        else:
            #login session was already available
            login_callback_location = "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen"
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

        # {
            # "1234567": {
                # "account_details": {
                    # "id": "1234567",
                    # "libraryName": "Bibliotheek *****",
                    # "userName": "first last",
                    # "email": "email@mail.com",
                    # "alertEmailSync": false,
                    # "barcode": "1234567890123",
                    # "url": "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1234567"
                # },
                # "loans": {
                    # "loans": 0,
                    # "url": "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1234567/uitleningen",
                    # "history": "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1234567/leenhistoriek"
                # },
                # "reservations": {
                    # "reservations": 0,
                    # "url": "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1234567/reservaties"
                # },
                # "open_amounts": {
                    # "open_amounts": 0,
                    # "url": ""
                # }
            # }
        # }
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
            self.userdetails[account_details.get('id')]={'account_details': account_details , 'loans': { 'loans': loans, 'url': loans_url, 'history': loan_history_url}, 'reservations': {'reservations': reservations, 'url':reservations_url}, 'open_amounts': {'open_amounts': open_amounts, 'url':''}}
        _LOGGER.debug(f"self.userdetails {json.dumps(self.userdetails,indent=4)}")
        return self.userdetails
        


    # loand details example
    # {
        # "National Geographic junior--": {
            # "title": "National Geographic junior",
            # "author": "-",
            # "loan_type": "",
            # "url": "https://sint-pieters-leeuw.bibliotheek.be/resolver.ashx?extid=%7Cwise-vlaamsbrabant%7C4390213",
            # "image_src": "https://bibliotheek.be/themes/custom/library_portal_theme/assets/img/placeholder_book.png",
            # "days_remaining": 16,
            # "loan_from": "01/01/2022",
            # "loan_till": "01/01/2023",
            # "extend_loan_id": "12345678",
            # "library": "Bibliotheek *****"
        # },
        # "Peppers of the Caribbean-Ornella, Emanuele": {
            # "title": "Peppers of the Caribbean",
            # "author": "Ornella, Emanuele",
            # "loan_type": "",
            # "url": "https://sint-pieters-leeuw.bibliotheek.be/resolver.ashx?extid=%7Cwise-vlaamsbrabant%7C2472827",
            # "image_src": "https://bibliotheek.be/themes/custom/library_portal_theme/assets/img/placeholder_book.png",
            # "days_remaining": 16,
            # "loan_from": "01/01/2022",
            # "loan_till": "01/01/2023",
            # "extend_loan_id": "12345678",
            # "library": "Bibliotheek ***"
        # }
    # }
    def loan_details(self, url):
        loandetails = dict()
        header = {"Content-Type": "application/json"}

        _LOGGER.debug(f"loan details URL {url}")
        #lidmaatschap based on url in location of response received
        response = self.s.get(f"{url}",headers=header,timeout=10,allow_redirects=False)
        loan_details_response_header = response.headers
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code} response: {response.text}")
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get header: {response.headers}")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        #find all libs
        libs = soup.find_all('div', class_='my-library-user-library-account-loans__loan-wrapper')
        # _LOGGER.debug(f"accounts found: {accounts}")

        #iterate through each account
        for div in libs:
            # not working as within same loan-wrapper multiple libraries can appear
            # libname = div.find('h2').text         
            
            books = div.find_all('div', class_='my-library-user-library-account-loans__loan')
            for book in books:
                try:
                    libname = book.find('h3', class_='my-library-user-library-account-loans__loan-title').a.get('href').split('.')[0].split('//')[1].title()
                except AttributeError:
                    libname = ""
                try:
                    title = book.find('h3', class_='my-library-user-library-account-loans__loan-title').a.text.strip()
                except AttributeError:
                    title = ""
                try:
                    url = book.find('h3', class_='my-library-user-library-account-loans__loan-title').a.get('href')
                except AttributeError:
                    url = ""
                try:
                    image_src = book.find('img', class_='my-library-user-library-account-loans__loan-cover-img').get('src')
                except AttributeError:
                    image_src = ""
                try:
                    author = book.find('div', class_='author').text.strip()
                except AttributeError:
                    author = ""
                try:
                    loan_type = book.find('div', class_='my-library-user-library-account-loans__loan-type-label').text
                except AttributeError:
                    loan_type = "Unknown"
                try:
                    days_remaining = book.find('div', class_='my-library-user-library-account-loans__loan-days').text.strip()
                    days_remaining = int(days_remaining.lower().replace('nog ','').replace(' dagen',''))
                except AttributeError:
                    days_remaining = ""
                try:
                    loan_from = book.find('div', class_='my-library-user-library-account-loans__loan-from-to')
                    loan_from = loan_from.select_one('.my-library-user-library-account-loans__loan-from-to > div > span:nth-of-type(2)').text
                except AttributeError:
                    loan_from = ""
                try:
                    loan_till = book.find('div', class_='my-library-user-library-account-loans__loan-from-to')
                    loan_till = loan_till.select_one('.my-library-user-library-account-loans__loan-from-to > div:nth-of-type(2) > span:nth-of-type(2)').text
                except AttributeError:
                    loan_till = ""
                try:
                    extend_loan_id = book.find('div', class_='my-library-user-library-account-loans__extend-loan')
                    extend_loan_id = extend_loan_id.select_one('input[type="checkbox"]')['id']
                except (AttributeError, TypeError):
                    extend_loan_id = ""
                #example extension
                # https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1544061/uitleningen/verlengen?loan-ids=14870745%2C14871363%2C15549439%2C15707198%2C15933330%2C15938501%2C16370683%2C16490618%2C16584912%2C15468349%2C23001576%2C26583345
                loandetails[f"{title} ~ {author}"] = {'title': title, 'author': author, 'loan_type': loan_type, 'url': url, 'image_src': image_src, 'days_remaining': days_remaining, 'loan_from': loan_from, 'loan_till': loan_till, 'extend_loan_id':extend_loan_id, 'library': libname}
        # _LOGGER.info(f"loandetails {loandetails}") 
        _LOGGER.debug(f"loandetails {json.dumps(loandetails,indent=4)}") 
        return loandetails
        


    def extend_all(self, url, execute):
        loandetails = dict()
        header = {"Content-Type": "application/json"}

        _LOGGER.debug(f"extend_all URL {url}")
        #lidmaatschap based on url in location of response received
        response = self.s.get(f"{url}",headers=header,timeout=10,allow_redirects=False)
        loan_details_response_header = response.headers
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code} response: {response.text}")
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get header: {response.headers}")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        
        extend_loan_ids = f"{url}/velengen?loan-ids="
        num_id_found = 0
        
        #find all libs
        libs = soup.find_all('div', class_='my-library-user-library-account-loans__loan-wrapper')
        # _LOGGER.debug(f"accounts found: {accounts}")

        #iterate through each account
        for div in libs:
            libname = div.find('h2').text
            
            books = div.find_all('div', class_='my-library-user-library-account-loans__loan')
            for book in books:
                try:
                    extend_loan_id = book.find('div', class_='my-library-user-library-account-loans__extend-loan')
                    extend_loan_id = extend_loan_id.select_one('input[type="checkbox"]')['id']
                    if num_id_found == 0:
                        extend_loan_ids += f"%2C{extend_loan_id}"
                    else:
                        extend_loan_ids += f"{extend_loan_id}"
                    num_id_found += 1
                except (AttributeError, TypeError):
                    extend_loan_id = ""
        
        _LOGGER.debug(f"extend_loan_ids: {extend_loan_ids}") 
        
        if execute & num_id_found > 0:
            response = self.s.get(f"{extend_loan_ids}",headers=header,timeout=10,allow_redirects=False)
            assert response.status_code == 200
        #example extension
        # https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1544061/uitleningen/verlengen?loan-ids=14870745%2C14871363%2C15549439%2C15707198%2C15933330%2C15938501%2C16370683%2C16490618%2C16584912%2C15468349%2C23001576%2C26583345
        _LOGGER.debug(f"self.loandetails {self.loandetails}") 
        return num_id_found