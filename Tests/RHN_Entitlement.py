import unittest

#from Utils.utils import *
from Utils.environment import *

class RHN_Entitlement(unittest.TestCase):

    def setUp(self):
        print "Setup..."
        self.beaker_ip = beaker_ip
        self.rhn = rhn
        self.manifest = manifest_url
        self.variant = variant
        self.username, self.password = self.__get_username_password(self.rhn)

        #self.current_rel_version = get_os_release_version(self.beaker_ip)
        #self.current_arch = get_os_base_arch(self.beaker_ip)

    def test_RHN_Entitlement(self):
        print "test_RHN_Entitlement"
        #register_rhn(self.beaker_ip, self.username, self.password)

    def __get_username_password(rhn):
        if rhn == "Live":
            return account_rhn["Live"]["username"], account_rhn["Live"]["password"]
        elif rhn == "QA":
            return account_rhn["Live"]["username"], account_rhn["Live"]["password"]

    def tearDown(self):
        print "tearDown..."

if __name__ == '__main__':
    unittest.main()