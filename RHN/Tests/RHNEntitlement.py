import os
import unittest
import traceback
import logging
import logging.config

from Utils import beaker_username
from Utils import beaker_password
from Utils import beaker_ip
from RHN import rhn
from RHN import variant
from RHN import arch
from RHN import manifest_url
from RHN import server_url
from RHN import account_rhn

from RHN.RHNParseManifestXML import RHNParseManifestXML
from RHN.RHNVerification import RHNVerification


# Create logger
logger = logging.getLogger("entLogger")


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
        # Set logging config file
        log_path = os.path.join(os.getcwd(), "log")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        logging_conf_file = "{0}/logging.conf".format(os.getcwd())
        logging.config.fileConfig(logging_conf_file, defaults={'logfilepath': log_path})

        logger.info("--------------- Begin Init ---------------")
        try:
            # Get ip, username and password of beaker testing system
            self.system_info = {
                "ip": beaker_ip,
                "username": beaker_username,
                "password": beaker_password
            }

            # Get testing params passed by Jenkins
            self.rhn = rhn
            self.variant = variant
            self.arch = arch

            # Get manifest url, set json and xml manifest local path
            self.manifest_url = manifest_url
            self.manifest_path = os.path.join(os.getcwd(), "manifest")
            self.manifest_json = os.path.join(self.manifest_path, "rhn_test_manifest.json")
            self.manifest_xml = os.path.join(self.manifest_path, "rhn_test_manifest.xml")

            # Get username, password and serverUrl
            self.username, self.password = get_username_password()
            self.server_url = get_server_url()

            # Get system release version and arch
            self.current_rel_version = RHNVerification().get_os_release_version(self.system_info)
            self.current_arch = RHNVerification().get_os_base_arch(self.system_info)

            # Download and parse manifest
            RHNParseManifestXML(self.manifest_url, self.manifest_path, self.manifest_json, self.manifest_xml).parse_json_to_xml()

            # Remove non-redhat.repo
            RHNVerification().remove_non_redhat_repo(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when setup environment before RHN Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End Init ---------------")

    def testRHNEntitlement_VARIANT_ARCH(self):
        logger.info("--------------- Begin testRHNEntitlement --------------- ")

        try:
            # Register
            result = RHNVerification().register(self.system_info, self.username, self.password, self.server_url)
            self.assertTrue(result, msg="Test Failed - Failed to Register with RHN server!")

            # Get and print all testing channels
            # If 0 channel, exit
            channel_list = RHNVerification().get_channels_from_manifest(self.manifest_xml, self.current_arch, self.variant)
            self.assertNotEqual(channel_list, [], msg="Test Failed - There is no any channel.")

            if '6.5' in self.current_rel_version or "5" not in self.current_rel_version:
                result = RHNVerification().verify_channels(self.system_info, self.manifest_xml, self.username, self.password, self.current_arch, self.variant)
                self.assertTrue(result, msg="Test Failed - Failed to verify channels!")

            # Add base channel, such as rhel-x86_64-server-6
            master_release = RHNVerification().get_master_release(self.system_info)
            base_channel = "rhel-{0}-{1}-{2}".format(self.arch, self.variant, master_release)
            result = RHNVerification().add_channels(self.system_info, self.username, self.password, base_channel)
            self.assertTrue(result, msg="Test Failed - Failed to add base channel {0}!".format(base_channel))

            test_result = True
            for channel in channel_list:
                # Add test channel
                if channel != base_channel:
                    result = RHNVerification().add_channels(self.system_info, self.username, self.password, channel)
                    if not result:
                        logger.error("Test Failed - Failed to add test channel {0}".format(channel))
                        test_result &= result
                        continue
                # Installation testing
                test_result &= RHNVerification().installation(self.system_info, self.manifest_xml, channel)
                # Remove test channel
                if channel != base_channel:
                    test_result &= RHNVerification().remove_channels(self.system_info, self.username, self.password, channel)

            self.assertTrue(test_result, msg="Test Failed - Failed to do RHN Entitlement testing!")
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when do RHN Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End testRHNEntitlement --------------- ")

    def tearDown(self):
        logger.info("--------------- Begin tearDown ---------------")
        try:
            # Unregister
            RHNVerification().unregister(self.system_info)

            # Restore non-redhat.repo
            RHNVerification().restore_non_redhat_repo(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when tear down after RHN Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End tearDown ---------------")


if __name__ == '__main__':
    unittest.main()