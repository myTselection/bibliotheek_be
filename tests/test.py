import unittest
import requests
import logging
import json
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
# from "../custom_components/telenet_telemeter/utils" import .
# import sys
# sys.path.append('../custom_components/telenet_telemeter/')
# from utils import ComponentSession, dry_setup
# from sensor import *
from secret import USERNAME, PASSWORD

_LOGGER = logging.getLogger(__name__)

config = dict();
config["username"]: USERNAME
config["password"]: PASSWORD
hass = "test"
def async_add_devices(sensors): 
     _LOGGER.debug(f"session.userdetails {json.dumps(sensorsindent=4)}")

#run this test on command line with: python -m unittest test_component_session

logging.basicConfig(level=logging.DEBUG)

def login():
    s = requests.Session()
    s.headers["User-Agent"] = "Python/3"
    userdetails = dict()

    header = {"Content-Type": "application/json"}
    response = s.get("https://bibliotheek.be/mijn-bibliotheek/aanmelden",headers=header,timeout=10,allow_redirects=False)
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
    response = s.get(oauth_location,headers=header,timeout=10,allow_redirects=False)
    _LOGGER.debug(f"bibliotheek.be auth get result status code: {response.status_code}")
    _LOGGER.debug(f"bibliotheek.be auth get header: {response.headers}")
    assert response.status_code == 200
    
    # data = f"hint={hint}&token={oauth_token}&callback=https%3A%2F%2Fbibliotheek.be%2Fmy-library%2Flogin%2Fcallback&email={username}&password={password}"
    data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": USERNAME, "password": PASSWORD}
    #login
    #example header response: https://bibliotheek.be/my-library/login/callback?oauth_token=f68491752279e1a5c0a4ee9b6a349836&oauth_verifier=d369ffff4a5c4a05&uilang=nl
    response = s.post('https://mijn.bibliotheek.be/openbibid/rest/auth/login',headers=header,data=data,timeout=10,allow_redirects=False)
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
    response = s.get(login_location,headers=header,timeout=10,allow_redirects=False)
    login_callback_location = response.headers.get('location')
    _LOGGER.debug(f"bibliotheek.be login callback get result status code: {response.status_code}")
    _LOGGER.debug(f"bibliotheek.be login callback get header: {response.headers} text {response.text}")
    assert response.status_code == 302
    # if response.status_code == 302:        
    #     # request access code, https://mijn.bibliotheek.be/openbibid-api.html#_authenticatie
    #     data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
    #     response = s.post('https://mijn.bibliotheek.be/openbibid/rest/accessToken',headers=header,data=data,timeout=10,allow_redirects=False)
    #     _LOGGER.debug(f"bibliotheek.be login get result status code: {response.status_code}")
    # else:
    #     #login session was already available
    #     login_callback_location = "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen"
    login_callback_location = "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen"
    #lidmaatschap based on url in location of response received
    response = s.get(f"{login_callback_location}",headers=header,timeout=10,allow_redirects=False)
    lidmaatschap_response_header = response.headers
    _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code}") # response: {response.text}")
    _LOGGER.debug(f"bibliotheek.be lidmaatschap get header: {response.headers}")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')
    
    
    #find all accounts
    accounts = soup.find_all('div', class_='my-library-user-library-account-list__account')
    _LOGGER.debug(f"accounts found: {accounts}")


login()