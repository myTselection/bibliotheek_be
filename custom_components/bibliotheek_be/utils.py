import json
import logging
import pprint
import re #regular expression
from urllib.parse import urlparse
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
# from pydantic import BaseModel
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
import httpx
from homeassistant.helpers.httpx_client import get_async_client
from collections import OrderedDict


import voluptuous as vol
# from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"
_TIMEOUT = 30

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


def extract_libraryname_from_url(url):
    hostname = urlparse(url).hostname
    return hostname.split(".")[0]  # first part: koksijde, beersel, ...

class ComponentSession(object):
    def __init__(self, hass):
        self.hass = hass
        # self.s = httpx.Client(http2=True, max_redirects=0)
        # self.s = requests.Session()
        self.s = get_async_client(self.hass)
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.userdetails = dict()

    async def login(self, username, password):
    # https://bibliotheek.be/mijn-bibliotheek/aanmelden, GET
    # example payload
    # example response: 
    # header: location: https://mijn.bibliotheek.be/openbibid/rest/auth/authorize?hint=login&oauth_callback=https://bibliotheek.be/my-library/login/callback&oauth_token=**************&uilang=nl
        # Get OAuth2 state / nonce
        header = {"Content-Type": "application/json"}
        response = await self.s.get("https://bibliotheek.be/mijn-bibliotheek/aanmelden",headers=header,timeout=_TIMEOUT)
        _LOGGER.debug(f"bibliotheek.be login post result status code: {response.status_code}")
        _LOGGER.debug(f"bibliotheek.be login header: {response.headers}")
        oauth_location = response.headers.get('location')
        oauth_locatonurl_parsed = urlsplit(oauth_location)
        query_params = parse_qs(oauth_locatonurl_parsed.query)
        oauth_callback_url = query_params.get('oauth_callback', [None])[0]
        oauth_token = query_params.get('oauth_token', [None])[0]
        hint = query_params.get('hint', [None])[0]
        _LOGGER.debug(f"bibliotheek.be url params parsed: oauth_callback_url: {oauth_callback_url}, oauth_token: {oauth_token}, hint: {hint}")
        require_auth = True
        if (response.status_code != 302):
            # already authenticated
            require_auth = False
        
        if require_auth:
            #authorize based on url in location of response received
            response = await self.s.get(oauth_location,headers=header,timeout=_TIMEOUT)
            _LOGGER.debug(f"bibliotheek.be auth get result status code: {response.status_code}")
            _LOGGER.debug(f"bibliotheek.be auth get header: {response.headers}")
            assert response.status_code == 200
            
            header["Content-Type"] = "application/x-www-form-urlencoded"
            header["Host"] = "mijn.bibliotheek.be"
            header["Origin"] = "https://bibliotheek.be"
            header["Referer"] = oauth_location
            header["Accept-Language"] = "en-US,en;q=0.9,nl;q=0.8,fr;q=0.7"
            # data = f"hint={hint}&token={oauth_token}&callback=https%3A%2F%2Fbibliotheek.be%2Fmy-library%2Flogin%2Fcallback&email={username}&password={password}"
            data = {"hint": hint, "token": oauth_token, "callback": "https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
            #login
            #example header response: https://bibliotheek.be/my-library/login/callback?oauth_token=*******************&oauth_verifier=**********&uilang=nl
            response = await self.s.post('https://mijn.bibliotheek.be/openbibid/rest/auth/login',headers=header,data=data,timeout=_TIMEOUT)
            _LOGGER.debug(f"bibliotheek.be login post result status code: {response.status_code}")
            _LOGGER.debug(f"bibliotheek.be login post header: {response.headers}")
            _LOGGER.debug(f"bibliotheek.be login post cookies: {response.cookies}")
            _LOGGER.debug(f"bibliotheek.be login session cookies: {self.s.cookies}")
            login_location = response.headers.get('location')
            login_locationurl_parsed = urlsplit(login_location)
            login_query_params = parse_qs(login_locationurl_parsed.query)
            oauth_verifier = login_query_params.get('oauth_verifier', [None])[0]
            oauth_token = query_params.get('oauth_token', [None])[0]
            _LOGGER.debug(f"bibliotheek.be url params parsed: login_location: {login_location}, oauth_token: {oauth_token}, oauth_verifier: {oauth_verifier}")
            #example login_location: https://bibliotheek.be/my-library/login/callback?oauth_token=***************&oauth_verifier=*********&uilang=nl
            
            assert response.status_code in [200,303]
            if response.status_code == 303:
            # if response.status_code in [200,303]:
                self.s.headers["Content-Type"] = "application/x-www-form-urlencoded"
                self.s.headers["referer"] = "https://mijn.bibliotheek.be/"
                self.s.headers["pragma"] = "no-cache"
                self.s.headers["upgrade-insecure-requests"] = "1"
                # header["X-Cache"] = "MISS ausy-cultuurconnect-web7"
                # self.s.headers["accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                # header["Accept-Encoding"]= "gzip, deflate, br, zstd"
                #login callback based on url in location of response received
                _LOGGER.debug(f"bibliotheek.be login session header: {self.s.headers}")
                # response = self.s.get(login_location,headers=header,timeout=_TIMEOUT)
                response = await self.s.get(login_location,timeout=_TIMEOUT,follow_redirects=False)
                login_callback_location = response.headers.get('location')
                _LOGGER.debug(f"bibliotheek.be login callback get result status code: {response.status_code}")
                _LOGGER.debug(f"bibliotheek.be login callback get header: {response.headers} ") #text {response.text}")
                # assert response.status_code == 302
                if response.status_code == 302:        
                    # request access code, https://mijn.bibliotheek.be/openbibid-api.html#_authenticatie
                    data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
                    response = await self.s.post('https://mijn.bibliotheek.be/openbibid/rest/accessToken',headers=header,data=data,timeout=_TIMEOUT,follow_redirects=True)
                    _LOGGER.debug(f"bibliotheek.be login get result status code: {response.status_code}")
                else:
                    #login session was already available
                    login_callback_location = "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen"


        login_callback_location = "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen"
        #lidmaatschap based on url in location of response received
        # response = await self.s.get(f"{login_callback_location}",headers=header,timeout=_TIMEOUT)
        response = await self.s.get(f"{login_callback_location}",timeout=_TIMEOUT,follow_redirects=False)
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code}") # response: {response.text}")
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get header: {response.headers}")
        # _LOGGER.debug(f"bibliotheek.be lidmaatschap get text: {response.text}")
        assert response.status_code == 200
        # soup = BeautifulSoup(response.text, 'html.parser')

        # MEMBERSHIPS:
        # https://bibliotheek.be/api/my-library/memberships
        #   activities per account id, for which hasError is false
        #https://bibliotheek.be/api/my-library/123456789/activities

        # open payments: https://bibliotheek.be/my-library-user/open-payments-count
        # https://bibliotheek.be/my-library-user/new-recommendations-count
        # https://bibliotheek.be/my-library-user/messages-count
        # https://bibliotheek.be/my-library-user/unconfirmed-memberships-count

        responseMemberships = await self.s.get(f"https://bibliotheek.be/api/my-library/memberships",timeout=_TIMEOUT,follow_redirects=True)
        assert responseMemberships.status_code == 200
        _LOGGER.debug(f"bibliotheek.be memberships get result status code: {responseMemberships.status_code}, response: {responseMemberships.text}")
        memberships = responseMemberships.json()

        
        libraryDetails = {}

        for library_region_name, libraryRegionType in memberships.items():
            _LOGGER.debug(f"bibliotheek.be lidmaatschap library: {library_region_name}, libraryRegionType: {libraryRegionType}")
            libraryAccounts = libraryRegionType.get("library",libraryRegionType.get("region",None))
            if isinstance(libraryAccounts, dict):
                accounts = []
                for barcode, account in libraryAccounts.items():
                    accounts.extend(account)
            else:
                accounts = libraryAccounts


            for account in accounts:
                _LOGGER.debug(f"bibliotheek.be lidmaatschap account: {account}")
                if not account.get("hasError", True) and account.get("id"):
                    
                    account['barcode_spell'] = self.count_repeated_numbers(account.get('barcode',''))
                    account['userName'] = account.get('name','')
                    libraryUrl = account.get('library','')
                    account['libraryLongName'] = account.get('libraryName','')
                    libraryname_from_url = urlparse(libraryUrl).hostname.split(".")[0]
                    account['libraryName'] = f"{libraryname_from_url}".title()
                    libraryDetails[libraryname_from_url] = account.get('library','')

                    
                    responseActivities = await self.s.get(f"https://bibliotheek.be/api/my-library/{account['id']}/activities",timeout=_TIMEOUT,follow_redirects=True)
                    assert responseActivities.status_code == 200
                    activities = responseActivities.json()
                   
                    # Final data structure
                    self.userdetails[account.get('id')] = {
                        'account_details': account,
                        'loans': {
                            'loans': activities.get("numberOfLoans",0),
                            'url': f"https://bibliotheek.be/my-library/memberships/{account['id']}/loans",
                            'history': f"{account.get('library','')}{activities.get("loanHistoryUrl", "")}"
                        },
                        'reservations': {
                            'reservations': activities.get("numberOfHolds",0),
                            'url': f"https://bibliotheek.be/my-library/memberships/{account['id']}/holds"
                        },
                        'open_amounts': {
                            'open_amounts': activities.get("openAmount",0),
                            'url': f"https://bibliotheek.be/my-library/memberships/{account['id']}/pay"
                        },
                        'updated': True
                    }
                    _LOGGER.debug(f"account_details: {json.dumps(self.userdetails[account.get('id')],indent=4)}")

        # _LOGGER.debug(f"self.userdetails {json.dumps(self.userdetails,indent=4)}")

        
        responseLoans = await self.s.get(f"https://bibliotheek.be/my-library-overview-loans",timeout=_TIMEOUT,follow_redirects=True)
        assert responseLoans.status_code == 200
        loandetails = responseLoans.json()
        _LOGGER.debug(f"loandetails my-library-overview-loans: {json.dumps(loandetails,indent=4)}")

        
        responseReservations = await self.s.get(f"https://bibliotheek.be/my-library-overview-reservations",timeout=_TIMEOUT,follow_redirects=True)
        assert responseReservations.status_code == 200
        reservations = responseReservations.json()
        _LOGGER.debug(f"reservations my-library-overview-reservations: {json.dumps(reservations,indent=4)}")
        userdetailsAndLoans = {'userdetails': self.userdetails, 'loandetails': loandetails, 'reservationdetails': reservations, 'librarydetails': libraryDetails}
        _LOGGER.debug(f"userdetailsAndLoans: {json.dumps(userdetailsAndLoans,indent=4)}")

        return userdetailsAndLoans
        
    def count_repeated_numbers(self, input_string):
        counts = []
        current_char = None
        current_count = 0

        for char in input_string:
            if char == current_char:
                current_count += 1
            else:
                if current_count > 1:
                    counts.append(str(current_count) + "x" + current_char)
                elif current_char is not None:
                    counts.append(current_char)
                current_char = char
                current_count = 1

        if current_count > 1:
            counts.append(str(current_count) + "x" + current_char)
        else:
            counts.append(current_char)

        return counts
    
    async def library_details(self, url):
        header = {"Content-Type": "application/json"}

        _LOGGER.debug(f"library details URL {url}")

        #lidmaatschap based on url in location of response received
        # response = await self.s.get(f"{url}",headers=header,timeout=_TIMEOUT)
        response = await self.s.get(f"{url}",timeout=_TIMEOUT,follow_redirects=True)
        library_details_response_header = response.headers
        _LOGGER.debug(f"bibliotheek.be library get result status code: {response.status_code}") #response: {response.text}")
        _LOGGER.debug(f"bibliotheek.be library get header: {response.headers}")
        
        login_location = response.headers.get('location')
        if login_location is not None:
            _LOGGER.debug(f"Following redirection: {login_location}")
            response = await self.s.get(login_location,timeout=_TIMEOUT,follow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        libraryArticle = soup.find('article',class_='library library--page-item')
        # libraryArticle = soup.find('div',class_='block block-system block-system-main-block')
        library_info = {}
        library_info['url'] = url.replace('/adres-en-openingsuren','')
        url = library_info.get("url", "")
        _LOGGER.debug(f"libraryNameFromUrl: {urlparse(url).hostname.split(".")[0]}")
        libraryNameFromUrl = extract_libraryname_from_url(url)
        library_info['libraryNameFromUrl'] = libraryNameFromUrl
        if libraryArticle is None:
            _LOGGER.error(f"No library info found, {url}") 
            return library_info
        # library_info['name'] = libraryArticle.find('a', class_='.library--page-item').text.strip()

        hours = {}
        for dl in libraryArticle.find_all('dl',class_='library__date-open'):
            day = dl.dt.text.strip()
            times = []
            for span in dl.select('.timespan time'):
                times.append(span.text.strip())
            hours[day] = times
        library_info['hours'] = hours

        gps_element = libraryArticle.find('div',class_='library__pane--address-address--gps')
        if gps_element:
            gps_element = gps_element.text.replace('\n', ' ').replace('\u00b0','').replace('Gps','').strip()
            gps_element = gps_element.strip().split('NB')
            lat = gps_element[0]
            lon = gps_element[1].strip().split('OL')[0]
            library_info['lat'] = lat
            library_info['lon'] = lon
            _LOGGER.debug(f"gps {gps_element} lat {lat} lon {lon}")

        address_element = libraryArticle.find('div',class_='library__pane--address--address')
        if address_element:
            library_info['address'] = address_element.text.replace('\n', ' ').replace('Adres','').replace('Toon op kaart','').strip().replace('         ',',')

        phone_element = libraryArticle.find('a',class_='tel')
        if phone_element:
            library_info['phone'] = libraryArticle.find('a',class_='tel').text.strip()
        
        email_element = libraryArticle.find('span',class_='spamspan')
        if email_element:
            library_info['email'] = libraryArticle.find('span',class_='spamspan').text.strip().replace(' [at] ', '@')

        closed_dates = []
        for dl in libraryArticle.find_all('dl',class_='library__date-closed'):
            date = dl.dt.text.strip()
            reason = dl.dd.text.strip()
            closed_dates.append({'date': date, 'reason': reason})
        library_info['closed_dates'] = closed_dates
        library_info['updated'] = True

        _LOGGER.debug(f"librarydetails {json.dumps(library_info,indent=4)}") 
        return library_info

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

    async def user_lists(self):
        listdetails = dict()
        _LOGGER.debug(f"user_lists")

        response = await self.s.get(f"https://bibliotheek.be/mijn-bibliotheek/lijsten",timeout=_TIMEOUT,follow_redirects=True)
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')

        _LOGGER.debug(f"user_lists soup: {soup}")


        # find the tag
        tag = soup.find("item-lists-overview")

        # get the JSON string from the :lists attribute
        json_str = tag.get(":lists")

        # parse the JSON
        data = json.loads(json_str)


        for item in data:
            list_id = item["url"].split("/")[-1]
            name = item["title"]
            url = item["url"]
            num_items = item["numberOfItems"]
            last_changed = item["modifiedDate"]

            _LOGGER.debug(f"Listname: {name}, URL: {url}, Items: {num_items}, Last changed: {last_changed}")

            listdetails[list_id] = {
                'id': list_id,
                'name': name,
                'url': f"https://bibliotheek.be{url}",
                'num_items': num_items,
                'last_changed': last_changed,
                'updated': True
            }
            response = await self.s.get(f"https://bibliotheek.be/my-library/list/{list_id}/list-items?items_per_page=300&status=1",timeout=_TIMEOUT,follow_redirects=True)
            assert response.status_code == 200
            listItemDetails = response.json()
            _LOGGER.debug(f"listItemDetails: {json.dumps(listItemDetails,indent=4)} list_id: {list_id}")

            # too many data elements received, eg:
                #  'id': '123456789',
                # 'cover': 'https://webservices.bibliotheek.be/index.php?func=cover&ISBN=9789082410617&VLACCnr=123456&CDR=&EAN=&ISMN=&EBS=&coversize=small',
                # 'title': 'Het smelt',
                # 'url': 'https://bibliotheek.be/catalogus/lize-spit/het-smelt/boek/library-marc-vlacc_123456',
                # 'author': 'Lize Spit',
                # 'publicationYear': 'Uitgave van: 2023',
                # 'itemId': '|library/marc/vlacc|123456',
                # 'wiseIds': '123456789',
                # 'addToListUrl': '/my-library/add-to-list/123456/nojs?catalog_items%5B0%5D=library-marc-vlacc_123456&destination=/my-library/list/123456/list-items%3Fitems_per_page%3D300%26status%3D1&exclude_lists%5B0%5D=322528',
                # 'deleteUrl': '/my-library/lists/123456/item/8704917/delete',
                # 'searchBibUrl': '/?itemid=%7Clibrary/marc/vlacc%7123456',
                # 'dateAdded': {
                #     'date': '2024-12-09 22:21:39.000000',
                #     'timezone_type': 1,
                #     'timezone': '+00:00'
                # },
                # 'year': '2023',
                # 'status': 1
            # Extract only the desired fields
            filtered_data = [
                {
                    'title': item.get('title',""),
                    'author': item.get('author',""),
                    'url': item.get('url',""),
                    "catalogItemId": item.get('catalogItemId',""),
                    "cover": item.get('cover',""),
                    "creationDateTimestamp": item.get('creationDateTimestamp',""),
                    "format": item.get('format',""),
                    "formatRaw": item.get('formatRaw',""),
                    "id": item.get('id',""),
                    "read": item.get('read',""),
                    "wiseIds": item.get('wiseIds',"")

                }
                for item in listItemDetails
            ]
            listdetails[list_id]['items'] = filtered_data

        return listdetails


    async def loan_details(self, url):
        loandetails = dict()
        header = {"Content-Type": "application/json"}

        _LOGGER.debug(f"loan details URL {url}")
        match = re.search(r"/memberships/(\d+)/", url)
        if match:
            accountid = match.group(1)
        else:
            accountid = None
        _LOGGER.debug(f"loan details URL {url} id: {accountid}")


        #lidmaatschap based on url in location of response received
        # response = await self.s.get(f"{url}",headers=header,timeout=_TIMEOUT)
        response = await self.s.get(f"{url}",timeout=_TIMEOUT,follow_redirects=True)
        login_location = response.headers.get('location')
        if login_location is not None:
            _LOGGER.debug(f"Following redirection: {login_location}")
            response = await self.s.get(login_location,timeout=_TIMEOUT,follow_redirects=True)
        loan_details_response_header = response.headers
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code}") # response: {response.text}")
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
                    days_remaining = book.find('div', class_='my-library-user-library-account-loans__loan-days').text.strip()
                    days_remaining = int(days_remaining.lower().replace('nog ','').replace(' dagen','').replace(' dag',''))
                except (AttributeError,ValueError):
                    days_remaining = 0
                try:
                    extend_loan_id = book.find('div', class_='my-library-user-library-account-loans__extend-loan')
                    extend_loan_id = extend_loan_id.select_one('input[type="checkbox"]')['id']
                except (AttributeError, TypeError):
                    extend_loan_id = ""
                #example extension
                # https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1234567/uitleningen/verlengen?loan-ids=14870745%2C14871363%2C15549439%2C15707198%2C15933330%2C15938501%2C16370683%2C16490618%2C16584912%2C15468349%2C23001576%2C26583345
                loandetails[f"{title}{extend_loan_id}"] = {'title': title, 'author': author, 'loan_type': loan_type, 'url': url, 'image_src': image_src, 'days_remaining': days_remaining, 'loan_from': loan_from, 'loan_till': loan_till, 'extend_loan_id':extend_loan_id, 'library': libname, 'accountid': accountid}
        # _LOGGER.info(f"loandetails {loandetails}") 
        _LOGGER.debug(f"loandetails {json.dumps(loandetails,indent=4)}") 
        return loandetails
        

    #example extension url:
    # https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen/1234567/uitleningen/verlengen?loan-ids=14870745

    async def extend_multiple_ids(self, base_url, extend_loan_ids, execute):
        loandetails = dict()
        header = {"Content-Type": "application/json"}

        _LOGGER.debug(f"extend_multiple_ids URL {base_url}")
        
        extend_loan_ids_url = f"{base_url}/extend?loan-ids="
        num_id_found = 0
        
        for extend_loan_id in extend_loan_ids:
            if num_id_found == 0:
                extend_loan_ids_url += f"{extend_loan_id}"
            else:
                extend_loan_ids_url += f"%2C{extend_loan_id}"
            num_id_found += 1
        
        _LOGGER.debug(f"extend_multiple_ids extend_loan_ids: {extend_loan_ids_url}") 
        
        if num_id_found > 0 and execute:
            _LOGGER.debug(f"extend_loan_ids url: {extend_loan_ids_url}")
            await self._confirm_extension(extend_loan_ids_url, base_url)
        _LOGGER.info(f"extend_multiple_ids done for {num_id_found} items") 
        return num_id_found        
    
    async def _confirm_extension(self,url, base_url):
        header = {"Content-Type": "application/json"}
        _LOGGER.debug(f"confirm_extension extend_loan_ids url: {url}, base_url {base_url}")
        # response = await self.s.get(f"{url}",headers=header,timeout=_TIMEOUT,allow_redirects=False)
        response = await self.s.get(f"{url}",timeout=_TIMEOUT,follow_redirects=True)
        _LOGGER.debug(f"confirm_extension  result status code: {response.status_code} response: {response.text}")
        response = await self.s.get(f"{base_url}",timeout=_TIMEOUT,follow_redirects=True)
        _LOGGER.debug(f"confirm_extension  base_url result status code: {response.status_code} response: {response.text}")
        # assert response.status_code == 200
        #retrieve loan extension form token to confirm extension
        # soup = BeautifulSoup(response.text, 'html.parser')
        # div = soup.find('form', class_='my-library-extend-loan-form')
        # _LOGGER.debug(f"div my-library-extend-loan-form: {div}")
        # if div:
        #     input_fields = soup.find_all('input')
        #     data = {input_field.get('name'): input_field.get('value') for input_field in input_fields}
        #     header = {"Content-Type": "application/x-www-form-urlencoded"}
        #     _LOGGER.debug(f"confirm_extensionextend_loan_ids confirm data: {data} url: {url}")
        #     response = await self.s.post(f"{url}",headers=header,data=data,timeout=_TIMEOUT)
        #     _LOGGER.debug(f"confirm_extension confirmation result status code: {response.status_code} response: {response.text}")
        #     # assert response.status_code == 200
    



## NO LONGER NEEDED
    async def extend_all(self, url, max_days_remaining, execute):
        loandetails = dict()
        header = {"Content-Type": "application/json"}

        _LOGGER.debug(f"extend_all URL {url}")
        #lidmaatschap based on url in location of response received
        # response = self.s.get(f"{url}",headers=header,timeout=_TIMEOUT,allow_redirects=False)
        response = await self.s.get(f"{url}",timeout=_TIMEOUT)
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code} response: {response.text}")
        _LOGGER.debug(f"bibliotheek.be lidmaatschap get header: {response.headers}")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        
        extend_loan_ids = f"{url}/extend?loan-ids="
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
                    days_remaining = book.find('div', class_='my-library-user-library-account-loans__loan-days').text.strip()
                    days_remaining = int(days_remaining.lower().replace('nog ','').replace(' dagen','').replace(' dag',''))
                    if days_remaining > max_days_remaining:
                        continue
                except AttributeError:
                    days_remaining = ""
                try:
                    extend_loan_id = book.find('div', class_='my-library-user-library-account-loans__extend-loan')
                    extend_loan_id = extend_loan_id.select_one('input[type="checkbox"]')['id']
                    if num_id_found == 0:
                        extend_loan_ids += f"{extend_loan_id}"
                    else:
                        extend_loan_ids += f"%2C{extend_loan_id}"
                    num_id_found += 1
                except (AttributeError, TypeError):
                    extend_loan_id = ""
        
        _LOGGER.debug(f"extend_all extend_loan_ids: {extend_loan_ids}") 
        
        if execute and num_id_found > 0:
            _LOGGER.debug(f"extend_loan_ids url: {extend_loan_ids}")
            await self._confirm_extension(extend_loan_ids, url)
        _LOGGER.info(f"extend_all done for {num_id_found} items") 
        return num_id_found
    


# # #manual tests - enable debug logging

# _LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)
# if not logging.getLogger().hasHandlers():
#     logging.basicConfig(level=logging.DEBUG)
# _LOGGER.debug("Debug logging is now enabled.")

# hass = None

# async def test(hass):
#     session = ComponentSession(hass)

#     # #LOCAL TESTS

#     # _userdetails = session.login("username", "password")
#     print(_userdetails)
#     user_lists = session.user_lists()
#     print(user_lists)


#     for user_id, userdetail in _userdetails.items():
#         url = userdetail.get('loans').get('url')
#         if url:
#             _LOGGER.info(f"Calling loan details {userdetail.get('account_details').get('userName')}")
#             loandetails = session.loan_details(url)
#             # print(loandetails)

