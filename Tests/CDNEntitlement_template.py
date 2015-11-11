import unittest

#from Utils.utils import *
from Utils.environment import *

class CDNEntitlement_PID(unittest.TestCase):

    def setUp(self):
        print "Setup..."
        self.beaker_ip = beaker_ip
        self.cdn = cdn
        self.manifest = manifest_url
        self.variant = variant
        self.username, self.password, self.sku = self.__get_username_password(self.cdn, self.pid)

        self.current_rel_version = get_os_release_version(self.beaker_ip)
        self.current_arch = get_os_base_arch(self.beaker_ip)

        #
        #remove_non_redhat_repo(self.beaker_ip)

    def testCDNEntitlement(self):
        print "test_CDN_Entitlement"
        #register(beaker_ip, self.username, self.password)

    def __get_username_password(cdn, pid):
        if cdn == "QA":
            return account_cdn_stage[pid]["username"], account_cdn_stage[pid]["password"], account_cdn_stage[pid]["sku"]
        elif cdn == "Prod":
            return account_cdn_prod["username"], account_cdn_prod["password"], account_cdn_prod["sku"][pid]

    def tearDown(self):
        print "tearDown..."
        #restore_non_redhat_repo(self.beaker_ip)

if __name__ == '__main__':
    unittest.main()