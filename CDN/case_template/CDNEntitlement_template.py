import os
import unittest
import traceback
import logging
import logging.config

from Utils import beaker_username
from Utils import beaker_password
from CDN import beaker_ip
from CDN import cdn
from CDN import release_ver
from CDN import blacklist
from CDN import variant
from CDN import arch
from CDN import manifest_url
from CDN import candlepin

from CDN import account_cdn_stage
from CDN import account_cdn_prod

from CDN.CDNParseManifestXML import CDNParseManifestXML
from CDN.CDNVerification import CDNVerification


pid = "PID"

# Create logger
logger = logging.getLogger("entLogger")


def get_username_password():
    if cdn == "QA":
        if pid in account_cdn_stage.keys():
            return account_cdn_stage[pid]["username"], account_cdn_stage[pid]["password"], account_cdn_stage[pid]["sku"], account_cdn_stage[pid]["base_sku"], account_cdn_stage[pid]["base_pid"]
        else:
            assert False, "Failed to get PID {0} in account_cdn_stage.".format(pid)
    elif cdn == "Prod":
        return account_cdn_prod["username"], account_cdn_prod["password"], account_cdn_prod[pid]["sku"], account_cdn_prod[pid]["base_sku"], account_cdn_prod[pid]["base_pid"]

def get_hostname():
    if cdn == "QA":
        hostname = "subscription.rhn.stage.redhat.com"
    else:
        hostname = "subscription.rhn.redhat.com"
    return hostname

def get_baseurl():
    if candlepin == "QA":
        baseurl = "https://cdn.qa.redhat.com"
    else:
        baseurl = "https://cdn.redhat.com"
    return baseurl


class CDNEntitlement_PID(unittest.TestCase):
    def setUp(self):
        # Set our logging config file
        log_path = os.path.join(os.getcwd(), "log/{0}".format(pid))
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        logging_conf_file = "{0}/logging.conf".format(os.getcwd())
        logging.config.fileConfig(logging_conf_file, defaults={'logfilepath': log_path})

        """
        #logger = logging.getLogger()
        #logger.setLevel(logging.DEBUG)
        self.file_handler_debug, self.file_handler_info, self.file_handler_error, self.console_handler = CDNVerification().log_setting(variant, arch, cdn, pid)
        logger.addHandler(self.file_handler_debug)
        logger.addHandler(self.file_handler_info)
        logger.addHandler(self.file_handler_error)
        logger.addHandler(self.console_handler)
        """
        logger.info("--------------- Begin Init for product {0} ---------------".format(pid))
        try:
            # Get ip, username and password of beaker testing system
            self.system_info = {
                "ip": beaker_ip,
                "username": beaker_username,
                "password": beaker_password
            }

            # Get testing params passed by Jenkins
            self.release_ver = release_ver
            self.blacklist = blacklist
            self.variant = variant
            self.arch = arch

            # Get manifest url, set json and xml manifest local path
            self.manifest_url = manifest_url
            self.manifest_path = os.path.join(os.getcwd(), "manifest")
            self.manifest_json = os.path.join(self.manifest_path, "cdn_test_manifest.json")
            self.manifest_xml = os.path.join(self.manifest_path, "cdn_test_manifest.xml")

            # Get pid, base pid, sku, base sku, username, password
            self.pid = pid
            self.username, self.password, self.sku, self.base_sku, self.base_pid = get_username_password()

            # Config hostname and baseurl in /etc/rhsm/rhsm.conf
            self.hostname = get_hostname()
            self.baseurl = get_baseurl()
            CDNVerification().config_testing_environment(self.system_info, self.hostname, self.baseurl)

            # Get system release version and arch
            self.current_release_ver = CDNVerification().get_os_release_version(self.system_info)
            self.current_arch = CDNVerification().get_os_base_arch(self.system_info)
            if self.release_ver == "":
                self.release_ver = self.current_release_ver

            # Stop rhcertd service. As headling(autosubscribe) operation will be run every 2 mins after start up system,
            # then every 24 hours after that, which will influence our subscribe test.
            CDNVerification().stop_rhsmcertd(self.system_info)

            # Stop service yum-updatesd on RHEL5 in order to avoid yum lock to save testing time
            # Need to investigate it on RHEL6 and RHEL7
            CDNVerification().stop_yum_updatesd(self.system_info)

            # Synchronize system time with clock.redhat.com, it's a workaround when system time is not correct,
            # commands "yum repolist" and "subscription-manager repos --list" return nothing
            CDNVerification().ntpdate_redhat_clock(self.system_info)

            # Download and parse manifest
            CDNParseManifestXML(self.manifest_url, self.manifest_path, self.manifest_json, self.manifest_xml).parse_json_to_xml()

            # Remove non-redhat.repo
            CDNVerification().remove_non_redhat_repo(self.system_info)

            # Space extend
            CDNVerification().extend_system_space(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when do CDN Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End Init for product {0} ---------------".format(pid))

    def testCDNEntitlement_VARIANT_ARCH_PID(self):
        logger.info("--------------- Begin testCDNEntitlement for product {0} ---------------".format(pid))
        test_result = True
        try:
            # Register
            result = CDNVerification().register(self.system_info, self.username, self.password)
            self.assertTrue(result, msg="Test Failed - Failed to Register with CDN server!")

            # Get subscription list
            sku_pool_dict = {}
            if self.current_arch == 'i386' and self.pid in ["92", "94", "132", "146"]:
                # Products SF, SAP, HPN are not supported on i386, and keep them pass currently.
                logger.info("Product {0} could not be supported on arch i386.".format(self.pid))
                return
            else:
                sku_pool_dict = CDNVerification().get_sku_pool(self.system_info)
                self.assertNotEqual(sku_pool_dict, {}, msg="Test Failed - Failed to get subscription pool list!")
                logger.info("Subsciption pool list:")
                CDNVerification().print_list(sku_pool_dict)
                # sku_pool_dict:
                # {
                # 'MCT3115': ['8a99f984508e9fbf01509432f2e9054c'],
                # 'RH0103708': ['8a99f9865154360c015156e8a8250f6e', '8a99f9865154360c015156e8a7c20f57'],
                # 'RH00284': ['8a99f984508e9fbf01509432f3b80561']
                # }

            # Try to subscribe layered product, and then check the sku and pid in the entitlement cert
            if self.sku in sku_pool_dict.keys():
                result, entitlement_cert = CDNVerification().subscribe(self.system_info, sku_pool_dict[self.sku][0])
                self.assertTrue(result, msg="Test Failed - Failed to Subscribe with sku {0}!".format(self.sku))
                if len(entitlement_cert) != 0:
                    result &= CDNVerification().verify_productid_in_entitlement_cert(self.system_info, entitlement_cert[0], self.pid)
                    result &= CDNVerification().verify_sku_in_entitlement_cert(self.system_info, entitlement_cert[0], self.sku)
                else:
                    test_result = False
                    logging.error("Test Failed - Failed to generate entitlement certificate after subscribe sku {0}".format(self.sku))
            else:
                self.assertTrue(False, "No suitable subscription for sku {0}".format(self.sku))

            # Try to subscribe base product, and then check the sku and pid in the entitlement cert
            if self.base_sku != self.sku:
                if self.base_sku in sku_pool_dict.keys():
                    result, entitlement_cert = CDNVerification().subscribe(self.system_info, sku_pool_dict[self.base_sku][0])
                    self.assertTrue(result, msg="Test Failed - Failed to Subscribe with base sku {0}!".format(self.base_sku))
                    if len(entitlement_cert) != 0:
                        result &= CDNVerification().verify_productid_in_entitlement_cert(self.system_info, entitlement_cert[0], self.base_pid)
                        result &= CDNVerification().verify_sku_in_entitlement_cert(self.system_info, entitlement_cert[0], self.base_sku)
                    else:
                        test_result = False
                        logging.error("Test Failed - Failed to generate entitlement certificate after subscribe base sku {0}".format(self.base_sku))
                else:
                    self.assertTrue(False, "No suitable subscription for base sku  {0}".format(self.base_sku))

            # Backup /etc/yum.repos.d/redhat.repo, and archive it in Jenkins job
            CDNVerification().redhat_repo_backup(self.system_info)

            # Set system release
            releasever_set = ""
            if self.release_ver != self.current_release_ver:
                releasever_set = CDNVerification().set_release(self.system_info, self.release_ver)
                self.assertNotEqual(releasever_set, False, msg="Test Failed - Failed to set system release!")

            # Clear yum cache
            test_result &= CDNVerification().clean_yum_cache(self.system_info, releasever_set)

            # Get and print repo list from package manifest
            # If 0 repo, exit
            repo_list = CDNVerification().get_repo_list_from_manifest(self.manifest_xml, self.pid, self.current_arch, self.release_ver)
            self.assertNotEqual(repo_list, [], msg="Test Failed - There is no any repository for pid {0} in release {1}.".format(self.pid, self.release_ver))

            # Enable all test repos listed in manifest to ensure the repo correctness
            test_result &= CDNVerification().test_repos(self.system_info, repo_list, self.blacklist, releasever_set, self.release_ver, self.current_arch)

            # Change gpgkey for all testrepos for rhel snapshot testing against qa cdn
            if self.blacklist == 'GA':
                # NOTICE: it's very dangerous if it's tested on Prod CDN, think about it...
                test_result &= CDNVerification().change_gpgkey(self.system_info, repo_list)

            for repo in repo_list:
                # Enable the test repo
                test_result &= CDNVerification().enable_repo(self.system_info, repo)

                # Product id certificate installation
                test_result &= CDNVerification().pid_cert_installation(self.system_info, repo, releasever_set, self.blacklist, self.manifest_xml, self.pid, self.base_pid, self.current_arch, self.release_ver)

                # All package installation
                test_result &= CDNVerification().verify_all_packages_installation(self.system_info, self.manifest_xml, self.pid, repo, self.arch, self.release_ver, releasever_set, self.blacklist)

                # Disable the test repo
                test_result &= CDNVerification().disable_repo(self.system_info, repo)

            self.assertTrue(test_result, msg="Test Failed - Failed to do CDN Entitlement testing!")
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when do CDN Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End testCDNEntitlement for product {0} ---------------".format(pid))

    def tearDown(self):
        logger.info("--------------- Begin tearDown for product {0} ---------------".format(pid))

        try:
            # Unregister
            CDNVerification().unregister(self.system_info)

            # Restore non-redhat.repo
            CDNVerification().restore_non_redhat_repo(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error("Test Failed - Raised error when do CDN Entitlement testing!")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info("--------------- End tearDown for product {0} ---------------".format(pid))

        """
        # Remove log handlers from current logger
        logger.removeHandler(self.file_handler_debug)
        logger.removeHandler(self.file_handler_info)
        logger.removeHandler(self.file_handler_error)
        logger.removeHandler(self.console_handler)
        """

if __name__ == '__main__':
    unittest.main()
