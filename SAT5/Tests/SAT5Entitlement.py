import os
import unittest
import traceback
import logging
import logging.config

from Utils import system_username
from Utils import system_password
from Utils import system_ip
from SAT5 import variant
from SAT5 import arch
from SAT5 import manifest_url
from SAT5 import sat5_server
from SAT5 import sat5_account

from SAT5.SAT5ParseManifestXML import SAT5ParseManifestXML
from SAT5.SAT5Verification import SAT5Verification


# Create logger
logger = logging.getLogger("entLogger")


def get_username_password():
    return sat5_account["username"], sat5_account["password"]


def get_server_url():
    return "https://" + sat5_server + "/XMLRPC"


class SAT5Entitlement(unittest.TestCase):
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
                "ip": system_ip,
                "username": system_username,
                "password": system_password
            }

            # Get username, password and serverUrl
            self.sat5_server = sat5_server
            self.username, self.password = get_username_password()
            self.server_url = get_server_url()

            # Get testing variant and arch
            self.variant = variant
            self.arch = arch

            # Get manifest url, set json and xml manifest local path
            self.manifest_url = manifest_url
            self.manifest_path = os.path.join(os.getcwd(), "manifest")
            self.manifest_json = os.path.join(self.manifest_path, "sat5_test_manifest.json")
            self.manifest_xml = os.path.join(self.manifest_path, "sat5_test_manifest.xml")

            # Download certificate from SAT5 Server
            result = SAT5Verification().download_cert(self.system_info, self.sat5_server)
            self.assertTrue(result, msg="Test Failed - Failed to download certificate from SAT5 Server!")

            # Update sslCACert and serverUrl in file up2date on SAT5 Server
            result = SAT5Verification().update_up2date(self.system_info, self.server_url)
            self.assertTrue(result, msg="Test Failed - Failed to set sslCACert or sslServerUrl in up2date file!")

            # Get system release version and arch
            self.current_rel_version = SAT5Verification().get_os_release_version(self.system_info)
            self.current_arch = SAT5Verification().get_os_base_arch(self.system_info)

            # Download and parse manifest
            SAT5ParseManifestXML(self.manifest_url, self.manifest_path, self.manifest_json, self.manifest_xml).parse_json_to_xml()

            # Remove non-redhat.repo
            SAT5Verification().remove_non_redhat_repo(self.system_info)

            # Generate file polarion.prop for Polarion case properties to create run automatically
            SAT5Verification().copy_polarion_props(self.system_info)

            # Space extend
            SAT5Verification().extend_system_space(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when setup environment before SAT5 Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End Init ---------------")

    def testSAT5Entitlement_VARIANT_ARCH(self):
        logger.info("--------------- Begin testSAT5Entitlement --------------- ")

        try:
            # Register
            result = SAT5Verification().register(self.system_info, self.username, self.password, self.server_url)
            self.assertTrue(result, msg="Test Failed - Failed to Register with SAT5 server!")

            # Get and print all testing channels
            # If 0 channel, exit
            channel_list = SAT5Verification().get_channels_from_manifest(self.manifest_xml, self.current_arch, self.variant)
            self.assertNotEqual(channel_list, [], msg="Test Failed - There is no any channel.")

            if '6.5' in self.current_rel_version or "5" not in self.current_rel_version:
                result = SAT5Verification().verify_channels(self.system_info, self.manifest_xml, self.username, self.password, self.current_arch, self.variant)
                self.assertTrue(result, msg="Test Failed - Failed to verify channels!")

            # Add base channel, such as rhel-x86_64-server-6
            master_release = SAT5Verification().get_master_release(self.system_info)
            base_channel = "rhel-{0}-{1}-{2}".format(self.arch, self.variant.lower(), master_release)
            result = SAT5Verification().add_channels(self.system_info, self.username, self.password, base_channel)
            self.assertTrue(result, msg="Test Failed - Failed to add base channel {0}!".format(base_channel))

            test_result = True
            for channel in channel_list:
                # Add test channel
                if channel != base_channel:
                    result = SAT5Verification().add_channels(self.system_info, self.username, self.password, channel)
                    if not result:
                        logger.error("Test Failed - Failed to add test channel {0}".format(channel))
                        test_result &= result
                        continue
                # Installation testing
                test_result &= SAT5Verification().installation(self.system_info, self.manifest_xml, channel)
                # Remove test channel
                if channel != base_channel:
                    test_result &= SAT5Verification().remove_channels(self.system_info, self.username, self.password, channel)

            self.assertTrue(test_result, msg="Test Failed - Failed to do SAT5 Entitlement testing!")
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when do SAT5 Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End testSAT5Entitlement --------------- ")

    def tearDown(self):
        logger.info("--------------- Begin tearDown ---------------")
        try:
            # Unregister
            SAT5Verification().unregister(self.system_info)

            # Restore non-redhat.repo
            #SAT5Verification().restore_non_redhat_repo(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when tear down after SAT5 Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End tearDown ---------------")


if __name__ == '__main__':
    unittest.main()