import unittest
import requests
import logging
import json
# from "../custom_components/bibliotheek_be/utils" import .
import sys
from secret import USERNAME, PASSWORD
sys.path.append('../custom_components/bibliotheek_be')
# from custom_components.bibliotheek_be import utils
from utils import ComponentSession
# from bibliotheek_be import utils


_LOGGER = logging.getLogger(__name__)

#run this test on command line with: python -m unittest test_component_session

logging.basicConfig(level=logging.DEBUG)
class TestComponentSession(unittest.TestCase):
    def setUp(self):
        self.session = ComponentSession()

    def test_login(self):
        # Test successful login
        self.session.login(USERNAME, PASSWORD)
        self.assertIsNotNone(self.session.userdetails)
        _LOGGER.debug(f"self.session.userdetails {json.dumps(self.session.userdetails,indent=4)}")
        # _LOGGER.debug(f"userdetails: {self.session.userdetails}")
        
        for id, userdetail in self.session.userdetails.items():
            # _LOGGER.info(f"userdetail: {userdetail}")
            url = userdetail.get('loans').get('url')
            _LOGGER.info(f"id {id}, userdetail: {self.session.userdetails}")
            _LOGGER.info(f"userdetail: {self.session.userdetails.get(id).get('account_details').get('barcode')}")
            
            if url:
                _LOGGER.info(f"calling loan details")
                loandetails = self.session.loan_details(url)
                _LOGGER.debug(f"loandetails {json.dumps(loandetails,indent=4)}") 
                self.assertIsNotNone(loandetails)
                
                _LOGGER.info(f"calling extend_all")
                num_extensions = self.session.extend_all(url, 1, False)
                _LOGGER.info(f"num of extensions found: {num_extensions}")
                
        # Test login failure
        self.session = ComponentSession()
        try:
            self.session.s = requests.Session() # reset session object
            self.assertEqual(self.session.userdetails,{})
        except AssertionError:
            self.assertEqual(self.session.userdetails,{})

    # def test_library_details(self):
    #     library_url = f"https://gent.bibliotheek.be/adres-en-openingsuren"
    #     self.session.library_details(library_url)

if __name__ == '__main__':
    unittest.main()