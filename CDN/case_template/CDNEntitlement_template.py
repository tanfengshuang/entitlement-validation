import os
import unittest
import logging
import traceback

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

"""
import logging.config
# Set our logging config file
log_path = os.path.join(os.getcwd(), "log/{0}/".format(pid))
if not os.path.exists(log_path):
    os.makedirs(log_path)
logging_conf_file = "{0}/logging.conf".format(os.getcwd())
logging.config.fileConfig(logging_conf_file, defaults={'logfilepath': log_path})

# Create logger
logger = logging.getLogger("entLogger")
"""

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_username_password():
    if cdn == "QA":
        if pid in account_cdn_stage.keys():
            return account_cdn_stage[pid]["username"], account_cdn_stage[pid]["password"], account_cdn_stage[pid]["sku"], account_cdn_stage[pid]["base_sku"], account_cdn_stage[pid]["base_pid"]
        else:
            logger.error("Test Failed - Failed to get PID {0} in account_cdn_stage.".format(pid))
            exit(1)
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
        self.file_handler_debug, self.file_handler_info, self.file_handler_error, self.console_handler = CDNVerification().log_setting(variant, arch, cdn, pid)
        logger.addHandler(self.file_handler_debug)
        logger.addHandler(self.file_handler_info)
        logger.addHandler(self.file_handler_error)
        logger.addHandler(self.console_handler)
        logger.info("--------------- Begin Init for product {0} ---------------".format(pid))
        try:
            self.system_info = {
                "ip": beaker_ip,
                "username": beaker_username,
                "password": beaker_password
            }

            self.release_ver = release_ver
            self.blacklist = blacklist
            self.variant = variant
            self.arch = arch

            # Download and parse manifest
            self.manifest_url = manifest_url
            self.manifest_path = os.path.join(os.getcwd(), "manifest")
            self.manifest_json = os.path.join(self.manifest_path, "cdn_test_manifest.json")
            self.manifest_xml = os.path.join(self.manifest_path, "cdn_test_manifest.xml")

            self.pid = pid
            self.username, self.password, self.sku, self.base_sku, self.base_pid = get_username_password()

            self.hostname = get_hostname()
            self.baseurl = get_baseurl()
            CDNVerification().config_testing_environment(self.system_info, self.hostname, self.baseurl)

            self.current_release_ver = CDNVerification().get_os_release_version(self.system_info)
            self.current_arch = CDNVerification().get_os_base_arch(self.system_info)
            if self.release_ver == "":
                self.release_ver = self.current_release_ver

            # Stop rhcertd service. As headling(autosubscribe) operation will be run every 2 mins after start up system,
            # then every 24 hours after that, which will influence our subscribe test.
            CDNVerification().stop_rhsmcertd(self.system_info)

            # Stop service yum-updatesd on RHEL5 in order to avoid yum lock to save testing time
            CDNVerification().stop_yum_updatesd(self.system_info)

            # Synchronize system time with clock.redhat.com, it's a workaround when system time is not correct,
            # commands "yum repolist" and "subscription-manager repos --list" return nothing
            CDNVerification().ntpdate_redhat_clock(self.system_info)

            CDNParseManifestXML(self.manifest_url, self.manifest_path, self.manifest_json, self.manifest_xml).parse_json_to_xml()

            # Remove
            CDNVerification().remove_non_redhat_repo(self.system_info)

            # Space extend
            CDNVerification().extend_system_space(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            logger.error("Test Failed - Raised error when do CDN Entitlement testing!")
            exit(1)
        logger.info("--------------- End Init for product {0} ---------------".format(pid))

    def testCDNEntitlement_VARIANT_ARCH_PID(self):
        logger.info("--------------- Begin testCDNEntitlement for product {0} ---------------".format(pid))
        test_result = True
        try:
            # Register
            test_result &= CDNVerification().register(self.system_info, self.username, self.password)

            # Get subscription list
            sku_pool_dict = {}
            if self.current_arch == 'i386' and self.pid in ["92", "94", "132", "146"]:
                # Products SF, SAP, HPN are not supported on i386, and keep them pass currently.
                logger.info("Product {0} could not be supported on arch i386.".format(self.pid))
                exit(0)
            else:
                sku_pool_dict = CDNVerification().get_sku_pool(self.system_info)
                logger.info("sku_pool_dict:")
                CDNVerification().print_list(sku_pool_dict)
                # sku_pool_dict:
                # {
                # 'MCT3115': ['8a99f984508e9fbf01509432f2e9054c'],
                # 'RH0103708': ['8a99f9865154360c015156e8a8250f6e', '8a99f9865154360c015156e8a7c20f57'],
                # 'RH00284': ['8a99f984508e9fbf01509432f3b80561']
                # }

            # Try to subscribe layered product, and then check the sku in the entitlement cert
            if self.sku in sku_pool_dict.keys():
                test_result &= CDNVerification().subscribe(self.system_info, self.pid, self.sku, sku_pool_dict[self.sku][0])
            else:
                logger.error("No suitable subscription for sku {0}".format(self.sku))
                exit(1)

            # Try to subscribe base product, and then check the sku in the entitlement cert
            if self.base_sku != self.sku:
                if self.base_sku in sku_pool_dict.keys():
                    test_result &= CDNVerification().subscribe(self.system_info, self.base_pid, self.base_sku, sku_pool_dict[self.base_sku][0])
                else:
                    logger.error("No suitable subscription for base sku {0}".format(self.base_sku))
                    exit(1)

            # Backup /etc/yum.repos.d/redhat.repo to /tmp/redhat.repo, and archive it in Jenkins job
            CDNVerification().redhat_repo_backup(self.system_info)

            # Set system release
            releasever_set = ""
            if self.release_ver != self.current_release_ver:
                releasever_set = CDNVerification().set_release(self.system_info, self.release_ver)

            # Clear yum cache
            test_result &= CDNVerification().clean_yum_cache(self.system_info, releasever_set)

            # Get repo list from package manifest
            repo_list = CDNVerification().get_repo_list_from_manifest(self.manifest_xml, self.pid, self.current_arch, self.release_ver)

            # Enable all test repos listed in manifest to ensure the correctness
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

        except Exception, e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            logger.error("Test Failed - Raised error when do CDN Entitlement testing!")
            exit(1)

        self.assertTrue(test_result)
        logger.info("--------------- End testCDNEntitlement for product {0} ---------------".format(pid))

    def tearDown(self):
        logger.info("--------------- Begin tearDown for product {0} ---------------".format(pid))

        try:
            CDNVerification().unregister(self.system_info)
            CDNVerification().restore_non_redhat_repo(self.system_info)
        except Exception, e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            logger.error("Test Failed - Raised error when do CDN Entitlement testing!")
            exit(1)
        logger.info("--------------- End tearDown for product {0} ---------------".format(pid))

        # Remove log handlers from current logger
        logger.removeHandler(self.file_handler_debug)
        logger.removeHandler(self.file_handler_info)
        logger.removeHandler(self.file_handler_error)
        logger.removeHandler(self.console_handler)

if __name__ == '__main__':
    unittest.main()
