import os
import time
import random
import logging
import ConfigParser

from Utils.RemoteSHH import RemoteSHH
from Utils.EntitlementBase import EntitlementBase
from CDN.CDNReadXML import CDNReadXML


# Create logger
logger = logging.getLogger("entLogger")


class CDNVerification(EntitlementBase):
    def redhat_repo_backup(self, system_info):
        # Download content of file redhat.repo remotely, and save it locally
        remote_path = "/etc/yum.repos.d/redhat.repo"
        local_path = os.path.join(os.getcwd(), "redhat.repo")
        RemoteSHH().download_file(system_info, remote_path, local_path)
        ret, output = RemoteSHH().run_cmd(None, "ls {0}".format(local_path), "Trying to check {0}.".format(local_path))
        if "No such file or directory" in output:
            logger.warning("Failed to download {0} to {1}".format(remote_path, local_path))
        else:
            logger.info("It's successful to download {0} to {1}".format(remote_path, local_path))

    def stop_rhsmcertd(self, system_info):
        # Stop rhsmcertd service. As headling(autosubscribe) operation will be run every 2 mins after start up system,
        # then every 24 hours after that, which will influence our subscribe test.
        cmd = 'service rhsmcertd status'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get status of service rhsmcertd...")
        if 'stopped' in output or 'Stopped' in output:
            return True

        cmd = 'service rhsmcertd stop'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to stop service rhsmcertd...")
        if ret == 0:
            cmd = 'service rhsmcertd status'
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get status of service rhsmcertd...")
            if 'stopped' in output or 'Stopped' in output:
                logger.info("It's successful to stop rhsmcertd service.")
                return True
            else:
                logger.error("Failed to stop rhsmcertd service.")
                return False
        else:
            logger.error("Failed to stop rhsmcertd service.")
            return False

    def config_testing_environment(self, system_info, hostname, baseurl):
        # Config hostname and baseurl in /etc/rhsm/rhsm.conf
        cmd = "subscription-manager config --server.hostname={0}".format(hostname)
        RemoteSHH().run_cmd(system_info, cmd, "Trying to set hostname in /etc/rhsm/rhsm.conf...")

        cmd = "subscription-manager config --rhsm.baseurl={0}".format(baseurl)
        RemoteSHH().run_cmd(system_info, cmd, "Trying to set baseurl in /etc/rhsm/rhsm.conf...")

    def check_registered(self, system_info):
        # Check if registered
        cmd = "subscription-manager identity"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check if registered with cdn server...")
        if ret == 0:
            logger.info("The system is registered with cdn server now.")
            return True
        else:
            logger.info("The system is not registered with cdn server now.")
            return False

    def unregister(self, system_info):
        # Unregister with CDN server
        if self.check_registered(system_info):
            cmd = "subscription-manager unregister"
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to unregister...")

            if ret == 0:
                logger.info("It's successful to unregister.")
                return True
            else:
                logger.error("Test Failed - Failed to unregister.")
                return False
        else:
            logger.info("The system is not registered with cdn server now.")
            return True

    def register(self, system_info, username, password):
        # Register with CDN server
        cmd = "subscription-manager register --username={0} --password='{1}'".format(username, password)

        if self.check_registered(system_info):
            logger.info("The system is already registered, need to unregister first!")
            if not self.unregister(system_info):
                logger.info("Failed to unregister, try to use '--force'!")
                cmd += " --force"

        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to register cdn server...")
        if ret == 0:
            logger.info("It's successful to register.")
            return True
        else:
            logger.error("Test Failed - Failed to register.")
            return False

    def check_subscription(self, system_info, sku):
        cmd = "subscription-manager list --available --all | grep {0}".format(sku)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list sbuscription {0}...".format(sku))
        if ret == 0 and sku in output:
            logger.info("It's successful to get sku {0} in available list.".format(sku))
            return True
        else:
            logger.info("Test Failed - Failed to get sku {0} in available list.".format(sku))
            return False

    def get_sku_pool(self, system_info):
        # Get available entitlement pools
        time.sleep(5)
        cmd = "subscription-manager  list --avail --all| egrep 'SKU|Pool ID' | grep -v Subscription"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list all available SKU and Pool ID...")

        sku_pool_dict = {}
        if ret == 0:
            if output != "":
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
            else:
                logger.error("No suitable pools!")
                logger.error("Test Failed - Failed to get available pools.")
        else:
            logger.error("Test Failed - Failed to get available pools.")

        return sku_pool_dict

    def subscribe_pool(self, system_info, poolid):
        cmd = "subscription-manager subscribe --pool={0}".format(poolid)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to subscribe with poolid {0}".format(poolid))

        if ret == 0:
            logger.info("It's successful to subscribe.")
            return True
        else:
            logger.error("Test Failed - Failed to subscribe.")
            return False

    def get_certificate_list(self, system_info):
        cmd = "ls /etc/pki/entitlement/ | grep -v key.pem"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list all certificate files under /etc/pki/entitlement/...")
        return output.splitlines()

    def subscribe(self, system_info, poolid):
        # Get certificate list before subscribe
        cert_list1 = self.get_certificate_list(system_info)

        result = self.subscribe_pool(system_info, poolid)

        # Get certificate list after subscribe
        cert_list2 = self.get_certificate_list(system_info)

        entitlement_cert = list(set(cert_list2)-set(cert_list1))
        return result, entitlement_cert


    def verify_productid_in_entitlement_cert(self, system_info, entitlement_cert, pid):
        # Verify if one specific product id in one entitlement cert
        cmd = "rct cat-cert /etc/pki/entitlement/{0} | grep ID | egrep -v 'Stacking ID|Pool ID'".format(entitlement_cert)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check PID {0} in entitlement certificate {1} with rct...".format(pid, entitlement_cert))

        if ret == 0:
            # Output:
            #    ID: 240
            #    ID: 281
            #    ID: 285
            #    ID: 286
            #    ID: 69
            #    ID: 83
            #    ID: 85
            if pid in [i.split(":")[1].strip() for i in output.splitlines()]:
                logger.info("It's successful to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))
                return True
            else:
                logger.error("Test Failed - Failed to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))
                return False
        else:
            # Output:
            # sh: rct: command not found
            prefix_str = '1.3.6.1.4.1.2312.9.1.'
            cmd = 'openssl x509 -text -noout -in /etc/pki/entitlement/{0} | grep --max-count=1 -A 1 {1}{2}'.format(entitlement_cert, prefix_str, pid)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check PID {0} in entitlement certificate {1} with openssl...".format(pid, entitlement_cert))
            if ret == 0 and output != '':
                logger.info("It's successful to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))
                return True
            else:
                logger.error("Test Failed - Failed to verify PID {0} in entitlement certificate {1}.".format(pid, entitlement_cert))
                return False

    def verify_sku_in_entitlement_cert(self, system_info, entitlement_cert, sku):
        # Verify if one specific sku id in one entitlement cert
        cmd = "rct cat-cert /etc/pki/entitlement/{0} | grep SKU".format(entitlement_cert)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check SKU {0} in entitlement certificate {1} with rct...".format(sku, entitlement_cert))

        if ret == 0:
            # Output:
            # SKU: MCT2887
            if sku in [i.strip().split(":")[1].strip() for i in output.splitlines()]:
                logger.info("It's successful to verify sku {0} in entitlement certificate {1}.".format(sku, entitlement_cert))
                return True
            else:
                logger.error("Test Failed - Failed to verify sku {0} in entitlement cert {1}.".format(sku, entitlement_cert))
                return False
        else:
            # Output:
            # sh: rct: command not found
            cmd = 'openssl x509 -text -noout -in /etc/pki/entitlement/{0} | grep {1}'.format(entitlement_cert, sku)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check SKU {0} in entitlement certificate {1} with openssl...".format(sku, entitlement_cert))
            if ret == 0 and output != '':
                logger.info("It's successful to verify sku {0} in entitlement cert {1}.".format(sku, entitlement_cert))
                return True
            else:
                logger.error("Test Failed - Failed to verify sku {0} in entitlement cert {1}." .format(sku, entitlement_cert))
                return False

    def verify_arch_in_entitlement_cert(self, system_info, entitlement_cert, manifest_xml, pid, current_release_ver):
        # Get arch list from manifest
        arch_manifest = self.get_arch_list_from_manifest(manifest_xml, pid)

        # Get supported arches in entitlement certificate
        cmd = "rct cat-cert /etc/pki/entitlement/{0}  | grep -A 3 'ID: {1}' | grep Arch".format(entitlement_cert, pid)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get supported arches for pid {0} in entitlement certificate {1} with rct cat-cert...".format(pid, entitlement_cert))
        if ret == 0:
            if output != "":
                # Output:
                # Arch: x86_64,x86
                arches = output.split(":")[1].strip().split(",")
                arch_cert = []
                for arch in arches:
                        if arch == 'x86':
                                arch_cert.append('i386')
                        elif arch == 'ppc' and current_release_ver.find('6') >= 0:
                                arch_cert.append('ppc64')
                        elif arch == 'ppc64' and current_release_ver.find('5') >= 0:
                                arch_cert.append('ppc')
                        elif arch == 's390':
                                arch_cert.append('s390x')
                        elif arch == 'ia64' and current_release_ver.find('6') >= 0:
                                continue
                        else:
                                arch_cert.append(arch)
                logging.info("Supported arch in entitlement cert are: {0}".format(arch_cert))

                error_arch_list = self.cmp_arrays(arch_manifest, arch_cert)
                if len(error_arch_list) > 0:
                    logging.error("Failed to verify arches for product {0} in entitlement certificate.".format(pid))
                    logging.info('Below are arches got from in manifest but not in entitlement cert:')
                    self.print_list(error_arch_list)
                    logging.error("Test Failed - Failed to verify arch in entitlement certificate for product {0}.".format(pid))
                    return False
                else:
                    logging.info("It's successful to verify arch in entitlement certificate for product {0}.".format(pid))
                    return True
            else:
                logging.error("Test Failed - Failed to verify arch in entitlement certificate for product {0}.".format(pid))
                return False
        else:
            # Output:
            # sh: rct: command not found
            str = '1.3.6.1.4.1.2312.9.1.{0}.3:'.format(pid)
            cmd = 'openssl x509 -text -noout -in /etc/pki/entitlement/{0} | grep {1} -A 2'.format(entitlement_cert, str)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get supported arches for pid {0} in entitlement certificate {1} with openssl...".format(pid, entitlement_cert))
            if ret == 0 and output != '':
                for i in arch_manifest:
                    if i in output:
                        continue
                    else:
                        logger.error("Test Failed - Failed to verify in entitlement certificate for product {0}.".format(pid))
                        return False
                logger.info("It's successful to verify arch in entitlement certificate for product {0}.".format(pid))
                return True
            else:
                logger.error("Test Failed - Failed to verify in entitlement certificate for product {0}.".format(pid))
                return False

    def set_config_file(self, system_info, release_ver, config_file):
        cmd = '''sed -i "s/yumvars\['releasever'\] = /yumvars\['releasever'\] = '%s' # /" %s''' % (release_ver, config_file)
        RemoteSHH().run_cmd(system_info, cmd, "Trying to modify config.py to set the system release as {0}...".format(release_ver))

        cmd = '''cat %s | grep "yumvars\['releasever'\]"''' % config_file
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check the setting in config.py...")
        if release_ver in output:
            logger.info("It's successful to set system release.")
            return True
        else:
            logger.error("Test Failed - Failed to set system release." )
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
            logger.info("It's successful to set system release as {0}.".format(release_ver))
            cmd = "subscription-manager release"
            RemoteSHH().run_cmd(system_info, cmd, "Trying to check the release version after setting...".format(release_ver))
        elif ret == 0 and 'Usage: subscription-manager' in output:
            self.set_config_file(system_info, release_ver, config_file)
        elif 'No releases match' in output:
            if master_release == '5':
                self.set_config_file(system_info, release_ver, config_file)
            elif master_release in ["6", "7"]:
                releasever_set = '--releasever=%s' % release_ver
                logger.info("It's successfully to set variable --releasever={0}.".format(release_ver))
            else:
                logger.error("Test Failed - Failed to set system release as {0}.".format(release_ver))
                return False
        else:
            logger.error("Test Failed - Failed to set system release as {0}.".format(release_ver))
            return False
        return releasever_set

    def clean_yum_cache(self, system_info, releasever_set):
        # Clean yum cache
        cmd = 'yum clean all --enablerepo=* {0}'.format(releasever_set)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yum clean cache...")
        if ret == 0:
            logger.info("It's successful to clean yum cache")
            return True
        else:
            logger.error("Test Failed - Failed to clean yum cache")
            return False

    def get_repo_list_from_manifest(self, manifest_xml, pid, current_arch, release_ver):
        # Get repo list from xml format manifest
        logger.info("--------------- Begin to get repo list from manifest: {0} {1} {2} ---------------".format(pid, current_arch, release_ver))
        repo_list = CDNReadXML().get_repo_list(manifest_xml, release_ver, pid, current_arch)
        if len(repo_list) == 0:
            logger.error("Got 0 repository from manifest for pid {0} on release {1}!".format(pid, release_ver))
            return []
        else:
            logger.info("Got {0} Repos from manifest for pid {1} on release {2}:".format(len(repo_list), pid, release_ver))
            self.print_list(repo_list)
        logger.info("--------------- End to get repo list from manifest: {0} {1} {2} ---------------".format(pid, current_arch, release_ver))
        return repo_list

    def get_package_list_from_manifest(self, manifest_xml, pid, repo, current_arch, release_ver, type="name"):
        # Get package list from manifest file
        logger.info("--------------- Begin to get package list from manifest: {0} {1} {2} {3} ---------------".format(pid, current_arch, repo, release_ver))
        package_list = CDNReadXML().get_package_list(manifest_xml, repo, release_ver, pid, current_arch)
        logger.info("It's successful to get {0} packages from package manifest".format(len(package_list)))
        if len(package_list) != 0:
            if type == "name":
                package_list = [p.split()[0] for p in package_list]
            elif type == "full-name":
                # "%{name}-%{version}-%{release}.src"
                package_list = ["{0}-{1}-{2}.{3}".format(i.split()[0], i.split()[1], i.split()[2], i.split()[3]) for i in package_list]
            self.print_list(package_list)
        logger.info("--------------- End to get package list from manifest: PASS ---------------")
        return package_list

    def get_arch_list_from_manifest(self, manifest_xml, pid):
        # Get arch list from xml format manifest
        logger.info("--------------- Begin to get arch list for pid {0} from manifest ---------------".format(pid))
        arch_list = CDNReadXML().get_arch_list(manifest_xml, pid)
        if len(arch_list) == 0:
            logger.error("Got none arch from manifest for pid {0}!".format(pid))
            return []
        else:
            logger.info("Got {0} arch(es) from manifest for pid {1}:".format(len(arch_list), pid))
            self.print_list(arch_list)
        logger.info("--------------- End to get arch list for pid {0} from manifest ---------------".format(pid))
        return arch_list

    def test_repos(self, system_info, repo_list, blacklist, releasever_set, release_ver, current_arch):
        # Check all enabled repos to see if there are broken repos
        repo_file = os.path.join(os.getcwd(), "redhat.repo")
        if not os.path.exists(repo_file):
            logger.error("There is no {0} backuped.".format(repo_file))
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

            logger.info("=========================Summary of repos and baseurls=======================================")
            logger.error("Followings are failed repos (total: {0})".format(len(error_list)))
            for i in error_list:
                logger.info("repo: {0}".format(i["repo"]))
                logger.info("      {1}".format(i["url"]))
            logger.error("Failed to do yum repolist.")
            return False
        else:
            logger.info("It's successful to do yum repolist.")
            return True

    def enable_repo(self, system_info, repo):
        # Enable a repo before test this repo
        cmd = "subscription-manager repos --enable={0}".format(repo)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to enable repo {0}...".format(repo))
        if ret == 0:
            logger.info("It's successful to enable repo {0}.".format(repo))
            return True
        else:
            logger.error("Test Failed - Failed to enable repo {0}.".format(repo))
            return False

    def disable_repo(self, system_info, repo):
        # Disable a repo after finish testing this repo
        cmd = "subscription-manager repos --disable={0}".format(repo)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to disable repo {0}...".format(repo))
        if ret == 0:
            logger.info("It's successful to disable repo {0}.".format(repo))
            return True
        else:
            logger.error("Test Failed - Failed to disable repo {0}.".format(repo))
            return False

    def disable_all_repo(self, system_info):
        # Disabling all default enabled repos
        cmd = "subscription-manager repos --disable=*"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to disable all repos...")
        if ret == 0:
            logger.info("sucessfully disabled all repos")
            return True
        else:
            logger.error("test Failed - Failed to diable default enabled repo")
            return False

    def change_gpgkey(self, system_info, repo_list):
        # Change gpgkey for all the test repos listed in manifest
        logger.info("--------------- Begin to change gpgkey for test repos ---------------")
        result = True
        for repo in repo_list:
            cmd = "subscription-manager repo-override --repo %s --add=gpgkey:file:///etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-beta,file:///etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release" % repo
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to change gpgkey for repo %s in /etc/yum.repos.d/redhat.repo...".format(repo))
            if ret == 0:
                logger.info("It's successful to change gpgkey for repo {0} in /etc/yum.repos.d/redhat.repo".format(repo))
                logger.info("--------------- End to change gpgkey for test repos ---------------")
            else:
                logger.error("Test Failed - Failed to change gpgkey for repo {0} /etc/yum.repos.d/redhat.repo.".format(repo))
                logger.info("--------------- End to change gpgkey for test repos ---------------")
                result = False
        return result

    def yum_download_one_source_package(self, system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver):
        # Download one package for source repo with yumdownloader
        formatstr = "%{name}-%{version}-%{release}.src"
        cmd = '''repoquery --pkgnarrow=available --all --repoid=%s --archlist=src --qf "%s" %s''' % (repo, formatstr, releasever_set)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to repoquery available source packages for repo {0}...".format(repo), timeout=3600)

        # Delete string "You have mail in /var/spool/mail/root" from repoquery output
        output = output.split("You have mail in")[0]

        if ret == 0:
            logger.info("It's successful to repoquery available source packages for the repo '%s'." % repo)
            pkg_list = output.strip().splitlines()
            if len(pkg_list) == 0:
                logger.info("No available source package for repo {0}.".format(repo))
                return True
        else:
            logger.error("Test Failed - Failed to repoquery available source packages for the repo {0}.".format(repo))
            return False

        manifest_pkgs = self.get_package_list_from_manifest(manifest_xml, pid, repo, current_arch, release_ver, "full-name")
        if len(manifest_pkgs) == 0:
            logger.info("There is no package in manifest for pid:repo {0}:{1} on release {2}".format(pid, repo, release_ver))
            return False

        # Get a available package list which are uninstalled got from repoquery and also in manifest.
        avail_pkgs = list(set(pkg_list) & set(manifest_pkgs))
        if len(avail_pkgs) == 0:
            logger.error("There is no available package for repo {0}!".format(repo))
            return True

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
                logger.info("It's successful to yumdownloader source package {0} of repo {1}.".format(pkg_name, repo))
                return True
            else:
                logger.error("Test Failed - Failed to yumdownloader source package {0} of repo {1}.".format(pkg_name, repo))
                return False
        else:
            logger.error("Test Failed - Failed to yumdownloader source package {0} of repo {1}.".format(pkg_name, repo))
            return False


    def verify_productid_in_product_cert(self, system_info, pid, base_pid):
        # Check product id in product entitlement certificate
        str = '1.3.6.1.4.1.2312.9.1.'

        time.sleep(20)
        ret, output = RemoteSHH().run_cmd(system_info, "ls /etc/pki/product/", "Trying to list all the product certificates...")
        product_ids = output.split()

        if "{0}.pem".format(pid) in product_ids:
            logger.info("It's successful to install the product cert {0}!".format(pid))

            cmd = 'openssl x509 -text -noout -in /etc/pki/product/{0}.pem | grep {1}{2}'.format(pid, str, pid)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to verify product id in product certificate...")

            if ret == 0 and output != '':
                logger.info("It's successful to verify PID {0} in product cert.".format(pid))
                return True
            else:
                logger.error("Test Failed - Failed to verify PID {0} in product cert.".format(pid))
                return False
        else:
            error_list = list(set(product_ids) - set([base_pid]))
            if len(error_list) == 0:
                logger.error("Test Failed - Failed to install the product cert {0}.pem.".format(pid))
            else:
                logger.error("Test Failed - Failed to install correct product cert {0}, but installed cert {1}.".format(pid, error_list))
            return False

    def yum_install_one_package(self, system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver):
        # Install one package with yum
        formatstr = "%{name}"
        cmd = '''repoquery --pkgnarrow=available --all --repoid=%s --qf "%s" %s''' % (repo, formatstr, releasever_set)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to repoquery available packages...", timeout=3600)

        if ret == 0:
            logger.info("It's successful to repoquery available packages for the repo {0}.".format(repo))
            pkgs = output.strip().splitlines()
            if len(pkgs) == 0:
                logger.info("No available package for the repo {0}.".format(repo))
                return True
        else:
            logger.error("Test Failed - Failed to repoquery available packages for the repo {0}.".format(repo))
            return False

        # Get all packages list from packages manifest
        manifest_pkgs = self.get_package_list_from_manifest(manifest_xml, pid, repo, current_arch, release_ver, "name")
        if len(manifest_pkgs) == 0:
            logger.info("There is no package in manifest for pid:repo {0}:{1} on release {2}".format(pid, repo, release_ver))
            return True

        # Get a available packages list which are uninstalled got from repoquery and also in manifest.
        avail_pkgs = list(set(pkgs) & set(manifest_pkgs))
        if len(avail_pkgs) == 0:
            logger.error("There is no available packages for repo {0}, as all packages listed in manifest have been installed before, please uninstall first, then re-test!".format(repo))
            return False

        # Get one package randomly to install
        pkg_name = random.sample(avail_pkgs, 1)[0]

        if blacklist == 'Beta':
            cmd = "yum -y install --disablerepo=* --enablerepo=*beta* --skip-broken %s %s" % (pkg_name, releasever_set)
        elif blacklist == 'HTB':
            cmd = "yum -y install --disablerepo=* --enablerepo=*htb* --skip-broken %s %s" % (pkg_name, releasever_set)
        else:
            cmd = "yum -y install --skip-broken %s %s" % (pkg_name, releasever_set)

        checkresult = True
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yum install package {0}...".format(pkg_name))
        if ret == 0 and ("Complete!" in output or "Nothing to do" in output):
            logger.info("It's successful to yum install package {0} of repo {1}.".format(pkg_name, repo))

            if ("optional" not in repo) and ("supplementary" not in repo) and ("debug" not in repo):
                if base_pid == pid:
                    logger.info("For RHEL testing, skip product cert testing, the default rhel product cert is located in the folder '/etc/pki/product-default/', and will not be downloaded into '/etc/pki/product/' anew.")
                else:
                    checkresult = self.verify_productid_in_product_cert(system_info, pid, base_pid)
        else:
            logger.error("Test Failed - Failed to yum install package {0} of repo {1}.".format(pkg_name, repo))
            checkresult = False
        return checkresult

    def remove_layered_product_cert(self, system_info, base_pid):
        # Remove the layered product certificate before install package
        logger.info("------------------ Begin to remove the none base product cert before install the packages -----------------------")
        cmd = "ls /etc/pki/product/"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list product cert...")

        product_cert_list = output.split()
        remove_list = list(set(product_cert_list) - set(base_pid))

        if len(remove_list) == 0:
            logger.info("There is only base product cert, no need to remove any layered product cert.")
        else:
            for cert in remove_list:
                cmd = "rm -f /etc/pki/product/{0}".format(cert)
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to remove the layered product cert {0}...".format(cert))
                if ret == 0:
                    logger.info("It is successful to remove the none base product cert: {0}".format(cert))
        logger.info("--------------------End to remove the none product cert before install the packages-----------------------------")

    def package_smoke_installation(self, system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver):
        # Verify package's installable or downloadable
        logger.info("--------------- Begin to verify package's installable or downloadable for the repo {0} of the product {1} ---------------".format(repo, pid))
        if ("source" in repo) or ("src" in repo):
            # yumdownloader source package
            result = self.yum_download_one_source_package(system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver)
        else:
            self.remove_layered_product_cert(system_info, ["{0}.pem".format(base_pid)])
            result = self.yum_install_one_package(system_info, repo, releasever_set, blacklist, manifest_xml, pid, base_pid, current_arch, release_ver)

            if result:
                logger.info("--------------- End to verify productcert installation for the repo {0} of the product {1}: PASS ---------------".format(repo, pid))
            else:
                logger.error("--------------- End to verify productcert installation for the repo {0} of the product {1}: FAIL -------------".format(repo, pid))
        return result

    def verify_all_packages_installation(self, system_info, manifest_xml, pid, repo, arch, release_ver, releasever_set, blacklist):
        logger.info("--------------- Begin to verify all packages installation of repo %s ---------------" % repo)
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
                    logger.info("It's successful to download source packages.")
                else:
                    if "No Match for argument" in output:
                        checkresult = False
                        error_list = [s for s in output.splitlines() if "No Match" in s]
                        failed_src_pkglist = [error.replace('No Match for argument ', '').replace('\r', '') for error in error_list]
                        logger.error("Failed to download following {0} source packages:".format(len(failed_src_pkglist)))
                        self.print_list(failed_src_pkglist)
            else:
                logger.info("There is no source packages for pid:repo {0}:{1}".format(pid, repo))
        else:
            # Get all packages already installed in testing system before installation testing
            system_pkglist = self.get_sys_pkglist(system_info)

            # Store the failed packages when 'yum remove'.
            remove_failed_pkglist = []

            # Get packages from manifest and distinct them
            pkg_list = self.get_package_list_from_manifest(manifest_xml, pid, repo, arch, release_ver, "name")
            pkg_list = list(set(pkg_list))

            # Print out the package list
            logger.info("Ready to install below {0} rpm packages.".format(len(pkg_list)))
            self.print_list(pkg_list)

            number = 0
            total_number = len(pkg_list)

            for pkg in pkg_list:
                number += 1
                if blacklist == 'Beta':
                    cmd = 'yum install -y --disablerepo=* --enablerepo=*beta* --skip-broken {0} {1}'.format(pkg, releasever_set)
                else:
                    cmd = 'yum install -y --skip-broken {0} {1}'.format(pkg, releasever_set)
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to install package [{0}/{1}] {2} of repo {3}...".format(number, total_number, pkg, repo))

                if ret == 0:
                    if ("Complete!" in output) or ("Nothing to do" in output) or ("conflicts" in output):
                        logger.info("It's successful to install package [{0}/{1}] {2} of repo {3}...".format(number, total_number, pkg, repo))
                    else:
                        logger.error("Test Failed - Failed to install package [{0}/{1}] {2} of repo {3}...".format(number, total_number, pkg, repo))
                        checkresult = False
                else:
                    if ("conflicts" in output):
                        logger.info("It's successful to install package [{0}/{1}] {2} of repo {3}...".format(number, total_number, pkg, repo))
                    else:
                        logger.error("Test Failed - Failed to install package [{0}/{1}] {2} of repo {3}...".format(number, total_number, pkg, repo))
                        checkresult = False

                if checkresult:
                    if pkg not in system_pkglist:
                        # Remove this package if it is not in the system package list.
                        # It is used to solve the dependency issue which describe in https://bugzilla.redhat.com/show_bug.cgi?id=1272902.
                        if not self.remove_pkg(system_info, pkg, repo):
                            remove_failed_pkglist.append(pkg)
                            logging.warning("Failed to remove {0} of repo {1}.".format(pkg, repo))

            if len(remove_failed_pkglist) != 0:
                logger.warning("Failed to remove following {0} packages for repo {1}:".format(len(remove_failed_pkglist), repo))
                self.print_list(remove_failed_pkglist)

        if checkresult:
            logger.info("--------------- End to verify packages full installation of repo {0}: PASS ---------------".format(repo))
        else:
            logger.error("--------------- End to verify packages full installation of repo {0}: FAIL ---------------".format(repo))

        return checkresult