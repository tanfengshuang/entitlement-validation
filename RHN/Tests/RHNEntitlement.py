import os
import unittest
import logging

from Utils import beaker_username
from Utils import beaker_password
from RHN import beaker_ip
from RHN import rhn
from RHN import variant
from RHN import arch
from RHN import manifest_url
from RHN import server_url
from RHN import account_rhn

from RHN.RHNParseManifestXML import RHNParseManifestXML
from RHN.RHNVerification import RHNVerification

def get_username_password():
    if rhn == "Live":
        return account_rhn["Live"]["username"], account_rhn["Live"]["password"]
    elif rhn == "QA":
        return account_rhn["QA"]["username"], account_rhn["QA"]["password"]

def get_server_url():
    if rhn == "QA":
        return server_url["QA"]
    else:
        return server_url["Live"]

class RHNEntitlement(unittest.TestCase):
    def setUp(self):
        RHNVerification().log_setting(variant, arch, rhn)
        logging.info("--------------- Begin Init ---------------")
        try:
            self.system_info = {
                "ip": beaker_ip,
                "username": beaker_username,
                "password": beaker_password
            }
            self.rhn = rhn
            self.variant = variant
            self.arch = arch

            self.manifest_url = manifest_url
            self.manifest_path = os.path.join(os.getcwd(), "manifest")
            self.manifest_json = os.path.join(self.manifest_path, "rhn_test_manifest.json")
            self.manifest_xml = os.path.join(self.manifest_path, "rhn_test_manifest.xml")

            self.username, self.password = get_username_password()
            self.server_url = get_server_url()

            self.current_rel_version = RHNVerification().get_os_release_version(self.system_info)
            self.current_arch = RHNVerification().get_os_base_arch(self.system_info)

            RHNParseManifestXML(self.manifest_url, self.manifest_path, self.manifest_json, self.manifest_xml).parse_json_to_xml()

            RHNVerification().remove_non_redhat_repo(self.system_info)
        except Exception, e:
            logging.error(str(e))
            logging.error("Test Failed - Raised error when do content testing!")
            exit(1)
        logging.info("--------------- End Init ---------------")

    def testRHNEntitlement(self):
        logging.info("--------------- Begin testRHNEntitlement --------------- ")
        testresult = True

        try:
            # Register
            testresult &= RHNVerification().register(self.system_info, self.username, self.password, self.server_url)

            # Get all testing channels
            channel_list = RHNVerification().get_channels_from_manifest(self.manifest_xml, self.current_arch, self.variant)

            if '6.5' in self.current_rel_version or "5" not in self.current_rel_version:
                testresult &= RHNVerification().verify_channels(self.system_info, self.manifest_xml, self.username, self.password, self.current_arch, self.variant)

            for channel in channel_list:
                if RHNVerification().add_channels(self.system_info, self.username, self.password, channel):
                    testresult &= RHNVerification().installation(self.system_info, self.manifest_xml, channel)
                    testresult &= RHNVerification().remove_channels(self.system_info, self.username, self.password, channel)

            if not testresult:
                logging.error("Test Failed - Failed to do main rhn content test.")
                exit(1)
        except Exception, e:
            logging.error(str(e))
            logging.error("Test Failed - Raised error when do RHN Entitlement testing!")
            exit(1)

        logging.info("--------------- End testRHNEntitlement --------------- ")

    def tearDown(self):
        logging.info("--------------- Begin tearDown ---------------")
        try:
            RHNVerification().unregister(self.system_info)
            RHNVerification().restore_non_redhat_repo(self.system_info)
        except Exception, e:
            logging.error(str(e))
            logging.error("Test Failed - Raised error when do RHN Entitlement testing!")
            exit(1)
        logging.info("--------------- End tearDown ---------------")

if __name__ == '__main__':
    unittest.main()