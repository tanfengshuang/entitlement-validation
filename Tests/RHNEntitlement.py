import os
import unittest
import logging

from Utils.ParseManifestXML import RHNParseManifestXML
from Utils.RHNVerification import RHNVerification
from Utils.environment import *

class RHNEntitlement(unittest.TestCase):
    def setUp(self):
        logging.info("--------------- Begin Init ---------------")
        try:
            self.beaker_ip = beaker_ip
            self.beaker_username = beaker_username
            self.beaker_password = beaker_password
            self.system_info = {
                "ip": beaker_ip,
                "username": beaker_username,
                "password": beaker_password
            }
            self.rhn = rhn
            self.variant = variant
            self.arch = arch
            self.manifest_url = manifest_url
            self.manifest_json = os.path.join(os.getcwd(), "entitlement-validation/manifest/rhn_test_manifest.json")
            self.manifest_xml = os.path.join(os.getcwd(), "entitlement-validation/manifest/rhn_test_manifest.xml")

            self.username, self.password = self.__get_username_password()
            self.server_url = self.__get_server_url()

            self.current_rel_version = RHNVerification().get_os_release_version(self.system_info)
            self.current_arch = RHNVerification().get_os_base_arch(self.system_info)

            RHNParseManifestXML(self.manifest_url, self.manifest_json, self.manifest_xml).parse_json_to_xml()

            RHNVerification().remove_non_redhat_repo(self.system_info)
        except Exception, e:
            logging.error(str(e))
            logging.error("Test Failed - error happened when do content testing!")
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
            logging.error("Test Failed - error happened when do content testing!")
            exit(1)

        logging.info("--------------- End testRHNEntitlement --------------- ")

    def __get_username_password(self):
        if self.rhn == "Live":
            return account_rhn["Live"]["username"], account_rhn["Live"]["password"]
        elif self.rhn == "QA":
            return account_rhn["QA"]["username"], account_rhn["QA"]["password"]

    def __get_server_url(self):
        if self.rhn == "QA":
            return server_url["QA"]
        else:
            return server_url["Live"]

    def tearDown(self):
        logging.info("--------------- Begin tearDown ---------------")
        try:
            RHNVerification().unregister(self.system_info)
            RHNVerification().restore_non_redhat_repo(self.system_info)
        except Exception, e:
            logging.error(str(e))
            logging.error("Test Failed - error happened when do content testing!")
            exit(1)
        logging.info("--------------- End tearDown ---------------")

if __name__ == '__main__':
    unittest.main()