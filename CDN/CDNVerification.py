import os
import time
import random
import logging
import ConfigParser

from Utils.RemoteSHH import RemoteSHH
from Utils.EntitlementBase import EntitlementBase
from CDN.CDNReadXML import CDNReadXML

class CDNVerification(EntitlementBase):
    def __init__(self):
        pass

    def redhat_repo_backup(self, system_info):
        # Get content of file redhat.repo on guest and prepare it on host
        ret, output = RemoteSHH().run_cmd(system_info, "cat /etc/yum.repos.d/redhat.repo", "Trying to backup the content of /etc/yum.repos.d/redhat.repo content...")
        repo_file = "/tmp/redhat.repo"
        with open(repo_file, 'w') as f:
            f.write(output)

    def stop_rhsmcertd(self, system_info):
        # Stop rhsmcertd because healing(autosubscribe) will run 2 mins after the machine is started, then every 24
        # hours after that, which will influence our content test.
        cmd = 'service rhsmcertd status'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get status of service rhsmcertd...")
        if 'stopped' in output or 'Stopped' in output:
            return

        cmd = 'service rhsmcertd stop'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to stop service rhsmcertd...")
        if ret == 0:
            cmd = 'service rhsmcertd status'
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get status of service rhsmcertd...")
            if 'stopped' in output or 'Stopped' in output:
                logging.info("It's successful to stop rhsmcertd service.")
            else:
                logging.error("Failed to stop rhsmcertd service.")
        else:
            logging.error("Failed to stop rhsmcertd service.")

    def stop_yum_updatesd(self, system_info, current_rel_version):
        # Stop the yum_updatesd service in RHEL5.9 in order to avoid the yum lock issue
        if "5" in current_rel_version and ".5" not in current_rel_version:
            cmd = 'service yum-updatesd status'
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get status of service yum-updatesd...")
            if 'stopped' in output or "yum-updatesd: unrecognized service" in output:
                return

            cmd = 'service yum-updatesd stop'
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to stop yum-updatesd service...")
            if ret == 0:
                cmd = 'service yum-updatesd status'
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get status of service yum-updatesd...")
                if 'stopped' in output:
                        logging.info("It's successful to stop yum-updatesd service.")
                else:
                    logging.error("Failed to stop yum-updatesd service.")
            else:
                logging.error("Failed to stop yum-updatesd service.")

    def ntpdate_redhat_clock(self, system_info):
        # ntpdate clock of redhat.com as a workaround for time of some systems are not correct, which will result in no
        # info dislaying with "yum repolist" or "s-m repos --list"
        cmd = 'ntpdate clock.redhat.com'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to ntpdate system time with clock of redhat.com...")
        print output
        if ret == 0 or "the NTP socket is in use, exiting" in output:
            logging.info("It's successful to ntpdate system time with clock of redhat.com.")
        else:
            logging.error("Test Failed - Failed to ntpdate system time with clock of redhat.com.")
            exit(1)

    def config_testing_environment(self, system_info, hostname, baseurl):

        cmd = "subscription-manager config --server.hostname={0}".format(hostname)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to set hostname in /etc/rhsm/rhsm.conf...")

        cmd = "subscription-manager config --rhsm.baseurl={0}".format(baseurl)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to set baseurl in /etc/rhsm/rhsm.conf...")


    def check_registered(self, system_info):
        cmd = "subscription-manager identity"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check if registered with cdn server...")
        if ret == 0:
            logging.info("The system is registered with cdn server now.")
            return True
        else:
            logging.info("The system is not registered with cdn server now.")
            return False

    def unregister(self, system_info):
        if self.check_registered(system_info):
            cmd = "subscription-manager unregister"
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to unregister...")

            if ret == 0:
                if ("System has been unregistered." in output) or ("System has been un-registered." in output):
                        logging.info("It's successful to unregister.")
                else:
                    logging.error("Test Failed - The information shown after unregistered is not correct.")
                    exit(1)
            else:
                logging.error("Test Failed - Failed to unregister.")
                exit(1)
        else:
            logging.info("The system is not registered with cdn server now.")

    def register(self, system_info, username, password, subtype=""):
        if subtype == "":
            cmd = "subscription-manager register --username={0} --password='{1}'".format(username, password)
        else:
            cmd = "subscription-manager register --type={0} --username={1} --password='{2}'".format(subtype, username, password)

        if self.check_registered(system_info):
            logging.info("The system is already registered, need to unregister first!")
            cmd_unregister = "subscription-manager unregister"
            ret, output = RemoteSHH().run_cmd(system_info, cmd_unregister, "Trying to unregister cdn server firstly...")

            if ret == 0:
                if "System has been unregistered." in output or "System has been un-registered." in output:
                    logging.info("It's successful to unregister.")
                else:
                    logging.info("The system is failed to unregister, try to use '--force'!")
                    cmd += " --force"

        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to register cdn server...")
        if ret == 0:
            if "The system has been registered with ID:" in output or "The system has been registered with id:" in output:
                logging.info("It's successful to register.")
                return True
            else:
                logging.error("Test Failed - The information shown after registered is not correct.")
                exit(1)
        else:
            logging.error("Test Failed - Failed to register.")
            exit(1)


    def check_subscription(self, system_info, sku):
        cmd = "subscription-manager list --available --all | grep {0}".format(sku)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list sbuscription {0}...".format(sku))
        if ret == 0 and sku in output:
            logging.info("It's successful to get sku {0} in available list.".format(sku))
            return True
        else:
            logging.info("Test Failed - Failed to get sku {0} in available list.".format(sku))
            return False

    def get_sku_pool(self, system_info):
        # Get available entitlement pools
        time.sleep(5)
        cmd = "subscription-manager  list --avail --all| egrep 'SKU|Pool ID' | grep -v Subscription"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list all available SKU and Pool ID...")

        if ret == 0:
            if output != "":
                sku_pool_dict = {}
                i = 0
                sku = ""
                for line in output.splitlines():
                    if line != "":
                        if i % 2 == 0:
                            sku = line.split(":")[1].strip()
                        if i % 2 != 0:
                            pool = line.split(":")[1].strip()
                            if i != 0:
                                if sku in sku_pool_dict.keys():
                                    sku_pool_dict[sku].append(pool)
                                else:
                                    sku_pool_dict[sku] = [pool]
                        i += 1
                return sku_pool_dict
            else:
                logging.error("No suitable pools!")
                logging.error("Test Failed - Failed to get available pools.")
                exit(1)
        else:
            logging.error("Test Failed - Failed to get available pools.")
            exit(1)

    def subscribe_pool(self, system_info, poolid):
        cmd = "subscription-manager subscribe --pool={0}".format(poolid)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to subscribe with poolid {0}".format(poolid))

        if ret == 0:
            # Note: the exact output should be as below:
            # For 6.2: "Successfully subscribed the system to Pool"
            # For 5.8: "Successfully consumed a subscription from the pool with id"
            if "Successfully " in output:
                logging.info("It's successful to subscribe.")
                return True
            else:
                logging.error("Test Failed - The information shown after subscribing is not correct.")
                exit(1)
        else:
            logging.error("Test Failed - Failed to subscribe.")
            exit(1)

    def get_certificate_list(self, system_info):
        cmd = "ls /etc/pki/entitlement/ | grep -v key.pem"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list all certificate files under /etc/pki/entitlement/...")
        return output.splitlines()

    def verify_productid_in_entitlement_cert(self, system_info, entitlement_cert, pid):
        # verify one product id in one entitlement cert
        cmd = "rct cat-cert /etc/pki/entitlement/{0} | grep ID | egrep -v 'Stacking ID|Pool ID'".format(entitlement_cert)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check PID {0} in entitlement certificate {1} with rct...".format(pid, entitlement_cert))

        if ret == 0:
            # output:
            #    ID: 240
            #    ID: 281
            #    ID: 285
            #    ID: 286
            #    ID: 69
            #    ID: 83
            #    ID: 85
            if pid in [i.split(":")[1].strip() for i in output.splitlines()]:
                logging.info(" It's successful to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))
                return True
            else:
                logging.error("Test Failed - Failed to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))
                exit(1)
        else:
            # output:
            # sh: rct: command not found
            prefix_str = '1.3.6.1.4.1.2312.9.1.'
            cmd = 'openssl x509 -text -noout -in /etc/pki/entitlement/{0} | grep --max-count=1 -A 1 {1}{2}'.format(entitlement_cert, prefix_str, pid)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check PID {0} in entitlement certificate {1} with openssl...".format(pid, entitlement_cert))
            if ret == 0 and output != '':
                logging.info(" It's successful to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))
                return True
            else:
                logging.error("Test Failed - Failed to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))

    def verify_sku_in_entitlement_cert(self, system_info, entitlement_cert, sku):
        # verify one sku id in one entitlement cert
        cmd = "rct cat-cert /etc/pki/entitlement/{0} | grep SKU".format(entitlement_cert)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check SKU {0} in entitlement certificate {1} with rct...".format(sku, entitlement_cert))

        if ret == 0:
            # output: SKU: MCT2887
            if sku in output.split(":")[1].strip():
                logging.info(" It's successful to verify sku {0} in entitlement certificate {1}.".format(sku, entitlement_cert))
                return True
            else:
                logging.error("Test Failed - Failed to verify sku {0} in entitlement cert {1}.".format(sku, entitlement_cert))
                exit(1)
        else:
            # output:
            # sh: rct: command not found
            cmd = 'openssl x509 -text -noout -in /etc/pki/entitlement/{0} | grep {1}'.format(entitlement_cert, sku)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check SKU {0} in entitlement certificate {1} with openssl...".format(sku, entitlement_cert))
            if ret == 0 and output != '':
                logging.info(" It's successful to verify sku {0} in entitlement cert {1}.".format(sku, entitlement_cert))
                return True
            else:
                logging.error("Test Failed - Failed to verify sku {0} in entitlement cert {1}." .format(sku, entitlement_cert))
                exit(1)

    def subscribe(self, system_info, pid, sku, poolid):
        result = True
        # Get certificate list before subscribe
        list1 = self.get_certificate_list(system_info)

        result &= self.subscribe_pool(system_info, poolid)

        # Get certificate list after subscribe
        list2 = self.get_certificate_list(system_info)
        
        entitlement_cert = list(set(list2)-set(list1))[0]

        result &= self.verify_productid_in_entitlement_cert(system_info, entitlement_cert, pid)
        result &= self.verify_sku_in_entitlement_cert(system_info, entitlement_cert, sku)

        return result

    def set_config_file(self, system_info, release_ver, config_file):
        cmd = '''sed -i "s/yumvars\['releasever'\] = /yumvars\['releasever'\] = '%s' # /" %s''' % (release_ver, config_file)
        RemoteSHH().run_cmd(system_info, cmd, "Trying to modify config.py to set the system release as {0}...".format(release_ver))

        cmd = '''cat %s | grep "yumvars\['releasever'\]"''' % config_file
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check the setting in config.py...")
        if release_ver in output:
            logging.info("It's successful to set system release.")
            return True
        else:
            logging.error("Test Failed - Failed to set system release." )
            return False

    def get_config_file(self, master_release):
        if master_release == "5":
            config_file = "/usr/lib/python2.4/site-packages/yum/config.py"
        elif master_release == "6":
            config_file = "/usr/lib/python2.6/site-packages/yum/config.py"
        else:
            config_file = "/usr/lib/python2.7/site-packages/yum/config.py"
        return config_file

    def set_release(self, system_info, release_ver):
        releasever_set = ""
        master_release = self.get_master_release(system_info)
        config_file = self.get_config_file(master_release)

        cmd = "subscription-manager release --set={0}".format(release_ver)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to set release version as {0}...".format(release_ver))

        if ret == 0 and 'Release set to' in output:
            logging.info("It's successful to set system release as {0}.".format(release_ver))
            cmd = "subscription-manager release"
            RemoteSHH().run_cmd(system_info, cmd, "Trying to check the release version after setting...".format(release_ver))
        elif ret == 0 and 'Usage: subscription-manager' in output:
            self.set_config_file(system_info, release_ver, config_file)
        elif 'No releases match' in output:
            if master_release == '5':
                self.set_config_file(system_info, release_ver, config_file)
            elif master_release in ["6", "7"]:
                releasever_set = '--releasever=%s' % release_ver
                logging.info("It's successfully to set variable --releasever={0}.".format(release_ver))
            else:
                logging.error("Test Failed - Failed to set system release as {0}.".format(release_ver))
                exit(1)
        else:
            logging.error("Test Failed - Failed to set system release as {0}.".format(release_ver))
            exit(1)
        return releasever_set

    def clear_yum_cache(self, system_info, releasever_set):
        # get repolist
        cmd = 'yum clean all --enablerepo=* {0}'.format(releasever_set)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yum clean cache...")
        if ret == 0:
            logging.info("It's successful to clear yum cache")
            return True
        else:
            logging.error("Test Failed - Failed to clear yum cache")
            exit(1)

    def get_repo_list_from_manifest(self, manifest_xml, pid, current_arch, release_ver):
        # Get repo list from xml manifest
        logging.info("--------------- Begin to get repo list from manifest: {0} {1} {2} ---------------".format(pid, current_arch, release_ver))
        repo_list = CDNReadXML().get_repo_list(manifest_xml, release_ver, pid, current_arch)
        if len(repo_list) == 0:
            logging.error("Repo list is empty!")
            logging.error("Test Failed - There is no repo for pid {0} in release {1}.".format(pid, release_ver))
            exit(1)
        else:
            logging.info("Repos got from manifest:")
            self.print_list(repo_list)
        return repo_list

    def get_package_list_from_manifest(self, manifest_xml, pid, repo, current_arch, release_ver, type="name"):
        # Get package list from manifest file
        logging.info("--------------- Begin to get package list from manifest: {0} {1} {2} {3} ---------------".format(pid, current_arch, repo, release_ver))
        package_list = CDNReadXML().get_package_list(manifest_xml, repo, release_ver, pid, current_arch)
        if type == "name":
            package_list = [p.split()[0] for p in package_list]
        elif type == "full-name":
            # "%{name}-%{version}-%{release}.src"
            package_list = ["{0}-{1}-{2}-{3}".format(i.split()[0], i.split()[1], i.split()[2], i.split()[3]) for i in package_list]
        logging.info("It's successful to get {0} packages from package manifest".format(len(package_list)))
        logging.info("--------------- End to get package list from manifest: PASS ---------------")
        return package_list

    def test_repos(self, system_info, repo_list, blacklist, releasever_set, release_ver, current_arch):
        # Check all enabled repos to see if there are broken repos
        repo_file = "/tmp/redhat.repo"
        if not os.path.exists(repo_file):
            logging.error("There is no /tmp/redhat.repo backuped.")
            return False

        config = ConfigParser.ConfigParser()
        config.read(repo_file)

        if blacklist == "Beta" or blacklist == "HTB":
            cmd = "yum repolist --disablerepo=* --enablerepo={0} {1}".format(",".join(repo_list), releasever_set)
        else:
            cmd = "yum repolist --enablerepo={0} {1}".format(",".join(repo_list), releasever_set)

        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to test enabled repos...")
        if "ERROR" in output:
            result = False
            # Get baseurl/repo pairs from redhat.repo file
            url_repo_dict = {}
            for s in config.sections():
                for i in config.items(s):
                    if i[0] == "baseurl":
                        url_repo_dict[i[1]] = s

            # Check $releasever $basearch in redhat.repo file, then replace the following error url according to it
            src_str = ""
            dest_str = ""
            if url_repo_dict.keys()[0].count("$") == 2:
                src_str = "%s/%s" % (release_ver, current_arch)
                dest_str = "$releasever/$basearch"
            elif url_repo_dict.keys()[0].count("$") == 1:
                src_str = current_arch
                dest_str = "$basearch"

            error_list = []
            while not result:
                disablerepo = []
                # Get error url
                # http://download.lab.bos.redhat.com/released/RHEL-6/6.7/Server/optional/x86_64/os3/repodata/repomd.xml: [Errno 14] PYCURL ERROR 22 - "The requested URL returned error: 404 Not Found"
                # Trying other mirror.
                start_position = output.index("http")
                error_end_position = output.index("Trying other mirror") - 1
                error_url = output[start_position:error_end_position]

                # Get repo url
                repo_url_end_position = output.index("/repodata/repomd.xml")
                repo_url = output[start_position:repo_url_end_position]

                # Get base url, and then get the repo name
                base_url = repo_url.replace(src_str, dest_str)
                repo_name = url_repo_dict[base_url]

                # Set error dict
                error_dict = {}
                error_dict['url'] = error_url
                error_dict["repo"] = repo_name

                error_list.append(error_dict)

                disablerepo.append(repo_name)
                cmd += " --disablerepo={0}".format(",".join(disablerepo))

                ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to disablerepo {0}...".format(disablerepo))

                if "ERROR" not in output:
                    result = True

            logging.info("=========================Summary of repos and baseurls=======================================")
            logging.error("Followings are failed repos (total: {0})".format(len(error_list)))
            for i in error_list:
                logging.info("repo: {0}".format(i["repo"]))
                logging.info("      {1}".format(i["url"]))
            logging.error("Failed to do yum repolist.")
            return False
        else:
            logging.info("It's successful to do yum repolist.")
            return True

    def enable_repo(self, system_info, repo):
        # Enable a repo before test this repo
        cmd = "subscription-manager repos --enable={0}".format(repo)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to enable repo {0}...".format(repo))
        if ret == 0:
            logging.info("It's successful to enable repo {0}.".format(repo))
            return True
        else:
            logging.error("Test Failed - Failed to enable repo {0}.".format(repo))
            return False

    def disable_repo(self, system_info, repo):
        # Disable a repo after finish testing this repo
        cmd = "subscription-manager repos --disable={0}".format(repo)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to disable repo {0}...".format(repo))
        if ret == 0:
            logging.info("It's successful to disable repo {0}.".format(repo))
            return True
        else:
            logging.error("Test Failed - Failed to disable repo {0}.".format(repo))
            return False

    def change_gpgkey(self, system_info, repo_list):
        # Change gpgkey for all the test repos listed in manifest
        logging.info("--------------- Begin to change gpgkey for test repos ---------------")
        result = True
        for repo in repo_list:
            cmd = "subscription-manager repo-override --repo %s --add=gpgkey:file:///etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-beta,file:///etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release" % repo
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to change gpgkey for repo %s in /etc/yum.repos.d/redhat.repo...".format(repo))
            if ret == 0:
                logging.info("It's successful to change gpgkey for repo {0} in /etc/yum.repos.d/redhat.repo".format(repo))
                logging.info("--------------- End to change gpgkey for test repos ---------------")
            else:
                logging.error("Test Failed - Failed to change gpgkey for repo {0} /etc/yum.repos.d/redhat.repo.".format(repo))
                logging.info("--------------- End to change gpgkey for test repos ---------------")
                result = False
        return result

    def yum_download_source_package(self, system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver):
        # yum download one package for source repo
        formatstr = "%{name}-%{version}-%{release}.src"
        cmd = '''repoquery --pkgnarrow=available --all --repoid=%s --archlist=src --qf "%s" %s''' % (repo, formatstr, releasever_set)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to repoquery available source packages for repo {0}...".format(repo))

        # Delete string "You have mail in /var/spool/mail/root" from repoquery output
        output = output.split("You have mail in")[0]

        if ret == 0:
            logging.info("It's successful to repoquery available source packages for the repo '%s'." % repo)
            pkg_list = output.strip().splitlines()
            if len(pkg_list) == 0:
                logging.info("No available source package for repo {0}.".format(repo))
                return True
        else:
            logging.error("Test Failed - Failed to repoquery available source packages for the repo {0}.".format(repo))
            return False

        manifest_pkgs = self.get_package_list_from_manifest(manifest_xml, pid, repo, current_arch, release_ver, "full-name")
        if len(manifest_pkgs) == 0:
            logging.info("There is no package in manifest for pid:repo {0}:{1} on release {2}".format(pid, repo, release_ver))
            return True

        # Get a available package list which are uninstalled got from repoquery and also in manifest.
        avail_pkgs = list(set(pkg_list) & set(manifest_pkgs))
        if len(avail_pkgs) == 0:
            logging.error("There is no available package for repo {0}, as all packages listed in manifest have been installed before, please uninstall first, then re-test!".format(repo))
            return False

        # Get one package randomly to download
        pkg_name = random.sample(avail_pkgs, 1)[0]
        if blacklist == 'Beta':
            cmd = "yumdownloader --destdir /tmp --disablerepo=* --enablerepo=*beta* --source %s %s" % (pkg_name, releasever_set)
        elif blacklist == 'HTB':
            cmd = "yumdownloader --destdir /tmp --disablerepo=* --enablerepo=*htb* --source %s %s" % (pkg_name, releasever_set)
        else:
            cmd = "yumdownloader --destdir /tmp --source %s %s" % (pkg_name, releasever_set)

        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yumdownloader source package {0}...".format(pkg_name))

        if ret == 0 and ("Trying other mirror" not in output):
            cmd = "ls /tmp/{0}*".format(pkg_name)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check downloaded source package {0} just now...".format(pkg_name))

            if ret == 0 and pkg_name in output:
                logging.info("It's successful to yumdownloader source package {0} of repo {1}.".format(pkg_name, repo))
                return True
            else:
                logging.error("Test Failed - Failed to yumdownloader source package {0} of repo {1}.".format(pkg_name, repo))
                return False
        else:
            logging.error("Test Failed - Failed to yumdownloader source package {0} of repo {1}.".format(pkg_name, repo))
            return False


    def verify_productid_in_product_cert(self, system_info, pid, base_pid):
        # Check product id in product entitlement certificate
        str = '1.3.6.1.4.1.2312.9.1.'

        time.sleep(20)
        ret, output = RemoteSHH().run_cmd(system_info, "ls /etc/pki/product/", "Trying to list all the product certificates...")
        product_ids = output.split()

        if "{0}.pem".format(pid) in product_ids:
            logging.info("It's successful to install the product cert {0}!".format(pid))

            cmd = 'openssl x509 -text -noout -in /etc/pki/product/{0}.pem | grep {1}{2}'.format(pid, str, pid)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to verify product id in product certificate...")

            if ret == 0 and output != '':
                logging.info(" It's successful to verify PID {0} in product cert.".format(pid))
                return True
            else:
                logging.error("Test Failed - Failed to verify PID {0} in product cert.".format(pid))
                return False
        else:
            error_list = list(set(product_ids) - set([base_pid]))
            if len(error_list) == 0:
                logging.error("Test Failed - Failed to install the product cert {0}.pem.".format(pid))
            else:
                logging.error("Test Failed - Failed to install correct product cert {0}, but installed cert {1}.".format(pid, error_list))
            return False

    def yum_install_one_package(self, system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver):
        # yum install one package
        formatstr = "%{name}"
        cmd = '''repoquery --pkgnarrow=available --all --repoid=%s --qf "%s" %s''' % (repo, formatstr, releasever_set)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to repoquery available packages...")

        if ret == 0:
            logging.info("It's successful to repoquery available packages for the repo {0}.".format(repo))
            pkgs = output.strip().splitlines()
            if len(pkgs) == 0:
                logging.info("No available package for the repo {0}.".format(repo))
                return True
        else:
            logging.error("Test Failed - Failed to repoquery available packages for the repo {0}.".format(repo))
            return False

        # Get all packages list from packages manifest
        manifest_pkgs = self.get_package_list_from_manifest(manifest_xml, pid, repo, current_arch, release_ver, "name")
        if len(manifest_pkgs) == 0:
            logging.info("There is no package in manifest for pid:repo {0}:{1} on release {2}".format(pid, repo, release_ver))
            return True

        # Get a available packages list which are uninstalled got from repoquery and also in manifest.
        avail_pkgs = list(set(pkgs) & set(manifest_pkgs))
        if len(avail_pkgs) == 0:
            logging.error("There is no available packages for repo {0}, as all packages listed in manifest have been installed before, please uninstall first, then re-test!".format(repo))
            return False

        # Get one package randomly to install
        pkg_name = random.sample(avail_pkgs, 1)[0]

        if blacklist == 'Beta':
            cmd = "yum -y install --disablerepo=* --enablerepo=*beta* --skip-broken %s %s" % (pkg_name, releasever_set)
        elif blacklist == 'HTB':
            cmd = "yum -y install --disablerepo=* --enablerepo=*htb* --skip-broken %s %s" % (pkg_name, releasever_set)
        else:
            cmd = "yum -y install --skip-broken %s %s" % (pkg_name, releasever_set)

        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yum install package {0}...".format(pkg_name))
        if ret == 0 and ("Complete!" in output or "Nothing to do" in output):
            logging.info("It's successful to yum install package {0} of repo {1}.".format(pkg_name, repo))

        if ("optional" not in repo) and ("supplementary" not in repo) and ("debug" not in repo):
            if base_pid == pid:
                logging.info("For RHEL testing, skip product cert testing, the default rhel product cert is located in the folder '/etc/pki/product-default/', and will not be downloaded into '/etc/pki/product/' anew.")
                checkresult = True
            else:
                checkresult = self.verify_productid_in_product_cert(system_info, pid, base_pid)
            return checkresult
        else:
            logging.error("Test Failed - Failed to yum install package {0} of repo {1}.".format(pkg_name, repo))
            return False

    def remove_layered_product_cert(self, system_info, base_pid):
        # Remove the none base product cert before install package
        logging.info("------------------ Begin to remove the none base product cert before install the packages-----------------------")
        cmd = "ls /etc/pki/product/"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list product cert...")

        product_cert_list = output.split()
        remove_list = list(set(product_cert_list) - set(base_pid))

        if len(remove_list) == 0:
            logging.info("There is only base product cert, no need to remove any layered product cert.")
        else:
            for cert in remove_list:
                cmd = "rm -f /etc/pki/product/{0}".format(cert)
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to remove the layered product cert {0}...".format(cert))
                if ret == 0:
                    logging.info("It is successful to remove the none base product cert: {0}".format(cert))
        logging.info("--------------------End to remove the none product cert before install the packages-----------------------------")

    def pid_cert_installation(self, system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver):
        # Verify product cert installation after install one package with yum
        logging.info("--------------- Begin to verify productcert installation for the repo {0} of the product {1} ---------------".format(repo, pid))
        if ("source" in repo) or ("src" in repo):
            # yumdownloader source package
            result = self.yum_download_source_package(system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver)
        else:
            self.remove_layered_product_cert(system_info, ["{0}.pem".format(base_pid)])
            result = self.yum_install_one_package(system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver)

            if result:
                logging.info("--------------- End to verify productcert installation for the repo {0} of the product {1}: PASS ---------------".format(repo, pid))
            else:
                logging.error("--------------- End to verify productcert installation for the repo {0} of the product {1}: FAIL -------------".format(repo, pid))
        return result

    def get_sys_pkglist(self, system_info):
        # Get system packages list before installation testing, and then make sure these packages will not be removed during installation testing.
        cmd = 'rpm -qa --qf "%{name}\n"'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list all packages in system before installation testing...")
        if ret == 0:
            sys_pkglist = output.splitlines()
            logging.info("It's successful to get {0} packages from the system.\n".format(len(sys_pkglist)))
            return sys_pkglist
        else:
            logging.error("Test Failed - Failed to list all packages in system before level3.")
            exit(1)

    def remove_pkg(self, system_info, pkg, repo):
        # Yum remove a package after install in order to resolve dependency issue which described in
        # https://bugzilla.redhat.com/show_bug.cgi?id=1272902
        cmd = "yum remove -y {0}".format(pkg)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to remove package {0} of repo {1}...".format(pkg, repo))
        if ret == 0:
            logging.info("It's successful to remove package '{0}'.\n".format(pkg))
            return True
        else:
            logging.warning("Warning -- Can't remove package '{0}'.\n".format(pkg))
            return False

    def verify_all_packages_installation(self, system_info, manifest_xml, pid, repo, arch, release_ver, releasever_set, blacklist):
        logging.info("--------------- Begin to verify all packages installation of repo %s ---------------" % repo)
        # Get all packages already installed in testing system before installation testing
        system_pkglist = self.get_sys_pkglist(system_info)

        # Use to store the failed packages after 'yum remove'.
        remove_failed_pkglist = []

        checkresult = True
        if "source" in repo:
            pkg_list = self.get_package_list_from_manifest(manifest_xml, pid, repo, arch, release_ver, "full-name")
            if len(pkg_list) != 0:
                pkgs = " ".join(pkg_list)
                if blacklist == 'Beta':
                    cmd = 'yumdownloader --destdir /tmp --disablerepo=* --enablerepo=*beta* --source %s %s' % (pkgs, releasever_set)
                else:
                    cmd = 'yumdownloader --destdir /tmp --source %s %s' % (pkgs, releasever_set)
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yumdownloader all source packages for repo {0}...".format(repo))
                if ret == 0:
                    logging.info(" It's successful to download source packages.")
                else:
                    if "No Match for argument" in output:
                        error_list = [s for s in output.splitlines() if "No Match" in s]
                        failed_src_pkglist = [error.replace('No Match for argument ', '').replace('\r', '') for error in error_list]
                        logging.error("Failed to download following source packages: %s" % failed_src_pkglist)
            else:
                logging.info("There is no source packages for pid:repo {0}:{1}".format(pid, repo))
        else:
            pkg_list = self.get_package_list_from_manifest(manifest_xml, pid, repo, arch, release_ver, "name")
            # uniquify pkgs
            pkg_list = list(set(pkg_list))

            # print the package list, and number every package
            logging.info("Ready to install below rpm packages:")
            self.print_list(pkg_list)

            number = 0
            total_number = len(pkg_list)

            for pkg in pkg_list:
                number += 1
                if blacklist == 'Beta':
                    cmd = 'yum install -y --disablerepo=* --enablerepo=*beta* --skip-broken {0} {1}'.format(pkg, releasever_set)
                else:
                    cmd = 'yum install -y --skip-broken {0} {1}'.format(pkg, releasever_set)
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to install package [{0}/{1}] {2} for repo {3}...".format(number, total_number, pkg, repo))

                if ret == 0:
                    if ("Complete!" in output) or ("Nothing to do" in output) or ("conflicts" in output):
                        logging.info(" It's successful to install package [{0}/{1}] {2} for repo {3}...".format(number, total_number, pkg, repo))
                    else:
                        logging.error("Test Failed - Failed to install package [{0}/{1}] {2} for repo {3}...".format(number, total_number, pkg, repo))
                        checkresult = False
                else:
                    if ("conflicts" in output):
                        logging.info(" It's successful to install package [{0}/{1}] {2} for repo {3}...".format(number, total_number, pkg, repo))
                    else:
                        logging.error("Test Failed - Failed to install package [{0}/{1}] {2} for repo {3}...".format(number, total_number, pkg, repo))
                        checkresult = False

                if checkresult:
                    if pkg not in system_pkglist:
                        # Remove this package if it is not in the system package list.
                        # It is used to solve the dependency issue which describe in https://bugzilla.redhat.com/show_bug.cgi?id=1272902.
                        if not self.remove_pkg(system_info, pkg, repo):
                            remove_failed_pkglist.append(pkg)

            if checkresult:
                logging.info("--------------- End to verify packages full installation of repo {0}: PASS ---------------".format(repo))
            else:
                logging.error("--------------- End to verify packages full installation of repo {0}: FAIL ---------------".format(repo))

        if len(remove_failed_pkglist) != 0:
            logging.warning("----------------------Warning -- Can't remove following packages: {0}".format(remove_failed_pkglist))

        return checkresult